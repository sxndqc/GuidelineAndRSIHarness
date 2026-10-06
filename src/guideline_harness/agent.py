"""Controller-mediated tool agent with immutable test assets and auditable logs."""
from __future__ import annotations
import copy
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from .data import read_json, write_json, digest
from .protocol import AgentView, BudgetLedger, trajectory
from .metrics import score_snacs, score_categorical
from .ontology import SNACS_LABELS
from .codex_model import CodexBackendUnavailable
from .model import ChatModel, CostMeter, BudgetExceeded, QuotaExhausted
from .sandbox import run_python

SYSTEM = '''You annotate according to authorized guidelines and examples. Use tools by emitting ONE JSON object:
{"action": "tool_name", "arguments": {...}}. There is no unrestricted filesystem or network.
Tools (call the native functions when available):
list_materials({})
read_material({"name":str,"start":int,"length":int})
search_materials({"query":str})
read_example({"id":str})
read_examples({"ids":[str,...]}) [read up to16 purchased examples in one call]
search_examples({"query":str,"limit":int}) [lexical retrieval from all purchased examples, returns full input and gold]
write_asset({"name":str,"text":str}) [adaptation only when allowed]
run_program({"script":str,"input":object}) [program condition only; script is the relative name of an existing .py asset, not source code. stdlib Python reads JSON from stdin and prints JSON to stdout]
finish({"prediction": {target_id: [scene_role, lexical_function]}}) [evaluation]
finish({"summary":str}) [adaptation]
Prediction keys must exactly match the given targets. Return labels with their p. prefix.
Guidelines are available through tools and are not injected in full. Do not invent observations or gold labels.
''' + '\nValid labels: '+', '.join(sorted(SNACS_LABELS))

def episode(model, view, instruction, allow_code=False, max_calls=16, system_prompt=None, prediction_kind="pair", prior=None):
    instruction={**instruction,'maximum_model_calls':max_calls,'available_guidelines':sorted(view.materials),'available_assets':sorted(view.assets)}
    if view.assets:
        instruction['asset_instruction']='Read relevant persistent assets before deciding; their contents are available through read_material.'
    messages=[{'role':'system','content':system_prompt or SYSTEM},{'role':'user','content':json.dumps(instruction,ensure_ascii=False)}]
    if prior and prior['status']=='backend_unavailable' and prior.get('backend_reason') not in ('capacity','timeout','legacy_audited_resource'):
        raise CodexBackendUnavailable('Refusing continuation of an unclassified or isolation interruption',prior.get('backend_reason','unknown'))
    trace=copy.deepcopy(prior.get('trace',[])) if prior else []
    if prior:
        view.log=copy.deepcopy(prior.get('tool_log',[]))
        last_action=None
        for entry in trace:
            if 'text' in entry:
                messages.append({'role':'assistant','content':entry['text']})
                try:last_action=json.loads(entry['text'])
                except (ValueError,TypeError):last_action=None
            elif 'tool_result' in entry:
                messages.append({'role':'user','content':json.dumps({'tool_result':entry['tool_result'],'remaining_model_calls':max_calls-entry['step']-1},ensure_ascii=False)})
                if entry.get('tool_name')=='write_asset' and last_action and view.writable:
                    args=last_action['arguments'];view.assets[entry['tool_result']['written']]=args['text']
            elif 'tool_or_schema_error' in entry:messages.append({'role':'user','content':json.dumps({'error':entry['tool_or_schema_error'],'remaining_model_calls':max_calls-entry['step']-1})})
    if prior and prior['status'] not in ('backend_unavailable','cost_budget_exhausted'):return copy.deepcopy(prior)
    start_step=max((e['step'] for e in trace),default=-1)+1
    for step in range(start_step,max_calls):
        started=time.monotonic()
        try:
            response=model.complete(messages)
            trace.append({'step':step,**response})
            if response.get('finish_reason') == 'content_filter':
                return {'status':'cached_terminal_skip' if response.get('previously_recorded_refusal') else 'refused','trace':trace,'tool_log':view.log}
            if response.get('finish_reason') == 'length':
                return {'status':'truncated','trace':trace,'tool_log':view.log}
            if not isinstance(response.get('text'), str):
                raise ValueError('Model response must contain text')
            text=response['text'].strip()
            if text.startswith('```'):
                text=text.split('\n',1)[1].rsplit('```',1)[0].strip()
            messages.append({'role':'assistant','content':response['text']})
            action=json.loads(text)
            if not isinstance(action, dict) or not isinstance(action.get('action'), str):
                raise ValueError('Action must be an object with a string action')
            name,args=action['action'],action.get('arguments',{})
            if not isinstance(args, dict):
                raise ValueError('Tool arguments must be an object')
            if name=='finish':
                if instruction.get('phase') == 'evaluate':
                    pred=args.get('prediction')
                    if not isinstance(pred,dict) or (prediction_kind=='pair' and any(not isinstance(v,list) or len(v)!=2 or not all(isinstance(x,str) for x in v) for v in pred.values())) or (prediction_kind=='category' and any(not isinstance(v,str) for v in pred.values())):
                        raise ValueError('Finish requires a prediction object with '+('two-string label arrays' if prediction_kind=='pair' else 'string labels'))
                return {'status':'completed','answer':args,'trace':trace,'tool_log':view.log}
            if name=='run_program':
                if not allow_code: raise ValueError('Program tool is not enabled for this condition')
                output=run_python(view.assets,args['script'],args['input'])
                view.log.append({'tool':name,'arguments':args,'result':output})
            else:
                output=view.call(name,args)
            trace.append({'step':step,'tool_name':name,'tool_result':output})
            messages.append({'role':'user','content':json.dumps({'tool_result':output,'remaining_model_calls':max_calls-step-1},ensure_ascii=False)})
        except CodexBackendUnavailable as exc:
            return {'status':'backend_unavailable','trace':trace,'tool_log':view.log,'backend_reason':exc.reason,'backend_ledger_index':exc.ledger_index}
        except QuotaExhausted as exc:
            return {'status':'quota_exhausted','trace':trace,'tool_log':view.log,'http_status':exc.status,'provider_code':exc.provider_code}
        except BudgetExceeded:
            return {'status':'cost_budget_exhausted','trace':trace,'tool_log':view.log}
        except (ValueError,KeyError,TypeError) as exc:
            # Schema/tool errors are feedback, never gold-dependent feedback.
            error=f'{type(exc).__name__}: {exc}'
            trace.append({'step':step,'tool_or_schema_error':error})
            messages.append({'role':'user','content':json.dumps({'error':error,'remaining_model_calls':max_calls-step-1})})
        except Exception as exc:
            # Do not emit exception body: provider errors may echo credential headers.
            trace.append({'step':step,'provider_or_runtime_error':type(exc).__name__,
                          'latency_seconds':time.monotonic()-started,'http_status':getattr(exc,'status',None),'provider_code':getattr(exc,'provider_code',None)})
            return {'status':'failed','trace':trace,'tool_log':view.log,'error_type':type(exc).__name__}
    return {'status':'tool_budget_exhausted','trace':trace,'tool_log':view.log}

def pack_batches(records, groups_per_batch):
    if not isinstance(groups_per_batch,int) or groups_per_batch<0:raise ValueError('groups_per_batch must be a nonnegative integer')
    if not groups_per_batch:return records
    groups={}
    for row in records:groups.setdefault(row['group'],[]).append(row)
    keys=list(groups);batches=[]
    for start in range(0,len(keys),groups_per_batch):
        rows=[r for key in keys[start:start+groups_per_batch] for r in groups[key]]
        sentences=[];targets=[]
        for row in rows:
            value=copy.deepcopy(row['input'])
            value['id']=row['id']
            for t in value['targets']:t['id']=row['id']+'::'+t['id']
            sentences.append(value);targets.extend(value['targets'])
        batches.append({'id':f'batch{start//groups_per_batch:03d}','input':{'instances':sentences,'targets':targets},'_rows':rows})
    return batches



def archive_interruption(out,name,value):
    path=out/'resource-interruptions'/(Path(name).stem+'-'+digest(value)[:12]+'.json')
    if not path.exists():write_json(path,value)

def moderate(model,materials,visible,assets,system,kind,config,out,prefix):
    """One bounded error-guided addendum update, accepted only on adaptation gain.

    Adapted comparator, not full-handbook rewrite or numeric reproduction of Kim
    et al. Gold is controller feedback from purchased rows, never test labels.
    """
    rows=list(visible.values())
    if config.get('moderation_groups_per_batch',16)<1:raise ValueError('Moderation requires positive batch size')
    allowed=SNACS_LABELS if kind=='pair' else set(read_json(config['materials_manifest'])['labels'])
    def probe(state,stage):
        results={};episodes=[];valid=True
        saved=out/'episodes'/f'{prefix}-moderation-{stage}.json'
        previous=read_json(saved) if config.get('resume') and saved.exists() else []
        if previous:archive_interruption(out,saved.name,previous)
        for index,batch in enumerate(pack_batches(rows,config.get('moderation_groups_per_batch',16))):
            view=AgentView(materials,{},state,writable=False)
            result=episode(model,view,{'phase':'evaluate','input':batch['input'],'inline_guidelines':materials,'inline_assets':state,'instruction':'All current original guidelines and persistent assets are included. Predict adaptation labels and call finish directly. No labeled examples are accessible in this probe.'},max_calls=config.get('moderation_probe_calls',2),system_prompt=system,prediction_kind=kind,prior=previous[index] if index<len(previous) else None)
            episodes.append(result)
            write_json(out/'episodes'/f'{prefix}-moderation-{stage}.json',episodes)
            if result['status'] in ('backend_unavailable','cost_budget_exhausted','quota_exhausted'):raise BudgetExceeded('Moderation probe backend stopped')
            answer=result.get('answer',{}).get('prediction',{})
            expected={t['id'] for t in batch['input']['targets']}
            valid=valid and result['status']=='completed' and set(answer)==expected and all((isinstance(v,list) and len(v)==2 and all(x in allowed for x in v)) if kind=='pair' else (isinstance(v,str) and v in allowed) for v in answer.values())
            for row in batch['_rows']:
                results[row['id']]={k:answer.get(row['id']+'::'+k) for k in row['gold']}
        write_json(out/'episodes'/f'{prefix}-moderation-{stage}.json',episodes)
        correct=sum(results[r['id']].get(k)==v for r in rows for k,v in r['gold'].items())
        return results,correct,valid
    before,baseline,valid_before=probe(assets,'before')
    if not valid_before:
        write_json(out/'moderation'/f'{prefix}.json',{'accepted':False,'reason':'before_probe_invalid'})
        return copy.deepcopy(assets)
    errors={};correct=[]
    for row in rows:
        for target,gold in row['gold'].items():
            item={'input':row['input'],'target':target,'prediction':before[row['id']].get(target),'gold':gold}
            if item['prediction']==gold:correct.append(item)
            else:errors.setdefault(json.dumps([item['prediction'],gold],sort_keys=True),[]).append(item)
    if not errors:
        write_json(out/'moderation'/f'{prefix}.json',{'before_correct':baseline,'accepted':False,'reason':'no adaptation errors'})
        return copy.deepcopy(assets)
    selected=sorted(errors.items(),key=lambda x:(-len(x[1]),x[0]))[0][1][:5]
    base_instruction={'phase':'adapt','errors':selected,'correct_contrasts':correct[:5],'example_ids':list(visible)}
    view=AgentView(materials,visible,assets,writable=True)
    for stage,instruction,required_asset in [
      ('pattern','Compare the observed error examples with correct contrasts. Consult relevant original rules. Write error-pattern.md explaining the shared decision boundary and remaining uncertainty. Do not invent extra labeled cases.','error-pattern.md'),
      ('principle','Read error-pattern.md. Derive an IF/THEN annotation principle with explicit applicability conditions and negative constraints. Write candidate-principle.md. Ground it in the supplied evidence and original guideline.','candidate-principle.md'),
      ('update','Read the pattern and candidate principle. Revise policy-addendum.md with a concise reusable rule, preserving justified prior rules. This is an addendum to the original handbook, not a full rewrite. The controller will accept it only if adaptation accuracy improves.','policy-addendum.md')]:
        saved=out/'episodes'/f'{prefix}-moderation-{stage}.json'
        previous=read_json(saved) if config.get('resume') and saved.exists() else None
        if previous:archive_interruption(out,saved.name,previous)
        result=episode(model,view,{**base_instruction,'instruction':instruction},max_calls=config.get('moderation_stage_calls',8),system_prompt=system,prediction_kind=kind,prior=previous)
        write_json(out/'episodes'/f'{prefix}-moderation-{stage}.json',result)
        if result['status'] in ('backend_unavailable','cost_budget_exhausted','quota_exhausted'):raise BudgetExceeded('Moderation update backend stopped')
        if result['status']!='completed' or not view.assets.get(required_asset):
            write_json(out/'moderation'/f'{prefix}.json',{'accepted':False,'reason':'incomplete_stage','stage':stage})
            return copy.deepcopy(assets)
    candidate=copy.deepcopy(assets)
    if 'policy-addendum.md' in view.assets:candidate['policy-addendum.md']=view.assets['policy-addendum.md']
    if candidate==assets:
        write_json(out/'moderation'/f'{prefix}.json',{'accepted':False,'reason':'no_change'})
        return copy.deepcopy(assets)
    after,updated,valid_after=probe(candidate,'after')
    accepted=valid_after and updated>baseline
    write_json(out/'moderation'/f'{prefix}.json',{'before_correct':baseline,'after_correct':updated,'decisions':sum(len(r['gold']) for r in rows),'accepted':accepted,'after_probe_valid':valid_after,'selected_error_count':len(selected),'correct_contrast_count':len(correct[:5]),'update_unit':'one three-stage addendum proposal per budget; strict improvement rollback','candidate_assets_sha256':digest(candidate)})
    return candidate if accepted else copy.deepcopy(assets)

def run_agent(config_path):
    config=read_json(config_path)
    out=Path(config['output'])
    resume=config.get('resume',False)
    exists=out.exists() and any(out.iterdir())
    if exists and not resume:raise ValueError('Use a fresh output directory or explicit resource-only resume')
    if resume and exists:
        previous=read_json(out/'config.json')
        permitted={'resume','subscription_call_limit','workers'}
        if {k:v for k,v in previous.items() if k not in permitted}!={k:v for k,v in config.items() if k not in permitted}:raise ValueError('Resume may only change resource ceiling, not experimental settings')
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
    if config.get('backend')=='codex_cli':
        from .codex_model import CodexModel
        model=CodexModel(config['model'],reasoning_effort=config.get('reasoning_effort','medium'),ledger=config['subscription_ledger'],max_calls=config.get('subscription_call_limit',4096))
    else:
        model=ChatModel(config['model'],base_url=config.get('base_url'),key_env=config.get('key_env','ANNOTATION_API_KEY'),
                        max_tokens=config.get('max_completion_tokens',2000),reasoning_effort=config.get('reasoning_effort'),
                        meter=CostMeter(config['cost_ledger'],config['cost_ceiling_usd'],config.get('input_rate_ceiling',10),config.get('output_rate_ceiling',40)),native_tools=config.get('native_tools',True))
    task=config.get('task','snacs')
    if task not in ('snacs','cap_pa'):raise ValueError('Unknown task')
    if task!='snacs' and config.get('backend')!='codex_cli':raise ValueError('Categorical tasks currently require Codex controlled-action backend')
    kind='pair' if task=='snacs' else 'category'
    system=SYSTEM
    labels=set(manifest.get('labels',[]))
    if kind=='category':
        if not labels:raise ValueError('Empty category inventory')
        system=SYSTEM.split("\nValid labels:")[0].replace('finish({"prediction": {target_id: [scene_role, lexical_function]}})', 'finish({"prediction": {target_id: "policy code string"}})').replace('Return labels with their p. prefix.','Return PA policy codes as strings. This task reproduces project-published codes from bill summaries, not full legislative documents.')+'\nValid policy codes: '+', '.join(sorted(labels))
    def score(records,predictions):
        return score_snacs(records,predictions) if task=='snacs' else score_categorical(records,predictions,labels)
    root=Path(config['data_root']);split=config.get('evaluation_split','dev')
    if split not in ('dev','test'): raise ValueError('Invalid evaluation split')
    train=read_json(root/'private/train.json')
    evaluation=read_json(root/f'private/{split}.json')
    if config.get('exclude_evaluation_ids_file'):
        old=set(read_json(config['exclude_evaluation_ids_file']))
        excluded={r['group'] for r in evaluation if r['id'] in old}
        evaluation=[r for r in evaluation if r['group'] not in excluded]
    if config.get('evaluation_group_limit'):
        keys=trajectory(sorted({r['group'] for r in evaluation}),config['evaluation_seed'])[:config['evaluation_group_limit']]
        index={k:i for i,k in enumerate(keys)}
        evaluation=sorted([r for r in evaluation if r['group'] in index],key=lambda r:(index[r['group']],r['id']))
    if config.get('evaluation_limit'):
        evaluation=trajectory(evaluation,config['evaluation_seed'])[:config['evaluation_limit']]
    if not evaluation:raise ValueError('Empty evaluation set')
    batches=pack_batches(evaluation,config.get('groups_per_batch',0))
    def preserve(name,value):
        path=out/name
        if exists and path.exists():
            if read_json(path)!=value:raise ValueError('Resume input snapshot changed: '+name)
        else:write_json(path,value)
    preserve('batches.json',[{'id':b['id'],'record_ids':[r['id'] for r in b.get('_rows',[b])]} for b in batches])
    if not exists:write_json(out/'config.json',config)
    else:write_json(out/'resume-config.json',config)
    preserve('evaluation-ids.json',[r['id'] for r in evaluation])
    write_json(out/('resume-implementation-hashes.json' if exists else 'implementation-hashes.json'),{p.name:digest(p.read_text()) for p in Path(__file__).parent.glob('*.py')})
    preserve('materials-manifest.json',manifest)
    if (root/'manifest.json').exists():preserve('data-manifest.json',read_json(root/'manifest.json'))
    integrity={'train_sha256':digest(train),'evaluation_split_sha256':digest(read_json(root/f'private/{split}.json'))}
    preserve('data-content-hashes.json',integrity)
    if exists and not (out/'data-hash-provenance.json').exists():write_json(out/'data-hash-provenance.json',{'note':'Content hashes first captured on continuation for legacy runs; original source/material manifests and IDs were captured at initial execution.'})
    results=read_json(out/'results.json').get('results',[]) if exists and (out/'results.json').exists() else []
    completed={(r['condition'],r['seed'],r['budget']) for r in results}
    budgets=config['budgets']
    if budgets!=sorted(set(budgets)) or any(b<0 or b>len(train) for b in budgets):
        raise ValueError('Budgets must be strictly increasing, within the adaptation pool')
    for seed in config['seeds']:
        order=trajectory(train,seed)
        if config.get('unique_training_groups'):
            seen=set();order=[r for r in order if not (r['group'] in seen or seen.add(r['group']))]
        if max(budgets)>len(order):raise ValueError('Budget exceeds unique adaptation groups')
        for condition in config['conditions']:
            if condition not in ('frozen','notes','notes_program','static','moderation'): raise ValueError('Unknown condition')
            assets={}
            ledger=BudgetLedger(max(budgets))
            for budget in budgets:
                if budget==0 and (seed!=config['seeds'][0] or condition in ('notes','notes_program','moderation')):
                    continue
                ledger.limit=budget
                for record in order[:budget]:
                    if record['id'] not in ledger.revealed: ledger.reveal(record)
                visible={r['id']:r for r in order[:budget]}
                prefix=f'{condition}-s{seed}-b{budget}'
                if (condition,seed,budget) in completed:
                    assets=read_json(out/'assets'/f'{prefix}.json')
                    continue
                saved_assets=out/'assets'/f'{prefix}.json'
                if resume and saved_assets.exists():
                    assets=read_json(saved_assets)
                elif condition=='moderation':
                    assets=moderate(model,materials,visible,assets,system,kind,config,out,prefix)
                elif condition not in ('frozen','static'):
                    view=AgentView(materials,visible,assets,writable=True)
                    saved=out/'episodes'/f'{prefix}-adapt.json'
                    previous=read_json(saved) if resume and saved.exists() else None
                    if previous:archive_interruption(out,saved.name,previous)
                    adapted=episode(model,view,{'phase':'adapt','new_total_budget':budget,
                        'example_ids':list(visible),'instruction':'Review the authorized guidelines and these purchased examples. Persist useful general rules and exceptions as assets. '+('You may write executable Python.' if condition=='notes_program' else 'Program execution is unavailable.')},
                        allow_code=condition=='notes_program',max_calls=config.get('adapt_calls',24),system_prompt=system,prediction_kind=kind,prior=previous)
                    write_json(out/'episodes'/f'{prefix}-adapt.json',adapted)
                    if adapted['status'] in ('cost_budget_exhausted','quota_exhausted','backend_unavailable'):
                        write_json(out/'results.json',{'status':adapted['status'],'results':results})
                        raise BudgetExceeded('Stopped with partial adaptation trace saved')
                    # Retain partial assets on unsuccessful episodes; do not select winning runs.
                    assets=copy.deepcopy(view.assets)
                frozen_hash=digest(assets)
                write_json(out/'assets'/f'{prefix}.json',assets)
                predictions={};statuses=[];completed_records=0
                def evaluate_one(record):
                    saved_episode=out/'episodes'/f'{prefix}-{record["id"]}.json'
                    prior=None
                    if resume and saved_episode.exists():
                        previous_episode=read_json(saved_episode)
                        if previous_episode['status'] not in ('cost_budget_exhausted','backend_unavailable'):return record,previous_episode
                        archive_interruption(out,saved_episode.name,previous_episode)
                        prior=previous_episode
                    view=AgentView(materials,visible,assets,writable=False)
                    instruction={'phase':'evaluate','id':record['id'],'input':record['input'],
                        'example_ids':list(visible),'instruction':'Annotate this instance. Persistent state is frozen.'}
                    if condition=='static':
                        instruction.update(inline_guidelines=materials,inline_examples=list(visible.values()),
                            instruction='All guidelines and purchased examples are included below. Use them and call finish with your prediction directly.')
                    result=episode(model,view,instruction,
                        allow_code=condition=='notes_program',max_calls=config.get('predict_calls',12),system_prompt=system,prediction_kind=kind,prior=prior)
                    if digest(view.assets)!=frozen_hash: raise AssertionError('Evaluation mutated assets')
                    write_json(out/'episodes'/f'{prefix}-{record["id"]}.json',result)
                    return record,result
                with ThreadPoolExecutor(max_workers=config.get('workers',1)) as pool:
                    for record,result in pool.map(evaluate_one,batches):
                        statuses.append(result['status'])
                        if result['status']=='completed':completed_records+=len(record.get('_rows',[record]))
                        prediction=result.get('answer',{}).get('prediction',{})
                        if '_rows' not in record:
                            predictions[record['id']]=prediction
                        else:
                            known={r['id']+'::'+key for r in record['_rows'] for key in r['gold']}
                            for row in record['_rows']:
                                predictions[row['id']]={key:prediction[row['id']+'::'+key] for key in row['gold'] if row['id']+'::'+key in prediction}
                                if set(prediction)-known:predictions[row['id']]['__unexpected_batch_target__']=None
                if any(x in statuses for x in ('cost_budget_exhausted','quota_exhausted','backend_unavailable')):
                    write_json(out/'predictions'/f'{prefix}-partial.json',predictions)
                    write_json(out/'results.json',{'status':'backend_unavailable' if 'backend_unavailable' in statuses else ('quota_exhausted' if 'quota_exhausted' in statuses else 'cost_budget_exhausted'),'results':results})
                    raise BudgetExceeded('Stopped with partial traces saved')
                summary={'condition':condition,'seed':seed,'budget':budget,'model':config['model'],
                    'supervision':ledger.summary(),'asset_sha256':frozen_hash,'prediction_sha256':digest(predictions),
                    'metrics':score(evaluation,predictions),'evaluation_batches':len(batches),'completed_batches':statuses.count('completed'),'completed_instances':completed_records,
                    'failed_or_exhausted_batches':len(statuses)-statuses.count('completed'),'failed_or_exhausted_instances':len(evaluation)-completed_records}
                results.append(summary)
                write_json(out/'predictions'/f'{prefix}.json',predictions)
                write_json(out/'ledgers'/f'{prefix}.json',ledger.events)
                write_json(out/'results.json',{'status':'running','results':results})
    report={'status':'completed','results':results,'scope':task+' supplied-target track',
            'warning':'Do not call these from-scratch sample-complexity estimates; pretraining exposure is unknown.'}
    write_json(out/'results.json',report)
    return report
