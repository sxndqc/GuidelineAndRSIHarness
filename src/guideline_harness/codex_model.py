"""Official Codex CLI subscription adapter. Never reads or exports auth tokens.

Native host tools are disabled: the external controller owns evidence and Python
execution. Every call is ephemeral and emits one schema-constrained tool action.
"""
from __future__ import annotations
import fcntl,hashlib,json,subprocess,tempfile,time
from datetime import datetime,timezone
from pathlib import Path
from .model import BudgetExceeded

SCHEMA={'type':'object','properties':{
 'action':{'type':'string','enum':['list_materials','read_material','search_materials','read_example','search_examples','write_asset','run_program','finish']},
 'arguments_json':{'type':'string'}},'required':['action','arguments_json'],'additionalProperties':False}
DISABLED=['shell_tool','unified_exec','apps','plugins','multi_agent','browser_use','browser_use_external','computer_use','view_image','image_generation','hooks','memories','code_mode_host']

class CodexModel:
    def __init__(self,model,reasoning_effort='medium',ledger='runs/codex/subscription-ledger.json',max_calls=4096,timeout=180):
        self.model=model;self.reasoning_effort=reasoning_effort
        self.path=Path(ledger).resolve();self.path.parent.mkdir(parents=True,exist_ok=True)
        self.max_calls=max_calls;self.timeout=timeout
        self.driver=Path('/tmp/guideline-codex-driver');self.driver.mkdir(exist_ok=True)
        self.schema=self.driver/'action-schema.json';self.schema.write_text(json.dumps(SCHEMA))
        self.logdir=self.path.parent/'transport';self.logdir.mkdir(exist_ok=True)

    def record(self,event,index=None):
        with self.path.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            events=json.loads(self.path.read_text()) if self.path.exists() else []
            if index is None:
                if len(events)>=self.max_calls:raise BudgetExceeded('Codex subscription call ceiling reached')
                index=len(events);events.append(event)
            else:events[index].update(event)
            tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps(events,indent=2));tmp.replace(self.path)
            return index

    def complete(self,messages):
        prompt='''You are one actor in an externally controlled annotation experiment. Native host tools are unavailable and must not be called. Continue the serialized conversation below by emitting exactly one authorized action under the output schema. arguments_json must be a valid JSON encoding of that action's argument object. A finish action returns the requested prediction or adaptation summary. The external controller will execute tools and send their results on the next turn. Do not solve missing tool calls by accessing the host or internet.\n'''+json.dumps(messages,ensure_ascii=False)
        if len(prompt)>1_000_000:raise ValueError('Prompt exceeds fixed controller limit')
        started=time.monotonic()
        index=self.record({'status':'started','model':self.model,'reasoning_effort':self.reasoning_effort,'started_utc':datetime.now(timezone.utc).isoformat(),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'channel':'official_codex_cli_chatgpt_subscription'})
        output=self.logdir/f'{index:06d}-final.json'
        cmd=['codex','exec','--ignore-user-config','--ephemeral','--sandbox','read-only','--skip-git-repo-check','--json','-C',str(self.driver),'-m',self.model,'-c',f'model_reasoning_effort="{self.reasoning_effort}"','-c','project_doc_max_bytes=0','-c','web_search="disabled"']
        for feature in DISABLED:cmd+=['--disable',feature]
        cmd+=['--output-schema',str(self.schema),'-o',str(output),'-']
        try:r=subprocess.run(cmd,input=prompt,capture_output=True,text=True,timeout=self.timeout)
        except subprocess.TimeoutExpired:
            self.record({'status':'timeout','latency_seconds':time.monotonic()-started},index)
            raise RuntimeError('Codex CLI request timed out') from None
        (self.logdir/f'{index:06d}-events.jsonl').write_text(r.stdout)
        (self.logdir/f'{index:06d}-stderr.txt').write_text(r.stderr)
        events=[]
        for line in r.stdout.splitlines():
            try:events.append(json.loads(line))
            except ValueError:pass
        forbidden=[e.get('item',{}).get('type') for e in events if e.get('item',{}).get('type') not in (None,'agent_message','reasoning','error')]
        if forbidden:
            self.record({'status':'unauthorized_native_tool_event','types':forbidden},index)
            raise RuntimeError('Native tool event invalidates isolated model call')
        usage=next((e['usage'] for e in reversed(events) if e.get('type')=='turn.completed' and 'usage' in e),{})
        normalized={'prompt_tokens':usage.get('input_tokens',0),'completion_tokens':usage.get('output_tokens',0),'native':usage}
        thread=next((e.get('thread_id') for e in events if e.get('type')=='thread.started'),None)
        self.record({'status':'completed' if r.returncode==0 else 'failed','exit_code':r.returncode,'usage':normalized,'thread_id':thread,'latency_seconds':time.monotonic()-started},index)
        if r.returncode!=0 or not output.exists():raise RuntimeError('Codex CLI failed; retained local diagnostic log')
        action=json.loads(output.read_text());arguments=json.loads(action['arguments_json'])
        return {'text':json.dumps({'action':action['action'],'arguments':arguments},ensure_ascii=False),
                'usage':normalized,'model':self.model,'backend':'codex_cli_subscription','reasoning_effort':self.reasoning_effort,
                'response_id':thread,'finish_reason':'stop','latency_seconds':time.monotonic()-started,'ledger_index':index}
