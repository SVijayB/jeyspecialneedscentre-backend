# Django REST API Integration Test Suite

This directory contains a comprehensive integration test suite for the Jey Special Needs Centre Django REST API.

## Overview

These are **REAL integration tests** that:
- Create actual data in the database
- Test live API endpoints (not mocked)
- Use created data in subsequent tests
- Clean up everything automatically

## Test Structure

```
tests/
├── base_test.py           # Shared utilities, logging, HTTP client
├── resource_manager.py    # Create/cleanup shared resources
├── auth_tests.py          # Authentication tests
├── branch_tests.py        # Branch CRUD tests
├── user_tests.py          # User CRUD tests
├── attendance_tests.py    # Attendance CRUD tests
├── leave_tests.py         # Leave CRUD tests
├── qr_tests.py           # QR generation/scanning tests
├── integration_runner.py  # Main test coordinator
└── run_tests.py          # CLI interface
```

## Quick Start

1. **Start Django server**:
   ```bash
   cd src
   python manage.py runserver
   ```

2. **Run all tests**:
   ```bash
   cd tests
   python run_tests.py
   ```

3. **Run specific tests**:
   ```bash
   python run_tests.py --tests auth,user
   ```

## Requirements

- Django server running on `http://localhost:8000`
- Admin credentials: `username=admin`, `password=admin123`
- Python `requests` library

## Test Modules

- **auth** - Login, logout, token validation
- **branch** - Branch CRUD operations  
- **user** - User CRUD operations
- **attendance** - Attendance logging CRUD
- **leave** - Leave application CRUD
- **qr** - QR code generation and scanning

## Execution Order

Tests run in dependency order:
`auth → branch → user → attendance → leave → qr`

## Features

✅ **Real Integration Testing** - Creates actual database records  
✅ **Live API Testing** - Tests actual endpoints, not mocks  
✅ **Automatic Cleanup** - Removes all created data  
✅ **Dependency Management** - Creates required resources  
✅ **Failure Logging** - Logs only failures with full debug info  
✅ **Modular Design** - Each module can run independently  
✅ **Comprehensive Coverage** - Tests CRUD, validation, filtering  

## Usage Examples

```bash
# Run all tests
python run_tests.py

# Run specific modules
python run_tests.py --tests auth,branch,user

# Run without cleanup (for debugging)
python run_tests.py --no-cleanup

# List available modules
python run_tests.py --list

# Run individual module
python auth_tests.py --cleanup
```

## Test Data

All test data uses timestamps for uniqueness:
- Branches: `TestBranch_20240908_143022_123`
- Users: `testuser_20240908_143022_123@example.com`
- Employee IDs: `EMP_20240908_143022_123`

## Cleanup

- Automatic cleanup after all tests
- Manual cleanup with `--cleanup` flag
- Individual module cleanup supported
- Resources deleted in reverse dependency order

## Debugging

- Only failures are logged with full request/response details
- Use `--no-cleanup` to inspect created data
- Check individual test modules for specific failures
- Server logs provide additional debugging info

## Architecture

The test suite follows a modular architecture:

1. **BaseIntegrationTest** - Common functionality for all tests
2. **ResourceManager** - Handles shared resource creation
3. **Individual Test Modules** - Domain-specific test logic
4. **IntegrationTestRunner** - Coordinates execution
5. **CLI Interface** - User-friendly command line

This ensures maintainable, reliable integration testing that actually validates the live API functionality.
