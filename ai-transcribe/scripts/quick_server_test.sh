#!/bin/bash

echo "🚀 Quick Server Test"
echo "==================="

# Navigate to the app directory
cd /var/www/vhosts/olliecourse.com/ai.olliecourse.com/flaskapp

echo "📁 Current directory: $(pwd)"
echo "📋 Files present:"
ls -la main.py helpers.py chat_service.py tts_service.py speech_analysis.py

echo ""
echo "🐍 Python version:"
python3 --version

echo ""
echo "📦 Check if dependencies are installed:"
python3 -c "import fastapi, uvicorn, openai; print('✅ All key dependencies available')" 2>/dev/null || echo "❌ Missing dependencies"

echo ""
echo "🔧 Test if main.py can be imported:"
python3 -c "from main import app; print('✅ FastAPI app loaded successfully')" 2>/dev/null || echo "❌ Failed to load FastAPI app"

echo ""
echo "🌐 Quick API test (if server is running):"
curl -s http://localhost:5000/api/health 2>/dev/null | head -1 || echo "❌ Server not responding on port 5000"

echo ""
echo "📚 API Documentation (if server is running):"
curl -s http://localhost:5000/docs 2>/dev/null | grep -o "<title>.*</title>" || echo "❌ API docs not accessible" 