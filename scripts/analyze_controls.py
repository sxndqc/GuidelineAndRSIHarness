"""Derive tables, paired uncertainty and figure from actual saved predictions."""
import json
import os
from pathlib import Path
os.environ.setdefault("MPLCONFIGDIR", "/tmp/guideline-matplotlib")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/guideline-cache")
import numpy as np
from guideline_harness.data import read_json, write_json
from guideline_harness.metrics import score_snacs

root=Path('results/snacs-controls-v2')
report=read_json(root/'baseline-results.json')
gold=read_json('data/prepared/snacs/private/test.json')
groups=sorted({x['group'] for x in gold});group_index={x:i for i,x in enumerate(groups)}
counts=np.zeros(len(groups))
for row in gold:counts[group_index[row['group']]]+=len(row['gold'])
seeds=report['seeds'];budgets=report['budgets'];methods=['majority','lexical_majority','tfidf_nearest']
correct={}
for method in methods:
 for budget in budgets:
  correct[method,budget]=np.zeros((len(seeds),len(groups)))
  for i,seed in enumerate(seeds):
   p=read_json(root/'predictions'/f'{method}-b{budget}-s{seed}.json')
   for row in gold:
    correct[method,budget][i,group_index[row['group']]]+=sum(p[row['id']].get(k)==v for k,v in row['gold'].items())

# Paired two-axis resampling: same documents and seed identities in both methods.
# Descriptive with just five trajectories; not an agent hypothesis test.
rng=np.random.default_rng(20261006);repeats=2000
paired=[]
for budget in budgets:
 for left,right in [('lexical_majority','tfidf_nearest'),('lexical_majority','majority')]:
  delta=correct[left,budget]-correct[right,budget]
  samples=[]
  for _ in range(repeats):
   si=rng.integers(len(seeds),size=len(seeds));di=rng.integers(len(groups),size=len(groups))
   samples.append(float(delta[si][:,di].sum(axis=1).mean()/counts[di].sum()))
  ci=np.quantile(samples,[.025,.975])
  paired.append({'budget':budget,'left':left,'right':right,'accuracy_difference':float(delta.sum(axis=1).mean()/counts.sum()),
                 'descriptive_95_percentile_interval':[float(x) for x in ci],
                 'resampling':'paired adaptation trajectories and test documents','repeats':repeats})
write_json('results/control-analysis.json',{'paired_comparisons':paired,'caution':'Five trajectories; descriptive controls, no inference about LLM agents.'})

# Check revised metrics/projection did not change the original predictions.
old=read_json('results/snacs-controls/baseline-results.json')
oldhash={(r['method'],r['budget'],r['seed']):r['predictions_sha256'] for r in old['runs']}
assert all(oldhash[r['method'],r['budget'],r['seed']]==r['predictions_sha256'] for r in report['runs'])
write_json('results/verification.json',{'prediction_hashes_unchanged_after_review_fixes':True,'paired_runs':len(report['runs']),
 'gold_self_score':score_snacs(gold,{r['id']:r['gold'] for r in gold}),
 'empty_prediction_score':score_snacs(gold,{}),
 'model_experiments_executed':False})

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(6,3.4))
for method,label in [('majority','Majority'),('lexical_majority','Lexical majority'),('tfidf_nearest','TF-IDF nearest')]:
 selected=[r for r in report['summary'] if r['method']==method]
 ax.errorbar([r['budget'] for r in selected],[100*r['joint_accuracy_mean'] for r in selected],
             yerr=[100*r['run_sd'] for r in selected],label=label,marker='o',capsize=3)
ax.set_xscale('log',base=2);ax.set_xticks(budgets,labels=budgets)
ax.set_xlabel('New labeled sentences');ax.set_ylabel('Joint role/function accuracy (%)')
ax.set_title('SNACS non-LLM controls (five adaptation trajectories)')
ax.grid(alpha=.2);ax.legend(fontsize=8);fig.tight_layout()
fig.savefig('paper/control-learning-curves.pdf');fig.savefig('results/control-learning-curves.png',dpi=180)

lines=['| Labeled sentences | Majority | Lexical majority | TF-IDF nearest |','|---:|---:|---:|---:|']
for budget in budgets:
 cells=[]
 for method in methods:
  r=next(r for r in report['summary'] if r['budget']==budget and r['method']==method)
  cells.append(f"{100*r['joint_accuracy_mean']:.2f} ± {100*r['run_sd']:.2f}")
 lines.append('| '+str(budget)+' | '+' | '.join(cells)+' |')
Path('results/control-table.md').write_text('\n'.join(lines)+'\n\nPercent joint accuracy; mean ± adaptation-run SD, not confidence intervals. No LLM/agent experiments are included.\n')
tex=[]
for budget in budgets:
 cells=[]
 for method in methods:
  r=next(r for r in report['summary'] if r['budget']==budget and r['method']==method)
  cells.append(f"{100*r['joint_accuracy_mean']:.2f} $\\pm$ {100*r['run_sd']:.2f}")
 tex.append(str(budget)+' & '+' & '.join(cells)+r' \\')
Path('paper/control-table.tex').write_text('\\begin{tabular}{rccc}\n\\toprule\nBudget & Majority & Lexical & TF--IDF \\\\\\midrule\n'+'\n'.join(tex)+'\n\\bottomrule\n\\end{tabular}\n')
print('\n'.join(lines))
print(json.dumps(paired[-2:],indent=2))
