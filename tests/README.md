# OneNote MCP Tests

This directory contains the test suite for the OneNote MCP server.

## Test Structure

- `test_server.py` - Basic tests for server functionality
- `conftest.py` - Pytest configuration and fixtures
- `run_tests.py` - Test runner script

## Running Tests

### Using pytest directly:
```bash
pytest tests/
```

### Using the test runner:
```bash
python tests/run_tests.py
```

### Skip Microsoft Graph tests:
```bash
pytest -m "not microsoft_graph" tests/
```

## Test Categories

- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test Microsoft Graph API interactions
- **Microsoft Graph tests**: Tests that require Microsoft Graph API access (marked with `@pytest.mark.microsoft_graph`)

## Test Fixtures

- `mock_microsoft_graph`: Mock Microsoft Graph API for testing
- `sample_notebook_data`: Sample OneNote notebook data
- `sample_section_data`: Sample OneNote section data
- `sample_page_data`: Sample OneNote page data

## Environment Variables for Testing

Set these environment variables for integration tests:
- `AZURE_CLIENT_ID`: Azure app client ID
- `AZURE_CLIENT_SECRET`: Azure app client secret
- `AZURE_TENANT_ID`: Azure tenant ID

## Authentication Setup for Testing

For Microsoft Graph integration tests, you need to:

1. Register an Azure app with Microsoft Graph permissions
2. Set up the environment variables above
3. Create a test user account in Azure AD

## Adding New Tests

1. Create test files with the pattern `test_*.py`
2. Use descriptive test function names starting with `test_`
3. Mark Microsoft Graph-dependent tests with `@pytest.mark.microsoft_graph`
4. Use fixtures from `conftest.py` for common test setup




