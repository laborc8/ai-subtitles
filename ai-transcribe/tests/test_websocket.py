#!/usr/bin/env python3
"""
Simple test script for the WebSocket server
"""

import asyncio
import websockets
import json
import time

async def test_websocket():
    """Test the WebSocket server"""
    uri = "ws://localhost:5000/ws/test_client"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            
            # Test connection message
            connect_message = {
                "service_type": "ai_chat",
                "message_type": "connect",
                "data": {
                    "speech_confidence_analysis": False
                }
            }
            
            await websocket.send(json.dumps(connect_message))
            print("Sent connect message")
            
            # Wait for response
            response = await websocket.recv()
            print(f"Received: {response}")
            
            # Test chat request
            chat_message = {
                "service_type": "ai_chat",
                "message_type": "chat_request",
                "data": {
                    "message": "Hello, this is a test message",
                    "aiAgent": "train_sentences",
                    "prompt": "You are a helpful tutor.",
                    "promptAddon": "Current topic: Testing",
                    "speech_confidence_analysis": False
                }
            }
            
            await websocket.send(json.dumps(chat_message))
            print("Sent chat request")
            
            # Wait for streaming response
            start_time = time.time()
            while time.time() - start_time < 30:  # Wait up to 30 seconds
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    print(f"Received: {response}")
                except asyncio.TimeoutError:
                    print("No more responses, ending test")
                    break
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing WebSocket server...")
    asyncio.run(test_websocket()) 