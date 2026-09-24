"""Constants for OneNote MCP Server."""

import logging
import os
from pathlib import Path

logger = logging.getLogger("onenote_mcp.constants")

try:  # python-dotenv is transitive; never crash if a minimal env lacks it
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
except Exception as exc:
    logger.debug("dotenv load skipped: %s", exc)

# Microsoft Graph API configuration.
# Default is the public Graph Explorer client (works for /me-style calls but
# the OneNote workload rejects its opaque tokens with 40001). For real
# OneNote access register your own app (see docs/ONBOARDING.md) and set
# ONENOTE_CLIENT_ID in the environment or repo-root .env.
CLIENT_ID = os.environ.get("ONENOTE_CLIENT_ID", "14d82eec-204b-4c2f-b7e8-296a70dab67e")
SCOPES = ["Notes.Read.All", "Notes.ReadWrite.All", "User.Read"]

# Response limits
CHARACTER_LIMIT = 25000

# Token file name
TOKEN_FILE_NAME = ".access-token.txt"
