#!/usr/bin/env python3
"""
Test script to verify all services work correctly
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

def test_chat_service():
    """Test the chat service with two-part prompt structure"""
    print("Testing Chat Service...")
    
    try:
        from chat_service import ChatService
        
        chat_service = ChatService()
        
        # Test with default system prompt
        response1 = chat_service.chat(
            client_id="test_client", 
            user_instructions="Hello, how are you?"
        )
        
        # Test with custom system prompt
        custom_prompt = "You are a helpful assistant. Be concise in your responses."
        response2 = chat_service.chat(
            client_id="test_client_2", 
            user_instructions="What is 2+2?",
            system_prompt=custom_prompt
        )
        
        # Test getting system prompt from config
        system_prompt = chat_service.get_system_prompt("default")
        
        if response1 and response2 and len(response1) > 0 and len(response2) > 0:
            print("✓ Chat service working with two-part prompt structure")
            print(f"  Response 1: {response1[:100]}...")
            print(f"  Response 2: {response2[:100]}...")
            print(f"  System prompt from config: {system_prompt[:50] if system_prompt else 'None'}...")
            return True
        else:
            print("✗ Chat service returned empty response")
            return False
            
    except Exception as e:
        print(f"✗ Chat service failed: {e}")
        return False

async def test_tts_service():
    """Test the TTS service"""
    print("Testing TTS Service...")
    
    try:
        from tts_service import TTSService
        
        tts_service = TTSService()
        audio_base64 = await tts_service.synthesize_stream("Hello, this is a test.")
        
        if audio_base64 and len(audio_base64) > 0:
            print("✓ TTS service working")
            print(f"  Audio size: {len(audio_base64)} characters (base64)")
            return True
        else:
            print("✗ TTS service returned empty audio")
            return False
            
    except Exception as e:
        print(f"✗ TTS service failed: {e}")
        return False

def test_speech_analysis():
    """Test the speech analysis service"""
    print("Testing Speech Analysis Service...")
    
    try:
        from speech_analysis import SpeechAnalyzer
        
        # Get Azure credentials from config
        from config_loader import load_client_configs, get_client_config
        configs = load_client_configs()
        config = get_client_config(configs, 'default')
        
        if 'AZURE_SPEECH_KEY' not in config or 'AZURE_SPEECH_REGION' not in config:
            print("⚠ Azure Speech credentials not configured - skipping test")
            return True
            
        analyzer = SpeechAnalyzer(config["AZURE_SPEECH_KEY"], config["AZURE_SPEECH_REGION"])
        print("✓ Speech analyzer initialized")
        return True
        
    except Exception as e:
        print(f"✗ Speech analysis service failed: {e}")
        return False

def test_api_routes():
    """Test that API routes are properly defined"""
    print("Testing API Routes...")
    
    try:
        from main import app
        
        # Check if chat route exists
        routes = [route.path for route in app.routes]
        
        required_routes = [
            "/api/chat",
            "/api/transcribe", 
            "/api/subtitles",
            "/api/login",
            "/api/health"
        ]
        
        missing_routes = []
        for route in required_routes:
            if route not in routes:
                missing_routes.append(route)
        
        if not missing_routes:
            print("✓ All required API routes found")
            print(f"  Available routes: {len(routes)} total")
            return True
        else:
            print(f"✗ Missing routes: {missing_routes}")
            return False
            
    except Exception as e:
        print(f"✗ API routes test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("Whisper Transcription Service - Service Tests")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    tests = [
        ("Chat Service", test_chat_service),
        ("TTS Service", test_tts_service),
        ("Speech Analysis", test_speech_analysis),
        ("API Routes", test_api_routes)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All services are working correctly!")
        print("\nYou can now:")
        print("  - Start the server: python main.py")
        print("  - Test the API: curl http://localhost:5000/api/health")
        print("  - View docs: http://localhost:5000/docs")
        return 0
    else:
        print("❌ Some services failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 