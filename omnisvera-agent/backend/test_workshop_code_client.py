import unittest
from app.workshop_code_client import AnalysisAdapter, DENY
from app.ai_workshop_adapters import WorkshopAdapterError


class CodeClientTests(unittest.TestCase):
    def adapter(self, send):
        elapsed=[0.0]
        def sleep(seconds): elapsed[0]+=seconds
        return AnalysisAdapter(send, timeout=2, clock=lambda:elapsed[0], sleep=sleep)

    def job(self):
        return {'revision': 'v1', 'purpose': 'analisar', 'payload_json': {'sources': [
            {'path': 'fixture.txt', 'sha256': 'a' * 64, 'text': 'Dados de teste.'}]}}

    def transport(self, cost=0, permission=DENY, response=None, status=None):
        calls = []
        def send(method, path, body=None, **kw):
            calls.append((method, path, body))
            if path == '/provider': return {'connected': ['opencode'], 'all': [{'id': 'opencode', 'models': {
                'big-pickle': {'status': 'active', 'cost': {'input':cost,'output':cost,'cache':{'read':cost,'write':cost}}}}}]}
            if path == '/session': return {'id': 'ses_fixture'}
            if path == '/session/ses_fixture': return {'permission': permission}
            if path == '/experimental/tool/ids': return ['bash', 'read', 'mcp_fixture']
            if path.endswith('/prompt_async'): return None
            if path == '/session/status': return status or {}
            if path == '/permission': return []
            if path.endswith('/message'):
                if isinstance(response, Exception): raise response
                return [response or {'info': {'time': {'completed': 1}, 'tokens': {'input': 3, 'output': 2}},
                                    'parts': [{'type': 'text', 'text': 'Sugestão sem executar.'}]}]
            if path.endswith('/abort'): return True
            raise AssertionError(path)
        return send, calls

    def test_real_catalog_and_deny_all_are_required_before_dispatch(self):
        for kwargs in ({'cost': 1}, {'permission': []}):
            send, calls = self.transport(**kwargs)
            with self.assertRaises(WorkshopAdapterError): self.adapter(send)(self.job())
            self.assertFalse(any(p.endswith('/prompt_async') for _, p, _ in calls))

    def test_every_tool_disabled_and_text_remains_unexecuted(self):
        send, calls = self.transport()
        result = self.adapter(send)(self.job())
        body = next(b for _, p, b in calls if p.endswith('/prompt_async'))
        self.assertEqual(body['tools'], {'bash': False, 'read': False, 'mcp_fixture': False})
        self.assertFalse(result['output']['executed_suggestions'])
        self.assertEqual(result['status'], 'awaiting_approval')

    def test_ambiguous_dispatch_is_not_retried_and_only_own_session_aborted(self):
        send, calls = self.transport(response=TimeoutError())
        with self.assertRaises(WorkshopAdapterError) as caught: self.adapter(send)(self.job())
        self.assertTrue(caught.exception.ambiguous)
        self.assertEqual(sum(p.endswith('/prompt_async') for _, p, _ in calls), 1)
        self.assertEqual(calls[-1][1], '/session/ses_fixture/abort')

    def test_tool_call_or_incomplete_output_never_delivered(self):
        for response in ({'parts': [{'type': 'tool'}]}, {'parts': [{'type': 'text', 'text': 'unfinished'}]}):
            send, _ = self.transport(response=response)
            with self.assertRaises(WorkshopAdapterError): self.adapter(send)(self.job())

    def test_free_limit_is_reported_without_waiting_for_timeout(self):
        send,calls=self.transport(status={'ses_fixture':{'type':'retry','action':{'reason':'free_tier_limit'}}})
        with self.assertRaises(WorkshopAdapterError) as caught:self.adapter(send)(self.job())
        self.assertEqual(caught.exception.kind,'quota')
        self.assertEqual(caught.exception.message_code,'opencode_free_limit')
        self.assertEqual(sum(p.endswith('/prompt_async') for _,p,_ in calls),1)
        self.assertFalse(any(p.endswith('/message') for _,p,_ in calls))

    def test_other_sessions_quota_does_not_block_own_completed_output(self):
        send,_=self.transport(status={'ses_user':{'type':'retry','action':{'reason':'free_tier_limit'}}})
        self.assertEqual(self.adapter(send)(self.job())['status'],'awaiting_approval')

    def test_model_error_is_not_misreported_as_quota(self):
        send,_=self.transport(response={'info':{'error':{'name':'UnknownError','data':{'message':'provider unavailable'}}},'parts':[]})
        with self.assertRaises(WorkshopAdapterError) as caught:self.adapter(send)(self.job())
        self.assertEqual(caught.exception.kind,'provider_error')
