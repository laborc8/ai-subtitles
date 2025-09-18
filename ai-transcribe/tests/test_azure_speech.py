#!/usr/bin/env python3
"""
Test script for Azure Speech Services
Helps diagnose configuration and audio format issues
"""

import os
import sys
import tempfile
import wave
import numpy as np
from config_loader import load_client_configs, get_client_config
from speech_analysis import SpeechAnalyzer
from logger_config import logger

def create_test_audio():
    """Create a simple test WAV file"""
    try:
        # Create a temporary WAV file with a simple tone
        temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_wav.close()
        
        # Create a simple 1-second audio file (440 Hz sine wave)
        sample_rate = 16000
        duration = 1.0
        frequency = 440.0
        
        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Write WAV file
        with wave.open(temp_wav.name, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        logger.info(f"Created test audio file: {temp_wav.name}")
        return temp_wav.name
        
    except Exception as e:
        logger.error(f"Error creating test audio: {e}")
        return None

def test_azure_config():
    """Test Azure Speech configuration"""
    try:
        # Load client configs
        client_configs = load_client_configs()
        config = get_client_config(client_configs, 'default')
        
        # Check Azure credentials
        azure_key = config.get('AZURE_SPEECH_KEY')
        azure_region = config.get('AZURE_SPEECH_REGION')
        
        print(f"Azure Speech Configuration:")
        print(f"  Region: {azure_region}")
        print(f"  Key: {azure_key[:10]}..." if azure_key else "  Key: Not set")
        
        if not azure_key or azure_key == "your-azure-speech-key-here":
            print("❌ Azure Speech key not configured properly")
            return False
            
        if not azure_region:
            print("❌ Azure Speech region not configured")
            return False
            
        print("✅ Azure Speech configuration looks good")
        return True
        
    except Exception as e:
        print(f"❌ Error checking Azure config: {e}")
        return False

def test_speech_analyzer():
    """Test SpeechAnalyzer initialization"""
    try:
        client_configs = load_client_configs()
        config = get_client_config(client_configs, 'default')
        
        azure_key = config.get('AZURE_SPEECH_KEY')
        azure_region = config.get('AZURE_SPEECH_REGION')
        
        if not azure_key or azure_key == "your-azure-speech-key-here":
            print("❌ Cannot test SpeechAnalyzer - Azure key not configured")
            return False
        
        print("Testing SpeechAnalyzer initialization...")
        analyzer = SpeechAnalyzer(azure_key, azure_region)
        print("✅ SpeechAnalyzer initialized successfully")
        return analyzer
        
    except Exception as e:
        print(f"❌ Error initializing SpeechAnalyzer: {e}")
        return False

def test_audio_analysis(analyzer):
    """Test audio analysis with a simple test file"""
    try:
        print("Creating test audio file...")
        test_audio = create_test_audio()
        if not test_audio:
            print("❌ Could not create test audio file")
            return False
        
        print("Testing audio analysis...")
        result = analyzer.analyze(test_audio)
        
        print(f"Analysis result: {result}")
        
        if result.get('status') == 'success':
            print("✅ Audio analysis successful")
            return True
        else:
            print(f"❌ Audio analysis failed: {result.get('error', result.get('reason', 'Unknown error'))}")
            return False
            
    except Exception as e:
        print(f"❌ Error during audio analysis: {e}")
        return False
    finally:
        # Clean up test file
        if 'test_audio' in locals() and test_audio and os.path.exists(test_audio):
            try:
                os.unlink(test_audio)
                print(f"Cleaned up test file: {test_audio}")
            except:
                pass

def main():
    """Main test function"""
    print("=== Azure Speech Services Test ===")
    print()
    
    # Test 1: Configuration
    print("1. Testing Azure configuration...")
    if not test_azure_config():
        print("❌ Configuration test failed")
        return
    
    # Test 2: SpeechAnalyzer initialization
    print("\n2. Testing SpeechAnalyzer initialization...")
    analyzer = test_speech_analyzer()
    if not analyzer:
        print("❌ SpeechAnalyzer test failed")
        return
    
    # Test 3: Audio analysis
    print("\n3. Testing audio analysis...")
    if test_audio_analysis(analyzer):
        print("\n✅ All tests passed! Azure Speech Services is working correctly.")
    else:
        print("\n❌ Audio analysis test failed")
        print("\nTroubleshooting tips:")
        print("- Check your Azure Speech key and region")
        print("- Ensure your Azure Speech resource is active")
        print("- Check if FFmpeg is installed (for audio conversion)")
        print("- Review the logs for detailed error information")

if __name__ == "__main__":
    main() 