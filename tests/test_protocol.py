import copy
import json
import unittest
from guideline_harness.protocol import AgentView, BudgetLedger, trajectory, safe_path
from guideline_harness.data import project_snacs
from guideline_harness.metrics import score_snacs
from guideline_harness.baselines import predict
from guideline_harness.agent import episode

RECORD={'id':'doc-1','group':'doc','input':{'text':'for work','tokens':['for','work'],
    'targets':[{'id':'swes:1','token_indices':[1],'text':'for'}]},'gold':{'swes:1':['p.Purpose','p.Purpose']}}

class ProtocolTests(unittest.TestCase):
    def test_budget_repeat_and_overrun(self):
        ledger=BudgetLedger(1)
        first=ledger.reveal(RECORD);ledger.reveal(RECORD)
        first['gold'].clear()
        self.assertEqual(len(RECORD['gold']),1)
        other=copy.deepcopy(RECORD);other['id']='doc-2'
        with self.assertRaises(ValueError):ledger.reveal(other)
        self.assertEqual(ledger.summary()['unique_labeled_sentences'],1)
        self.assertEqual(ledger.summary()['labeled_decisions'],1)
        self.assertEqual(ledger.summary()['reveal_calls'],2)

    def test_frozen_assets_and_unpurchased_examples(self):
        original={'rules.md':'a'}
        view=AgentView({'manual':'b'},{},original,writable=False)
        with self.assertRaises(ValueError):view.call('write_asset',{'name':'x','text':'changed'})
        with self.assertRaises(ValueError):view.call('read_example',{'id':RECORD['id']})
        with self.assertRaises(ValueError):view.call('read_material',{'name':'/tmp/gold'})
        view.assets['rules.md']='local'
        self.assertEqual(original['rules.md'],'a')

    def test_path_traversal(self):
        for path in ['/etc/passwd','../gold','x/../../gold','name\x00.py']:
            with self.assertRaises(ValueError):safe_path(path)

    def test_projection_strips_hidden_labels(self):
        raw={'sent_id':'reviews-001-0001','text':'for work','toks':[{'word':'for','misc':['SECRET'],'head':2},{'word':'work'}],
             'swes':{'1':{'ss':'p.Purpose','ss2':'p.Purpose','toknums':[1],'lexcat':'P'}},'smwes':{}}
        result,ignored=project_snacs(raw)
        dumped=json.dumps(result['input'])
        self.assertNotIn('SECRET',dumped)
        self.assertNotIn('p.Purpose',dumped)
        self.assertNotIn('head',dumped)
        self.assertEqual(result['group'],'reviews-001')
        self.assertEqual(ignored,0)

    def test_metrics_gold_empty_invalid(self):
        gold={RECORD['id']:RECORD['gold']}
        self.assertEqual(score_snacs([RECORD],gold)['joint_accuracy'],1)
        self.assertEqual(score_snacs([RECORD],{})['joint_accuracy'],0)
        self.assertEqual(score_snacs([RECORD],{RECORD['id']:{'swes:1':['garbage','garbage']}})['valid_output_rate'],0)
        self.assertEqual(score_snacs([RECORD],{RECORD['id']:{'swes:1':'bad'}})['valid_output_rate'],0)
        extra={RECORD['id']:{**RECORD['gold'],'invented':['p.Time','p.Time']}}
        self.assertEqual(score_snacs([RECORD],extra)['sentence_exact'],0)

    def test_trajectories_nested(self):
        records=[{'id':str(i)} for i in range(20)]
        self.assertEqual(trajectory(records,11)[:4],trajectory(records,11)[:16][:4])
        self.assertNotEqual(trajectory(records,11),trajectory(records,23))

    def test_predict_ignores_test_gold(self):
        original=predict('tfidf_nearest',[RECORD],[RECORD])
        changed=copy.deepcopy(RECORD);changed['gold']={'swes:1':['p.Time','p.Time']}
        self.assertEqual(original,predict('tfidf_nearest',[RECORD],[changed]))
        del changed['gold']
        self.assertEqual(original,predict('tfidf_nearest',[RECORD],[changed]))

    def test_episode_tools_frozen_and_logs(self):
        class Stub:
            # Unit test fixture only, never an empirical model result.
            def __init__(self):self.calls=0
            def complete(self,messages):
                self.calls+=1
                action={'action':'write_asset','arguments':{'name':'bad','text':'x'}} if self.calls==1 else {'action':'finish','arguments':{'prediction':RECORD['gold']}}
                return {'text':json.dumps(action),'usage':{}}
        view=AgentView({}, {},writable=False)
        result=episode(Stub(),view,{},max_calls=2)
        self.assertEqual(result['status'],'completed')
        self.assertEqual(view.assets,{})
        self.assertTrue(any('tool_or_schema_error' in item for item in result['trace']))

class AgentSchemaTests(unittest.TestCase):
    def test_malformed_finish_does_not_escape(self):
        for args in [None, [], {}, {'prediction': None}, {'prediction': []}]:
            class Stub:
                def complete(self,messages):
                    return {'text':json.dumps({'action':'finish','arguments':args}), 'usage':{}}
            result=episode(Stub(),AgentView({},{}),{'phase':'evaluate'},max_calls=1)
            self.assertEqual(result['status'],'tool_budget_exhausted')

    def test_truncation_preserves_usage(self):
        class Stub:
            def complete(self,messages):
                return {'text':'{', 'usage':{'completion_tokens':123},'finish_reason':'length','response_id':'unit-test'}
        result=episode(Stub(),AgentView({},{}),{'phase':'evaluate'})
        self.assertEqual(result['status'],'truncated')
        self.assertEqual(result['trace'][0]['usage']['completion_tokens'],123)

if __name__=='__main__':unittest.main()
