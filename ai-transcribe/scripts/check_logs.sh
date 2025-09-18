#!/bin/bash

echo "=== Whisper Backend Log Files ==="

# Check possible log directories
log_dirs=(
    "/tmp/whisper-logs"
    "/var/log/whisper"
    "/var/www/vhosts/olliecourse.com/ai.olliecourse.com/flaskapp/logs"
)

echo "Searching for log files in possible directories..."

for dir in "${log_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo ""
        echo "📁 Directory: $dir"
        echo "   Permissions: $(ls -ld "$dir")"
        
        if [ -r "$dir" ]; then
            echo "   Files:"
            ls -la "$dir" 2>/dev/null || echo "   (Cannot list files)"
            
            # Check for specific log files
            for log_file in "$dir"/flask.log "$dir"/transcribe.log; do
                if [ -f "$log_file" ]; then
                    echo "   📄 $log_file"
                    echo "   Size: $(ls -lh "$log_file" | awk '{print $5}')"
                    echo "   Last modified: $(ls -l "$log_file" | awk '{print $6, $7, $8}')"
                fi
            done
        else
            echo "   (Directory not readable)"
        fi
    fi
done

echo ""
echo "=== System Journal Logs ==="
echo "Recent systemd service logs:"
sudo journalctl -u whisper-backend.service --no-pager -n 10

echo ""
echo "=== Service Status ==="
sudo systemctl status whisper-backend.service --no-pager

echo ""
echo "=== Quick Log Check Commands ==="
echo "To view flask.log in real-time:"
echo "  tail -f /tmp/whisper-logs/flask.log"
echo ""
echo "To view transcribe.log in real-time:"
echo "  tail -f /tmp/whisper-logs/transcribe.log"
echo ""
echo "To view systemd logs:"
echo "  sudo journalctl -u whisper-backend.service -f" 