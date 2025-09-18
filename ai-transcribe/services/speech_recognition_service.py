import openai
import os
import time
from logger_config import logger

class SpeechRecognitionService:
    def __init__(self):
        self.whisper_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.microsoft_speech = None
        
    def initialize_microsoft_speech(self):
        """Initialize Microsoft Speech SDK"""
        try:
            if os.getenv("MICROSOFT_SPEECH_KEY"):
                import azure.cognitiveservices.speech as speechsdk
                self.microsoft_speech = speechsdk.SpeechConfig(
                    subscription=os.getenv("MICROSOFT_SPEECH_KEY"),
                    region=os.getenv("MICROSOFT_SPEECH_REGION")
                )
                logger.info("Microsoft Speech SDK initialized successfully")
            else:
                logger.warning("Microsoft Speech SDK not configured - using OpenAI Whisper")
        except Exception as e:
            logger.error(f"Failed to initialize Microsoft Speech SDK: {e}")
    
    async def transcribe_audio(self, audio_data, use_microsoft=False):
        """
        Transcribe audio using either OpenAI Whisper or Microsoft Speech
        
        Args:
            audio_data: Audio data to transcribe
            use_microsoft: Whether to use Microsoft Speech SDK
        """
        if use_microsoft and self.microsoft_speech:
            return await self._transcribe_with_microsoft(audio_data)
        else:
            return await self._transcribe_with_whisper(audio_data)
    
    async def _transcribe_with_microsoft(self, audio_data):
        """Transcribe using Microsoft Speech SDK with confidence scoring"""
        try:
            # Implementation for Microsoft Speech SDK
            # This would require the actual Microsoft Speech SDK implementation
            # For now, we'll return a mock response
            logger.info("Using Microsoft Speech SDK for transcription")
            return {
                'text': 'Microsoft speech transcription placeholder',
                'confidence': 0.95,
                'is_final': True
            }
        except Exception as e:
            logger.error(f"Microsoft speech transcription error: {str(e)}")
            return None
    
    async def _transcribe_with_whisper(self, audio_data):
        """Transcribe using OpenAI Whisper"""
        try:
            # Convert audio_data to file-like object if needed
            import tempfile
            import io
            
            # Create a temporary file for the audio data
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                with open(temp_file_path, "rb") as audio_file:
                    response = self.whisper_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json"
                    )
                
                return {
                    'text': response.text,
                    'confidence': 1.0,  # Whisper doesn't provide confidence scores
                    'segments': response.segments,
                    'is_final': True
                }
            finally:
                # Clean up temporary file
                import os
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Whisper transcription error: {str(e)}")
            return None 