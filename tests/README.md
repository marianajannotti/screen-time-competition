# Test Organization

This directory contains all tests for the Screen Time Competition project.

## Structure

```
tests/
├── backend/
│   ├── unit/              # Unit tests for services, models
│   │   └── test_streak_service.py
│   └── integration/       # API endpoint tests
│       ├── test_screen_time.py
│       ├── test_badges_api.py
│       ├── test_friendship.py
│       └── test_leaderboard.py
│
├── frontend/              # Frontend tests (future)
│   ├── components/        # Component tests
│   ├── integration/       # Integration tests
│   └── e2e/              # End-to-end tests
│
└── conftest.py           # Shared pytest fixtures
```

## Running Tests

### All Tests
```bash
pytest tests/
```

### Backend Tests Only
```bash
pytest tests/backend/
```

### Unit Tests Only
```bash
pytest tests/backend/unit/
```

### Integration Tests Only
```bash
pytest tests/backend/integration/
```

### Specific Test File
```bash
pytest tests/backend/unit/test_streak_service.py
```

### With Coverage
```bash
pytest tests/ --cov=backend --cov-report=html
```

## Test Types

### Unit Tests (`backend/unit/`)
- Test individual components in isolation
- Focus on business logic (services, utilities)
- No HTTP requests, minimal database setup
- Fast execution
- Example: `test_streak_service.py` tests StreakService methods

### Integration Tests (`backend/integration/`)
- Test complete API endpoints
- Test interactions between components
- Include HTTP requests and database operations
- Example: `test_screen_time.py` tests `/api/screen-time/` endpoints

### Frontend Tests (`frontend/`)
- Component unit tests
- Integration tests for component interactions
- End-to-end tests for user workflows
- To be implemented with Vitest/Jest and Playwright

## Writing Tests

### Unit Test Example
```python
# tests/backend/unit/test_my_service.py
from backend.services import MyService

def test_calculate_something():
    result = MyService.calculate(10, 20)
    assert result == 30
```

### Integration Test Example
```python
# tests/backend/integration/test_my_api.py
import unittest
from backend import create_app
from backend.database import db

class MyAPITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
    
    def test_my_endpoint(self):
        response = self.client.get('/api/my-endpoint')
        self.assertEqual(response.status_code, 200)
```

## Test Data

Use factories or fixtures to create test data consistently:
- Database records for testing
- Mock API responses
- User credentials

## Continuous Integration

Tests are automatically run on:
- Pull requests
- Pushes to main branch
- Before deployments

All tests must pass before merging code.
