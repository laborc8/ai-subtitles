import openai
import os
import asyncio
from logger_config import logger

class StreamingTTSService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def stream_audio(self, text: str):
        """
        Stream audio from text using OpenAI TTS
        
        Args:
            text: Text to convert to speech
            
        Yields:
            Audio chunks as bytes
        """
        try:
            logger.info(f"Generating audio for text: {text[:50]}...")
            
            # For now, we'll use the regular TTS API and simulate streaming
            # In a real implementation, you'd use OpenAI's streaming TTS API
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            
            # Read the audio data in chunks to simulate streaming
            audio_data = response.content
            chunk_size = 1024  # 1KB chunks
            
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                yield {
                    'audio_chunk': chunk,
                    'is_final': i + chunk_size >= len(audio_data),
                    'progress': min(1.0, (i + chunk_size) / len(audio_data))
                }
                
                # Simulate some processing time
                await asyncio.sleep(0.01)
            
            logger.info("Audio generation completed")
            
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            yield {
                'error': str(e),
                'is_final': True
            }
    
    async def generate_audio_file(self, text: str, output_path: str = None):
        """
        Generate complete audio file from text
        
        Args:
            text: Text to convert to speech
            output_path: Optional path to save the audio file
            
        Returns:
            Audio data as bytes
        """
        try:
            logger.info(f"Generating audio file for text: {text[:50]}...")
            
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            
            audio_data = response.content
            
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                logger.info(f"Audio file saved to: {output_path}")
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Error generating audio file: {str(e)}")
            return None 