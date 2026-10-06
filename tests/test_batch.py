import copy,unittest
from guideline_harness.agent import pack_batches
from guideline_harness.protocol import AgentView
from guideline_harness.metrics import score_categorical

class BatchTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{'id':str(i),'group':str(i//2),'input':{'text':'text','targets':[{'id':'topic'}]},'gold':{'topic':'100'}} for i in range(6)]
    def test_whole_groups_and_no_gold(self):
        original=copy.deepcopy(self.rows)
        batches=pack_batches(self.rows,2)
        self.assertEqual([len(b['_rows']) for b in batches],[4,2])
        self.assertEqual(self.rows,original)
        self.assertNotIn('gold',str(batches[0]['input']))
        self.assertEqual(len({t['id'] for t in batches[0]['input']['targets']}),4)
    def test_batch_examples_access(self):
        view=AgentView({}, {r['id']:r for r in self.rows})
        self.assertEqual(len(view.call('read_examples',{'ids':['0','1']})),2)
        for ids in [[],['absent'],['0']*17]:
            with self.assertRaises(ValueError):view.call('read_examples',{'ids':ids})
    def test_category_missing_invalid_extra(self):
        pred={r['id']:r['gold'] for r in self.rows}
        self.assertEqual(score_categorical(self.rows,pred,{'100','200'})['accuracy'],1)
        pred['0']={'topic':[]};pred['1']={'topic':'100','extra':'100'}
        m=score_categorical(self.rows,pred,{'100','200'})
        self.assertAlmostEqual(m['accuracy'],5/6)
        self.assertAlmostEqual(m['valid_output_rate'],4/6)
if __name__=='__main__':unittest.main()
