# Backend Testing Documentation

This document provides comprehensive information about the backend testing suite for the Screen Time Competition application.

## Current Test Status

**Latest Test Run Results:**
- ✅ **127 passing tests** (59.3% success rate)
- ❌ 87 failing tests (40.7%)  
- 📊 **214 total tests** across 9 test files

**What's Working:**
- Authentication workflows (login, register, password reset)
- Badge achievement detection and awarding
- Email services (password reset emails)
- Friendship management (requests, acceptance)
- Screen time logging (basic operations)
- Integration API tests for auth and badges

**Known Issues:**
- Database constraint violations (foreign keys, uniqueness)
- Some service methods referenced by tests don't exist yet
- Advanced feature tests for functionality not yet implemented

See `FINAL_STATUS.md` for detailed analysis and remaining work.

## Overview

The testing suite includes both **unit tests** and **integration tests** using Python's `unittest` framework. All tests are located in the `backend/tests/` directory.

## Test Structure

```
backend/tests/
├── __init__.py
├── run_tests.py           # Main test runner script
├── test_config.py         # Test configuration and utilities
├── validate_tests.py      # Basic validation script
├── unit/                  # Unit tests for services
│   ├── __init__.py
│   ├── test_auth_service.py
│   ├── test_badge_achievement_service.py
│   ├── test_badge_service.py
│   ├── test_email_service.py
│   ├── test_friendship_service.py
│   ├── test_leaderboard_service.py
│   ├── test_screen_time_service.py
│   └── test_streak_service.py
└── integration/           # Integration tests for APIs
    ├── __init__.py
    ├── test_auth_api.py
    ├── test_badges_api.py
    ├── test_friendship.py
    ├── test_leaderboard.py
    └── test_screen_time.py
```

## Test Categories

### Unit Tests

Unit tests focus on testing individual service classes in isolation using mocks where necessary:

- **AuthService Tests**: User registration, authentication, password reset
- **BadgeService Tests**: Badge management, awarding, revocation  
- **BadgeAchievementService Tests**: Automatic badge detection and awarding
- **EmailService Tests**: Password reset email functionality
- **FriendshipService Tests**: Friend request management and operations
- **LeaderboardService Tests**: User ranking and statistics
- **ScreenTimeService Tests**: Screen time logging and validation
- **StreakService Tests**: Streak calculation and maintenance

### Integration Tests

Integration tests verify complete API workflows with real database interactions:

- **Auth API Tests**: Registration, login, logout endpoints
- **Badges API Tests**: Badge retrieval and management endpoints
- **Friendship API Tests**: Friend request and management endpoints
- **Leaderboard API Tests**: Ranking and statistics endpoints
- **Screen Time API Tests**: Data logging and retrieval endpoints

## Running Tests

### Prerequisites

1. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Ensure you're in the project root directory

### Running All Tests

```bash
# From project root
cd /path/to/screen-time-competition
python backend/tests/run_tests.py
```

### Running Specific Test Categories

```bash
# Unit tests only
python backend/tests/run_tests.py --type unit

# Integration tests only
python backend/tests/run_tests.py --type integration
```

### Running Specific Test Files

```bash
# Run specific test pattern
python backend/tests/run_tests.py --pattern "test_auth_*.py"
```

### Running Individual Test Files

```bash
# Using unittest
cd /path/to/screen-time-competition
python -m unittest backend.tests.unit.test_auth_service -v

# Using pytest (if available)
cd backend
python -m pytest tests/unit/test_auth_service.py -v
```

## Test Features

### Comprehensive Coverage

Each test module includes:

- **Happy Path Tests**: Normal operation scenarios
- **Edge Case Tests**: Boundary conditions and unusual inputs
- **Error Handling Tests**: Invalid inputs and error conditions
- **Security Tests**: SQL injection prevention, input sanitization
- **Concurrency Tests**: Race conditions and data integrity
- **Validation Tests**: Input validation and business rules

### Test Utilities

The `test_config.py` provides:

- **BaseTestCase**: Common setup/teardown for database tests
- **MockDatabaseTestCase**: Utilities for mocking database operations
- **Helper Methods**: User creation, login simulation, assertion helpers
- **Test Discovery**: Automated test suite creation

### Mocking Strategy

Tests use appropriate mocking for:

- Database operations (for pure unit tests)
- External services (email sending)
- Time-dependent operations
- File system operations

## Test Data Management

### Database Isolation

Each test case:
- Uses a temporary SQLite database
- Creates fresh database tables for each test
- Cleans up data after each test
- Ensures no test interference

### Test Fixtures

Common test fixtures include:
- Test users with known credentials
- Sample screen time data
- Badge configurations
- Friendship relationships

## Code Quality

### Test Naming Conventions

- Test methods start with `test_`
- Descriptive names indicating the scenario
- Format: `test_<method>_<scenario>_<expected_result>`

Examples:
```python
def test_register_duplicate_username(self):
def test_authenticate_invalid_password(self):
def test_send_friend_request_to_self(self):
```

### Documentation Standards

Each test method includes:
- Docstring describing the test purpose
- Clear parameter documentation
- Return value documentation
- Explanation of the test scenario

### Assertions

Tests use descriptive assertions:
```python
self.assertEqual(result.username, "expected_username")
self.assertIn("error message", str(context.exception))
self.assertIsNotNone(created_user)
```

## Common Test Scenarios

### Authentication Tests

- Valid/invalid credentials
- Password strength validation
- Account lockout scenarios
- Token expiration handling
- SQL injection prevention

### Screen Time Tests

- Valid time entry creation
- Invalid input handling (negative, excessive values)
- Date validation (future dates, very old dates)
- Data aggregation accuracy
- Concurrent entry handling

### Friendship Tests

- Friend request lifecycle
- Duplicate request prevention
- Self-friending prevention
- Privacy settings
- Mutual friend detection

### Badge Tests

- Automatic badge detection
- Badge awarding/revocation
- Progress tracking
- Concurrent badge awards
- Badge statistics

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running tests from the project root directory
2. **Database Errors**: Check that SQLite is available and writable
3. **Missing Dependencies**: Run `pip install -r requirements.txt`
4. **Path Issues**: Verify Python path includes the backend directory

### Debug Mode

Run tests with verbose output:
```bash
python backend/tests/run_tests.py --verbose
```

Add debug prints in test methods:
```python
def test_something(self):
    print(f"Debug: Testing with data {test_data}")
    # ... test code
```

### Test Isolation Issues

If tests interfere with each other:
1. Check that `tearDown` methods clean up properly
2. Ensure no global state is modified
3. Use separate test database instances
4. Clear caches between tests

## Contributing

When adding new tests:

1. Follow the existing naming conventions
2. Include comprehensive docstrings
3. Test both success and failure scenarios
4. Add edge cases and security tests
5. Mock external dependencies appropriately
6. Update this documentation

## Performance Considerations

- Unit tests should run quickly (< 1 second each)
- Integration tests may take longer but should be optimized
- Use database transactions for faster cleanup
- Mock expensive operations in unit tests
- Run integration tests against minimal datasets

## Continuous Integration

The test suite is designed to be run in CI/CD pipelines:

- All tests use relative paths
- No external dependencies (except database)
- Clean setup/teardown for parallel execution
- Detailed error reporting for debugging

## Test Metrics

Track test coverage and quality:
- Aim for >90% code coverage
- Monitor test execution time
- Track flaky test incidents
- Measure test effectiveness (bug detection rate)
