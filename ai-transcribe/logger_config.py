# logger_config.py
from loguru import logger
import os
import sys

# Try to create logs directory in a writable location
log_dirs = [
    "/tmp/whisper-logs",  # System temp directory (usually writable)
    "/var/log/whisper",   # System log directory
    "logs"                # Local directory (fallback)
]

log_dir = None
for dir_path in log_dirs:
    try:
        os.makedirs(dir_path, exist_ok=True)
        # Test if we can write to this directory
        test_file = os.path.join(dir_path, "test_write.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        log_dir = dir_path
        break
    except (OSError, PermissionError):
        continue

if log_dir is None:
    # If no writable directory found, log to stderr only
    print("Warning: No writable log directory found. Logging to stderr only.", file=sys.stderr)
    logger.add(sys.stderr, level="INFO")
else:
    # Add file logging
    logger.add(f"{log_dir}/flask.log", rotation="5 MB", retention="5 days", level="INFO")
    logger.add(f"{log_dir}/transcribe.log", rotation="5 MB", retention="7 days", level="DEBUG")

logger = logger.bind(app="flaskapp")
