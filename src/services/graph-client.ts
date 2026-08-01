/**
 * Microsoft Graph API client service
 */

import { Client } from '@microsoft/microsoft-graph-client';
import { DeviceCodeCredential } from '@azure/identity';
import { fileURLToPath } from 'url';
import path from 'path';
import fs from 'fs';
import { CLIENT_ID, SCOPES, TOKEN_FILE_NAME } from '../constants.js';
import type { GraphClientResult } from '../types.js';

// Get the current file's directory
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '../..');
const tokenFilePath = path.join(projectRoot, TOKEN_FILE_NAME);

// Token management
let accessToken: string | null = null;
let graphClient: Client | null = null;

/**
 * Load access token from file or environment variable
 */
function loadAccessToken(): string | null {
  if (accessToken) {
    return accessToken;
  }

  // Try to read from file
  try {
    if (fs.existsSync(tokenFilePath)) {
      const tokenData = fs.readFileSync(tokenFilePath, 'utf8');
      try {
        const parsedToken = JSON.parse(tokenData);
        accessToken = parsedToken.token;
        return accessToken;
      } catch (parseError) {
        // Fall back to raw token (old format)
        accessToken = tokenData.trim();
        return accessToken;
      }
    }
  } catch (error) {
    console.error('Error reading access token file:', error instanceof Error ? error.message : String(error));
  }

  // Check environment variable
  if (process.env.GRAPH_ACCESS_TOKEN) {
    accessToken = process.env.GRAPH_ACCESS_TOKEN;
    return accessToken;
  }

  return null;
}

/**
 * Save access token to file
 */
export function saveAccessToken(token: string): void {
  accessToken = token;
  const tokenData = JSON.stringify({ token: accessToken });
  try {
    fs.writeFileSync(tokenFilePath, tokenData, 'utf8');
  } catch (error) {
    console.error('Error saving access token:', error instanceof Error ? error.message : String(error));
    throw new Error(`Failed to save access token: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Get current access token
 */
export function getAccessToken(): string | null {
  return loadAccessToken();
}

/**
 * Ensure Graph client is created and authenticated
 */
export async function ensureGraphClient(): Promise<Client> {
  if (graphClient) {
    return graphClient;
  }

  const token = loadAccessToken();
  if (!token) {
    throw new Error("Access token not found. Please authenticate first using the 'onenote_authenticate' tool.");
  }

  graphClient = Client.initWithMiddleware({
    authProvider: {
      getAccessToken: async () => {
        return token;
      }
    }
  });

  return graphClient;
}

/**
 * Create Graph client with device code auth or access token
 */
export async function createGraphClient(): Promise<GraphClientResult> {
  const token = loadAccessToken();

  if (token) {
    // Use existing token
    graphClient = Client.initWithMiddleware({
      authProvider: {
        getAccessToken: async () => {
          return token;
        }
      }
    });
    return { type: 'token', client: graphClient };
  } else {
    // Use device code flow
    const credential = new DeviceCodeCredential({
      clientId: CLIENT_ID,
      userPromptCallback: (info) => {
        console.error('\n' + info.message);
      }
    });

    try {
      const tokenResponse = await credential.getToken(SCOPES);
      accessToken = tokenResponse.token;
      saveAccessToken(accessToken);

      graphClient = Client.initWithMiddleware({
        authProvider: {
          getAccessToken: async () => {
            return accessToken!;
          }
        }
      });

      return { type: 'device_code', client: graphClient };
    } catch (error) {
      console.error('Authentication error:', error);
      throw new Error(`Authentication failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
}

/**
 * Reset the Graph client (useful for testing or re-authentication)
 */
export function resetGraphClient(): void {
  graphClient = null;
  accessToken = null;
}
