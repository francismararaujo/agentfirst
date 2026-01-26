# AgentFirst2 MVP - Test Structure Guide

## Overview

All tests must follow a strict directory structure to ensure proper organization, discoverability, and maintainability.

## Directory Structure

```
app/tests/
├── __init__.py
├── conftest.py                          # ROOT CONFTEST (REQUIRED)
│                                        # - Environment setup
│                                        # - Global fixtures
│                                        # - Pytest markers
│                                        # - Sample data fixtures
│
├── unit/                                # Unit Tests
│   ├── __init__.py
│   ├── conftest.py                      # Unit-specific fixtures
│   ├── test_component_a.py
│   ├── test_component_b.py
│   └── ...
│
├── integration/                         # Integration Tests
│   ├── __init__.py
│   ├── conftest.py                      # Integration-specific fixtures
│   ├── test_workflow_a.py
│   ├── test_workflow_b.py
│   └── ...
│
├── performance/                         # Performance Tests
│   ├── __init__.py
│   ├── conftest.py                      # Performance-specific fixtures
│   ├── test_latency.py
│   ├── test_throughput.py
│   └── ...
│
└── e2e/                                 # End-to-End Tests
    ├── __init__.py
    ├── conftest.py                      # E2E-specific fixtures
    ├── test_user_journey.py
    ├── test_admin_workflow.py
    └── ...
```

## Root conftest.py (app/tests/conftest.py)

**REQUIRED** - Contains:

1. **Environment Setup**
   ```python
   os.environ["ENVIRONMENT"] = "test"
   os.environ["AWS_REGION"] = "us-east-1"
   os.environ["AWS_ACCESS_KEY_ID"] = "testing"
   os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
   ```

2. **Global Fixtures** (session-scoped)
   - `event_loop` - Async event loop for all tests
   - `mock_dynamodb` - Mock DynamoDB client
   - `mock_bedrock` - Mock Bedrock client
   - `mock_sns` - Mock SNS client
   - `mock_sqs` - Mock SQS client
   - `mock_secrets_manager` - Mock Secrets Manager client

3. **Sample Data Fixtures**
   - `sample_user_email` - Test email
   - `sample_telegram_id` - Test Telegram ID
   - `sample_user_data` - Test user object
   - `sample_session_data` - Test session object
   - `sample_telegram_message` - Test Telegram message
   - `sample_ifood_order` - Test iFood order

4. **Pytest Markers Registration**
   - `@pytest.mark.unit` - Unit tests
   - `@pytest.mark.integration` - Integration tests
   - `@pytest.mark.e2e` - End-to-end tests
   - `@pytest.mark.performance` - Performance tests
   - `@pytest.mark.property` - Property-based tests
   - `@pytest.mark.slow` - Slow running tests

## Category-Specific conftest.py

Each test category has its own `conftest.py` for category-specific fixtures:

### Unit Tests (app/tests/unit/conftest.py)
```python
@pytest.fixture
def unit_test_marker():
    """Marker for unit tests"""
    return "unit"
```

### Integration Tests (app/tests/integration/conftest.py)
```python
@pytest.fixture
def integration_test_marker():
    """Marker for integration tests"""
    return "integration"
```

### Performance Tests (app/tests/performance/conftest.py)
```python
@pytest.fixture
def performance_test_marker():
    """Marker for performance tests"""
    return "performance"
```

### E2E Tests (app/tests/e2e/conftest.py)
```python
@pytest.fixture
def e2e_test_marker():
    """Marker for e2e tests"""
    return "e2e"
```

## Test File Naming Convention

- **Unit tests**: `test_<component>.py`
  - Example: `test_dynamodb_repositories.py`, `test_secrets_manager.py`

- **Integration tests**: `test_<workflow>_integration.py`
  - Example: `test_dynamodb_integration.py`, `test_secrets_integration.py`

- **Performance tests**: `test_<component>_performance.py`
  - Example: `test_dynamodb_performance.py`, `test_secrets_performance.py`

- **E2E tests**: `test_<workflow>.py`
  - Example: `test_user_workflow.py`, `test_admin_workflow.py`

## Test Class Naming Convention

```python
# Unit Tests
class Test<Component>:
    """Tests for <Component>"""

# Integration Tests
class Test<Workflow>Integration:
    """Integration tests for <Workflow>"""

# Performance Tests
class Test<Component>Performance:
    """Performance tests for <Component>"""

# E2E Tests
class Test<Workflow>:
    """End-to-end tests for <Workflow>"""
```

## Test Method Naming Convention

```python
# Unit Tests
def test_<action>_<scenario>():
    """Test <action> in <scenario>"""

# Integration Tests
def test_<workflow>_<action>():
    """Test <workflow> with <action>"""

# Performance Tests
def test_<action>_latency():
    """Test that <action> completes within SLA"""

# E2E Tests
def test_complete_<workflow>_flow():
    """Test complete <workflow> flow"""
```

## Test Markers

Always mark your tests with appropriate markers:

```python
@pytest.mark.unit
class TestComponent:
    def test_something(self):
        pass

@pytest.mark.integration
class TestWorkflow:
    def test_something(self):
        pass

@pytest.mark.performance
class TestPerformance:
    def test_something(self):
        pass

@pytest.mark.e2e
class TestUserJourney:
    def test_something(self):
        pass

@pytest.mark.property
class TestProperties:
    @given(...)
    def test_something(self, data):
        pass
```

## Running Tests

```bash
# Run all tests
python -m pytest app/tests/ -v

# Run by category
python -m pytest app/tests/unit -v
python -m pytest app/tests/integration -v
python -m pytest app/tests/performance -v
python -m pytest app/tests/e2e -v

# Run by marker
python -m pytest app/tests/ -m unit -v
python -m pytest app/tests/ -m integration -v
python -m pytest app/tests/ -m performance -v
python -m pytest app/tests/ -m e2e -v

# Run specific test file
python -m pytest app/tests/unit/test_dynamodb_repositories.py -v

# Run specific test class
python -m pytest app/tests/unit/test_dynamodb_repositories.py::TestUserRepository -v

# Run specific test method
python -m pytest app/tests/unit/test_dynamodb_repositories.py::TestUserRepository::test_create_user -v

# Run with coverage
python -m pytest app/tests/ --cov=app --cov-report=html

# Run excluding slow tests
python -m pytest app/tests/ -m "not slow" -v
```

## Test Count Guidelines

- **Unit Tests**: 20-50 tests per component
- **Integration Tests**: 5-15 tests per workflow
- **Performance Tests**: 5-10 tests per component
- **E2E Tests**: 3-10 tests per workflow
- **Property-Based Tests**: 2-5 properties per component

## Fixtures Best Practices

1. **Use session-scoped fixtures** for expensive setup (event_loop, mock clients)
2. **Use function-scoped fixtures** for test-specific data
3. **Use class-scoped fixtures** for shared test class setup
4. **Keep fixtures in appropriate conftest.py** (root for global, category for specific)
5. **Document fixture purpose** with clear docstrings

## Example Test File Structure

```python
"""Unit tests for <Component> - Test <description>"""

import pytest
from unittest.mock import MagicMock, patch

from app.<module>.<component> import <Class>


@pytest.mark.unit
class Test<Class>:
    """Tests for <Class>"""

    @pytest.fixture
    def instance(self):
        """Create <Class> instance"""
        return <Class>()

    @pytest.fixture
    def mock_dependency(self):
        """Create mock dependency"""
        return MagicMock()

    def test_<action>_<scenario>(self, instance, mock_dependency):
        """Test <action> in <scenario>"""
        # Arrange
        expected = "value"
        
        # Act
        result = instance.<method>()
        
        # Assert
        assert result == expected


@pytest.mark.property
class Test<Class>Properties:
    """Property-based tests for <Class>"""

    @given(...)
    def test_<property>(self, data):
        """Validates: <Property description>"""
        # Test implementation
        pass
```

## Important Notes

- ✅ **Root conftest.py is REQUIRED** - Contains global setup and fixtures
- ✅ **Each category has its own conftest.py** - For category-specific fixtures
- ✅ **Always use markers** - For test categorization and filtering
- ✅ **Follow naming conventions** - For consistency and discoverability
- ✅ **Keep tests focused** - One concern per test
- ✅ **Use fixtures** - For setup and teardown
- ✅ **Document tests** - With clear docstrings
- ✅ **Organize by category** - Unit, Integration, Performance, E2E
