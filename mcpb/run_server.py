"""PyInstaller entrypoint for onenote-mcp HTTP sidecar."""

from __future__ import annotations

import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    base = Path(sys._MEIPASS)
else:
    base = Path(__file__).resolve().parent
if str(base / "src") not in sys.path:
    sys.path.insert(0, str(base / "src"))

os.environ.setdefault("MCP_TRANSPORT", "http")

if __name__ == "__main__":
    import uvicorn

    # Fleet standard (CORS_STANDARD.md): serve the CORS-wrapped mcp.http_app()
    # directly. The FastMCP app carries the custom routes at root (/health,
    # /api/*) and the streamable HTTP transport at /mcp - no FastAPI shell
    # wrapper needed (a shell mounting http_app under /mcp would drop the REST
    # surface and break the webapp).
    from onenote_mcp.server import http_app

    host = os.environ.get("ONENOTE_HOST", "127.0.0.1")
    port = int(os.environ.get("ONENOTE_PORT", os.environ.get("MCP_PORT", "10907")))
    log_level = os.environ.get("ONENOTE_LOG_LEVEL", "info")
    uvicorn.run(http_app, host=host, port=port, log_level=log_level)
