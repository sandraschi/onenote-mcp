"""Constants for OneNote MCP Server."""

# Microsoft Graph API configuration
CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"  # Microsoft Graph Explorer client ID
SCOPES = ["Notes.Read.All", "Notes.ReadWrite.All", "User.Read"]

# Response limits
CHARACTER_LIMIT = 25000

# Token file name
TOKEN_FILE_NAME = ".access-token.txt"
