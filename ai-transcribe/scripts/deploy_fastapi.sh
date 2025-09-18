#!/bin/bash

# FastAPI Deployment Script
# This script updates your systemd service to use FastAPI

echo "🚀 FastAPI Deployment Script"
echo "=============================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Backup current service
echo "📋 Backing up current service..."
cp /etc/systemd/system/whisper-backend.service /etc/systemd/system/whisper-backend.service.backup.$(date +%Y%m%d_%H%M%S)

# Stop current service
echo "⏹️  Stopping current service..."
systemctl stop whisper-backend.service

# Update virtual environment
echo "📦 Updating virtual environment..."
cd /var/www/vhosts/olliecourse.com/ai.olliecourse.com/flaskapp
source venv/bin/activate
pip install -r requirements.txt

# Copy new service file
echo "📄 Installing new service file..."
cp _docu/whisper-fastapi.service /etc/systemd/system/whisper-backend.service

# Reload systemd
echo "🔄 Reloading systemd..."
systemctl daemon-reload

# Enable and start service
echo "▶️  Starting FastAPI service..."
systemctl enable whisper-backend.service
systemctl start whisper-backend.service

# Check status
echo "📊 Checking service status..."
systemctl status whisper-backend.service --no-pager

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Useful commands:"
echo "  systemctl status whisper-backend.service"
echo "  systemctl restart whisper-backend.service"
echo "  journalctl -u whisper-backend.service -f"
echo ""
echo "🌐 Test your API:"
echo "  curl http://localhost:5000/api/health"
echo "  curl http://localhost:5000/api/ping"
echo ""
echo "📚 API Documentation:"
echo "  http://your-domain.com:5000/docs" 