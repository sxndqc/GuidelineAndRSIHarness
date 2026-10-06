import tempfile
import unittest
import io
import json
import urllib.error
from unittest.mock import patch
from pathlib import Path

from guideline_harness.model import CostMeter, BudgetExceeded, ChatModel, QuotaExhausted
from guideline_harness.protocol import AgentView


class RuntimeControls(unittest.TestCase):
    def test_quota_failure_stops_future_dispatches(self):
        body = io.BytesIO(json.dumps({'error': {'type': 'insufficient_quota', 'code': 'credit_balance_exhausted'}}).encode())
        error = urllib.error.HTTPError('https://example.invalid', 429, 'rejected', {}, body)
        with patch.dict('os.environ', {'TEST_API_CREDENTIAL': 'unit-test-fixture'}):
            model = ChatModel('fixture', 'https://example.invalid', 'TEST_API_CREDENTIAL')
        with patch('urllib.request.urlopen', side_effect=error) as request, patch.dict('os.environ', {'TEST_API_CREDENTIAL': 'unit-test-fixture'}):
            with self.assertRaises(QuotaExhausted):
                model.complete([])
            with self.assertRaises(QuotaExhausted):
                model.complete([])
            self.assertEqual(request.call_count, 1)

    def test_truncated_native_call_keeps_usage(self):
        response = {'choices': [{'message': {'content': None, 'tool_calls': [{'function': {'name': 'finish', 'arguments': '{'}}]}, 'finish_reason': 'length'}], 'usage': {'prompt_tokens': 5, 'completion_tokens': 10}}
        with patch.dict('os.environ', {'TEST_API_CREDENTIAL': 'unit-test-fixture'}):
            model = ChatModel('fixture', 'https://example.invalid', 'TEST_API_CREDENTIAL', native_tools=True)
            with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(response).encode())):
                result = model.complete([])
        self.assertEqual(result['finish_reason'], 'length')
        self.assertEqual(result['usage']['completion_tokens'], 10)

    def test_separate_meters_share_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'cost.json'
            a, b = CostMeter(path, .07), CostMeter(path, .07)
            a.reserve('fixture', [], 1000)
            with self.assertRaises(BudgetExceeded):
                b.reserve('fixture', [], 1000)

    def test_word_boundary_and_multiple_query_terms(self):
        view = AgentView({'manual': 'Nathan wrote this.\n' + 'x ' * 800 +
                          'Comparisons use than. C OMPARISON R EF is the label.'}, {})
        results = view.call('search_materials', {'query': 'than ComparisonRef'})
        self.assertTrue(results)
        self.assertIn('Comparisons', results[0]['text'])
        self.assertGreater(results[0]['start'], 0)

    def test_retrieval_ignores_gold_and_json_field_names(self):
        row = {'id': 'one', 'input': {'text': 'a dog', 'targets': []}, 'gold': {'x': ['p.Time', 'p.Time']}}
        view = AgentView({}, {'one': row})
        self.assertEqual(view.call('search_examples', {'query': 'Time token_indices'}), [])
        self.assertEqual(view.call('search_examples', {'query': 'dog'})[0]['example']['id'], 'one')


if __name__ == '__main__':
    unittest.main()
