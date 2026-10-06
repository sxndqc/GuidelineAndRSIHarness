"""Official Codex CLI subscription adapter. Never reads or exports auth tokens.

Native host tools are disabled: the external controller owns evidence and Python
execution. Every call is ephemeral and emits one schema-constrained tool action.
"""
from __future__ import annotations
import fcntl,hashlib,json,subprocess,tempfile,time,os,signal
from datetime import datetime,timezone
from pathlib import Path
from .model import BudgetExceeded

SCHEMA={'type':'object','properties':{
 'action':{'type':'string','enum':['list_materials','read_material','search_materials','read_example','read_examples','search_examples','write_asset','run_program','finish']},
 'arguments_json':{'type':'string'}},'required':['action','arguments_json'],'additionalProperties':False}
DISABLED=['shell_tool','unified_exec','apps','plugins','multi_agent','browser_use','browser_use_external','computer_use','view_image','image_generation','hooks','memories','code_mode_host','unbounded_connection_retries']

class CodexBackendUnavailable(RuntimeError):
    pass

class CodexModel:
    def __init__(self,model,reasoning_effort='medium',ledger='runs/codex/subscription-ledger.json',max_calls=4096,timeout=180):
        self.model=model;self.reasoning_effort=reasoning_effort
        self.path=Path(ledger).resolve();self.path.parent.mkdir(parents=True,exist_ok=True)
        self.max_calls=max_calls;self.timeout=timeout;self.blocked=False
        self.driver=Path('/tmp/guideline-codex-driver');self.driver.mkdir(exist_ok=True)
        self.schema=self.driver/('action-schema-'+hashlib.sha256(json.dumps(SCHEMA,sort_keys=True).encode()).hexdigest()[:12]+'.json');self.schema.write_text(json.dumps(SCHEMA))
        self.logdir=self.path.parent/(self.path.stem+'-transport');self.logdir.mkdir(exist_ok=True)

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
        if self.blocked:raise CodexBackendUnavailable('Backend halted after a transport or isolation failure')
        prompt='''You are one actor in an externally controlled annotation experiment. Native host tools are unavailable and must not be called. Continue the serialized conversation below by emitting exactly one authorized action under the output schema. arguments_json must be a valid JSON encoding of that action's argument object. A finish action returns the requested prediction or adaptation summary. The external controller will execute tools and send their results on the next turn. Do not solve missing tool calls by accessing the host or internet.\n'''+json.dumps(messages,ensure_ascii=False)
        if len(prompt)>1_000_000:raise ValueError('Prompt exceeds fixed controller limit')
        started=time.monotonic()
        index=self.record({'status':'started','model':self.model,'reasoning_effort':self.reasoning_effort,'started_utc':datetime.now(timezone.utc).isoformat(),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'channel':'official_codex_cli_chatgpt_subscription'})
        output=self.logdir/f'{index:06d}-final.json'
        cmd=['codex','exec','--ignore-user-config','--ephemeral','--sandbox','read-only','--skip-git-repo-check','--json','-C',str(self.driver),'-m',self.model,'-c',f'model_reasoning_effort="{self.reasoning_effort}"','-c','project_doc_max_bytes=0','-c','web_search="disabled"']
        for feature in DISABLED:cmd+=['--disable',feature]
        cmd+=['--output-schema',str(self.schema),'-o',str(output),'-']
        process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
        try:stdout,stderr=process.communicate(prompt,timeout=self.timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGTERM)
            try:stdout,stderr=process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);stdout,stderr=process.communicate()
            (self.logdir/f'{index:06d}-events.jsonl').write_text(stdout)
            (self.logdir/f'{index:06d}-stderr.txt').write_text(stderr)
            self.record({'status':'timeout','latency_seconds':time.monotonic()-started},index)
            self.blocked=True
            raise CodexBackendUnavailable('Codex CLI request timed out') from None
        r=subprocess.CompletedProcess(cmd,process.returncode,stdout,stderr)
        (self.logdir/f'{index:06d}-events.jsonl').write_text(r.stdout)
        (self.logdir/f'{index:06d}-stderr.txt').write_text(r.stderr)
        events=[]
        for line in r.stdout.splitlines():
            try:events.append(json.loads(line))
            except ValueError:
                if line.strip():
                    self.record({'status':'invalid_event_stream'},index)
                    self.blocked=True
                    raise CodexBackendUnavailable('Non-JSON line in official JSON event stream')
        allowed_events={'thread.started','turn.started','turn.completed','turn.failed','item.started','item.updated','item.completed','error'}
        unknown=[e.get('type') for e in events if e.get('type') not in allowed_events]
        if unknown:
            self.record({'status':'unrecognized_event_protocol','event_types':unknown},index)
            self.blocked=True
            raise CodexBackendUnavailable('Unrecognized CLI event protocol')
        forbidden=[e.get('item',{}).get('type') for e in events if e.get('item',{}).get('type') not in (None,'agent_message','reasoning','error')]
        if forbidden:
            self.record({'status':'unauthorized_native_tool_event','types':forbidden},index)
            self.blocked=True
            raise CodexBackendUnavailable('Native tool event invalidates isolated model call')
        usage=next((e['usage'] for e in reversed(events) if e.get('type')=='turn.completed' and 'usage' in e),{})
        normalized={'prompt_tokens':usage['input_tokens'],'completion_tokens':usage['output_tokens'],'native':usage} if 'input_tokens' in usage and 'output_tokens' in usage else {'usage_unknown':True,'native':usage}
        thread=next((e.get('thread_id') for e in events if e.get('type')=='thread.started'),None)
        self.record({'status':'transport_completed' if r.returncode==0 else 'failed','exit_code':r.returncode,'usage':normalized,'thread_id':thread,'latency_seconds':time.monotonic()-started},index)
        if r.returncode!=0 or not output.exists():
            self.blocked=True
            raise CodexBackendUnavailable('Codex CLI failed; retained local diagnostic log')
        try:
            action=json.loads(output.read_text());arguments=json.loads(action['arguments_json'])
            if action['action'] not in SCHEMA['properties']['action']['enum'] or not isinstance(arguments,dict):raise ValueError('Invalid action schema')
        except (ValueError,KeyError,TypeError):
            self.record({'status':'invalid_action'},index)
            raise ValueError('CLI output violated the controlled-action schema') from None
        self.record({'status':'action_validated'},index)
        return {'text':json.dumps({'action':action['action'],'arguments':arguments},ensure_ascii=False),
                'usage':normalized,'model':self.model,'backend':'codex_cli_subscription','reasoning_effort':self.reasoning_effort,
                'response_id':thread,'finish_reason':'stop','latency_seconds':time.monotonic()-started,'ledger_index':index}
