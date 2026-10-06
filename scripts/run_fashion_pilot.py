"""Real image/tool pilot. Only selected train regions are exposed to the agent."""
import argparse,base64,copy,json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from guideline_harness.model import ChatModel,CostMeter,BudgetExceeded
from guideline_harness.protocol import AgentView,trajectory
from guideline_harness.data import write_json,digest
ROOT=Path('data/prepared/fashion-pilot')
SYSTEM='''You annotate Fashionpedia given-box crops. The red outline identifies the target. This is a name/hierarchy taxonomy, not a complete annotation handbook. Use native tools to read_material, search_materials, read_example, search_examples, list_materials. write_asset is allowed only during adaptation. Program execution is unavailable. At evaluation finish with prediction {"region":["category ID as decimal string","comma-separated attribute IDs, or empty string"]}. Predict against the supplied inventory; do not invent IDs. During adaptation finish with summary. Purchased example images and gold may be read through read_example. During evaluation persistent notes are frozen. Read available notes before deciding.'''

def block(text,image=None):
    content=[{'type':'text','text':json.dumps(text,ensure_ascii=False)}]
    if image:
        content.append({'type':'image_url','image_url':{'url':'data:image/jpeg;base64,'+base64.b64encode(Path(image).read_bytes()).decode(),'detail':'high'}})
    return content

def episode(model,view,instruction,max_calls,categories):
    instruction={**instruction,'guidelines':list(view.materials),'assets':list(view.assets),'example_ids':list(view.examples),'category_inventory':categories}
    image=instruction.get('input',{}).get('image')
    messages=[{'role':'system','content':SYSTEM},{'role':'user','content':block(instruction,image)}]
    trace=[]
    for step in range(max_calls):
        try:
            response=model.complete(messages);trace.append({'step':step,**response})
            if response['finish_reason']=='length':return {'status':'truncated','trace':trace}
            action=json.loads(response['text']);messages.append({'role':'assistant','content':response['text']})
            name,args=action['action'],action.get('arguments',{})
            if name=='finish':
                return {'status':'completed','answer':args,'trace':trace,'tool_log':view.log}
            output=view.call(name,args)
            picture=output.get('input',{}).get('image') if isinstance(output,dict) else None
            trace.append({'step':step,'tool':name,'output':output})
            # Search returns records, but image viewing requires read_example; never inject unrelated gold.
            messages.append({'role':'user','content':block({'result':output,'remaining_calls':max_calls-step-1},picture)})
        except BudgetExceeded:
            return {'status':'cost_budget_exhausted','trace':trace,'tool_log':view.log}
        except (ValueError,KeyError,TypeError) as e:
            messages.append({'role':'user','content':json.dumps({'schema_or_tool_error':str(e)})})
            trace.append({'step':step,'error_type':type(e).__name__})
        except Exception as e:
            return {'status':'failed','trace':trace,'error_type':type(e).__name__,'http_status':getattr(e,'code',None)}
    return {'status':'tool_budget_exhausted','trace':trace,'tool_log':view.log}

def score(rows,predictions,category_ids,attribute_ids):
    correct=valid=tp=fp=fn=empty=0
    for row in rows:
        pred=predictions.get(row['id'],{})
        pair=pred.get('region') if isinstance(pred,dict) else None
        category=None;attrs=set();ok=False
        try:
            category=int(pair[0]);attrs=set(map(int,pair[1].split(','))) if pair[1].strip() else set()
            ok=category in category_ids and attrs.issubset(attribute_ids)
        except (ValueError,TypeError,IndexError,AttributeError):pass
        goldcat=int(row['gold']['region'][0]);goldattrs=set(map(int,row['gold']['region'][1].split(','))) if row['gold']['region'][1] else set()
        valid+=ok;correct+=bool(category in category_ids and category==goldcat)
        tp+=len(attrs & goldattrs);fp+=len(attrs-goldattrs);fn+=len(goldattrs-attrs);empty+=not goldattrs
    return {'instances':len(rows),'category_accuracy':correct/len(rows),'valid_output_rate':valid/len(rows),
            'published_attribute_micro_f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
            'attribute_tp':tp,'attribute_fp':fp,'attribute_fn':fn,'empty_gold_instances':empty,
            'warning':'Agreement with published annotation; unlisted attributes are not certified semantic negatives. Not official AP.'}

def main(config):
    out=Path(config['output'])
    if out.exists():raise ValueError('Fresh output required')
    train=trajectory(json.loads((ROOT/'train.json').read_text()),11)
    evaluation=json.loads((ROOT/'val.json').read_text())
    source=json.loads(Path('data/raw/fashionpedia/val.json').read_text())
    categories={str(x['id']):x['name'] for x in source['categories']}
    taxonomy='Official category and attribute names and supercategories. No unstated manual is implied.\n'
    for kind in ['categories','attributes']:
        taxonomy+=kind+'\n'+'\n'.join(f"{x['id']}: {x['name']} [{x['supercategory']}]" for x in source[kind])+'\n'
    materials={'fashionpedia-taxonomy.txt':taxonomy}
    model=ChatModel(config['model'],base_url='https://api.openai.com/v1',key_env='openai',max_tokens=1800,
                    reasoning_effort='none',native_tools=True,meter=CostMeter('results/api-research-cost-ledger.json',config.get('cost_ceiling_usd',25),config['input_rate'],config['output_rate']))
    write_json(out/'config.json',config);write_json(out/'selection.json',json.loads((ROOT/'selection.json').read_text()))
    write_json(out/'implementation.json',{'script_sha256':digest(Path(__file__).read_text()),'taxonomy_sha256':digest(taxonomy)})
    results=[]
    for condition in ['frozen','notes']:
        assets={}
        for budget in [0,4,16]:
            if budget==0 and condition=='notes':continue
            visible={r['id']:r for r in train[:budget]}
            prefix=f'{condition}-s11-b{budget}'
            if condition=='notes':
                view=AgentView(materials,visible,assets,writable=True)
                r=episode(model,view,{'phase':'adapt','instruction':'Study these purchased example crops and labels. Write reusable annotation notes, especially confusions and exceptions.'},24,categories)
                write_json(out/'episodes'/f'{prefix}-adapt.json',r)
                if r['status']=='cost_budget_exhausted':raise BudgetExceeded('Fashion adaptation budget exhausted')
                assets=copy.deepcopy(view.assets)
            frozen=digest(assets);write_json(out/'assets'/f'{prefix}.json',assets)
            def one(row):
                view=AgentView(materials,visible,assets,writable=False)
                r=episode(model,view,{'phase':'evaluate','input':row['input'],'instruction':'Classify this marked region. Do not update notes.'},8,categories)
                assert digest(view.assets)==frozen
                write_json(out/'episodes'/f'{prefix}-{row["id"]}.json',r)
                return row['id'],r
            with ThreadPoolExecutor(4) as pool:answers=list(pool.map(one,evaluation))
            predictions={ident:r.get('answer',{}).get('prediction',{}) for ident,r in answers}
            write_json(out/'predictions'/f'{prefix}.json',predictions)
            if any(r['status']=='cost_budget_exhausted' for _,r in answers):raise BudgetExceeded('Fashion prediction budget exhausted')
            result={'condition':condition,'budget':budget,'seed':11,'model':config['model'],'metrics':score(evaluation,predictions,{x['id'] for x in source['categories']},{x['id'] for x in source['attributes']}),'asset_sha256':frozen,'completed_instances':sum(r['status']=='completed' for _,r in answers)}
            results.append(result);write_json(out/'results.json',{'status':'running','results':results})
    write_json(out/'results.json',{'status':'completed','results':results})
    print(json.dumps({'output':str(out),'results':results}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('config');args=parser.parse_args()
    main(json.loads(Path(args.config).read_text()))
