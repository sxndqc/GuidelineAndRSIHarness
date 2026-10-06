"""Label-blind near-duplicate audit using 64-MinHash, 16 bands, exact Jaccard >=.85.
Candidate generation is approximate: absence of an edge is not proof of novelty.
"""
import csv,hashlib,json,re
from collections import defaultdict
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def main():
    raw=ROOT/'data/raw/cap-pa';docs={}
    with (raw/'bills_resolutions.csv').open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            norm=re.sub(r'\s+',' ',r['nuc'].lower()).strip()
            docs[hashlib.sha256(norm.encode()).hexdigest()]=norm
    keys=sorted(docs);parent=list(range(len(keys)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    rng=np.random.default_rng(20261006);a=rng.integers(1,2**31,size=64,dtype=np.uint64);b=rng.integers(0,2**31,size=64,dtype=np.uint64)
    bands=defaultdict(list);sets=[];edges=0;candidates=0;skipped=0
    for i,key in enumerate(keys):
        tokens=re.findall(r'\w+',docs[key]);shingles={' '.join(tokens[j:j+5]) for j in range(max(1,len(tokens)-4))}
        sets.append(shingles)
        hashes=np.array([int.from_bytes(hashlib.blake2b(x.encode(),digest_size=4).digest(),'big') for x in shingles],dtype=np.uint64)
        sig=((hashes[:,None]*a+b)%np.uint64(4294967291)).min(axis=0)
        bandkeys=[(j,sig[j*4:j*4+4].tobytes()) for j in range(16)]
        possible=set()
        for bk in bandkeys:
            if len(bands[bk])<=500:possible.update(bands[bk])
            else:skipped+=1
        for k in possible:
            candidates+=1;s=sets[k]
            if min(len(s),len(shingles))/max(len(s),len(shingles))<.85:continue
            if len(s&shingles)/len(s|shingles)>=.85:
                x,y=find(i),find(k)
                if x!=y:parent[max(x,y)]=min(x,y);edges+=1
        for bk in bandkeys:bands[bk].append(i)
    mapping={key:keys[find(i)] for i,key in enumerate(keys)}
    (raw/'near_duplicate_groups.json').write_text(json.dumps(mapping))
    report={'method':'64-MinHash/16 bands of 4; 5-word shingles; exact set Jaccard >=0.85; connected components','seed':20261006,'normalized_groups':len(keys),'families':len(set(mapping.values())),'union_edges':edges,'candidate_pairs':candidates,'overfull_band_queries_skipped':skipped,'limitations':'Approximate candidate retrieval; transitive components may include less similar endpoints. No claim of exhaustive near-duplicate removal. Label blind.'}
    (ROOT/'research/cap-near-duplicate-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
if __name__=='__main__':main()
