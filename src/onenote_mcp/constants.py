"""Constants for OneNote MCP Server."""

import logging
from pathlib import Path

logger = logging.getLogger("onenote_mcp.constants")

try:  # python-dotenv is transitive; never crash if a minimal env lacks it
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
except Exception as exc:
    logger.debug("dotenv load skipped: %s", exc)

# Microsoft Graph API configuration.
# The client ID / authority are NOT constants: every user registers their own Entra app and the
# app stores it (see app_config.py). The borrowed Graph Explorer ID is gone: its opaque tokens
# are rejected by the OneNote workload (40001).
# Fully-qualified base scopes (purpleslurple recipe): the OneNote workload
# honors these for personal accounts where bare `.All` scopes yield rejected
# tokens. NOTE: no `offline_access`/`openid`/`profile` here - MSAL injects
# those itself and RAISES if you pass them to initiate_auth_code_flow.
# Device-flow callers append offline_access explicitly (it tolerates it).
SCOPES = [
    "https://graph.microsoft.com/Notes.Read",
    "https://graph.microsoft.com/Notes.ReadWrite",
    "https://graph.microsoft.com/User.Read",
]

# Response limits
CHARACTER_LIMIT = 25000

# Token file name
TOKEN_FILE_NAME = ".access-token.txt"
