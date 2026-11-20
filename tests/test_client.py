import base64
import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch


CLIENT = Path(__file__).parents[1] / "scripts" / "nano_banana.py"
SPEC = importlib.util.spec_from_file_location("nano_banana", CLIENT)
CLIENT_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLIENT_MODULE)


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.TemporaryDirectory()
        self.original_home = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = self.home.name

    def tearDown(self):
        if self.original_home is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self.original_home
        self.home.cleanup()

    def test_save_key_is_private_on_unix(self):
        CLIENT_MODULE.save_key("sk-test-value")
        path = CLIENT_MODULE.config_path()
        self.assertEqual(json.loads(path.read_text())["api_key"], "sk-test-value")
        if os.name != "nt":
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)

    def test_request_uses_chongplus_endpoint_and_bearer_auth(self):
        CLIENT_MODULE.save_key("sk-test-value")
        response = MagicMock()
        response.status = 200
        response.read.return_value = b'{"data": []}'
        response.__enter__.return_value = response
        with patch.object(CLIENT_MODULE.urllib.request, "urlopen", return_value=response) as urlopen:
            self.assertEqual(CLIENT_MODULE.request("/v1/images/generations", b"{}", "application/json"), {"data": []})
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://ai.chongplus.plus/v1/images/generations")
        self.assertEqual(request.get_header("Authorization"), "Bearer sk-test-value")

    def test_request_does_not_retry_after_network_failure(self):
        CLIENT_MODULE.save_key("sk-test-value")
        with patch.object(CLIENT_MODULE.urllib.request, "urlopen", side_effect=urllib.error.URLError("unavailable")) as urlopen:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                CLIENT_MODULE.request("/v1/images/generations", b"{}", "application/json")
        self.assertEqual(urlopen.call_count, 1)

    def test_generate_payload_uses_nano_banana_model(self):
        args = CLIENT_MODULE.argparse.Namespace(action="generate", prompt="test prompt", size="1024x1024", n=1, output_dir=self.home.name, status_file=None)
        with patch.object(CLIENT_MODULE, "ensure_model_supported"), patch.object(CLIENT_MODULE, "request", return_value={"data": [{"b64_json": base64.b64encode(b"image-bytes").decode()}]}) as request:
            with contextlib.redirect_stdout(io.StringIO()):
                CLIENT_MODULE.run_image(args)
        payload = json.loads(request.call_args.args[1])
        self.assertEqual(payload["model"], "gemini-2.5-flash-image")
        self.assertEqual(payload["response_format"], "b64_json")

    def test_url_download_uses_authentication_headers(self):
        CLIENT_MODULE.save_key("sk-test-value")
        response = MagicMock()
        response.read.return_value = b"image-bytes"
        response.headers.get_content_type.return_value = "image/png"
        response.__enter__.return_value = response
        with patch.object(CLIENT_MODULE.urllib.request, "urlopen", return_value=response) as urlopen:
            CLIENT_MODULE.download_image("https://example.test/result")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer sk-test-value")

    def test_run_image_writes_success_status_without_sensitive_input(self):
        output_dir = Path(self.home.name) / "outputs"
        status_path = Path(self.home.name) / "status.json"
        args = CLIENT_MODULE.argparse.Namespace(action="generate", prompt="test prompt", size="1024x1024", n=1, output_dir=str(output_dir), status_file=str(status_path))
        response = {"data": [{"b64_json": base64.b64encode(b"image-bytes").decode()}]}
        with patch.object(CLIENT_MODULE, "ensure_model_supported"), patch.object(CLIENT_MODULE, "request", return_value=response):
            with contextlib.redirect_stdout(io.StringIO()):
                CLIENT_MODULE.run_image(args)
        status = json.loads(status_path.read_text())
        self.assertEqual(status["state"], "succeeded")
        self.assertEqual(status["action"], "generate")
        self.assertNotIn("prompt", status)
        self.assertNotIn("api_key", status)

    def test_cached_models_are_reused_until_ttl_expires(self):
        cache_path = CLIENT_MODULE.models_cache_path()
        cache_path.parent.mkdir(parents=True)
        cache_path.write_text(json.dumps({"checked_at": 1000, "fetched_at": 1000, "models": [CLIENT_MODULE.MODEL]}))
        with patch.object(CLIENT_MODULE.time, "time", return_value=1000 + CLIENT_MODULE.MODELS_CACHE_TTL_SECONDS - 1):
            with patch.object(CLIENT_MODULE, "fetch_models") as fetch:
                self.assertEqual(CLIENT_MODULE.supported_models(), [CLIENT_MODULE.MODEL])
        fetch.assert_not_called()

    def test_model_list_refresh_is_cached(self):
        CLIENT_MODULE.save_key("sk-test-value")
        response = MagicMock()
        response.read.return_value = json.dumps({"data": [{"id": CLIENT_MODULE.MODEL}, {"id": "other-image-model"}]}).encode()
        response.__enter__.return_value = response
        with patch.object(CLIENT_MODULE.urllib.request, "urlopen", return_value=response) as urlopen:
            models = CLIENT_MODULE.fetch_models()
        self.assertEqual(models, [CLIENT_MODULE.MODEL, "other-image-model"])
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 2)
        cache = json.loads(CLIENT_MODULE.models_cache_path().read_text())
        self.assertEqual(cache["models"], models)
        self.assertIn("checked_at", cache)
        self.assertNotIn("api_key", cache)

    def test_recent_failed_check_is_throttled_for_ttl(self):
        cache_path = CLIENT_MODULE.models_cache_path()
        cache_path.parent.mkdir(parents=True)
        now = CLIENT_MODULE.MODELS_CACHE_TTL_SECONDS + 1001
        cache_path.write_text(json.dumps({"checked_at": now - 1, "fetched_at": 1, "models": ["old-model"]}))
        with patch.object(CLIENT_MODULE.time, "time", return_value=now):
            with patch.object(CLIENT_MODULE, "fetch_models") as fetch:
                self.assertIsNone(CLIENT_MODULE.supported_models())
        fetch.assert_not_called()

    def test_query_failure_does_not_block_generation(self):
        args = CLIENT_MODULE.argparse.Namespace(action="generate", prompt="test prompt", size="1024x1024", n=1, output_dir=self.home.name, status_file=None)
        response = {"data": [{"b64_json": base64.b64encode(b"image-bytes").decode()}]}
        with patch.object(CLIENT_MODULE, "supported_models", return_value=None), patch.object(CLIENT_MODULE, "request", return_value=response) as request:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                CLIENT_MODULE.run_image(args)
        request.assert_called_once()

    def test_successful_query_missing_model_blocks_generation(self):
        args = CLIENT_MODULE.argparse.Namespace(action="generate", prompt="test prompt", size="1024x1024", n=1, output_dir=self.home.name, status_file=None)
        with patch.object(CLIENT_MODULE, "supported_models", return_value=["different-model"]), patch.object(CLIENT_MODULE, "request") as request:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                CLIENT_MODULE.run_image(args)
        request.assert_not_called()

    def test_missing_model_blocks_generation(self):
        args = CLIENT_MODULE.argparse.Namespace(action="generate", prompt="test prompt", size="1024x1024", n=1, output_dir=self.home.name, status_file=None)
        with patch.object(CLIENT_MODULE, "ensure_model_supported", side_effect=CLIENT_MODULE.ClientError("model unavailable")), patch.object(CLIENT_MODULE, "request") as request:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                CLIENT_MODULE.run_image(args)
        request.assert_not_called()

    def test_invalid_size_writes_failed_status(self):
        status_path = Path(self.home.name) / "status.json"
        args = CLIENT_MODULE.argparse.Namespace(action="generate", prompt="test prompt", size="invalid", n=1, output_dir=str(Path(self.home.name) / "outputs"), status_file=str(status_path))
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            CLIENT_MODULE.run_image(args)
        status = json.loads(status_path.read_text())
        self.assertEqual(status["state"], "failed")
        self.assertIn("Unsupported size", status["error"])
