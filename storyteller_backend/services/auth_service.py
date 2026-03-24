"""
Authentication Service

Manages OpenAI client creation and API key handling based on different
authentication modes:
- self_hosted: Uses API key from settings (Phase 1)
- per_request_key: Uses API key provided in each request (Phase 2)
- credit_system: Uses platform's OpenAI key, tracks user credits (Phase 3)
"""

from typing import Optional
from openai import OpenAI, AsyncOpenAI
from config.settings import settings


class AuthService:
    """
    Manages OpenAI client instances based on authentication mode.
    
    This service provides a centralized way to create OpenAI clients,
    supporting different authentication strategies for various deployment models.
    """
    
    def __init__(self):
        self.auth_mode = settings.auth_mode
        self._default_client: Optional[OpenAI] = None
        self._default_async_client: Optional[AsyncOpenAI] = None
    
    def get_client(self, api_key: Optional[str] = None) -> OpenAI:
        """
        Get a synchronous OpenAI client.
        
        Args:
            api_key: Optional API key for per-request authentication.
                     If None, uses the mode-appropriate default.
        
        Returns:
            OpenAI client instance
        
        Raises:
            ValueError: If API key is required but not provided
        """
        if self.auth_mode == "self_hosted":
            # Phase 1: Use API key from settings
            if self._default_client is None:
                self._default_client = OpenAI(api_key=settings.openai_api_key)
            return self._default_client
        
        elif self.auth_mode == "per_request_key":
            # Phase 2: Require API key in each request
            if api_key is None:
                raise ValueError(
                    "API key required for per_request_key mode. "
                    "Include 'x-openai-api-key' header in your request."
                )
            return OpenAI(api_key=api_key)
        
        elif self.auth_mode == "credit_system":
            # Phase 3: Use platform's API key
            if self._default_client is None:
                if not settings.platform_openai_key:
                    raise ValueError(
                        "PLATFORM_OPENAI_KEY not set in settings. "
                        "Required for credit_system mode."
                    )
                self._default_client = OpenAI(api_key=settings.platform_openai_key)
            return self._default_client
        
        else:
            raise ValueError(f"Unknown auth_mode: {self.auth_mode}")
    
    def get_async_client(self, api_key: Optional[str] = None) -> AsyncOpenAI:
        """
        Get an asynchronous OpenAI client.
        
        Args:
            api_key: Optional API key for per-request authentication.
                     If None, uses the mode-appropriate default.
        
        Returns:
            AsyncOpenAI client instance
        
        Raises:
            ValueError: If API key is required but not provided
        """
        if self.auth_mode == "self_hosted":
            # Phase 1: Use API key from settings
            if self._default_async_client is None:
                self._default_async_client = AsyncOpenAI(api_key=settings.openai_api_key)
            return self._default_async_client
        
        elif self.auth_mode == "per_request_key":
            # Phase 2: Require API key in each request
            if api_key is None:
                raise ValueError(
                    "API key required for per_request_key mode. "
                    "Include 'x-openai-api-key' header in your request."
                )
            return AsyncOpenAI(api_key=api_key)
        
        elif self.auth_mode == "credit_system":
            # Phase 3: Use platform's API key
            if self._default_async_client is None:
                if not settings.platform_openai_key:
                    raise ValueError(
                        "PLATFORM_OPENAI_KEY not set in settings. "
                        "Required for credit_system mode."
                    )
                self._default_async_client = AsyncOpenAI(api_key=settings.platform_openai_key)
            return self._default_async_client
        
        else:
            raise ValueError(f"Unknown auth_mode: {self.auth_mode}")
    
    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate an API key by making a lightweight API call.
        
        Args:
            api_key: The API key to validate
        
        Returns:
            True if valid, False otherwise
        """
        try:
            client = OpenAI(api_key=api_key)
            # Make a minimal API call to check validity
            client.models.list()
            return True
        except Exception:
            return False


# Global instance for convenience
_auth_service: Optional[AuthService] = None


def get_openai_client(api_key: Optional[str] = None) -> OpenAI:
    """
    Convenience function to get an OpenAI client.
    
    Args:
        api_key: Optional API key for per-request authentication
    
    Returns:
        OpenAI client instance
    """
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service.get_client(api_key)


def get_async_openai_client(api_key: Optional[str] = None) -> AsyncOpenAI:
    """
    Convenience function to get an async OpenAI client.
    
    Args:
        api_key: Optional API key for per-request authentication
    
    Returns:
        AsyncOpenAI client instance
    """
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service.get_async_client(api_key)

