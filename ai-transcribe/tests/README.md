# Tests Directory

This directory contains all test files and testing utilities for the Whisper Transcription Service.

## Test Files

### `test_language_handling.py`
- **Purpose**: Demonstrates and tests the fixed language handling behavior
- **Usage**: `python tests/test_language_handling.py`
- **Description**: Shows different language scenarios and how the system handles source language transcription vs target language translation

### `test_service_start.sh`
- **Purpose**: Tests the FastAPI service startup and basic functionality
- **Usage**: `./tests/test_service_start.sh`
- **Description**: Stops, starts, and verifies the service is running properly

### `test_setup.py`
- **Purpose**: Tests the overall setup and configuration
- **Usage**: `python tests/test_setup.py`
- **Description**: Validates environment variables, dependencies, and basic functionality

### `test_services.py`
- **Purpose**: Tests individual services (chat, TTS, speech analysis)
- **Usage**: `python tests/test_services.py`
- **Description**: Validates that all service modules work correctly

### `xtest.py`
- **Purpose**: Quick experimental tests
- **Usage**: `python tests/xtest.py`
- **Description**: Temporary or experimental test code

## Running Tests

### All Tests
```bash
# Run all Python tests
python -m pytest tests/ -v

# Or run individual test files
python tests/test_language_handling.py
python tests/test_setup.py
python tests/test_services.py
```

### Service Tests
```bash
# Make scripts executable and run
chmod +x tests/test_service_start.sh
./tests/test_service_start.sh
```

## Test Categories

1. **Language Handling Tests**: Verify correct transcription and translation behavior
2. **Service Tests**: Validate FastAPI service functionality
3. **Setup Tests**: Check environment and configuration
4. **Integration Tests**: Test complete workflows 