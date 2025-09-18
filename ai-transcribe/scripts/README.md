# Scripts Directory

This directory contains utility scripts for deployment, monitoring, and maintenance of the Whisper Transcription Service.

## Deployment Scripts

### `deploy_fastapi.sh`
- **Purpose**: Deploy the FastAPI service to production
- **Usage**: `./scripts/deploy_fastapi.sh`
- **Description**: Updates systemd service, installs dependencies, and restarts the service

### `post-deploy.sh`
- **Purpose**: Post-deployment verification and cleanup
- **Usage**: `./scripts/post-deploy.sh`
- **Description**: Verifies deployment success and performs cleanup tasks

## Monitoring Scripts

### `check_server_status.sh`
- **Purpose**: Check the status of the FastAPI service
- **Usage**: `./scripts/check_server_status.sh`
- **Description**: Shows service status, logs, and basic health information

### `check_logs.sh`
- **Purpose**: Find and display log files
- **Usage**: `./scripts/check_logs.sh`
- **Description**: Searches for log files in various locations and shows their status

### `quick_server_test.sh`
- **Purpose**: Quick test of server functionality
- **Usage**: `./scripts/quick_server_test.sh`
- **Description**: Tests API endpoints and basic service functionality

## Usage Examples

### Deployment Workflow
```bash
# Deploy the service
./scripts/deploy_fastapi.sh

# Verify deployment
./scripts/post-deploy.sh

# Check status
./scripts/check_server_status.sh
```

### Monitoring Workflow
```bash
# Check service status
./scripts/check_server_status.sh

# View logs
./scripts/check_logs.sh

# Quick test
./scripts/quick_server_test.sh
```

### Making Scripts Executable
```bash
# Make all scripts executable
chmod +x scripts/*.sh

# Or make individual scripts executable
chmod +x scripts/deploy_fastapi.sh
chmod +x scripts/check_server_status.sh
```

## Script Categories

1. **Deployment Scripts**: Automate deployment and updates
2. **Monitoring Scripts**: Check service health and status
3. **Maintenance Scripts**: Log management and cleanup
4. **Testing Scripts**: Quick functionality verification

## Notes

- All scripts are designed to be run from the project root directory
- Scripts use relative paths and assume the project structure is maintained
- Some scripts require sudo privileges for systemd operations
- Log files are typically located in `/tmp/whisper-logs/` or system journal 