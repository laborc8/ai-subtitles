#!/bin/bash

echo "=== Testing Whisper Backend Service ==="

# Stop the service if running
echo "1. Stopping service..."
sudo systemctl stop whisper-backend.service

# Wait a moment
sleep 2

# Start the service
echo "2. Starting service..."
sudo systemctl start whisper-backend.service

# Wait for service to start
sleep 3

# Check service status
echo "3. Checking service status..."
sudo systemctl status whisper-backend.service --no-pager

# Check if service is active
if sudo systemctl is-active --quiet whisper-backend.service; then
    echo "✅ Service is running!"
    
    # Test API endpoint
    echo "4. Testing API endpoint..."
    sleep 2
    curl -s http://127.0.0.1:5000/health || echo "❌ API not responding"
    
    # Check logs
    echo "5. Checking recent logs..."
    sudo journalctl -u whisper-backend.service --no-pager -n 20
    
else
    echo "❌ Service failed to start"
    echo "6. Checking error logs..."
    sudo journalctl -u whisper-backend.service --no-pager -n 30
fi

echo "=== Test Complete ===" 