#!/usr/bin/env python3
"""
Main entry point for the Whisper Transcription Service
FastAPI-only version with all functionality migrated from Flask
"""

import uvicorn
import os
from websocket_service import app

if __name__ == "__main__":
    # Get port from environment or default to 80
    port = int(os.getenv("PORT", "80"))
    
    print("Starting FastAPI server with WebSocket support...")
    print("Server will be available at:")
    print(f"  - HTTP API: http://localhost:{port}")
    print(f"  - WebSocket: ws://localhost:{port}/ws/{{client_id}}")
    print(f"  - Health check: http://localhost:{port}/api/health")
    print(f"  - Services: http://localhost:{port}/api/services")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    ) 