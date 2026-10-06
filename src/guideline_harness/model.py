"""Explicit model endpoint; never discover/copy credentials from login files."""
from __future__ import annotations
import json
import os
import time
import threading
import fcntl
from contextlib import contextmanager
from pathlib import Path
import urllib.request
import urllib.error
from urllib.parse import urlsplit

class BudgetExceeded(RuntimeError):
    pass

class ProviderError(RuntimeError):
    def __init__(self, status, provider_code=None):
        super().__init__(f'Provider HTTP {status}; code={provider_code}')
        self.status=status
        self.provider_code=provider_code

class QuotaExhausted(ProviderError):
    pass

class CostMeter:
    """Conservative USD accounting, persisted before dispatch; no automatic retries.

    Rates are explicit accounting ceilings, not a claim about the final invoice.
    UTF-8 byte count plus message overhead bounds ordinary text token inputs.
    Unknown outcomes retain the entire reservation.
    """
    def __init__(self, path, limit, input_per_million=10, output_per_million=40):
        self.path=Path(path)
        self.limit=limit
        self.input_rate=input_per_million
        self.output_rate=output_per_million
        self.lock=threading.Lock()
        self.events=json.loads(self.path.read_text()) if self.path.exists() else []

    @contextmanager
    def locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock, self.path.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.events=json.loads(self.path.read_text()) if self.path.exists() else []
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp=self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.events, indent=2))
        tmp.replace(self.path)

    def reserve(self, model, messages, maximum):
        amount=(len(json.dumps(messages,ensure_ascii=False).encode())+100*len(messages)+1000)*self.input_rate/1e6+maximum*self.output_rate/1e6
        with self.locked():
            if sum(e['charged_ceiling_usd'] for e in self.events)+amount>self.limit:
                raise BudgetExceeded('Conservative experiment cost ceiling reached')
            index=len(self.events)
            self.events.append({'model':model,'status':'reserved','reserved_usd':amount,'input_ceiling_per_million':self.input_rate,'output_ceiling_per_million':self.output_rate,'charged_ceiling_usd':amount})
            self.save()
        return index

    def reject(self, index, status, provider_code):
        with self.locked():
            self.events[index].update(status='rejected',http_status=status,provider_code=provider_code,
                charged_ceiling_usd=0,reason='Request explicitly rejected before model completion')
            self.save()

    def settle(self, index, response):
        usage=response.get('usage',{})
        if 'prompt_tokens' not in usage or 'completion_tokens' not in usage:
            return
        with self.locked():
            self.events[index].update(status='completed',usage=usage,response_id=response.get('id'),
                charged_ceiling_usd=(usage['prompt_tokens']*self.input_rate+usage['completion_tokens']*self.output_rate)/1e6)
            self.save()

def tool_schema():
    definitions={
        'list_materials': {},
        'read_material': {'name':{'type':'string'},'start':{'type':'integer'},'length':{'type':'integer'}},
        'search_materials': {'query':{'type':'string'}},
        'read_example': {'id':{'type':'string'}},
        'search_examples': {'query':{'type':'string'},'limit':{'type':'integer'}},
        'write_asset': {'name':{'type':'string'},'text':{'type':'string'}},
        'run_program': {'script':{'type':'string'},'input':{'type':'object'}},
        'finish': {'prediction':{'type':'object','additionalProperties':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':2}},'summary':{'type':'string'}}
    }
    return [{'type':'function','function':{'name':name,'description': 'Finish the current phase.' if name=='finish' else name.replace('_',' '),
        'parameters':{'type':'object','properties':properties,'additionalProperties':False}}} for name,properties in definitions.items()]

class ChatModel:
    def __init__(self, model, base_url=None, key_env='ANNOTATION_API_KEY', max_tokens=2000, reasoning_effort=None, meter=None, native_tools=False, api_style="chat"):
        self.model=model
        self.reasoning_effort=reasoning_effort
        self.meter=meter
        self.native_tools=native_tools
        self.api_style=api_style
        self.quota_blocked=False
        self.base_url=(base_url or os.environ.get('ANNOTATION_API_BASE','')).rstrip('/')
        self.key_env=key_env
        self.max_tokens=max_tokens
        if not self.base_url:
            raise RuntimeError('No ANNOTATION_API_BASE configured; model experiments have not run')
        parsed=urlsplit(self.base_url)
        if parsed.scheme!='https' or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('Model API must be an HTTPS endpoint without embedded credentials')
        if not os.environ.get(key_env):
            raise RuntimeError(f'Missing credential binding {key_env}; configure securely, never paste into chat')

    def complete(self, messages):
        if self.quota_blocked:
            raise QuotaExhausted(429,'credit_balance_exhausted')
        if self.native_tools and self.api_style=="responses":
            payload={'model':self.model,'input':messages,'max_output_tokens':self.max_tokens,
                     'tools':[{'type':'function',**t['function'],'strict':False} for t in tool_schema()],
                     'tool_choice':'required','parallel_tool_calls':False,'store':False}
            if self.reasoning_effort is not None: payload['reasoning']={'effort':self.reasoning_effort}
            endpoint='/responses'
        else:
            payload={'model':self.model,'messages':messages,'max_completion_tokens':self.max_tokens}
            if self.reasoning_effort is not None: payload['reasoning_effort']=self.reasoning_effort
            if self.native_tools: payload.update(tools=tool_schema(),tool_choice='required',parallel_tool_calls=False)
            endpoint='/chat/completions'
        reservation=self.meter.reserve(self.model,messages+([{'role':'system','content':json.dumps(tool_schema())}] if self.native_tools else []),self.max_tokens) if self.meter else None
        req=urllib.request.Request(self.base_url+endpoint,data=json.dumps(payload).encode(),
            headers={'Content-Type':'application/json','Authorization':'Bearer '+os.environ[self.key_env]})
        start=time.monotonic()
        try:
            with urllib.request.urlopen(req,timeout=180) as response:
                result=json.load(response)
        except urllib.error.HTTPError as exc:
            try: error=json.loads(exc.read()).get('error',{})
            except (ValueError,AttributeError): error={}
            # Preserve only machine codes: human error messages may echo credentials.
            code=error.get('code') or error.get('type')
            if not isinstance(code,str) or not all(c.isalnum() or c in '_-' for c in code): code=None
            if self.meter and exc.code in (400,401,403,404,429): self.meter.reject(reservation,exc.code,code)
            if code in ('credit_balance_exhausted','insufficient_quota') or error.get('type')=='insufficient_quota':
                self.quota_blocked=True
                raise QuotaExhausted(exc.code,code) from None
            raise ProviderError(exc.code,code) from None
        calls=[]
        if self.native_tools and self.api_style=="responses":
            native_usage=result.get('usage',{})
            result['usage']={'prompt_tokens':native_usage.get('input_tokens',0),
                             'completion_tokens':native_usage.get('output_tokens',0),
                             'total_tokens':native_usage.get('total_tokens',0),
                             'native':native_usage}
            if self.meter: self.meter.settle(reservation,result)
            calls=[x for x in result.get('output',[]) if x.get('type')=='function_call']
            text=json.dumps({'action':calls[0]['name'],'arguments':json.loads(calls[0]['arguments'])}) if calls and result.get('status')!='incomplete' else None
            reason='length' if result.get('status')=='incomplete' else 'stop'
        else:
            if self.meter: self.meter.settle(reservation,result)
            choice=result['choices'][0]
            text=choice['message'].get('content')
            calls=choice['message'].get('tool_calls',[])
            if calls and choice.get('finish_reason')!='length':
                call=calls[0]['function']
                text=json.dumps({'action':call['name'],'arguments':json.loads(call['arguments'])})
            reason=choice.get('finish_reason')
        return {'text':text,'native_tool_calls':calls,'usage':result.get('usage',{}),
                'model':result.get('model',self.model),'latency_seconds':time.monotonic()-start,
                'response_id':result.get('id'),'finish_reason':reason}
