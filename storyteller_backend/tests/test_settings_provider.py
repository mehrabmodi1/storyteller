import pytest
from unittest.mock import patch


class TestProviderConfig:

    def test_default_provider_is_gemini(self):
        from config.settings import Config, Provider
        c = Config()
        assert c.provider is Provider.GEMINI
        assert c.provider == "gemini"  # StrEnum equates to its string value

    def test_chat_model_resolves_for_gemini(self):
        from config.settings import Config, Settings, Provider
        with patch.object(Settings, '_Settings__validate_api_key'):
            s = Settings.__new__(Settings)
            s._config = Config()
            s._config.provider = Provider.GEMINI
            assert s.chat_model == "gemini-2.5-flash"

    def test_chat_model_resolves_for_openai(self):
        from config.settings import Config, Settings, Provider
        with patch.object(Settings, '_Settings__validate_api_key'):
            s = Settings.__new__(Settings)
            s._config = Config()
            s._config.provider = Provider.OPENAI
            assert s.chat_model == "gpt-4o-mini"

    def test_langchain_chat_provider_mapping(self):
        from config.settings import Config, Settings, Provider
        with patch.object(Settings, '_Settings__validate_api_key'):
            s = Settings.__new__(Settings)
            s._config = Config()
            s._config.provider = Provider.GEMINI
            assert s.langchain_chat_provider == "google_genai"

    def test_langchain_chat_provider_mapping_openai(self):
        from config.settings import Config, Settings, Provider
        with patch.object(Settings, '_Settings__validate_api_key'):
            s = Settings.__new__(Settings)
            s._config = Config()
            s._config.provider = Provider.OPENAI
            assert s.langchain_chat_provider == "openai"

    def test_image_size_resolves_per_provider(self):
        from config.settings import Config, Settings, Provider
        with patch.object(Settings, '_Settings__validate_api_key'):
            s = Settings.__new__(Settings)
            s._config = Config()
            s._config.provider = Provider.GEMINI
            assert s.image_size == "1K"
            s._config.provider = Provider.OPENAI
            assert s.image_size == "256x256"

    def test_image_quality_only_set_for_openai(self):
        from config.settings import Config, Settings, Provider
        with patch.object(Settings, '_Settings__validate_api_key'):
            s = Settings.__new__(Settings)
            s._config = Config()
            s._config.provider = Provider.GEMINI
            assert s.image_quality is None
            s._config.provider = Provider.OPENAI
            assert s.image_quality == "standard"

    def test_rpms_resolve_per_provider(self):
        from config.settings import Config, Settings, Provider
        with patch.object(Settings, '_Settings__validate_api_key'):
            s = Settings.__new__(Settings)
            s._config = Config()
            s._config.provider = Provider.GEMINI
            assert s.chat_rpm == 5
            assert s.embedding_rpm == 20
            s._config.provider = Provider.OPENAI
            assert s.chat_rpm == 0
            assert s.embedding_rpm == 0
