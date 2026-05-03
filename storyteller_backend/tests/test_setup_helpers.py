"""Unit tests for the pure helpers in setup.py.

These cover the parsing / regex logic that drives prereq checks, prompt
handling, .env validation, and settings.py rewriting. Filesystem and
subprocess interactions are intentionally untested here — those are
exercised by a real run from a fresh clone (Layer 3).
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# Load setup.py as a module — it lives at the repo root, not on sys.path.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SETUP_PATH = _REPO_ROOT / "setup.py"
_spec = importlib.util.spec_from_file_location("storyteller_setup", _SETUP_PATH)
storyteller_setup = importlib.util.module_from_spec(_spec)
sys.modules["storyteller_setup"] = storyteller_setup
_spec.loader.exec_module(storyteller_setup)


# ============================================================
# parse_node_major
# ============================================================

class TestParseNodeMajor:
    def test_standard_format(self):
        assert storyteller_setup.parse_node_major("v20.10.0") == 20

    def test_no_v_prefix(self):
        assert storyteller_setup.parse_node_major("18.17.1") == 18

    def test_with_trailing_whitespace(self):
        assert storyteller_setup.parse_node_major("v22.5.0\n") == 22

    def test_garbage_returns_none(self):
        assert storyteller_setup.parse_node_major("not a version") is None

    def test_empty_returns_none(self):
        assert storyteller_setup.parse_node_major("") is None


# ============================================================
# parse_provider_choice
# ============================================================

class TestParseProviderChoice:
    @pytest.mark.parametrize("inp", ["", "g", "G", "gemini", "Gemini", "  g  "])
    def test_gemini_variants(self, inp):
        assert storyteller_setup.parse_provider_choice(inp) == "gemini"

    @pytest.mark.parametrize("inp", ["o", "O", "openai", "OpenAI", "  openai  "])
    def test_openai_variants(self, inp):
        assert storyteller_setup.parse_provider_choice(inp) == "openai"

    @pytest.mark.parametrize("inp", ["x", "yes", "anthropic", "1"])
    def test_invalid_returns_none(self, inp):
        assert storyteller_setup.parse_provider_choice(inp) is None


# ============================================================
# env_has_real_key
# ============================================================

class TestEnvHasRealKey:
    def test_real_gemini_key(self):
        text = "GEMINI_API_KEY=AIzaSyAbcDefRealKey\n"
        assert storyteller_setup.env_has_real_key(text, "GEMINI_API_KEY") is True

    def test_quoted_value_works(self):
        text = 'GEMINI_API_KEY="AIzaSyAbc"\n'
        assert storyteller_setup.env_has_real_key(text, "GEMINI_API_KEY") is True

    def test_placeholder_value_rejected(self):
        text = "GEMINI_API_KEY=your-gemini-api-key-here\n"
        assert storyteller_setup.env_has_real_key(text, "GEMINI_API_KEY") is False

    def test_openai_placeholder_rejected(self):
        text = "OPENAI_API_KEY=sk-your-openai-api-key-here\n"
        assert storyteller_setup.env_has_real_key(text, "OPENAI_API_KEY") is False

    def test_empty_value_rejected(self):
        text = "GEMINI_API_KEY=\n"
        assert storyteller_setup.env_has_real_key(text, "GEMINI_API_KEY") is False

    def test_commented_line_ignored(self):
        text = "# GEMINI_API_KEY=AIzaSyReal\n"
        assert storyteller_setup.env_has_real_key(text, "GEMINI_API_KEY") is False

    def test_missing_key_returns_false(self):
        text = "OPENAI_API_KEY=sk-realkey\n"
        assert storyteller_setup.env_has_real_key(text, "GEMINI_API_KEY") is False

    def test_only_other_provider_key_present(self):
        text = (
            "# GEMINI_API_KEY=your-gemini-api-key-here\n"
            "OPENAI_API_KEY=sk-AbcDef123\n"
        )
        assert storyteller_setup.env_has_real_key(text, "GEMINI_API_KEY") is False
        assert storyteller_setup.env_has_real_key(text, "OPENAI_API_KEY") is True


# ============================================================
# apply_provider_to_settings
# ============================================================

class TestApplyProviderToSettings:
    BASE = (
        "class Config:\n"
        "    api_host: str = '0.0.0.0'\n"
        "    provider: Provider = Provider.GEMINI\n"
        "    something_else: int = 42\n"
    )

    def test_gemini_to_openai(self):
        result = storyteller_setup.apply_provider_to_settings(self.BASE, "openai")
        assert "provider: Provider = Provider.OPENAI" in result
        assert "Provider.GEMINI" not in result.split("\n")[2]

    def test_openai_to_gemini(self):
        text = self.BASE.replace("Provider.GEMINI", "Provider.OPENAI")
        result = storyteller_setup.apply_provider_to_settings(text, "gemini")
        assert "provider: Provider = Provider.GEMINI" in result

    def test_idempotent_when_already_set(self):
        result = storyteller_setup.apply_provider_to_settings(self.BASE, "gemini")
        assert result == self.BASE

    def test_preserves_indentation(self):
        text = "\n    provider: Provider = Provider.GEMINI\n"
        result = storyteller_setup.apply_provider_to_settings(text, "openai")
        assert "    provider: Provider = Provider.OPENAI" in result

    def test_only_changes_first_match(self):
        text = (
            "    provider: Provider = Provider.GEMINI\n"
            "    # provider: Provider = Provider.GEMINI  (commented)\n"
        )
        # The function should change the first non-commented occurrence;
        # the "commented" line begins with "#" so it isn't matched at start anyway.
        result = storyteller_setup.apply_provider_to_settings(text, "openai")
        # Live line was changed:
        assert "    provider: Provider = Provider.OPENAI" in result

    def test_raises_when_assignment_missing(self):
        text = "class Config:\n    api_host: str = '0.0.0.0'\n"
        with pytest.raises(ValueError, match="Could not find"):
            storyteller_setup.apply_provider_to_settings(text, "gemini")
