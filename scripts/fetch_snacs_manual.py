"""Fetch the pinned public reference locally; do not redistribute its full text."""
import hashlib,json,subprocess,urllib.request
from pathlib import Path
root=Path('data/raw/papers');root.mkdir(parents=True,exist_ok=True)
manifest=json.loads(Path('configs/snacs-materials.json').read_text())
pdf=root/'snacs-guidelines.pdf';text=root/'snacs-guidelines.txt'
with urllib.request.urlopen(manifest['source']['pdf_url'],timeout=60) as response:
    content=response.read(5_000_001)
assert len(content)<=5_000_000
assert hashlib.sha256(content).hexdigest()==manifest['source']['pdf_sha256'], 'Pinned manual changed; audit before use'
pdf.write_bytes(content)
subprocess.run(['pdftotext','-layout',str(pdf),str(text)],check=True)
assert hashlib.sha256(text.read_bytes()).hexdigest()==manifest['files'][0]['sha256'], 'Text extraction differs; audit extraction before use'
manifest['files'][0]['path']=str(text)
Path('configs/snacs-materials.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Pinned guideline fetched, extracted and verified.')
