"""Project the official PA dataset; split whole normalized-summary groups."""
import csv, hashlib, json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def main():
    raw=ROOT/'data/raw/cap-pa';out=ROOT/'data/prepared/cap-pa'
    text=(raw/'policy_topics_codebook.txt').read_text()
    labels=sorted(set(re.findall(r'^\s*(\d{3,4}):',text,re.M)))
    assert len(labels)==240,len(labels)
    near=json.loads((raw/'near_duplicate_groups.json').read_text())
    splits=defaultdict(list);quarantine=Counter();groups={};raw_groups=defaultdict(Counter)
    with (raw/'bills_resolutions.csv').open(encoding='utf-8-sig',newline='') as f:
        for i,row in enumerate(csv.DictReader(f)):
            code=row['pa_code'];summary=row['nuc']
            if code not in labels:quarantine[code]+=1;continue
            norm=re.sub(r'\s+',' ',summary.lower()).strip()
            group=near[sha(norm)]
            bucket=int(sha('cap-pa-v2-split-20261006:'+group)[:8],16)%100
            split='train' if bucket<70 else ('dev' if bucket<85 else 'test')
            groups[group]=split
            splits[split].append({'id':'pa'+sha('opaque-cap-id:'+row['bill_id'])[:16],'group':group,'input':{'text':summary,'targets':[{'id':'topic'}]},'gold':{'topic':code}})
            raw_groups[summary][code]+=1
    assert sum(quarantine.values())==17
    for split,records in splits.items():write(out/f'private/{split}.json',records)
    manifest={'dataset':'CAP Pennsylvania Bills and Resolutions','split':'custom label-blind near-duplicate family hash split 70/15/15; no official ML split','normalization':'lowercase + whitespace collapse only; original input preserved','split_seed':'cap-pa-v2-split-20261006','near_duplicate_control':'MinHash candidate retrieval + 5-word shingle Jaccard >=0.85 connected components; approximate, not exhaustive; see research/cap-near-duplicate-audit.json','target':'pa_code','labels':labels,'unsupported_codes_quarantined':dict(quarantine),'source_sha256':hashlib.sha256((raw/'bills_resolutions.csv').read_bytes()).hexdigest(),'counts':{s:{'rows':len(rs),'groups':len({r['group'] for r in rs}),'codes':len({r['gold']['topic'] for r in rs})} for s,rs in splits.items()},'raw_exact_conflicts':{'groups':sum(len(c)>1 for c in raw_groups.values()),'rows':sum(sum(c.values()) for c in raw_groups.values() if len(c)>1),'maximum_correct':sum(max(c.values()) for c in raw_groups.values() if len(c)>1)},'limitations':['Summary-only inputs are not proven sufficient for original annotation.','Published labels are not individually verified double-human annotations.','2019 handbook is officially paired with historical data but relabeling to its version is unverified.','Existing manual examples are additional supervision beyond purchased rows.']}
    write(out/'manifest.json',manifest);write(ROOT/'research/cap-pa-projection.json',manifest)
    material={'status':'audited','audit_scope':'Integrity, explicit code inventory, source and projection audit; not expert adjudication of every historical label','source':json.loads((raw/'source.json').read_text()),'files':[{'name':'pa-policy-topics.txt','path':'data/raw/cap-pa/policy_topics_codebook.txt','sha256':sha(text)}],'labels':labels,'embedded_labeled_examples':None,'embedded_example_inventory':{'Examples_sections':text.count('Examples:'),'Rule_sections':text.count('Rule:'),'exact_labeled_instance_count':'not established; includes illustrative phrases and cross references'},'license':'Project-coded variables CC BY-NC-SA 4.0; raw source rights separate; raw files not redistributed','limitations':manifest['limitations']}
    write(ROOT/'configs/cap-pa-materials.json',material)
    print(json.dumps(manifest['counts'],indent=2))
if __name__=='__main__':main()
