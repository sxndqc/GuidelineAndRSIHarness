import urllib.request,json,pathlib,io,zipfile,hashlib,random
ROOT=pathlib.Path('data/raw/fashionpedia'); ROOT.mkdir(parents=True,exist_ok=True)
TOTAL=0; LIMIT=90_000_000

def get(url,start=None,length=None):
 global TOTAL
 headers={} if start is None else {'Range':f'bytes={start}-{start+length-1}'}
 with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=40) as r:
  if start is not None and r.status!=206:raise RuntimeError('server ignored range')
  cap=length if length is not None else 30_000_000
  if TOTAL+cap>LIMIT:raise RuntimeError('transfer limit')
  b=r.read(cap+1)
  if len(b)>cap:raise RuntimeError('response exceeds cap')
  TOTAL+=len(b);return b

if not (ROOT/'val.json').exists():
 (ROOT/'val.json').write_bytes(get('https://s3.amazonaws.com/ifashionist-dataset/annotations/instances_attributes_val2020.json'))
u='https://s3.amazonaws.com/ifashionist-dataset/annotations/attributes_train2020.json'
p=ROOT/'global_train.json'
if not p.exists():p.write_bytes(get(u))
global_train=json.loads(p.read_text()); print('global train ready',len(global_train['images']),flush=True)
prefix=get('https://s3.amazonaws.com/ifashionist-dataset/annotations/instances_attributes_train2020.json',0,4_000_000)
s=prefix.decode();pos=s.index('[')+1;decoder=json.JSONDecoder();anns=[]
while pos<len(s):
 while pos<len(s) and s[pos] in ' \n\r\t,':pos+=1
 try:a,end=decoder.raw_decode(s,pos)
 except json.JSONDecodeError:break
 anns.append(a);pos=end
# Exclude final potentially incomplete image group. Use all annotations for selected complete image ids.
ids=list(dict.fromkeys(a['image_id'] for a in anns))
assert len(ids)>16, 'Need a following complete image group to bound selection'
chosen=ids[:16]; imap={i['id']:i for i in global_train['images']}
train={'images':[imap[i] for i in chosen], 'annotations':[a for a in anns if a['image_id'] in chosen], 'categories':json.loads((ROOT/'val.json').read_text())['categories'],'attributes':global_train['attributes'],'licenses':global_train['licenses']}
(ROOT/'train_prefix_pilot.json').write_text(json.dumps(train))
val=json.loads((ROOT/'val.json').read_text()); vids=random.Random(20261006).sample(sorted(i['id'] for i in val['images']),16); vset=set(vids)
valsmall={k:val[k] for k in ('categories','attributes','licenses')};valsmall['images']=[i for i in val['images'] if i['id'] in vset];valsmall['annotations']=[a for a in val['annotations'] if a['image_id'] in vset];(ROOT/'val_pilot.json').write_text(json.dumps(valsmall))
class Remote(io.RawIOBase):
 def __init__(self,url,size):self.url=url;self.size=size;self.pos=0
 def seekable(self):return True
 def readable(self):return True
 def tell(self):return self.pos
 def seek(self,off,whence=0):
  self.pos=off if whence==0 else self.pos+off if whence==1 else self.size+off;return self.pos
 def read(self,n=-1):
  n=self.size-self.pos if n<0 else min(n,self.size-self.pos)
  if n==0:return b''
  b=get(self.url,self.pos,n);self.pos+=len(b);return b
log=[]
for split,data,url,size in [('train',train,'https://s3.amazonaws.com/ifashionist-dataset/images/train2020.zip',3344364592),('val',valsmall,'https://s3.amazonaws.com/ifashionist-dataset/images/val_test2020.zip',236499034)]:
 folder=ROOT/'images'/split;folder.mkdir(parents=True,exist_ok=True)
 z=zipfile.ZipFile(Remote(url,size)); lookup={pathlib.PurePosixPath(n).name:n for n in z.namelist()};print('zip entries',split,len(lookup),flush=True)
 for i in data['images']:
  member=lookup[i['file_name']];b=z.read(member);p=folder/i['file_name'];p.write_bytes(b)
  log.append({'split':split,'image_id':i['id'],'file':str(p.relative_to(ROOT)),'source_zip':url,'zip_member':member,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
  print('image ready',split,i['id'],len(b),'transfer',TOTAL,flush=True)
(ROOT/'bounded_acquisition.json').write_text(json.dumps({'total_download_bytes':TOTAL,'train_selection':'first 16 complete image groups in 4MB instance train JSON prefix; engineering pilot only','val_seed':20261006,'images':log},indent=2))
print('DONE',TOTAL, len(train['annotations']),len(valsmall['annotations']),flush=True)
