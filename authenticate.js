import { DeviceCodeCredential } from '@azure/identity';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get current directory
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Path for storing the access token
const tokenFilePath = path.join(__dirname, '.access-token.txt');

// Client ID for Microsoft Graph API access
const clientId = '14d82eec-204b-4c2f-b7e8-296a70dab67e'; // Microsoft Graph Explorer client ID
const scopes = ['Notes.Read.All', 'Notes.ReadWrite.All', 'User.Read'];

async function authenticate() {
  try {
    // Use device code flow
    const credential = new DeviceCodeCredential({
      clientId: clientId,
      userPromptCallback: (info) => {
        // This will show the URL and code to the user
        console.log('\n' + info.message);
      }
    });

    // Get an access token using device code flow
    console.log('Starting authentication...');
    console.log('You will see a URL and code to enter shortly...');
    
    const tokenResponse = await credential.getToken(scopes);
    
    // Save the token for future use
    const accessToken = tokenResponse.token;
    fs.writeFileSync(tokenFilePath, JSON.stringify({ token: accessToken }));
    
    console.log('\nAuthentication successful!');
    console.log('Access token saved to:', tokenFilePath);
    
  } catch (error) {
    console.error('Authentication error:', error);
  }
}

// Run the authentication
authenticate(); 