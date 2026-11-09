"""
Unit tests for LLM-Based Build/Error-Log Summarization (app.py)

Run with:
    python -m unittest discover -s tests -v

All Gemini API calls are mocked – no live API key required.
"""

import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Make sure the project root is on sys.path so we can import app
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Stub out google.genai before importing app.py so tests never hit the
# network. We must NOT replace the real 'google' package because Streamlit
# depends on google.protobuf; we only add google.genai on top.
# ---------------------------------------------------------------------------
def _make_genai_stub():
    # Ensure the real google namespace package is loaded first
    import importlib
    real_google = importlib.import_module("google")

    genai_mod = types.ModuleType("google.genai")
    types_mod = types.ModuleType("google.genai.types")

    class _FakeConfig:
        def __init__(self, **kwargs):
            pass

    types_mod.GenerateContentConfig = _FakeConfig

    class _FakeClient:
        def __init__(self, api_key=""):
            self.models = MagicMock()

    genai_mod.Client = _FakeClient
    real_google.genai = genai_mod  # attach to the real google namespace

    sys.modules["google.genai"] = genai_mod
    sys.modules["google.genai.types"] = types_mod

_make_genai_stub()

import app  # noqa: E402  (import after stub)


# ---------------------------------------------------------------------------
# Helper: fake Gemini response text
# ---------------------------------------------------------------------------
FAKE_RESPONSE_TEXT = """
## 1. Build Status
Build FAILED.

## 2. Main Error
ModuleNotFoundError: No module named 'pandas'

## 3. Root Cause
The pandas package is not installed in the active Python environment.

## 4. Explanation in Simple Words
Python could not find the pandas library because it has not been installed yet.

## 5. Suggested Fix
Run: pip install pandas

## 6. Prevention Tips
- Use a requirements.txt file.
- Always activate your virtual environment before running scripts.
"""


# ===========================================================================
# Test Cases
# ===========================================================================

class TestValidateLog(unittest.TestCase):
    """Tests for the validate_log() helper."""

    def test_empty_string_is_invalid(self):
        self.assertIsNotNone(app.validate_log(""))

    def test_whitespace_only_is_invalid(self):
        self.assertIsNotNone(app.validate_log("   \n\t  "))

    def test_valid_log_passes(self):
        self.assertIsNone(app.validate_log("ModuleNotFoundError: No module named 'pandas'"))

    def test_log_at_size_limit_is_valid(self):
        # Exactly at the limit should be allowed
        log = "X" * app.MAX_LOG_SIZE_BYTES
        self.assertIsNone(app.validate_log(log))

    def test_log_over_size_limit_is_invalid(self):
        # One byte over the limit
        log = "X" * (app.MAX_LOG_SIZE_BYTES + 1)
        result = app.validate_log(log)
        self.assertIsNotNone(result)
        self.assertIn("too large", result.lower())


class TestSupportedExtensions(unittest.TestCase):
    """Tests for supported file extension constants."""

    def test_log_extension_supported(self):
        self.assertIn(".log", app.SUPPORTED_EXTENSIONS)

    def test_txt_extension_supported(self):
        self.assertIn(".txt", app.SUPPORTED_EXTENSIONS)

    def test_out_extension_supported(self):
        self.assertIn(".out", app.SUPPORTED_EXTENSIONS)

    def test_py_extension_not_supported(self):
        self.assertNotIn(".py", app.SUPPORTED_EXTENSIONS)

    def test_pdf_extension_not_supported(self):
        self.assertNotIn(".pdf", app.SUPPORTED_EXTENSIONS)


class TestLoadSampleLog(unittest.TestCase):
    """Tests for load_sample_log()."""

    def test_loads_existing_file(self):
        sample_path = os.path.join(
            PROJECT_ROOT, "sample_logs", "python_error.log"
        )
        content = app.load_sample_log(sample_path)
        self.assertIsInstance(content, str)
        self.assertGreater(len(content), 0)

    def test_missing_file_returns_empty_string(self):
        result = app.load_sample_log("nonexistent_path/fake.log")
        self.assertEqual(result, "")

    def test_all_sample_log_paths_exist(self):
        for label, path in app.SAMPLE_LOGS.items():
            if not path:
                continue  # Skip the placeholder entry
            full_path = os.path.join(PROJECT_ROOT, path)
            self.assertTrue(
                os.path.isfile(full_path),
                f"Sample log missing: {full_path} (entry: '{label}')",
            )


class TestBuildPrompt(unittest.TestCase):
    """Tests for build_prompt()."""

    def test_prompt_contains_log_text(self):
        log = "ERROR: something went wrong"
        prompt = app.build_prompt(log)
        self.assertIn(log, prompt)

    def test_prompt_contains_all_six_sections(self):
        prompt = app.build_prompt("some log")
        for heading in [
            "Build Status",
            "Main Error",
            "Root Cause",
            "Explanation in Simple Words",
            "Suggested Fix",
            "Prevention Tips",
        ]:
            self.assertIn(heading, prompt, f"Section missing from prompt: {heading}")

    def test_prompt_is_non_empty_string(self):
        prompt = app.build_prompt("any log")
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 50)


class TestSummarizeLog(unittest.TestCase):
    """Tests for summarize_log() – Gemini is fully mocked."""

    def _make_fake_response(self, text=FAKE_RESPONSE_TEXT):
        resp = MagicMock()
        resp.text = text
        return resp

    @patch("app.genai")
    def test_successful_summarization(self, mock_genai):
        # Arrange
        fake_client = MagicMock()
        fake_client.models.generate_content.return_value = self._make_fake_response()
        mock_genai.Client.return_value = fake_client

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-12345"}):
            result = app.summarize_log("ModuleNotFoundError: No module named 'pandas'")

        self.assertEqual(result, FAKE_RESPONSE_TEXT)

    @patch("app.genai")
    def test_missing_api_key_raises_value_error(self, _mock_genai):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
            # Remove from env entirely if present
            env = {k: v for k, v in os.environ.items() if k != "GEMINI_API_KEY"}
            with patch.dict(os.environ, env, clear=True):
                with self.assertRaises((ValueError, RuntimeError)):
                    app.summarize_log("some log text")

    @patch("app.genai")
    def test_invalid_api_key_raises_runtime_error(self, mock_genai):
        fake_client = MagicMock()
        fake_client.models.generate_content.side_effect = Exception(
            "API_KEY_INVALID – API key not valid"
        )
        mock_genai.Client.return_value = fake_client

        with patch.dict(os.environ, {"GEMINI_API_KEY": "bad-key"}):
            with self.assertRaises(RuntimeError) as ctx:
                app.summarize_log("some log")
        self.assertIn("Invalid Gemini API key", str(ctx.exception))

    @patch("app.genai")
    def test_quota_error_raises_runtime_error(self, mock_genai):
        fake_client = MagicMock()
        fake_client.models.generate_content.side_effect = Exception(
            "429 quota exceeded"
        )
        mock_genai.Client.return_value = fake_client

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with self.assertRaises(RuntimeError) as ctx:
                app.summarize_log("some log")
        self.assertIn("quota", str(ctx.exception).lower())


class TestSyntaxValidation(unittest.TestCase):
    """Verify app.py can be compiled without syntax errors."""

    def test_app_compiles_without_errors(self):
        app_path = os.path.join(PROJECT_ROOT, "app.py")
        with open(app_path, "r", encoding="utf-8") as fh:
            source = fh.read()
        try:
            compile(source, app_path, "exec")
        except SyntaxError as exc:
            self.fail(f"app.py has a syntax error: {exc}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
