"""Bounded continuation and artifact generation for the authorized long study.

Never retries refusals, semantic errors, exhausted tool budgets, isolation events,
or unknown failures. Only explicit capacity/resource interruptions qualify.
"""
import fcntl,json,os,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PYTHON=ROOT/'.venv/bin/python'
NAMES=['snacs-sol','snacs-luna','cap_pa-sol','cap_pa-luna']
def read(path):
 try:return json.loads(path.read_text())
 except (FileNotFoundError,json.JSONDecodeError):return None
def write(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)
def active_runs():
 result=subprocess.run(['pgrep','-af',r'^/workspace/GuidelineAndRSIHarness/.venv/bin/python .venv/bin/guideline-harness agent configs/codex-study-'],capture_output=True,text=True)
 active=set()
 for line in result.stdout.splitlines():
  cfg=read(ROOT/line.split()[-1])
  if cfg:active.add(cfg['output'])
 return active
def terminal_reason(directory,report):
 if report and report.get('status')=='cost_budget_exhausted':return 'cost_budget_exhausted'
 files=sorted((directory/'episodes').glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)
 for path in files:
  item=read(path)
  if item is None:continue
  episodes=item if isinstance(item,list) else [item]
  for ep in reversed(episodes):
   if ep.get('status')=='cost_budget_exhausted':return 'cost_budget_exhausted'
   if ep.get('status')=='backend_unavailable':return ep.get('backend_reason','unclassified_legacy_failure')
 return 'unclassified_process_exit'
def artifacts(final=False):
 env=dict(os.environ);env['MPLCONFIGDIR']='/tmp/guideline-mpl';env['XDG_CACHE_HOME']='/tmp/guideline-cache'
 with (ROOT/'runs/codex-study-v1/artifact-build.log').open('a') as log:
  for script in ['analyze_subscription_study.py','render_subscription_paper.py']:
   subprocess.run([str(PYTHON),str(ROOT/'scripts'/script)],cwd=ROOT,env=env,stdout=log,stderr=log,check=True)
  for cmd in [['pdflatex','-interaction=nonstopmode','-halt-on-error','subscription-study.tex'],['bibtex','subscription-study'],['pdflatex','-interaction=nonstopmode','-halt-on-error','subscription-study.tex'],['pdflatex','-interaction=nonstopmode','-halt-on-error','subscription-study.tex']]:
   subprocess.run(cmd,cwd=ROOT/'paper',env=env,stdout=log,stderr=log,check=True)
  if final:
   subprocess.run(['git','add','results','paper','research/subscription-supervisor-status.json','configs'],cwd=ROOT,stdout=log,stderr=log,check=True)
   changed=subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode
   if changed:
    subprocess.run(['git','commit','-m','Record bounded subscription study outcomes and regenerate review paper'],cwd=ROOT,stdout=log,stderr=log,check=True)
    subprocess.run(['git','push','origin','main'],cwd=ROOT,stdout=log,stderr=log,check=True)
def main():
 os.chdir(ROOT);run=ROOT/'runs/codex-study-v1';run.mkdir(parents=True,exist_ok=True)
 lock=(run/'supervisor.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 start=time.monotonic();previous=read(ROOT/'research/subscription-supervisor-status.json') or {};attempts={n:previous.get('supervisor_continuations',{}).get(n,0) for n in NAMES};due={};children=[];last_build=0
 while time.monotonic()-start<8*3600:
  children=[p for p in children if p.poll() is None]
  active=active_runs();states={};ledger=read(run/'subscription-ledger.json') or []
  for name in NAMES:
   original=read(ROOT/f'configs/codex-study-{name}.json');directory=ROOT/original['output'];report=read(directory/'results.json') or {};cells=len(report.get('results',[]))
   if original['output'] in active:states[name]={'state':'running','completed_cells':cells};continue
   if report.get('status')=='completed':states[name]={'state':'completed','completed_cells':cells};continue
   reason=terminal_reason(directory,report)
   if len(ledger)>=18000:reason='shared_call_ceiling'
   if reason not in ('capacity','cost_budget_exhausted') or attempts[name]>=2:
    states[name]={'state':'blocked','reason':reason,'completed_cells':cells};continue
   if name not in due:due[name]=time.monotonic()+180
   if time.monotonic()<due[name]:states[name]={'state':'cooldown','reason':reason,'completed_cells':cells};continue
   cfg={**original,'resume':True,'subscription_call_limit':18000,'workers':2 if name.endswith('luna') else 4}
   target=ROOT/f'configs/codex-study-{name}-resume.json';write(target,cfg)
   attempts[name]+=1;due.pop(name,None)
   log=(run/f'supervisor-{name}-{attempts[name]}.log').open('w')
   # Match the exact process identity used by already-running direct tool jobs.
   child=subprocess.Popen(['.venv/bin/guideline-harness','agent',str(target.relative_to(ROOT))],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);log.close();children.append(child)
   states[name]={'state':'resumed','reason':reason,'completed_cells':cells}
  status={'updated_utc':datetime.now(timezone.utc).isoformat(),'states':states,'supervisor_continuations':attempts,'transport_calls':len(ledger),'deadline_hours':8,'note':'Runs continue in the workspace while supervisor is alive. Blocked states are not completed experiments.'}
  write(ROOT/'research/subscription-supervisor-status.json',status)
  print(json.dumps(status),flush=True)
  if time.monotonic()-last_build>=300:
   try:artifacts()
   except Exception as exc:print('artifact_snapshot_error',type(exc).__name__,flush=True)
   last_build=time.monotonic()
  if all(s['state'] in ('completed','blocked') for s in states.values()):
   try:artifacts(final=True)
   except Exception as exc:print('final_artifact_error',type(exc).__name__,flush=True)
   return
  time.sleep(30)
 write(ROOT/'research/subscription-supervisor-status.json',{'state':'supervisor_deadline','updated_utc':datetime.now(timezone.utc).isoformat(),'note':'Supervisor deadline reached; inspect active processes before continuing. No experiment completion claim.'})
if __name__=='__main__':main()
