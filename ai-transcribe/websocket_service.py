import asyncio
import json
import time
from typing import Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from services.service_registry import service_registry, ServiceType
from services.base_service import ServiceMessage
from services.enhanced_chat_service import EnhancedChatService
from logger_config import logger

# Import old Flask functionality
from transcribe import process_s3_target
from helpers import (
    client_configs, STORAGE_DIR, serializer, VALID_USERNAME, VALID_PASSWORD, 
    STORAGE_API_KEY, validate_credentials, generate_signed_cloudfront_url, 
    generate_signed_url, get_client_config, get_supported_languages, 
    build_video_urls, handle_exception, clean_filename, clean_path, 
    sanitize_filename, sanitize_path
)
from itsdangerous import BadSignature
import os

class WebSocketManager:
    """Manages WebSocket connections and message routing"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_services: Dict[str, Set[ServiceType]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Handle new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_services[client_id] = set()
        logger.info(f"Client connected: {client_id}")
    
    def disconnect(self, client_id: str):
        """Handle WebSocket disconnection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        if client_id in self.client_services:
            service_registry.cleanup_client(client_id)
            del self.client_services[client_id]
        
        logger.info(f"Client disconnected: {client_id}")
    
    async def send_message(self, client_id: str, message: dict):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for client_id in list(self.active_connections.keys()):
            await self.send_message(client_id, message)
    
    async def handle_message(self, client_id: str, message_data: dict):
        """Route message to appropriate service"""
        try:
            logger.debug(f"Handling message for client {client_id}: {message_data}")
            
            service_type_str = message_data.get('service_type', 'ai_chat')
            service_type = ServiceType(service_type_str)
            
            service_message = ServiceMessage(
                service_type=service_type,
                message_type=message_data.get('type') or message_data.get('message_type', ''),
                data=message_data.get('data', {}),
                client_id=client_id,
                session_id=message_data.get('session_id'),
                timestamp=time.time()
            )
            
            service = service_registry.get_service(service_type)
            logger.debug(f"Got service: {service}")
            
            self.client_services[client_id].add(service_type)
            
            if hasattr(service, 'handle_message'):
                logger.debug(f"Calling handle_message on service")
                async for response in service.handle_message(service_message):
                    response['client_id'] = client_id
                    await self.send_message(client_id, response)
            else:
                logger.error(f"Service {service} does not have handle_message method")
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            logger.error(f"Message data: {message_data}")
            logger.error(f"Client ID: {client_id}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            error_message = {
                "type": "error",
                "service_type": message_data.get('service_type', 'unknown'),
                "data": {"error": str(e)},
                "client_id": client_id,
                "timestamp": time.time()
            }
            await self.send_message(client_id, error_message)

# Global WebSocket manager
websocket_manager = WebSocketManager()

# FastAPI app
app = FastAPI(title="Whisper Transcription & AI Chat Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register services
service_registry.register_service(ServiceType.AI_CHAT, EnhancedChatService)

# HTTP Endpoints (from old Flask app)
@app.get("/api/ping")
async def ping():
    logger.debug("Ping endpoint hit.")
    return {"status": "ok"}

@app.post("/api/login")
async def login(request_data: dict):
    """User authentication endpoint"""
    username = request_data.get("username")
    password = request_data.get("password")

    if validate_credentials(username, password):
        return {"success": True}
    else:
        return {"success": False, "error": "Invalid credentials"}

@app.post("/api/transcribe")
async def start_transcription(request_data: dict):
    """Start video transcription process"""
    try:
        bucket = request_data["bucket"]
        target = request_data["target"]
        lang = request_data.get("prompt_lang", "en")
        translate = request_data.get("enable_translation", False)
        upload = request_data.get("upload", False)
        upload_bucket = request_data.get("upload_bucket")
        upload_prefix = request_data.get("upload_prefix")
        advanced_encoding = request_data.get("advanced_encoding", False)
        translate_languages = request_data.get("languages", [])
        override = request_data.get("override", False)
        client_id = request_data.get("client_id", "default")

        logger.info(f"Starting transcription for {bucket}/{target} | lang={lang}, translate={translate}, upload={upload}, translate_languages={translate_languages}, override={override}, client_id={client_id}")

        # Get client config
        config = get_client_config(client_configs, client_id)

        result = process_s3_target(
            bucket,
            target,
            prompt_lang=lang,
            enable_translation=translate,
            upload=upload,
            upload_bucket=upload_bucket,
            upload_prefix=upload_prefix,
            cloudfront_base_url=config['CLOUDFRONT_BASE_URL'],
            advanced_encoding=advanced_encoding,
            translate_languages=translate_languages,
            override=override
        )

        # Only sign the video URL with CloudFront
        for item in result:
            if item.get("cloudfront_url"):
                item["video_url"] = generate_signed_cloudfront_url(item["source_video"], client_id)

        logger.debug("Transcription finished successfully")
        return result

    except Exception as e:
        return handle_exception(e, "transcription")

@app.get('/api/storage/{filename:path}')
async def serve_storage_file(filename: str, x_api_key: str = None):
    """Serve storage files with API key authentication"""
    if x_api_key != STORAGE_API_KEY:
        logger.warning("Unauthorized access to storage file.")
        return {"error": "Unauthorized"}
    
    storage_root = os.path.join(os.path.dirname(__file__), 'storage')
    full_path = os.path.join(storage_root, filename)
    
    # Security check: prevent directory traversal
    if not os.path.abspath(full_path).startswith(os.path.abspath(storage_root)):
        logger.warning("Path traversal detected.")
        return {"error": "Unauthorized"}
    
    if not os.path.exists(full_path):
        logger.warning(f"Requested file not found: {full_path}")
        return {"error": "File not found"}
    
    directory = os.path.dirname(full_path)
    file_name = os.path.basename(full_path)
    return {"file_path": full_path, "filename": filename}

@app.get('/api/storage-secure/{token}')
async def serve_subtitle_secure(token: str):
    """Serve files with secure token authentication"""
    try:
        filename = serializer.loads(token, max_age=300)  # 5 minutes
    except BadSignature:
        return {"error": "Invalid token"}
    
    safe_path = os.path.join(STORAGE_DIR, filename)
    if not os.path.exists(safe_path):
        return {"error": "File not found"}
    
    return {"file_path": safe_path, "filename": filename}

@app.post("/api/sign-url")
async def sign_url(request_data: dict):
    """Generate signed CloudFront URLs"""
    try:
        key = request_data.get("key")
        client_id = request_data.get("client_id", "default")
        logger.debug(f"Signing request for key: {key}")
        logger.debug(f"Request body: {request_data}")

        if not key:
            logger.warning("Missing 'key' in sign-url request.")
            return {"error": "Missing 'key'"}

        signed_url = generate_signed_cloudfront_url(key, client_id)
        return {"signed_url": signed_url}
    except Exception as e:
        return handle_exception(e, "sign_url")

@app.get("/api/subtitles")
async def get_subtitle_tracks(video_key: str, advanced: bool = False, client_id: str = "default"):
    """Get subtitle tracks for a video"""
    try:
        if not video_key:
            return {"error": "Missing video_key parameter"}

        logger.info(f"Getting subtitle tracks for {video_key} (advanced: {advanced}, client_id: {client_id})")

        # Get client config
        config = get_client_config(client_configs, client_id)

        # Parse the video key to derive subtitle directory and filename
        # Subtitles are stored under STORAGE_DIR/<base_key>/<filename>.vtt
        # where <base_key> is the full video key without extension (may contain parentheses)
        base_key_dir = os.path.splitext(video_key)[0]
        filename_base = clean_filename(os.path.basename(base_key_dir))

        subtitle_tracks = []
        languages = get_supported_languages()

        for lang_code, lang_label in languages.items():
            if lang_code == 'en':
                # Default English subtitle without _en
                filename = f"{filename_base}.vtt"
            else:
                filename = f"{filename_base}_{lang_code}.vtt"
            
            full_path = os.path.join(STORAGE_DIR, base_key_dir, filename)

            if os.path.exists(full_path):
                secure_url = generate_signed_url(f"{base_key_dir}/{filename}", client_id)
                subtitle_tracks.append({
                    "file": secure_url,
                    "label": lang_label,
                    "lang": lang_code
                })

        # Build video URLs with proper sanitization and CloudFront signing
        video_urls = build_video_urls(video_key, config, advanced, client_id)

        return {
            "tracks": subtitle_tracks,
            **video_urls
        }

    except Exception as e:
        return handle_exception(e, "get_subtitle_tracks")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_connections": len(websocket_manager.active_connections),
        "supported_services": len(service_registry.get_supported_services())
    }

@app.get("/api/services")
async def get_supported_services():
    """Get list of supported services"""
    return {
        "services": [
            {
                "type": service_type.value,
                "name": service_type.name,
                "description": f"{service_type.name} service"
            }
            for service_type in service_registry.get_supported_services()
        ]
    }

# WebSocket endpoint
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Main WebSocket endpoint"""
    await websocket_manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            await websocket_manager.handle_message(client_id, message_data)
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        websocket_manager.disconnect(client_id) 