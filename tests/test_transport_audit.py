import json,unittest
from guideline_harness.transport_audit import audit_timeout_stream
class TimeoutAuditTests(unittest.TestCase):
 def audit(self,*events):return audit_timeout_stream('\n'.join(json.dumps(e) for e in events))['resumable']
 def test_partial_safe_turn(self):
  self.assertTrue(self.audit({'type':'thread.started'},{'type':'turn.started'},{'type':'item.completed','item':{'type':'agent_message','text':json.dumps({'action':'search_materials','arguments_json':'{}'})}}))
 def test_native_tool_forbidden(self):
  self.assertFalse(self.audit({'type':'turn.started'},{'type':'item.completed','item':{'type':'command_execution'}}))
 def test_refusal_or_completed_turn_not_retried(self):
  for e in [{'type':'error','message':'policy refusal'},{'type':'turn.completed'},{'type':'turn.failed'},{'type':'item.completed','item':{'type':'error','message':'unknown'}}]:
   self.assertFalse(self.audit({'type':'turn.started'},e))
 def test_broken_stream(self):self.assertFalse(audit_timeout_stream('{broken')['resumable'])
if __name__=='__main__':unittest.main()
