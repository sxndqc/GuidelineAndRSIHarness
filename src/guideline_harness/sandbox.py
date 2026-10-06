"""Fail-closed Linux bubblewrap runner for agent-written stdlib Python.

It mounts no repository/data/API credentials, unshares networking and pids,
clears the environment, mounts assets read-only, and has CPU/file/time limits.
"""
from __future__ import annotations
import json
from pathlib import Path
import resource
import shutil
import subprocess
import tempfile
from .protocol import safe_path

def _limits():
    resource.setrlimit(resource.RLIMIT_CPU,(3,3))
    resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576))
    resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024))
    resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
    resource.setrlimit(resource.RLIMIT_NPROC,(64,64))

def run_python(assets, script, payload, timeout=8):
    script=safe_path(script)
    if script not in assets or not script.endswith('.py'):
        raise ValueError('Unknown Python asset')
    if not shutil.which('bwrap'):
        raise RuntimeError('Program execution unavailable: bubblewrap is required; no unsandboxed fallback')
    serialized=json.dumps(payload).encode()
    if len(serialized)>200000: raise ValueError('Program input too large')
    with tempfile.TemporaryDirectory(prefix='annotation-program-') as root:
        root=Path(root); work=root/'work';work.mkdir()
        for name,content in assets.items():
            name=safe_path(name);path=work/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
        cmd=['bwrap','--unshare-all','--die-with-parent','--new-session','--clearenv',
             '--setenv','PATH','/usr/bin','--setenv','PYTHONDONTWRITEBYTECODE','1']
        for path in ['/usr','/lib','/lib64']:
            if Path(path).exists(): cmd += ['--ro-bind',path,path]
        cmd += ['--proc','/proc','--dev','/dev','--tmpfs','/tmp','--ro-bind',str(work),'/work',
                '--chdir','/work','/usr/bin/python3','-I','/work/'+script]
        with (root/'stdout').open('wb') as stdout,(root/'stderr').open('wb') as stderr:
            try:
                done=subprocess.run(cmd,input=serialized,stdout=stdout,stderr=stderr,timeout=timeout,preexec_fn=_limits)
            except subprocess.TimeoutExpired:
                return {'exit_code':None,'error':'program_timeout'}
        out=(root/'stdout').read_text(errors='replace')[:32000]
        err=(root/'stderr').read_text(errors='replace')[:4000]
        return {'exit_code':done.returncode,'stdout':out,'stderr':err}
