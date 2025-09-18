#!/usr/bin/env python3
"""
Test script to verify the setup works correctly
"""

import os
import sys
from dotenv import load_dotenv

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from helpers import (
            client_configs, STORAGE_DIR, serializer, VALID_USERNAME, VALID_PASSWORD, 
            STORAGE_API_KEY, validate_credentials, generate_signed_cloudfront_url, 
            generate_signed_url, get_client_config, get_supported_languages, 
            build_video_urls, handle_exception
        )
        print("✓ Helpers module imported successfully")
    except Exception as e:
        print(f"✗ Failed to import helpers: {e}")
        return False
    
    try:
        from app import app as flask_app
        print("✓ Flask app imported successfully")
    except Exception as e:
        print(f"✗ Failed to import Flask app: {e}")
        return False
    
    try:
        from main import fastapi_app
        print("✓ FastAPI app imported successfully")
    except Exception as e:
        print(f"✗ Failed to import FastAPI app: {e}")
        return False
    
    try:
        from chat_service import ChatService
        from tts_service import TTSService
        from speech_analysis import SpeechAnalyzer
        print("✓ Service modules imported successfully")
    except Exception as e:
        print(f"✗ Failed to import service modules: {e}")
        return False
    
    return True

def test_config_loading():
    """Test configuration loading"""
    print("\nTesting configuration loading...")
    
    try:
        from config_loader import load_client_configs, get_client_config
        configs = load_client_configs()
        print(f"✓ Loaded {len(configs)} client configurations")
        
        default_config = get_client_config(configs, 'default')
        print(f"✓ Default client config loaded: {list(default_config.keys())}")
        
        return True
    except Exception as e:
        print(f"✗ Failed to load configurations: {e}")
        return False

def test_environment():
    """Test environment variables"""
    print("\nTesting environment variables...")
    
    load_dotenv()
    
    required_vars = [
        'OPENAI_API_KEY',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"✗ Missing environment variables: {missing_vars}")
        return False
    else:
        print("✓ All required environment variables are set")
        return True

def test_helpers():
    """Test helper functions"""
    print("\nTesting helper functions...")
    
    try:
        from helpers import get_supported_languages, handle_exception
        
        languages = get_supported_languages()
        print(f"✓ Supported languages: {len(languages)} languages")
        
        error_result = handle_exception(Exception("Test error"), "test_context")
        print(f"✓ Error handling works: {error_result}")
        
        return True
    except Exception as e:
        print(f"✗ Failed to test helpers: {e}")
        return False

def main():
    """Run all tests"""
    print("Whisper Transcription Service - Setup Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config_loading,
        test_environment,
        test_helpers
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! The setup is ready.")
        print("\nYou can now run:")
        print("  python main.py flask     # Run Flask server only")
        print("  python main.py fastapi   # Run FastAPI server only")
        print("  python main.py both      # Run both servers (default)")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 