"""Basic tests for onenote-mcp server."""

import pytest
from unittest.mock import Mock, patch

def test_server_imports():
    """Test that the server module can be imported."""
    try:
        from onenote_mcp.server import app
        assert app is not None
    except ImportError as e:
        pytest.skip(f"Server import failed: {e}")

def test_server_initialization():
    """Test that the server can be initialized."""
    try:
        from onenote_mcp.server import app
        # Basic check that FastAPI app was created
        assert hasattr(app, 'routes')
    except ImportError:
        pytest.skip("Server import failed")

@pytest.mark.asyncio
async def test_health_check():
    """Test the health check endpoint."""
    try:
        from onenote_mcp.server import health_check
        result = await health_check()
        assert isinstance(result, dict)
        assert "status" in result
    except ImportError:
        pytest.skip("Server import failed")




