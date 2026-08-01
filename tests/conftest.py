"""Pytest configuration for onenote-mcp tests."""

import sys
from pathlib import Path

import pytest

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


# Test fixtures for OneNote testing
@pytest.fixture
def mock_microsoft_graph():
    """Mock Microsoft Graph API for testing."""
    # This would mock the Microsoft Graph API responses
    return None


@pytest.fixture
def sample_notebook_data():
    """Sample OneNote notebook data for testing."""
    return {"id": "notebook-123", "displayName": "Test Notebook", "createdDateTime": "2023-01-01T00:00:00Z"}


@pytest.fixture
def sample_section_data():
    """Sample OneNote section data for testing."""
    return {
        "id": "section-123",
        "displayName": "Test Section",
        "pagesUrl": "https://graph.microsoft.com/v1.0/me/onenote/sections/section-123/pages",
    }


@pytest.fixture
def sample_page_data():
    """Sample OneNote page data for testing."""
    return {"id": "page-123", "title": "Test Page", "content": "<html><body>Test content</body></html>"}
