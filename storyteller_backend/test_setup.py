#!/usr/bin/env python3
"""
Incremental Setup Testing Script

This script tests each component as we build them.
Run this after adding new modules to verify everything still works.

Usage:
    python test_setup.py
"""

import sys
from pathlib import Path


def print_test(name: str, passed: bool, message: str = ""):
    """Print test result with formatting."""
    status = "✓" if passed else "✗"
    status_text = "PASS" if passed else "FAIL"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    
    print(f"{color}{status} {status_text}{reset}: {name}")
    if message:
        print(f"  → {message}")
    return passed


def test_config():
    """Test configuration module."""
    try:
        from config.settings import settings
        
        # Check required fields exist
        assert hasattr(settings, 'openai_api_key'), "Missing openai_api_key"
        assert hasattr(settings, 'api_host'), "Missing api_host"
        assert hasattr(settings, 'api_port'), "Missing api_port"
        
        # Check computed properties
        assert hasattr(settings, 'data_path'), "Missing data_path property"
        assert hasattr(settings, 'uses_azure_storage'), "Missing uses_azure_storage property"
        
        # Verify paths are Path objects
        assert isinstance(settings.data_path, Path), "data_path should be Path object"
        
        return print_test(
            "Configuration",
            True,
            f"Settings loaded successfully (auth_mode: {settings.auth_mode})"
        )
    except Exception as e:
        return print_test("Configuration", False, str(e))


def test_imports():
    """Test that all package imports work."""
    tests_passed = True
    
    # Test config import
    try:
        from config import settings
        tests_passed &= print_test("Import: config", True, "Settings module accessible")
    except Exception as e:
        tests_passed &= print_test("Import: config", False, str(e))
    
    # Test models import
    try:
        from models import (
            StoryRequest, CorpusInfo, PersonaInfo,
            JourneyMeta, StorytellerState, Chunk
        )
        tests_passed &= print_test("Import: models", True, "All model classes accessible")
    except Exception as e:
        tests_passed &= print_test("Import: models", False, str(e))
    
    # Test embed_retrieve import
    try:
        from embed_retrieve import HybridRetriever, get_registry
        tests_passed &= print_test("Import: embed_retrieve", True, "Retriever and registry accessible")
    except Exception as e:
        tests_passed &= print_test("Import: embed_retrieve", False, str(e))
    
    # Test services import
    try:
        from services import (
            AuthService, get_openai_client,
            JourneyManager, get_journey_manager,
            ImageGenerator, get_image_generator
        )
        tests_passed &= print_test("Import: services", True, "All services accessible")
    except Exception as e:
        tests_passed &= print_test("Import: services", False, str(e))
    
    return tests_passed


def test_environment():
    """Test environment setup."""
    try:
        # Check if .env file exists
        env_file = Path(".env")
        env_example = Path(".env.example")
        
        if not env_file.exists():
            return print_test(
                "Environment",
                False,
                ".env file not found. Copy .env.example to .env and configure it."
            )
        
        # Try to load settings (will fail if OPENAI_API_KEY not set)
        from config.settings import settings
        
        if settings.openai_api_key == "sk-your-openai-api-key-here":
            return print_test(
                "Environment",
                False,
                "OPENAI_API_KEY not configured in .env file"
            )
        
        return print_test(
            "Environment",
            True,
            "Environment variables configured"
        )
        
    except Exception as e:
        return print_test("Environment", False, str(e))


def test_data_directories():
    """Test that data directories are accessible."""
    try:
        from config.settings import settings
        
        # Check if directories exist
        data_exists = settings.data_path.exists()
        graphs_exists = settings.saved_graphs_path.exists()
        
        if not data_exists:
            return print_test(
                "Data Directories",
                False,
                f"Data directory not found: {settings.data_path}"
            )
        
        if not graphs_exists:
            return print_test(
                "Data Directories",
                False,
                f"Saved graphs directory not found: {settings.saved_graphs_path}"
            )
        
        return print_test(
            "Data Directories",
            True,
            f"Both directories accessible"
        )
        
    except Exception as e:
        return print_test("Data Directories", False, str(e))


def test_models():
    """Test that Pydantic models work correctly."""
    try:
        from models import StoryRequest, CorpusInfo, PersonaInfo
        
        # Test StoryRequest validation
        request = StoryRequest(
            prompt="Tell me a story",
            story_length=1500,
            corpus_name="mahabharata"
        )
        assert request.prompt == "Tell me a story", "StoryRequest validation failed"
        assert request.story_length == 1500, "Story length validation failed"
        
        # Test CorpusInfo creation
        corpus = CorpusInfo(
            name="test",
            display_name="Test Corpus",
            description="Test",
            is_active=True,
            chunk_count=100,
            needs_rebuild=False
        )
        assert corpus.name == "test", "CorpusInfo creation failed"
        
        return print_test(
            "Data Models",
            True,
            "Pydantic models validate correctly"
        )
    except Exception as e:
        return print_test("Data Models", False, str(e))


def test_corpus_registry():
    """Test that corpus registry can load corpuses."""
    try:
        from embed_retrieve import get_registry
        
        registry = get_registry()
        
        # Check if registry has corpuses
        corpuses = registry.list_corpuses()
        if not corpuses:
            return print_test(
                "Corpus Registry",
                False,
                "No corpuses found. Run batch_ingest to create corpuses."
            )
        
        # Check if mahabharata exists (default corpus)
        mahabharata = registry.get_corpus("mahabharata")
        if not mahabharata:
            return print_test(
                "Corpus Registry",
                False,
                "Mahabharata corpus not found"
            )
        
        return print_test(
            "Corpus Registry",
            True,
            f"Registry loaded with {len(corpuses)} corpus(es)"
        )
    except Exception as e:
        return print_test("Corpus Registry", False, str(e))


def test_auth_service():
    """Test that auth service can create OpenAI clients."""
    try:
        from services import get_openai_client, AuthService
        from config.settings import settings
        
        # Test auth service instantiation
        auth_service = AuthService()
        assert auth_service.auth_mode == "self_hosted", "Auth mode mismatch"
        
        # Test client creation (don't make actual API calls in tests)
        client = get_openai_client()
        assert client is not None, "Failed to create OpenAI client"
        assert hasattr(client, "chat"), "Client missing chat attribute"
        
        return print_test(
            "Auth Service",
            True,
            f"OpenAI client created (auth_mode: {settings.auth_mode})"
        )
    except Exception as e:
        return print_test("Auth Service", False, str(e))


def test_journey_manager():
    """Test that journey manager can list saved graphs."""
    try:
        from services import get_journey_manager
        
        # Test journey manager instantiation
        manager = get_journey_manager()
        assert manager is not None, "Failed to create journey manager"
        
        # Test listing journeys for a test user (may be empty)
        # We use a test username to avoid interfering with real data
        journeys = manager.list_journeys("mehrab")
        
        return print_test(
            "Journey Manager",
            True,
            f"Journey manager initialized ({len(journeys)} journey(s) found for mehrab)"
        )
    except Exception as e:
        return print_test("Journey Manager", False, str(e))


def test_image_generator():
    """Test that image generator initializes correctly."""
    try:
        from services import get_image_generator
        
        # Test image generator instantiation
        generator = get_image_generator()
        assert generator is not None, "Failed to create image generator"
        assert generator.enable_generation == True, "Image generation not enabled"
        assert generator.client is not None, "OpenAI client not initialized"
        
        # Check if Azure is configured
        azure_status = "enabled" if generator.use_azure_storage else "disabled"
        
        return print_test(
            "Image Generator",
            True,
            f"Image generator initialized (Azure: {azure_status})"
        )
    except Exception as e:
        return print_test("Image Generator", False, str(e))


def main():
    """Run all tests."""
    print("=" * 60)
    print("Storyteller Backend - Setup Test")
    print("=" * 60)
    print()
    
    all_passed = True
    
    # Test 1: Configuration
    print("1. Testing Configuration...")
    all_passed &= test_config()
    print()
    
    # Test 2: Imports
    print("2. Testing Imports...")
    all_passed &= test_imports()
    print()
    
    # Test 3: Environment
    print("3. Testing Environment...")
    all_passed &= test_environment()
    print()
    
    # Test 4: Data Directories
    print("4. Testing Data Directories...")
    all_passed &= test_data_directories()
    print()
    
    # Test 5: Data Models
    print("5. Testing Data Models...")
    all_passed &= test_models()
    print()
    
    # Test 6: Corpus Registry
    print("6. Testing Corpus Registry...")
    all_passed &= test_corpus_registry()
    print()
    
    # Test 7: Auth Service
    print("7. Testing Auth Service...")
    all_passed &= test_auth_service()
    print()
    
    # Test 8: Journey Manager
    print("8. Testing Journey Manager...")
    all_passed &= test_journey_manager()
    print()
    
    # Test 9: Image Generator
    print("9. Testing Image Generator...")
    all_passed &= test_image_generator()
    print()
    
    # Summary
    print("=" * 60)
    if all_passed:
        print("✓ All tests passed! Setup is complete.")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

