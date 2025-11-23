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

