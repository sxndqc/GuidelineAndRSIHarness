import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from guideline_harness.agent import moderate
ROW={'id':'r','group':'g','input':{'text':'for work','targets':[{'id':'t'}]},'gold':{'t':['p.Purpose','p.Purpose']}}
class ModerationTests(unittest.TestCase):
    def run_case(self,side):
        with tempfile.TemporaryDirectory() as d:
            with patch('guideline_harness.agent.episode',side_effect=side) as mock:
                result=moderate(None,{}, {'r':ROW},{},'', 'pair',{},Path(d),'test')
                logs=list((Path(d)/'moderation').glob('*.json'))
                return result,mock.call_count,logs[0].read_text()
    def test_failed_probe_never_becomes_semantic_error(self):
        result,n,log=self.run_case([{'status':'tool_budget_exhausted'}])
        self.assertEqual(result,{})
        self.assertEqual(n,1)
        self.assertIn('before_probe_invalid',log)
    def test_missing_stage_asset_rejected(self):
        before={'status':'completed','answer':{'prediction':{'r::t':['p.Time','p.Time']}}}
        result,n,log=self.run_case([before,{'status':'completed','answer':{'summary':'done'}}])
        self.assertEqual(result,{})
        self.assertEqual(n,2)
        self.assertIn('incomplete_stage',log)
    def test_no_error_skips_update(self):
        before={'status':'completed','answer':{'prediction':{'r::t':['p.Purpose','p.Purpose']}}}
        result,n,log=self.run_case([before])
        self.assertEqual(n,1)
        self.assertIn('no adaptation errors',log)
if __name__=='__main__':unittest.main()
