"""Summarize every completed registered cell; retain explicit incomplete status.
Paired resampling uses adaptation seeds and evaluation batches, not target IID.
"""
import json,hashlib
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from guideline_harness.metrics import score_snacs,score_categorical
from guideline_harness.protocol import trajectory
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def main():
    summary={'scope':'Frozen Codex CLI-system study; additional supervision, not from-scratch learning','runs':[],'aggregates':[],'paired_effects':[],'uncertainty':'Descriptive 95% percentile bootstrap over paired adaptation seeds and fixed evaluation batches; three seeds and sixteen batches limit calibration. No multiple-comparison correction or universal sufficiency claim.'}
    for directory in sorted((ROOT/'results').glob('codex-study-*')):
        if not (directory/'config.json').exists():continue
        cfg=read(directory/'config.json');task=cfg['task'];metric='joint_accuracy' if task=='snacs' else 'accuracy'
        data=ROOT/cfg['data_root'];rows={r['id']:r for r in read(data/f'private/{cfg["evaluation_split"]}.json')}
        evaluation=[rows[i] for i in read(directory/'evaluation-ids.json')];batches=read(directory/'batches.json')
        train=read(data/'private/train.json');labelset=set(read(ROOT/cfg['materials_manifest']).get('labels',[]))
        report=read(directory/'results.json') if (directory/'results.json').exists() else {'status':'running','results':[]}
        cells=[];arrays={};counts=np.array([sum(len(rows[i]['gold']) for i in b['record_ids']) for b in batches])
        for cell in report['results']:
            condition,seed,budget=cell['condition'],cell['seed'],cell['budget'];tag=f'{condition}-s{seed}-b{budget}'
            pred=read(directory/'predictions'/f'{tag}.json')
            measured=score_snacs(evaluation,pred) if task=='snacs' else score_categorical(evaluation,pred,labelset)
            for key,v in cell['metrics'].items():assert np.isclose(measured[key],v),(directory,tag,key)
            arrays[condition,seed,budget]=np.array([sum(pred.get(i,{}).get(k)==v for i in b['record_ids'] for k,v in rows[i]['gold'].items()) for b in batches])
            order=trajectory(train,seed);seen=set();order=[r for r in order if not(r['group'] in seen or seen.add(r['group']))][:budget]
            supported={json.dumps(v) for r in order for v in r['gold'].values()}
            strata=defaultdict(lambda:[0,0])
            for row in evaluation:
                for k,v in row['gold'].items():
                    key='purchased_label_seen' if json.dumps(v) in supported else 'purchased_label_unseen'
                    strata[key][0]+=pred.get(row['id'],{}).get(k)==v;strata[key][1]+=1
            stats=Counter();usage=Counter();records=[]
            assets=read(directory/'assets'/f'{tag}.json')
            for path in sorted((directory/'episodes').glob(tag+'-*.json')):
                value=read(path);eps=value if isinstance(value,list) else [value]
                phase='adaptation' if ('-adapt.' in path.name or '-moderation-' in path.name) else 'evaluation'
                for ep in eps:
                    stats[phase+'_'+ep['status']]+=1
                    stats[phase+'_asset_read_episodes']+=any(t.get('tool')=='read_material' and t.get('arguments',{}).get('name') in assets for t in ep.get('tool_log',[]))
                    for event in ep.get('trace',[]):
                        if 'usage' in event:
                            stats[phase+'_calls']+=1
                            u=event['usage']
                            if u.get('usage_unknown'):stats['calls_unknown_usage']+=1
                            for key in ('prompt_tokens','completion_tokens'):usage[phase+'_'+key]+=u.get(key,0)
                records.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            cells.append({**cell,'label_support':{k:{'correct':v[0],'targets':v[1],'accuracy':v[0]/v[1]} for k,v in strata.items()},'trace_statistics':dict(stats),'usage':dict(usage)})
            write(directory/'trace-summary'/f'{tag}.json',{'trace_statistics':dict(stats),'usage':dict(usage),'raw_trace_hashes':records})
        for condition in cfg['conditions']:
            for budget in cfg['budgets']:
                selected=[c for c in cells if c['condition']==condition and c['budget']==budget]
                if not selected:continue
                values=[c['metrics'][metric] for c in selected]
                arr=np.stack([arrays[condition,c['seed'],budget] for c in selected]);rng=np.random.default_rng(20261008);samples=[]
                for _ in range(2000):
                    ss=rng.integers(len(arr),size=len(arr));bs=rng.integers(len(counts),size=len(counts));samples.append(arr[ss][:,bs].sum()/(counts[bs].sum()*len(ss)))
                ci=np.quantile(samples,[.025,.975])
                summary['aggregates'].append({'task':task,'model':cfg['model'],'condition':condition,'budget':budget,'seeds':len(selected),'mean':float(np.mean(values)),'min':min(values),'max':max(values),'descriptive95_interval':ci.tolist(),'valid_output_rate':float(np.mean([c['metrics']['valid_output_rate'] for c in selected]))})
        for condition in ('notes','moderation'):
            for budget in (4,16,64):
                seeds=[s for s in cfg['seeds'] if (condition,s,budget) in arrays and ('frozen',s,budget) in arrays]
                if len(seeds)!=len(cfg['seeds']):continue
                delta=np.stack([arrays[condition,s,budget]-arrays['frozen',s,budget] for s in seeds]);rng=np.random.default_rng(20261008);samples=[]
                for _ in range(2000):
                    ss=rng.integers(len(seeds),size=len(seeds));bs=rng.integers(len(counts),size=len(counts));samples.append(delta[ss][:,bs].sum()/(counts[bs].sum()*len(ss)))
                summary['paired_effects'].append({'task':task,'model':cfg['model'],'condition_minus_frozen':condition,'budget':budget,'difference':float(delta.sum()/(counts.sum()*len(seeds))),'descriptive95_interval':np.quantile(samples,[.025,.975]).tolist()})
        summary['runs'].append({'directory':str(directory.relative_to(ROOT)),'status':report['status'],'expected_cells':28,'completed_cells':len(cells),'evaluation_rows':len(evaluation),'targets':int(counts.sum()),'groups':len({r['group'] for r in evaluation}),'batches':len(batches),'observed_gold_labels':len({json.dumps(v) for r in evaluation for v in r['gold'].values()}),'cells':cells})
    ledger=ROOT/'runs/codex-study-v1/subscription-ledger.json'
    if ledger.exists():
        events=read(ledger);summary['transport']={'calls':len(events),'states':dict(Counter(e['status'] for e in events)),'usage':{key:sum(e.get('usage',{}).get(key,0) for e in events) for key in ('prompt_tokens','completion_tokens')},'unknown_usage_calls':sum('usage' not in e or e.get('usage',{}).get('usage_unknown',False) for e in events)}
    write(ROOT/'results/subscription-study-analysis.json',summary)
    print(json.dumps({'runs':[{k:v for k,v in r.items() if k!='cells'} for r in summary['runs']],'transport':summary.get('transport')},indent=2))
if __name__=='__main__':main()
