import unittest
import httpx
from app.cloudflare_provider import _http_error


class CloudflareErrorTests(unittest.TestCase):
    def error(self, code, message):
        return str(_http_error(httpx.Response(429, json={'errors': [{'code': code, 'message': message}]})))

    def test_observed_4006_confirms_daily_quota_without_exposing_raw_message(self):
        message = 'AiError: you have used up your daily free allocation of 10,000 neurons, secret-token'
        result = self.error(4006, message)
        self.assertIn('confirmada pelo provider', result)
        self.assertIn('21h', result)
        self.assertNotIn('secret-token', result)

    def test_4006_without_explicit_explanation_remains_unknown(self):
        self.assertIn('não foi confirmada', self.error(4006, 'Another error'))

    def test_capacity_is_not_daily_quota(self):
        self.assertIn('não foi confirmada', self.error(3040, 'Capacity temporarily exceeded'))

    def test_documented_daily_quota_code(self):
        self.assertIn('confirmada pelo provider', self.error(3036, ''))
