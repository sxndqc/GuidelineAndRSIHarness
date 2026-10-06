"""Deterministic, label-independent given-box crops; not official Fashionpedia AP."""
import json, random, hashlib
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path('data/raw/fashionpedia')
OUT=Path('data/prepared/fashion-pilot')
OUT.mkdir(parents=True,exist_ok=True)
metadata={}
for split,filename in [('train','train_prefix_pilot.json'),('val','val_pilot.json')]:
    source=json.loads((ROOT/filename).read_text())
    rows=[]; excluded=0
    for image in sorted(source['images'],key=lambda x:x['id']):
        candidates=[]
        for a in source['annotations']:
            if a['image_id']!=image['id']:continue
            x,y,w,h=a['bbox']
            if w<=0 or h<=0:excluded+=1;continue
            candidates.append(a)
        if not candidates:continue
        a=random.Random(20261006+image['id']).choice(sorted(candidates,key=lambda a:a['id']))
        x,y,w,h=a['bbox'];pad=.1*max(w,h)
        box=[max(0,int(x-pad)),max(0,int(y-pad)),min(image['width'],int(x+w+pad+1)),min(image['height'],int(y+h+pad+1))]
        im=Image.open(ROOT/'images'/split/image['file_name']).convert('RGB').crop(box)
        draw=ImageDraw.Draw(im);draw.rectangle([x-box[0],y-box[1],x+w-box[0],y+h-box[1]],outline='red',width=max(1,round(min(w,h)*.02)))
        original=im.size;im.thumbnail((512,512))
        path=OUT/f'{split}-{image["id"]}-{a["id"]}.jpg';im.save(path,quality=90)
        rows.append({'id':str(a['id']),'group':str(image['id']),'input':{'text':'Identify the marked object in this provided bounding-box crop.','image':str(path),'targets':[{'id':'region','text':'marked region'}]},'gold':{'region':[str(a['category_id']),','.join(map(str,sorted(a['attribute_ids'])))]},'crop':{'bbox':a['bbox'],'context_box':box,'original_crop_size':original,'model_image_size':im.size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}})
    (OUT/f'{split}.json').write_text(json.dumps(rows,indent=2))
    metadata[split]={'examples':len(rows),'ids':[r['id'] for r in rows],'images':[r['group'] for r in rows],'invalid_bbox_exclusions':excluded}
    if split=='train':
        taxonomy={'categories':source['categories'],'attributes':source['attributes']}
        (OUT/'taxonomy.txt').write_text('This is the official name/hierarchy inventory, not a complete annotation manual.\n'+json.dumps(taxonomy,ensure_ascii=False,indent=2))
(OUT/'selection.json').write_text(json.dumps(metadata,indent=2))
print(json.dumps(metadata,indent=2))
