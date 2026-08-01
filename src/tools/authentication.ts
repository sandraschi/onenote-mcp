/**
 * Authentication tools for OneNote MCP Server
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { createGraphClient, saveAccessToken, ensureGraphClient } from '../services/graph-client.js';
import { AuthenticateInputSchema, SaveTokenInputSchema } from '../schemas/index.js';
import type { AuthenticateInput, SaveTokenInput } from '../schemas/index.js';
import { formatErrorResponse } from '../services/error-handler.js';

/**
 * Register authentication tools
 */
export function registerAuthenticationTools(server: McpServer): void {
  server.registerTool(
    "onenote_authenticate",
    {
      title: "Authenticate with OneNote",
      description: `Start the authentication flow with Microsoft Graph using device code flow.

This tool initiates the Microsoft Graph authentication process. If you already have an access token, use 'onenote_save_token' instead.

The authentication process:
1. A URL and code will be displayed in the console (stderr)
2. Visit the URL in your browser
3. Enter the code when prompted
4. Sign in with your Microsoft account
5. Grant permissions for OneNote access
6. The access token will be automatically saved for future use

Returns:
  - Success message indicating authentication started or already authenticated

Examples:
  - Use when: "Authenticate with my OneNote account"
  - Use when: "Connect to Microsoft OneNote"
  - Don't use when: You already have a valid access token (use 'onenote_save_token' instead)

Error Handling:
  - Returns error if authentication fails
  - Check console (stderr) for device code and URL`,
      inputSchema: AuthenticateInputSchema,
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: false,
        openWorldHint: false
      }
    },
    async (params: AuthenticateInput) => {
      try {
        const result = await createGraphClient();
        if (result.type === 'device_code') {
          return {
            content: [{
              type: "text",
              text: "Authentication started. Please check the console (stderr) for the URL and code to enter."
            }]
          };
        } else {
          return {
            content: [{
              type: "text",
              text: "Already authenticated with an access token."
            }]
          };
        }
      } catch (error) {
        console.error("Error in authentication:", error);
        throw new Error(`Authentication failed: ${error instanceof Error ? error.message : String(error)}`);
      }
    }
  );

  server.registerTool(
    "onenote_save_token",
    {
      title: "Save Access Token",
      description: `Save a Microsoft Graph access token for later use.

This tool allows you to manually provide an access token if you already have one from another source. The token will be saved to a local file for future use.

Args:
  - token (string, required): The Microsoft Graph access token to save

Returns:
  - Success message confirming the token was saved

Examples:
  - Use when: "Save this access token: eyJ0eXAi..."
  - Use when: You have a token from Azure Portal or another source
  - Don't use when: You need to authenticate (use 'onenote_authenticate' instead)

Error Handling:
  - Returns error if token is invalid or save fails`,
      inputSchema: SaveTokenInputSchema,
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: false
      }
    },
    async (params: SaveTokenInput) => {
      try {
        saveAccessToken(params.token);
        await ensureGraphClient();
        return {
          content: [{
            type: "text",
            text: "Access token saved successfully"
          }]
        };
      } catch (error) {
        console.error("Error saving access token:", error);
        return formatErrorResponse(error);
      }
    }
  );
}
