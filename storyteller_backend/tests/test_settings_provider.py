import pytest
from unittest.mock import patch


class TestProviderConfig:

    def test_default_provider_is_gemini(self):
        from config.settings import Config
        c = Config()
        assert c.provider == "gemini"

    def test_chat_model_resolves_for_gemini(self):
        from config.settings import Config, Settings
        with patch.object(Settings, '_Settings__validate_api_key'):
            s = Settings.__new__(Settings)
            s._config = Config()
            s._config.provider = "gemini"
            assert s.chat_model == "gemini-2.5-flash"

    def test_chat_model_resolves_for_openai(self):
        from config.settings import Config, Settings
        with patch.object(Settings, '_Settings__validate_api_key'):
            s = Settings.__new__(Settings)
            s._config = Config()
            s._config.provider = "openai"
            assert s.chat_model == "gpt-4o-mini"

    def test_langchain_chat_provider_mapping(self):
        from config.settings import Config, Settings
        with patch.object(Settings, '_Settings__validate_api_key'):
            s = Settings.__new__(Settings)
            s._config = Config()
            s._config.provider = "gemini"
            assert s.langchain_chat_provider == "google_genai"

    def test_langchain_chat_provider_mapping_openai(self):
        from config.settings import Config, Settings
        with patch.object(Settings, '_Settings__validate_api_key'):
            s = Settings.__new__(Settings)
            s._config = Config()
            s._config.provider = "openai"
            assert s.langchain_chat_provider == "openai"

    def test_image_size_resolves_per_provider(self):
        from config.settings import Config, Settings
        with patch.object(Settings, '_Settings__validate_api_key'):
            s = Settings.__new__(Settings)
            s._config = Config()
            s._config.provider = "gemini"
            assert s.image_size == "1K"
            s._config.provider = "openai"
            assert s.image_size == "256x256"
