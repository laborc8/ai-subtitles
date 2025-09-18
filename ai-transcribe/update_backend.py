#!/usr/bin/env python3
"""
Quick script to update the backend with the client session fix
"""
import os
import subprocess
import sys

def update_backend():
    """Update the backend service with the latest changes"""
    
    # Path to the enhanced_chat_service.py file
    service_file = "services/enhanced_chat_service.py"
    
    print("🔧 Updating backend service...")
    
    # Check if file exists
    if not os.path.exists(service_file):
        print(f"❌ Error: {service_file} not found")
        return False
    
    print(f"✅ Found {service_file}")
    
    # Restart the service
    try:
        print("🔄 Restarting whisper-backend service...")
        result = subprocess.run(
            ["sudo", "systemctl", "restart", "whisper-backend.service"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Service restarted successfully")
        
        # Check service status
        status_result = subprocess.run(
            ["sudo", "systemctl", "status", "whisper-backend.service", "--no-pager"],
            capture_output=True,
            text=True,
            check=True
        )
        print("📊 Service status:")
        print(status_result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error restarting service: {e}")
        print(f"Error output: {e.stderr}")
        return False

if __name__ == "__main__":
    success = update_backend()
    sys.exit(0 if success else 1)

