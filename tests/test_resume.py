import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from guideline_harness.agent import run_agent
class ResumeTests(unittest.TestCase):
 def test_completed_cells_not_rerun_and_settings_locked(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);(p/'private').mkdir();manual=p/'guide.txt';manual.write_text('test fixture')
   row={'id':'r','group':'g','input':{'text':'test','targets':[{'id':'t'}]},'gold':{'t':['p.Time','p.Time']}}
   for split in ['train','test']:(p/'private'/f'{split}.json').write_text(json.dumps([row]))
   manifest=p/'materials.json';manifest.write_text(json.dumps({'status':'audited','files':[{'name':'guide','path':str(manual),'sha256':hashlib.sha256(manual.read_bytes()).hexdigest()}]}))
   cfg={'backend':'codex_cli','model':'fixture','subscription_ledger':str(p/'ledger'),'data_root':td,'output':str(p/'out'),'materials_manifest':str(manifest),'evaluation_split':'test','conditions':['frozen'],'budgets':[0,1],'seeds':[11]};path=p/'config.json';path.write_text(json.dumps(cfg))
   with patch('guideline_harness.codex_model.CodexModel') as model:
    model.return_value.complete.return_value={'text':json.dumps({'action':'finish','arguments':{'prediction':row['gold']}})}
    first=run_agent(path);self.assertEqual(model.return_value.complete.call_count,2)
   cfg.update(resume=True,subscription_call_limit=999);path.write_text(json.dumps(cfg))
   with patch('guideline_harness.codex_model.CodexModel') as model:
    second=run_agent(path);self.assertEqual(model.return_value.complete.call_count,0);self.assertEqual(first['results'],second['results'])
   cfg['predict_calls']=99;path.write_text(json.dumps(cfg))
   with self.assertRaises(ValueError):run_agent(path)
if __name__=='__main__':unittest.main()

class EpisodeContinuationTests(unittest.TestCase):
 def test_transport_continuation_preserves_exact_messages(self):
  import copy
  from guideline_harness.agent import episode
  from guideline_harness.protocol import AgentView
  from guideline_harness.codex_model import CodexBackendUnavailable
  captured=[]
  class Interrupted:
   def complete(self,messages):
    captured.append(copy.deepcopy(messages))
    if len(captured)==1:return {'text':json.dumps({'action':'read_material','arguments':{'name':'guide'}})}
    raise CodexBackendUnavailable('fixture interruption','capacity')
  first=episode(Interrupted(),AgentView({'guide':'test'},{}),{'phase':'evaluate'},max_calls=4)
  class Continued:
   def complete(self,messages):
    self.messages=copy.deepcopy(messages)
    return {'text':json.dumps({'action':'finish','arguments':{'prediction':{}}})}
  model=Continued();second=episode(model,AgentView({'guide':'test'},{}),{'phase':'evaluate'},max_calls=4,prior=first)
  self.assertEqual(captured[-1],model.messages)
  self.assertEqual(second['status'],'completed')

class AssetContinuationTests(unittest.TestCase):
 def test_successful_write_restored_without_second_model_call(self):
  from guideline_harness.agent import episode
  from guideline_harness.protocol import AgentView
  class Once:
   def complete(self,messages):raise AssertionError('Completed episode must not invoke model again')
  action={'action':'write_asset','arguments':{'name':'dir//rules.md','text':'observed rule'}}
  prior={'status':'completed','answer':{'summary':'done'},'trace':[{'step':0,'text':json.dumps(action)},{'step':0,'tool_name':'write_asset','tool_result':{'written':'dir/rules.md','characters':13}},{'step':1,'text':json.dumps({'action':'finish','arguments':{'summary':'done'}})}],'tool_log':[]}
  view=AgentView({}, {},writable=True);result=episode(Once(),view,{'phase':'adapt'},prior=prior)
  self.assertEqual(result,prior);self.assertEqual(view.assets,{'dir/rules.md':'observed rule'})

class RefuseUnsafeContinuation(unittest.TestCase):
 def test_isolation_failure_cannot_resume(self):
  from guideline_harness.agent import episode
  from guideline_harness.protocol import AgentView
  from guideline_harness.codex_model import CodexBackendUnavailable
  with self.assertRaises(CodexBackendUnavailable):
   episode(None,AgentView({},{}),{},prior={'status':'backend_unavailable','backend_reason':'isolation_violation','trace':[]})
