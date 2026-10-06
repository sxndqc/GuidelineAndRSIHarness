"""Analyze all pre-registered predictions; never select successful instances."""
import json
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from guideline_harness.metrics import score_snacs
ROOT=Path('results')
read=lambda p:json.loads(Path(p).read_text())
all_test={r['id']:r for r in read('data/prepared/snacs/private/test.json')}
summary={'scope':'small registered pilot; intervals descriptive, no sufficient-sample threshold established','snacs':{},'fashion':{},'paired_effects':[]}
rows=[]
for tier in ['mini','strong']:
    for mode,prefix in [('agent','snacs-agent-pilot-'),('static','snacs-static-pilot-')]:
        path=ROOT/(prefix+tier)
        report=read(path/'results.json')
        if report['status']!='completed':
            summary['snacs'][tier+'_'+mode]={'status':report['status'],'excluded_from_aggregate':'Incomplete cell; retained separately, never treated as completed benchmark'}
            continue
        evaluation=[all_test[i] for i in read(path/'evaluation-ids.json')]
        for r in report['results']:
            tag=f"{r['condition']}-s{r['seed']}-b{r['budget']}"
            prediction=read(path/'predictions'/f'{tag}.json')
            assert score_snacs(evaluation,prediction)==r['metrics']
            stats=Counter();usage=Counter();known_cost=0;program_errors=Counter()
            assets=read(path/'assets'/f'{tag}.json')
            for p in (path/'episodes').glob(tag+'-*.json'):
                ep=read(p);phase='adapt' if p.name.endswith('-adapt.json') else 'eval'
                stats[phase+'_episodes']+=1;stats[phase+'_'+ep['status']]+=1
                tools=ep.get('tool_log',[])
                stats[phase+'_guide_access_episodes']+=any(t.get('tool')=='search_materials' or (t.get('tool')=='read_material' and t.get('arguments',{}).get('name') not in assets) for t in tools)
                stats[phase+'_asset_read_episodes']+=any(t.get('tool')=='read_material' and t.get('arguments',{}).get('name') in assets for t in tools)
                stats[phase+'_program_calls']+=sum(t.get('tool')=='run_program' for t in tools)
                for t in ep['trace']:
                    if 'usage' not in t:continue
                    u=t['usage'];usage[phase+'_input_tokens']+=u.get('prompt_tokens',0);usage[phase+'_output_tokens']+=u.get('completion_tokens',0);stats[phase+'_model_calls']+=1
                    a,b=(.75,4.5) if tier=='mini' else (2.5,15)
                    known_cost+=(u.get('prompt_tokens',0)*a+u.get('completion_tokens',0)*b)/1e6
            row={**r,'tier':tier,'trace_statistics':dict(stats),'usage':dict(usage),'known_usage_cost_upper_bound_usd':known_cost,'assets':list(assets),'directory':str(path)}
            rows.append(row)
        summary['snacs'][tier+'_'+mode]={'evaluation_sentences':len(evaluation),'evaluation_targets':sum(len(r['gold']) for r in evaluation),'evaluation_documents':len({r['group'] for r in evaluation})}
summary['snacs_runs']=rows
# Aggregate paired trajectory means/ranges, not misleading multi-seed B0 replication.
groups=defaultdict(list)
for row in rows:groups[(row['tier'],row['condition'],row['budget'])].append(row)
aggregates=[]
for (tier,condition,budget),group in groups.items():
    values=[r['metrics']['joint_accuracy'] for r in group]
    aggregates.append({'tier':tier,'condition':condition,'budget':budget,'runs':len(group),'mean_joint_accuracy':float(np.mean(values)),'min':min(values),'max':max(values),'valid_output_rate':float(np.mean([r['metrics']['valid_output_rate'] for r in group]))})
summary['snacs_aggregates']=aggregates
# Paired two-axis resampling. Two adaptation draws severely limit calibration.
for tier in ['mini','strong']:
    path=ROOT/('snacs-agent-pilot-'+tier);evaluation=[all_test[i] for i in read(path/'evaluation-ids.json')]
    docs=sorted({r['group'] for r in evaluation})
    for condition in ['notes','notes_program']:
        for budget in [4,16]:
            differences=[];denominators=[]
            for seed in [11,23]:
                a=read(path/'predictions'/f'{condition}-s{seed}-b{budget}.json');b=read(path/'predictions'/f'frozen-s{seed}-b{budget}.json')
                delta=[];count=[]
                for doc in docs:
                    subset=[r for r in evaluation if r['group']==doc]
                    delta.append(sum(int(a.get(r['id'],{}).get(k)==v)-int(b.get(r['id'],{}).get(k)==v) for r in subset for k,v in r['gold'].items()))
                    count.append(sum(len(r['gold']) for r in subset))
                differences.append(delta);denominators.append(count)
            d=np.array(differences);n=np.array(denominators);rng=np.random.default_rng(20261006);samples=[]
            for _ in range(2000):
                ss=rng.integers(0,2,2);dd=rng.integers(0,len(docs),len(docs));samples.append(d[ss][:,dd].sum()/n[ss][:,dd].sum())
            lo,hi=np.quantile(samples,[.025,.975])
            summary['paired_effects'].append({'tier':tier,'condition_minus_frozen':condition,'budget':budget,'difference':float(d.sum()/n.sum()),'descriptive95_interval':[float(lo),float(hi)],'qualification':'Two adaptation trajectories; exploratory descriptive interval, not a reliable population hypothesis test.'})
# TeX table stays within a column.
lines=['\\begin{tabular}{llrrr}','\\toprule','Tier & $B$ & Frozen & Notes & +Code \\\\','\\midrule']
for tier in ['mini','strong']:
    for budget in [0,4,16]:
        values=[]
        for condition in ['frozen','notes','notes_program']:
            g=groups.get((tier,condition,budget))
            values.append(f"{100*np.mean([r['metrics']['joint_accuracy'] for r in g]):.1f}" if g else '--')
        lines.append(f"{tier.title()} & {budget} & "+' & '.join(values)+' \\\\')
lines+=['\\bottomrule','\\end{tabular}'];Path('paper/agent-table.tex').write_text('\n'.join(lines)+'\n')
fig,axs=plt.subplots(1,2,figsize=(7,2.7),sharey=True)
for ax,tier in zip(axs,['mini','strong']):
    for condition in ['frozen','notes','notes_program']:
        g=[a for a in aggregates if a['tier']==tier and a['condition']==condition];g.sort(key=lambda a:a['budget'])
        ax.plot([a['budget'] for a in g],[a['mean_joint_accuracy']*100 for a in g],marker='o',label=condition.replace('notes_program','notes + code'))
        for a in g:ax.vlines(a['budget'],a['min']*100,a['max']*100,alpha=.4)
    ax.set_title(tier.title());ax.set_xlabel('Additional labeled sentences');ax.set_xticks([0,4,16]);ax.set_ylim(0,100);ax.grid(alpha=.2)
axs[0].set_ylabel('Joint accuracy (%)');axs[1].legend(fontsize=7);fig.tight_layout();fig.savefig('paper/agent-learning-curves.pdf');fig.savefig('results/agent-learning-curves.png',dpi=160)
for tier in ['mini','strong']:
    p=ROOT/('fashion-agent-pilot-'+tier)/'results.json'
    if p.exists():summary['fashion'][tier]=read(p)
(ROOT/'agent-analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'snacs':summary['snacs'],'aggregates':aggregates,'paired_effects':summary['paired_effects']},indent=2))
