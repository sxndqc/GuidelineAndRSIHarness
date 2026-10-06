"""Download official paired CAP PA sources with fixed hashes and verified TLS."""
import hashlib,json,subprocess,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='https://minio.la.utexas.edu/compagendas/'
SOURCES=[('bills_resolutions.csv','datasetfiles/AlltopicsBillsandResolutionsRegularSessions1979_2019_11132019_CAP.csv','0d9909058b2f00d6005840484d5fb711930e039c49b060dd6d48e2ba4d1bded3'),('policy_topics_codebook.pdf','codebookfiles/II._Policy_Topics_Coding_061719_1.pdf','d68c499a6f1f877294936ab8dc3cdde41c3df28a34dd1d81c8e4f76fc65d6944')]
def main():
 raw=ROOT/'data/raw/cap-pa';raw.mkdir(parents=True,exist_ok=True);records=[]
 for name,url,expected in SOURCES:
  path=raw/name
  if not path.exists():
   req=urllib.request.Request(BASE+url,headers={'User-Agent':'GuidelineAndRSIHarness research source fetch'})
   with urllib.request.urlopen(req,timeout=120) as response:body=response.read(50_000_001)
   if len(body)>50_000_000:raise ValueError('Source exceeded bounded download size')
   if hashlib.sha256(body).hexdigest()!=expected:raise ValueError('Source changed; re-audit required')
   path.write_bytes(body)
  if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('Local source checksum mismatch')
  records.append({'file':name,'url':BASE+url,'sha256':expected,'bytes':path.stat().st_size})
 text=raw/'policy_topics_codebook.txt'
 subprocess.run(['pdftotext','-layout',str(raw/'policy_topics_codebook.pdf'),str(text)],check=True)
 if hashlib.sha256(text.read_bytes()).hexdigest()!='033cbacffdc3b6240565e84c6bdfb0c1d850a418f71543cadda10d605ec92763':raise ValueError('Extraction differs; review before preparing data')
 (raw/'source.json').write_text(json.dumps({'url':records[0]['url'],'bytes':records[0]['bytes'],'sha256':records[0]['sha256'],'rows':102727},indent=2)+'\n')
 print(json.dumps(records,indent=2))
if __name__=='__main__':main()
