"""Non-LLM controls under the exact new study trajectories and evaluation IDs."""
import json
from pathlib import Path
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from guideline_harness.protocol import trajectory
from guideline_harness.baselines import predict
from guideline_harness.metrics import score_snacs,score_categorical
ROOT=Path(__file__).resolve().parents[1]
read=lambda p:json.loads(p.read_text())
def main():
 output=[]
 for task in ['snacs','cap_pa']:
  cfg=read(ROOT/f'configs/codex-study-{task}-sol.json');data=ROOT/cfg['data_root'];train=read(data/'private/train.json');test={r['id']:r for r in read(data/'private/test.json')};ids=read(ROOT/cfg['output']/'evaluation-ids.json');evaluation=[test[i] for i in ids];labels=set(read(ROOT/cfg['materials_manifest']).get('labels',[]))
  for seed in cfg['seeds']:
   order=trajectory(train,seed);seen=set();order=[r for r in order if not(r['group'] in seen or seen.add(r['group']))]
   for budget in [4,16,64]:
    purchased=order[:budget]
    for method in (['majority','lexical_majority','tfidf_nearest'] if task=='snacs' else ['majority','tfidf_nearest']):
     if task=='snacs':pred=predict(method,purchased,evaluation);metrics=score_snacs(evaluation,pred)
     else:
      majority=Counter(r['gold']['topic'] for r in purchased).most_common(1)[0][0]
      if method=='majority':pred={r['id']:{'topic':majority} for r in evaluation}
      else:
       vector=TfidfVectorizer(ngram_range=(1,2));a=vector.fit_transform([r['input']['text'] for r in purchased]);b=vector.transform([r['input']['text'] for r in evaluation]);sim=cosine_similarity(b,a)
       pred={r['id']:{'topic':purchased[int(np.argmax(sim[i]))]['gold']['topic'] if sim[i].max()>0 else majority} for i,r in enumerate(evaluation)}
      metrics=score_categorical(evaluation,pred,labels)
     target=ROOT/f'results/subscription-controls/{task}-{method}-s{seed}-b{budget}.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(pred,indent=2)+'\n')
     output.append({'task':task,'method':method,'seed':seed,'budget':budget,'metrics':metrics,'predictions':str(target.relative_to(ROOT))})
 (ROOT/'results/subscription-controls/results.json').write_text(json.dumps({'status':'completed','sampling':'shuffle rows then keep first per family, same as agent study','results':output},indent=2)+'\n');print('completed',len(output),'control cells')
if __name__=='__main__':main()
