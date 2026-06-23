import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from services.ai_agent import LightweightContactAgent


def _mock_requests_response(content_dict, status_code=200):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": json.dumps(content_dict)}}]
    }
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def _mock_requests_error(status_code=403):
    import requests
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    http_err = requests.exceptions.HTTPError(response=mock_resp)
    mock_resp.raise_for_status.side_effect = http_err
    return mock_resp


class TestIsRemoteAvailable(unittest.TestCase):
    @patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test", "OPENROUTER_API_KEY": ""})
    def test_true_when_groq_key_set(self):
        agent = LightweightContactAgent()
        self.assertTrue(agent.is_remote_available)

    @patch.dict(os.environ, {"GROQ_API_KEY": "", "OPENROUTER_API_KEY": "or_test"})
    def test_true_when_openrouter_key_set(self):
        agent = LightweightContactAgent()
        self.assertTrue(agent.is_remote_available)

    @patch.dict(os.environ, {"GROQ_API_KEY": "", "OPENROUTER_API_KEY": ""})
    def test_false_when_no_keys(self):
        agent = LightweightContactAgent()
        self.assertFalse(agent.is_remote_available)


class TestCallApi(unittest.TestCase):
    @patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test", "OPENROUTER_API_KEY": ""})
    def test_uses_groq_when_key_present(self):
        agent = LightweightContactAgent()
        with patch("services.ai_agent._requests.post", return_value=_mock_requests_response({"ok": True})) as mock_post:
            result = agent._call_api([{"role": "user", "content": "test"}])
        url = mock_post.call_args[0][0]
        self.assertIn("groq.com", url)
        self.assertIn("ok", result)

    @patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test", "OPENROUTER_API_KEY": "or_test"})
    def test_falls_back_to_openrouter_when_groq_fails(self):
        agent = LightweightContactAgent()
        call_count = 0

        def side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if "groq.com" in url:
                raise Exception("Groq unavailable")
            return _mock_requests_response({"fallback": True})

        with patch("services.ai_agent._requests.post", side_effect=side_effect):
            result = agent._call_api([{"role": "user", "content": "test"}])

        self.assertEqual(call_count, 2)
        self.assertIn("fallback", result)

    @patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test", "OPENROUTER_API_KEY": "or_test"})
    def test_raises_when_both_fail(self):
        agent = LightweightContactAgent()

        def always_fail(url, **kwargs):
            raise Exception("network error")

        with patch("services.ai_agent._requests.post", side_effect=always_fail):
            with self.assertRaises(RuntimeError) as ctx:
                agent._call_api([{"role": "user", "content": "test"}])
        self.assertIn("Groq", str(ctx.exception))
        self.assertIn("OpenRouter", str(ctx.exception))

    @patch.dict(os.environ, {"GROQ_API_KEY": "", "OPENROUTER_API_KEY": ""})
    def test_raises_no_provider_configured(self):
        agent = LightweightContactAgent()
        with self.assertRaises(RuntimeError) as ctx:
            agent._call_api([{"role": "user", "content": "test"}])
        self.assertIn("No AI provider configured", str(ctx.exception))

    @patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test", "OPENROUTER_API_KEY": ""})
    def test_uses_vision_model_when_use_vision_true(self):
        agent = LightweightContactAgent()
        captured = {}

        def capture(url, **kwargs):
            captured["model"] = kwargs["json"]["model"]
            return _mock_requests_response({"vision": True})

        with patch("services.ai_agent._requests.post", side_effect=capture):
            agent._call_api([{"role": "user", "content": "img"}], use_vision=True)

        self.assertEqual(captured["model"], agent.groq_vision_model)


if __name__ == "__main__":
    unittest.main()
