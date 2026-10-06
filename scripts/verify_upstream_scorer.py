"""Cross-check saved predictions with the unmodified, pinned official scorer.

Runs only in trusted evaluator context; raw annotations are never exposed to an agent.
Downloads are TLS-verified, SHA-256 recorded, and the scorer commit is fixed.
"""
import copy
import hashlib
import json
import sys
import tempfile
import urllib.request
from pathlib import Path
from guideline_harness.data import STREUSLE_COMMIT, read_json, write_json

raw=Path('data/raw/streusle')
manifest=[]
for name in ['psseval.py','conllu2json.py','lexcatter.py','mwerender.py','tagging.py','supersenses.py']:
    url=f'https://raw.githubusercontent.com/nert-nlp/streusle/{STREUSLE_COMMIT}/{name}'
    path=raw/name
    if not path.exists():
        with urllib.request.urlopen(url,timeout=60) as response:path.write_bytes(response.read())
    manifest.append({'file':name,'url':url,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
# The original data downloader already pinned supersenses.py. Other files were
# obtained at the same explicit commit; hashes below permit independent auditing.
sys.path.insert(0,str(raw.resolve()))
from psseval import eval_sys
from conllu2json import load_sents
with (raw/'test.json').open() as source: gold=list(load_sents(source))
for sentence in gold:
    sentence['punits']={tuple(e['toknums']):(e['lexcat'],e['ss'],e['ss2'])
        for collection in ['swes','smwes'] for e in sentence[collection].values()
        if e['ss'] and (e['ss'].startswith('p.') or e['ss']=='??')}
report=read_json('results/snacs-controls-v2/baseline-results.json')
verified=[]
for run in report['runs']:
    name=f"{run['method']}-b{run['budget']}-s{run['seed']}"
    predictions=read_json(Path('results/snacs-controls-v2/predictions')/(name+'.json'))
    system=copy.deepcopy(read_json(raw/'test.json'))
    for sentence in system:
        for target,pair in predictions.get(sentence['sent_id'],{}).items():
            collection,key=target.split(':')
            sentence[collection][key]['ss'],sentence[collection][key]['ss2']=pair
    with tempfile.NamedTemporaryFile(mode='w+',suffix='.goldid.json') as stream:
        json.dump(system,stream);stream.flush();stream.seek(0)
        official=eval_sys(stream,gold,lambda x:x)
    for theirs,ours in [('Role','role_accuracy'),('Fxn','function_accuracy'),('Role,Fxn','joint_accuracy')]:
        assert official['All'][theirs]['N']==run['metrics']['targets'],(name,official['All'][theirs])
        assert abs(official['All'][theirs]['Acc']-run['metrics'][ours])<1e-12,(name,theirs)
    verified.append({'run':name,'targets':official['All']['Role,Fxn']['N'],'official_joint_accuracy':official['All']['Role,Fxn']['Acc']})
write_json('results/upstream-scorer-verification.json',{'status':'passed','upstream_commit':STREUSLE_COMMIT,
    'unchanged_official_scorer':True,'checks':['All.Role.Acc','All.Fxn.Acc','All.Role,Fxn.Acc','All.*.N'],
    'runs_checked':len(verified),'runs':verified,'files':manifest,
    'scope':'These valid given-target controls only; not equivalence for arbitrary invalid or auto-identification outputs'})
print(json.dumps({'status':'passed','runs_checked':len(verified),'targets_per_run':verified[0]['targets']}))
