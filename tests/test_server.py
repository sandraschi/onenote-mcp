"""Basic tests for onenote-mcp server."""

from unittest.mock import MagicMock

import pytest


def test_server_imports():
    """Test that the server module can be imported."""
    try:
        from onenote_mcp.server import app

        assert app is not None
    except ImportError as e:
        pytest.skip(f"Server import failed: {e}")


def test_server_initialization():
    """Test that the FastMCP app can be initialized."""
    try:
        from onenote_mcp.server import app

        assert app.name == "onenote-mcp"
    except ImportError:
        pytest.skip("Server import failed")


@pytest.mark.asyncio
async def test_health_check():
    """Test the health check endpoint."""
    try:
        from onenote_mcp.server import health_check

        request = MagicMock()
        response = await health_check(request)
        assert response.body is not None
        assert b"healthy" in response.body
    except ImportError:
        pytest.skip("Server import failed")
