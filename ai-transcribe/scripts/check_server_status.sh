#!/bin/bash

echo "🔍 Checking current server status..."
echo "=================================="

# Check if the service is running
if systemctl is-active --quiet whisper-backend.service; then
    echo "✅ Service is currently RUNNING"
    echo "📊 Service status:"
    systemctl status whisper-backend.service --no-pager
else
    echo "❌ Service is NOT RUNNING"
fi

echo ""
echo "📋 Service details:"
systemctl show whisper-backend.service --property=ExecStart,WorkingDirectory,User

echo ""
echo "📝 Recent logs:"
journalctl -u whisper-backend.service --no-pager -n 20

echo ""
echo "🌐 Test if port 5000 is listening:"
netstat -tlnp | grep :5000 || echo "Port 5000 not listening"

echo ""
echo "📁 Check if files exist:"
ls -la /var/www/vhosts/olliecourse.com/ai.olliecourse.com/flaskapp/main.py
ls -la /var/www/vhosts/olliecourse.com/ai.olliecourse.com/flaskapp/requirements.txt 