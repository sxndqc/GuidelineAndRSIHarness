"""Explicit model endpoint; never discover/copy credentials from login files."""
from __future__ import annotations
import json
import os
import time
import urllib.request
from urllib.parse import urlsplit

class ChatModel:
    def __init__(self, model, base_url=None, key_env='ANNOTATION_API_KEY', max_tokens=2000):
        self.model=model
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
        payload={'model':self.model,'messages':messages,'max_completion_tokens':self.max_tokens}
        req=urllib.request.Request(self.base_url+'/chat/completions',data=json.dumps(payload).encode(),
            headers={'Content-Type':'application/json','Authorization':'Bearer '+os.environ[self.key_env]})
        start=time.monotonic()
        # No silent retries: failures are recorded by the caller and count as failures.
        with urllib.request.urlopen(req,timeout=180) as response:
            result=json.load(response)
        choice=result['choices'][0]
        return {'text':choice['message']['content'],'usage':result.get('usage',{}),
                'model':result.get('model',self.model),'latency_seconds':time.monotonic()-start,
                'response_id':result.get('id'),'finish_reason':choice.get('finish_reason')}
