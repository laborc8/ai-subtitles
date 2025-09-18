from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ServiceType(Enum):
    AI_CHAT = "ai_chat"
    CHAT = "chat"
    TRANSCRIPTION = "transcription"
    TTS = "tts"

@dataclass
class ServiceMessage:
    service_type: ServiceType
    message_type: str
    data: Dict[str, Any]
    client_id: str
    session_id: Optional[str] = None
    timestamp: float = None

class BaseService(ABC):
    """Base interface for all WebSocket services"""
    
    def __init__(self, service_type: ServiceType):
        self.service_type = service_type
    
    @abstractmethod
    async def handle_message(self, message: ServiceMessage) -> Dict[str, Any]:
        """Handle incoming service message"""
        pass
    
    @abstractmethod
    async def handle_connection(self, client_id: str, session_id: Optional[str] = None):
        """Handle new client connection"""
        pass
    
    @abstractmethod
    async def handle_disconnection(self, client_id: str):
        """Handle client disconnection"""
        pass
    
    @abstractmethod
    async def cleanup(self, client_id: str):
        """Cleanup resources for client"""
        pass 