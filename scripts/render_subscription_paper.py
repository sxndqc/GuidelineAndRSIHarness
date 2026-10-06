"""Render only observed results, marking every pending cell explicitly."""
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
def main():
 s=json.loads((ROOT/'results/subscription-study-analysis.json').read_text());runs=s['runs'];n=sum(r['completed_cells'] for r in runs);complete=n==112 and all(r['status']=='completed' for r in runs)
 status='Completed bounded experimental matrix; limitations still apply.' if complete else f'Experiment in progress or interrupted: {n}/112 configuration cells completed. This PDF is a live sample, not a completed-study claim.'
 (ROOT/'paper/subscription-status.tex').write_text('\\noindent\\fbox{\\parbox{0.94\\columnwidth}{\\textbf{Review draft.} '+status+'}}\n')
 aggregates={(a['task'],a['model'],a['condition'],a['budget']):a for a in s['aggregates']}
 lines=['\\begin{table*}[t]','\\centering\\small','\\begin{tabular}{llrrrr}','\\toprule','Task & Tier & $B$ & Retrieval & Notes & Moderation \\\\','\\midrule']
 for task in ['snacs','cap_pa']:
  for tier in ['luna','sol']:
   for budget in [0,4,16,64]:
    values=[]
    for condition in ['frozen','notes','moderation']:
     a=aggregates.get((task,'gpt-6-'+tier,condition,budget))
     values.append(f"{a['mean']*100:.1f} ({a['seeds']})" if a else ('shared B0' if budget==0 and condition!='frozen' else 'pending'))
    lines.append(f'{"SNACS" if task=="snacs" else "CAP PA"} & {tier.title()} & {budget} & '+' & '.join(values)+' \\\\')
 lines+=['\\bottomrule','\\end{tabular}','\\caption{Observed primary accuracy (\\%) and number of completed adaptation trajectories in parentheses. Pending cells have no imputed score. B0 is one shared retrieval starting point. Comparisons with incomplete or unequal trajectory counts are provisional. All evaluated targets, including refusals and call exhaustion, remain in denominators.}','\\label{tab:subscription}','\\end{table*}']
 t=s.get('transport',{});lines += [f"At this snapshot, {n} of 112 configuration cells are complete. The transport ledger records {t.get('calls',0):,} actor requests. Completed cell scores appear in Table~\\ref{{tab:subscription}}; missing cells are not scored as zero. Operational statuses are retained separately from semantic errors."]
 if s['paired_effects']:
  lines+=['\\paragraph{Completed paired comparisons.}']
  for e in s['paired_effects']:
   lo,hi=e['descriptive95_interval'];lines.append(f"{e['task'].replace('_',' ')} / {e['model'].replace('gpt-6-','').title()}, {e['condition_minus_frozen']} minus retrieval at $B={e['budget']}$: {e['difference']*100:.1f} points (descriptive 95\\% interval {lo*100:.1f} to {hi*100:.1f}).")
 else:lines+=['No full three-seed paired condition contrast has completed in this snapshot; no adaptation-effect estimate is claimed.']
 controls=json.loads((ROOT/'results/subscription-controls/results.json').read_text())['results'];groups=defaultdict(list)
 for c in controls:
  if c['budget']==64:groups[c['task'],c['method']].append(c['metrics']['joint_accuracy' if c['task']=='snacs' else 'accuracy'])
 lines+=['\\paragraph{Matched non-LLM controls.} All 45 control cells completed on the same new study samples and purchased trajectories. At $B=64$, mean primary accuracies over the three seeds are: '+ '; '.join(f"{task.replace('_',' ')} {method.replace('_',' ')} {np.mean(v)*100:.1f}\\%" for (task,method),v in groups.items())+'. These controls do not receive guideline knowledge. They are diagnostics, not substitutes for a strong full-context model baseline.']
 lines+=['\\begin{figure*}[t]','\\centering','\\includegraphics[width=.92\\textwidth]{subscription-curves.pdf}','\\caption{Observed completed-cell means. Vertical ranges span completed trajectory values, not confidence intervals; absent points are pending. The figure is descriptive until the planned trajectories complete.}','\\end{figure*}']
 (ROOT/'paper/subscription-results.tex').write_text('\n'.join(lines)+'\n')
 fig,axes=plt.subplots(2,2,figsize=(9,5),sharey=True)
 for row,task in enumerate(['snacs','cap_pa']):
  for col,tier in enumerate(['luna','sol']):
   ax=axes[row,col]
   for condition in ['frozen','notes','moderation']:
    vals=[a for a in s['aggregates'] if a['task']==task and a['model']=='gpt-6-'+tier and a['condition']==condition];vals.sort(key=lambda a:a['budget'])
    if vals:
     xs=[np.log2(1+a['budget']) for a in vals];ax.plot(xs,[100*a['mean'] for a in vals],marker='o',label=condition)
     for x,a in zip(xs,vals):ax.vlines(x,a['min']*100,a['max']*100,alpha=.4)
   ax.set_title(('SNACS' if task=='snacs' else 'CAP PA')+' / '+tier.title());ax.set_ylim(0,100);ax.set_xlim(-.1,np.log2(65)+.1);ax.set_xticks(np.log2(np.array([0,4,16,64])+1),['0','4','16','64']);ax.grid(alpha=.2)
   if col==0:ax.set_ylabel('Primary accuracy (%)')
   if row==1:ax.set_xlabel('New labeled records (log budget spacing)')
   handles,labels=ax.get_legend_handles_labels()
   if handles:ax.legend(fontsize=7)
 fig.tight_layout();fig.savefig(ROOT/'paper/subscription-curves.pdf');fig.savefig(ROOT/'results/subscription-curves.png',dpi=160)
 print(status)
if __name__=='__main__':main()
