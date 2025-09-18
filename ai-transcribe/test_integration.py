#!/usr/bin/env python3
"""
Integration test script to verify all functionality is working
"""

import sys
import os

def test_imports():
    """Test all imports are working"""
    print("Testing imports...")
    
    try:
        # Test core imports
        from websocket_service import app
        print("✅ websocket_service import successful")
        
        from transcribe import process_s3_target
        print("✅ transcribe import successful")
        
        from helpers import (
            client_configs, STORAGE_DIR, serializer, VALID_USERNAME, VALID_PASSWORD,
            STORAGE_API_KEY, validate_credentials, generate_signed_cloudfront_url,
            generate_signed_url, get_client_config, get_supported_languages,
            build_video_urls, handle_exception
        )
        print("✅ helpers import successful")
        
        from config_loader import load_client_configs, get_client_config
        print("✅ config_loader import successful")
        
        from services.enhanced_chat_service import EnhancedChatService
        print("✅ EnhancedChatService import successful")
        
        from services.service_registry import service_registry
        print("✅ service_registry import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_config_loading():
    """Test configuration loading"""
    print("\nTesting configuration loading...")
    
    try:
        from config_loader import load_client_configs, get_client_config
        
        client_configs = load_client_configs()
        print(f"✅ Loaded {len(client_configs)} client configurations")
        
        default_config = get_client_config(client_configs, 'default')
        print(f"✅ Default config loaded: {list(default_config.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_helpers():
    """Test helper functions"""
    print("\nTesting helper functions...")
    
    try:
        from helpers import get_supported_languages, handle_exception
        
        languages = get_supported_languages()
        print(f"✅ Supported languages: {list(languages.keys())}")
        
        # Test exception handling
        test_exception = Exception("Test error")
        result = handle_exception(test_exception, "test")
        print(f"✅ Exception handling: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Helper functions error: {e}")
        return False

def test_api_endpoints():
    """Test API endpoint definitions"""
    print("\nTesting API endpoints...")
    
    try:
        from websocket_service import app
        
        # Check if all endpoints are defined
        routes = [route.path for route in app.routes]
        expected_endpoints = [
            "/api/ping",
            "/api/login", 
            "/api/transcribe",
            "/api/storage/{filename:path}",
            "/api/storage-secure/{token}",
            "/api/sign-url",
            "/api/subtitles",
            "/api/health",
            "/api/services",
            "/ws/{client_id}"
        ]
        
        for endpoint in expected_endpoints:
            if endpoint in routes or any(endpoint.replace('{', '').replace('}', '') in route for route in routes):
                print(f"✅ Endpoint {endpoint} found")
            else:
                print(f"❌ Endpoint {endpoint} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoints error: {e}")
        return False

def test_services():
    """Test service registration"""
    print("\nTesting service registration...")
    
    try:
        from services.service_registry import service_registry
        from services.enhanced_chat_service import EnhancedChatService
        
        # Check if AI_CHAT service is registered
        services = service_registry.get_supported_services()
        print(f"✅ Registered services: {[s.value for s in services]}")
        
        # Test getting AI_CHAT service
        ai_chat_service = service_registry.get_service(service_registry.get_supported_services()[0])
        print(f"✅ AI_CHAT service loaded: {type(ai_chat_service)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service registration error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Integration Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config_loading,
        test_helpers,
        test_api_endpoints,
        test_services
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Integration successful.")
        return True
    else:
        print("❌ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 