import openai
import os
import time
import asyncio
from typing import Dict, Any, Optional
from services.base_service import BaseService, ServiceType, ServiceMessage
from services.speech_recognition_service import SpeechRecognitionService
from services.streaming_tts_service import StreamingTTSService
from logger_config import logger

# Import chat service (conditional)
try:
    from chat_service import ChatService
    CHAT_SERVICE_AVAILABLE = True
except ImportError:
    logger.warning("ChatService not available, using basic OpenAI client")
    CHAT_SERVICE_AVAILABLE = False

class EnhancedChatService(BaseService):
    """Enhanced ChatService with streaming capabilities"""
    
    def __init__(self):
        super().__init__(ServiceType.AI_CHAT)
        if CHAT_SERVICE_AVAILABLE:
            self.chat_service = ChatService()
        else:
            # Create basic OpenAI client
            self.chat_service = None
            self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.speech_service = SpeechRecognitionService()
        self.tts_service = StreamingTTSService()
        self.client_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def handle_connection(self, client_id: str, session_id: Optional[str] = None):
        """Handle new AIChat client connection"""
        self.client_sessions[client_id] = {
            'session_id': session_id,
            'conversation_history': [],
            'is_listening': False,
            'speech_confidence_analysis': False,
            'current_request': None
        }
        logger.info(f"AIChat client connected: {client_id}")
    
    async def handle_disconnection(self, client_id: str):
        """Handle AIChat client disconnection"""
        if client_id in self.client_sessions:
            await self.cleanup(client_id)
            del self.client_sessions[client_id]
        logger.info(f"AIChat client disconnected: {client_id}")
    
    async def handle_message(self, message: ServiceMessage):
        """Handle AIChat specific messages"""
        client_id = message.client_id
        
        # Ensure client session exists
        if client_id not in self.client_sessions:
            await self.handle_connection(client_id)
        
        if message.message_type == "connect":
            async for response in self._handle_connect(message):
                yield response
        elif message.message_type == "chat_request":
            async for response in self._handle_chat_request(message):
                yield response
        elif message.message_type == "speech_start":
            async for response in self._handle_speech_start(message):
                yield response
        elif message.message_type == "speech_data":
            async for response in self._handle_speech_data(message):
                yield response
        elif message.message_type == "speech_end":
            async for response in self._handle_speech_end(message):
                yield response
        elif message.message_type == "interrupt":
            async for response in self._handle_interrupt(message):
                yield response
        else:
            yield {
                "type": "error",
                "service_type": "ai_chat",
                "data": {"error": f"Unknown message type: {message.message_type}"},
                "client_id": message.client_id,
                "timestamp": time.time()
            }
    
    async def _handle_connect(self, message: ServiceMessage):
        """Handle initial connection with configuration"""
        client_id = message.client_id
        config = message.data
        
        self.client_sessions[client_id]['speech_confidence_analysis'] = config.get(
            'speech_confidence_analysis', False
        )
        
        yield {
            "type": "connect_ack",
            "service_type": "ai_chat",
            "supported_features": ["streaming", "speech_recognition", "tts"],
            "speech_confidence_analysis": self.client_sessions[client_id]['speech_confidence_analysis']
        }
    
    async def _handle_chat_request(self, message: ServiceMessage):
        """Handle chat request with streaming response"""
        client_id = message.client_id
        request_data = message.data
        
        # Store current request for potential interruption
        self.client_sessions[client_id]['current_request'] = request_data
        
        try:
            # Get system prompt from config or use default
            system_prompt = request_data.get('prompt') or self._get_default_system_prompt()
            
            # Stream chat response
            async for chunk in self._stream_chat_response(
                client_id=client_id,
                user_instructions=request_data['message'],
                system_prompt=system_prompt,
                speech_confidence_analysis=request_data.get('speech_confidence_analysis', False)
            ):
                yield {
                    "type": "chat_response_chunk",
                    "service_type": "ai_chat",
                    "data": chunk,
                    "client_id": client_id,
                    "timestamp": time.time()
                }
            
        
        except Exception as e:
            logger.error(f"Error in chat request: {str(e)}")
            yield {
                "type": "error",
                "service_type": "ai_chat",
                "data": {"error": str(e)},
                "client_id": client_id,
                "timestamp": time.time()
            }
    
    async def _stream_chat_response(self, client_id: str, user_instructions: str, 
                                   system_prompt: str, speech_confidence_analysis: bool):
        """Stream chat response using OpenAI"""
        try:
            if CHAT_SERVICE_AVAILABLE:
                # Use existing chat service
                if client_id not in self.chat_service.conversations:
                    self.chat_service.conversations[client_id] = [{
                        'role': 'system',
                        'content': system_prompt
                    }]
                
                self.chat_service.conversations[client_id].append({
                    'role': 'user', 
                    'content': user_instructions
                })
                
                response = self.chat_service.client.chat.completions.create(
                    model="gpt-4o",
                    messages=self.chat_service.conversations[client_id],
                    temperature=0.5,
                    stream=True
                )
                
                assistant_message = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        assistant_message += content
                        yield {
                            'content': content,
                            'timestamp': time.time()
                        }
                
                self.chat_service.conversations[client_id].append({
                    'role': 'assistant', 
                    'content': assistant_message
                })
                
                # Generate TTS audio if speech confidence analysis is enabled
                if speech_confidence_analysis and assistant_message.strip():
                    try:
                        logger.info(f"Generating TTS audio for message: {assistant_message[:50]}...")
                        async for audio_chunk in self.tts_service.stream_audio(assistant_message):
                            yield {
                                "type": "audio_chunk",
                                "service_type": "ai_chat",
                                "data": audio_chunk,
                                "client_id": client_id,
                                "timestamp": time.time()
                            }
                    except Exception as e:
                        logger.error(f"Error generating TTS audio: {str(e)}")
            else:
                # Use basic OpenAI client
                messages = [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_instructions}
                ]
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.5,
                    stream=True
                )
                
                assistant_message = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        assistant_message += content
                        yield {
                            'content': content,
                            'timestamp': time.time()
                        }
                
                # Generate TTS audio if speech confidence analysis is enabled
                if speech_confidence_analysis and assistant_message.strip():
                    try:
                        logger.info(f"Generating TTS audio for message: {assistant_message[:50]}...")
                        async for audio_chunk in self.tts_service.stream_audio(assistant_message):
                            yield {
                                "type": "audio_chunk",
                                "service_type": "ai_chat",
                                "data": audio_chunk,
                                "client_id": client_id,
                                "timestamp": time.time()
                            }
                    except Exception as e:
                        logger.error(f"Error generating TTS audio: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error streaming chat response: {str(e)}")
            yield {
                'content': f"Sorry, I encountered an error: {str(e)}",
                'timestamp': time.time()
            }
    
    async def _handle_speech_start(self, message: ServiceMessage):
        """Handle speech recognition start"""
        client_id = message.client_id
        self.client_sessions[client_id]['is_listening'] = True
        
        yield {
            "type": "speech_start_ack",
            "service_type": "ai_chat",
            "data": {"status": "listening"},
            "client_id": client_id,
            "timestamp": time.time()
        }
    
    async def _handle_speech_data(self, message: ServiceMessage):
        """Handle incoming speech data"""
        client_id = message.client_id
        audio_data = message.data['audio_data']
        
        # Transcribe audio
        transcription = await self.speech_service.transcribe_audio(
            audio_data,
            use_microsoft=self.client_sessions[client_id]['speech_confidence_analysis']
        )
        
        if transcription:
            yield {
                "type": "speech_transcription",
                "service_type": "ai_chat",
                "data": {
                    "text": transcription['text'],
                    "confidence": transcription.get('confidence'),
                    "is_final": transcription.get('is_final', False)
                },
                "client_id": client_id,
                "timestamp": time.time()
            }
        else:
            yield {
                "type": "error",
                "service_type": "ai_chat",
                "data": {"error": "Transcription failed"},
                "client_id": client_id,
                "timestamp": time.time()
            }
    
    async def _handle_speech_end(self, message: ServiceMessage):
        """Handle speech recognition end"""
        client_id = message.client_id
        self.client_sessions[client_id]['is_listening'] = False
        
        yield {
            "type": "speech_end_ack",
            "service_type": "ai_chat",
            "data": {"status": "stopped"},
            "client_id": client_id,
            "timestamp": time.time()
        }
    
    async def _handle_interrupt(self, message: ServiceMessage):
        """Handle conversation interruption"""
        client_id = message.client_id
        
        # Cancel current request if any
        if self.client_sessions[client_id]['current_request']:
            # Implementation for canceling ongoing requests
            self.client_sessions[client_id]['current_request'] = None
        
        yield {
            "type": "interrupt_ack",
            "service_type": "ai_chat",
            "data": {"status": "interrupted"},
            "client_id": client_id,
            "timestamp": time.time()
        }
    
    async def cleanup(self, client_id: str):
        """Cleanup AIChat resources for client"""
        if client_id in self.client_sessions:
            session = self.client_sessions[client_id]
            if session['is_listening']:
                # Stop speech recognition
                pass
            if session['current_request']:
                # Cancel ongoing request
                pass
    
    def _get_default_system_prompt(self):
        """Get default system prompt"""
        return (
            'You are a helpful nice instructor / teacher assistant. '
            'When you formulate an answer can you only use simple words as if you are talking to a kid. '
            'When I give you a sentence - can you then evaluate if the "at" in the sentence fulfills my 1st definition of at: '
            '"Shows the place or position of something or someone." and can you make sure that it is correctly used. '
            'When you answer can you first say CORRECT or FLUNK (if not correct with a short explanation why it is wrong - if correct a nice acknowledgement) '
            'and then ask for another example.'
        ) 