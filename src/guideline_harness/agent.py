"""Controller-mediated tool agent with immutable test assets and auditable logs."""
from __future__ import annotations
import copy
import json
import time
from pathlib import Path
from .data import read_json, write_json, digest
from .protocol import AgentView, BudgetLedger, trajectory
from .metrics import score_snacs
from .model import ChatModel
from .sandbox import run_python

SYSTEM = '''You annotate according to authorized guidelines and examples. Use tools by emitting ONE JSON object:
{"action": "tool_name", "arguments": {...}}. There is no unrestricted filesystem or network.
Tools:
list_materials({})
read_material({"name":str,"start":int,"length":int})
search_materials({"query":str})
read_example({"id":str})
write_asset({"name":str,"text":str}) [adaptation only when allowed]
run_program({"script":str,"input":object}) [program condition only; stdlib Python, JSON stdin, stdout]
finish({"prediction": {target_id: [scene_role, lexical_function]}}) [evaluation]
finish({"summary":str}) [adaptation]
Prediction keys must exactly match the given targets. Return labels with their p. prefix.
Guidelines are available through tools and are not injected in full. Do not invent observations or gold labels.
'''

def episode(model, view, instruction, allow_code=False, max_calls=16):
    messages=[{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps(instruction,ensure_ascii=False)}]
    trace=[]
    for step in range(max_calls):
        started=time.monotonic()
        try:
            response=model.complete(messages)
            trace.append({'step':step,**response})
            if response.get('finish_reason') == 'length':
                return {'status':'truncated','trace':trace,'tool_log':view.log}
            if not isinstance(response.get('text'), str):
                raise ValueError('Model response must contain text')
            text=response['text'].strip()
            if text.startswith('```'):
                text=text.split('\n',1)[1].rsplit('```',1)[0].strip()
            action=json.loads(text)
            if not isinstance(action, dict) or not isinstance(action.get('action'), str):
                raise ValueError('Action must be an object with a string action')
            name,args=action['action'],action.get('arguments',{})
            if not isinstance(args, dict):
                raise ValueError('Tool arguments must be an object')
            messages.append({'role':'assistant','content':response['text']})
            if name=='finish':
                if instruction.get('phase') == 'evaluate':
                    pred=args.get('prediction')
                    if not isinstance(pred,dict) or any(not isinstance(v,list) or len(v)!=2 or not all(isinstance(x,str) for x in v) for v in pred.values()):
                        raise ValueError('Finish requires a prediction object of two-string label arrays')
                return {'status':'completed','answer':args,'trace':trace,'tool_log':view.log}
            if name=='run_program':
                if not allow_code: raise ValueError('Program tool is not enabled for this condition')
                output=run_python(view.assets,args['script'],args['input'])
                view.log.append({'tool':name,'arguments':args,'result':output})
            else:
                output=view.call(name,args)
            messages.append({'role':'user','content':json.dumps({'tool_result':output},ensure_ascii=False)})
        except (ValueError,KeyError,TypeError) as exc:
            # Schema/tool errors are feedback, never gold-dependent feedback.
            error=f'{type(exc).__name__}: {exc}'
            trace.append({'step':step,'tool_or_schema_error':error})
            messages.append({'role':'user','content':json.dumps({'error':error})})
        except Exception as exc:
            # Do not emit exception body: provider errors may echo credential headers.
            trace.append({'step':step,'provider_or_runtime_error':type(exc).__name__,
                          'latency_seconds':time.monotonic()-started})
            return {'status':'failed','trace':trace,'tool_log':view.log,'error_type':type(exc).__name__}
    return {'status':'tool_budget_exhausted','trace':trace,'tool_log':view.log}

def run_agent(config_path):
    config=read_json(config_path)
    out=Path(config['output'])
    if out.exists() and any(out.iterdir()): raise ValueError('Use a fresh output directory; never overwrite a run')
    # No artificial mini-guide quietly substituted for a real annotation handbook.
    manifest=read_json(config['materials_manifest'])
    if manifest.get('status')!='audited':
        raise RuntimeError('Guideline materials have not passed version/example/license audit')
    materials={}
    for entry in manifest['files']:
        contents=Path(entry['path']).read_text()
        import hashlib
        if hashlib.sha256(contents.encode()).hexdigest()!=entry['sha256']:
            raise ValueError('Guideline checksum mismatch')
        materials[entry['name']]=contents
    model=ChatModel(config['model'],base_url=config.get('base_url'),key_env=config.get('key_env','ANNOTATION_API_KEY'),
                    max_tokens=config.get('max_completion_tokens',2000))
    root=Path(config['data_root']);split=config.get('evaluation_split','dev')
    if split not in ('dev','test'): raise ValueError('Invalid evaluation split')
    train=read_json(root/'private/train.json')
    evaluation=read_json(root/f'private/{split}.json')
    if config.get('evaluation_limit'):
        evaluation=evaluation[:config['evaluation_limit']]
    write_json(out/'config.json',config)
    write_json(out/'materials-manifest.json',manifest)
    results=[]
    budgets=config['budgets']
    if budgets!=sorted(set(budgets)) or any(b<0 or b>len(train) for b in budgets):
        raise ValueError('Budgets must be strictly increasing, within the adaptation pool')
    for seed in config['seeds']:
        order=trajectory(train,seed)
        for condition in config['conditions']:
            if condition not in ('frozen','notes','notes_program'): raise ValueError('Unknown condition')
            assets={}
            ledger=BudgetLedger(max(budgets))
            for budget in budgets:
                ledger.limit=budget
                for record in order[:budget]:
                    if record['id'] not in ledger.revealed: ledger.reveal(record)
                visible={r['id']:r for r in order[:budget]}
                prefix=f'{condition}-s{seed}-b{budget}'
                if condition!='frozen':
                    view=AgentView(materials,visible,assets,writable=True)
                    adapted=episode(model,view,{'phase':'adapt','new_total_budget':budget,
                        'example_ids':list(visible),'instruction':'Review the authorized guidelines and these purchased examples. Persist useful general rules and exceptions as assets. '+('You may write executable Python.' if condition=='notes_program' else 'Program execution is unavailable.')},
                        allow_code=condition=='notes_program',max_calls=config.get('adapt_calls',24))
                    write_json(out/'episodes'/f'{prefix}-adapt.json',adapted)
                    # Retain partial assets on unsuccessful episodes; do not select winning runs.
                    assets=copy.deepcopy(view.assets)
                frozen_hash=digest(assets)
                write_json(out/'assets'/f'{prefix}.json',assets)
                predictions={};statuses=[]
                for record in evaluation:
                    view=AgentView(materials,visible,assets,writable=False)
                    result=episode(model,view,{'phase':'evaluate','id':record['id'],'input':record['input'],
                        'example_ids':list(visible),'instruction':'Annotate this instance. Persistent state is frozen.'},
                        allow_code=condition=='notes_program',max_calls=config.get('predict_calls',12))
                    statuses.append(result['status'])
                    predictions[record['id']]=result.get('answer',{}).get('prediction',{})
                    if digest(view.assets)!=frozen_hash: raise AssertionError('Evaluation mutated assets')
                    write_json(out/'episodes'/f'{prefix}-{record["id"]}.json',result)
                summary={'condition':condition,'seed':seed,'budget':budget,'model':config['model'],
                    'supervision':ledger.summary(),'asset_sha256':frozen_hash,'prediction_sha256':digest(predictions),
                    'metrics':score_snacs(evaluation,predictions),'completed_instances':statuses.count('completed'),
                    'failed_or_exhausted_instances':len(statuses)-statuses.count('completed')}
                results.append(summary)
                write_json(out/'predictions'/f'{prefix}.json',predictions)
                write_json(out/'ledgers'/f'{prefix}.json',ledger.events)
                write_json(out/'results.json',{'status':'running','results':results})
    report={'status':'completed','results':results,'scope':'SNACS given-target track',
            'warning':'Do not call these from-scratch sample-complexity estimates; pretraining exposure is unknown.'}
    write_json(out/'results.json',report)
    return report
