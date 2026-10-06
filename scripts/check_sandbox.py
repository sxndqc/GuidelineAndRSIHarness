"""Real isolation integration test, not a benchmark/annotation experiment."""
import json
import os
import tempfile
from pathlib import Path
from guideline_harness.sandbox import run_python

with tempfile.TemporaryDirectory(prefix='hidden-evaluator-') as directory:
    sentinel=Path(directory)/'test-gold.json';sentinel.write_text('SECRET_GOLD_SENTINEL')
    # A non-secret marker demonstrates that inherited environment is cleared.
    os.environ['HARNESS_ISOLATION_TEST_MARKER']='present-in-controller-only'
    code='''import json, os, socket
from pathlib import Path
p=json.load(__import__('sys').stdin)
s=socket.socket();s.settimeout(.2)
try:
 s.connect(('1.1.1.1',80));network=True
except OSError: network=False
print(json.dumps({'gold_visible':Path(p['sentinel']).exists(), 'repo_visible':Path('/workspace/GuidelineAndRSIHarness').exists(), 'marker_visible':'HARNESS_ISOLATION_TEST_MARKER' in os.environ, 'network_connected':network}))
'''
    result=run_python({'probe.py':code},'probe.py',{'sentinel':str(sentinel)})
    if result['exit_code']!=0:raise RuntimeError(result)
    observed=json.loads(result['stdout'])
    assert not any(observed.values()),observed
    print(json.dumps({'status':'passed','checks':observed,'sandbox':'bubblewrap unshare-all; read-only assets; clearenv'}))
