#!/usr/bin/env node

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { Client } from '@microsoft/microsoft-graph-client';
import { DeviceCodeCredential } from '@azure/identity';
import { z } from 'zod';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import path from 'path';
import fs from 'fs';
import fetch from 'node-fetch';

// Load environment variables
dotenv.config();

// Get the current file's directory
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Path for storing the access token
const tokenFilePath = path.join(__dirname, '.access-token.txt');

// Create the MCP server
const server = new McpServer({
  name: "onenote-mcp",
  version: "1.0.0"
});

// Try to read the stored access token
let accessToken = null;
try {
  if (fs.existsSync(tokenFilePath)) {
    const tokenData = fs.readFileSync(tokenFilePath, 'utf8');
    try {
      const parsedToken = JSON.parse(tokenData);
      accessToken = parsedToken.token;
    } catch (parseError) {
      accessToken = tokenData.trim();
    }
  }
} catch (error) {
  console.error('Error reading access token file:', error.message);
}

// Alternatively, check if token is in environment variables
if (!accessToken && process.env.GRAPH_ACCESS_TOKEN) {
  accessToken = process.env.GRAPH_ACCESS_TOKEN;
}

let graphClient = null;

// Client ID for Microsoft Graph API access
const clientId = '14d82eec-204b-4c2f-b7e8-296a70dab67e';
const scopes = ['Notes.Read.All', 'Notes.ReadWrite.All', 'User.Read'];

// Function to ensure Graph client is created
async function ensureGraphClient() {
  if (!graphClient) {
    if (!accessToken) {
      throw new Error("Access token not found. Please authenticate first using the 'onenote_authenticate' tool.");
    }

    graphClient = Client.initWithMiddleware({
      authProvider: {
        getAccessToken: async () => {
          return accessToken;
        }
      }
    });
  }
  return graphClient;
}

// Create graph client with device code auth or access token
async function createGraphClient() {
  if (accessToken) {
    graphClient = Client.initWithMiddleware({
      authProvider: {
        getAccessToken: async () => {
          return accessToken;
        }
      }
    });
    return { type: 'token', client: graphClient };
  } else {
    const credential = new DeviceCodeCredential({
      clientId: clientId,
      userPromptCallback: (info) => {
        console.error('\n' + info.message);
      }
    });

    try {
      const tokenResponse = await credential.getToken(scopes);
      accessToken = tokenResponse.token;
      fs.writeFileSync(tokenFilePath, JSON.stringify({ token: accessToken }), 'utf8');

      graphClient = Client.initWithMiddleware({
        authProvider: {
          getAccessToken: async () => {
            return accessToken;
          }
        }
      });

      return { type: 'device_code', client: graphClient };
    } catch (error) {
      console.error('Authentication error:', error);
      throw new Error(`Authentication failed: ${error.message}`);
    }
  }
}

// Register tools using modern API with Zod schemas
server.registerTool(
  "onenote_authenticate",
  {
    title: "Authenticate with OneNote",
    description: "Start the authentication flow with Microsoft Graph using device code flow",
    inputSchema: z.object({})
  },
  async () => {
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
      throw new Error(`Authentication failed: ${error.message}`);
    }
  }
);

server.registerTool(
  "onenote_save_token",
  {
    title: "Save Access Token",
    description: "Save a Microsoft Graph access token for later use",
    inputSchema: z.object({
      token: z.string().describe("The access token to save")
    })
  },
  async (params) => {
    try {
      accessToken = params.token;
      const tokenData = JSON.stringify({ token: accessToken });
      fs.writeFileSync(tokenFilePath, tokenData, 'utf8');
      await createGraphClient();
      return {
        content: [{
          type: "text",
          text: "Access token saved successfully"
        }]
      };
    } catch (error) {
      console.error("Error saving access token:", error);
      throw new Error(`Failed to save access token: ${error.message}`);
    }
  }
);

server.registerTool(
  "onenote_list_notebooks",
  {
    title: "List Notebooks",
    description: "List all OneNote notebooks",
    inputSchema: z.object({})
  },
  async () => {
    try {
      await ensureGraphClient();
      const response = await graphClient.api("/me/onenote/notebooks").get();
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.value, null, 2)
        }]
      };
    } catch (error) {
      console.error("Error listing notebooks:", error);
      throw new Error(`Failed to list notebooks: ${error.message}`);
    }
  }
);

server.registerTool(
  "onenote_get_notebook",
  {
    title: "Get Notebook",
    description: "Get details of a specific notebook by name or index",
    inputSchema: z.object({
      notebook_name: z.string().optional().describe("Name of the notebook (partial match supported)")
    })
  },
  async (params) => {
    try {
      await ensureGraphClient();
      const response = await graphClient.api(`/me/onenote/notebooks`).get();

      if (params.notebook_name) {
        const searchName = params.notebook_name.toLowerCase();
        const notebook = response.value.find(n =>
          n.displayName.toLowerCase().includes(searchName)
        );
        if (!notebook) {
          const available = response.value.map(n => n.displayName).join(', ');
          throw new Error(`Notebook "${params.notebook_name}" not found. Available: ${available}`);
        }
        return {
          content: [{
            type: "text",
            text: JSON.stringify(notebook, null, 2)
          }]
        };
      } else {
        return {
          content: [{
            type: "text",
            text: JSON.stringify(response.value[0] || null, null, 2)
          }]
        };
      }
    } catch (error) {
      console.error("Error getting notebook:", error);
      throw new Error(`Failed to get notebook: ${error.message}`);
    }
  }
);

server.registerTool(
  "onenote_list_sections",
  {
    title: "List Sections",
    description: "List all sections in notebooks or a specific notebook",
    inputSchema: z.object({
      notebook_name: z.string().optional().describe("Name of the notebook (optional)")
    })
  },
  async (params) => {
    try {
      await ensureGraphClient();
      let url = '/me/onenote/sections';

      if (params.notebook_name) {
        const notebooksResponse = await graphClient.api('/me/onenote/notebooks').get();
        const notebook = notebooksResponse.value.find(n =>
          n.displayName.toLowerCase().includes(params.notebook_name.toLowerCase())
        );
        if (!notebook) {
          throw new Error(`Notebook "${params.notebook_name}" not found`);
        }
        url = `/me/onenote/notebooks/${notebook.id}/sections`;
      }

      const response = await graphClient.api(url).get();
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.value, null, 2)
        }]
      };
    } catch (error) {
      console.error("Error listing sections:", error);
      throw new Error(`Failed to list sections: ${error.message}`);
    }
  }
);

server.registerTool(
  "onenote_list_pages",
  {
    title: "List Pages",
    description: "List all pages in a section",
    inputSchema: z.object({
      section_name: z.string().optional().describe("Name of the section (optional, uses first section if not provided)")
    })
  },
  async (params) => {
    try {
      await ensureGraphClient();
      const sectionsResponse = await graphClient.api(`/me/onenote/sections`).get();

      if (sectionsResponse.value.length === 0) {
        return {
          content: [{
            type: "text",
            text: "[]"
          }]
        };
      }

      let sectionId;
      if (params.section_name) {
        const section = sectionsResponse.value.find(s =>
          s.displayName.toLowerCase().includes(params.section_name.toLowerCase())
        );
        if (!section) {
          throw new Error(`Section "${params.section_name}" not found`);
        }
        sectionId = section.id;
      } else {
        sectionId = sectionsResponse.value[0].id;
      }

      const response = await graphClient.api(`/me/onenote/sections/${sectionId}/pages`).get();
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response.value, null, 2)
        }]
      };
    } catch (error) {
      console.error("Error listing pages:", error);
      throw new Error(`Failed to list pages: ${error.message}`);
    }
  }
);

server.registerTool(
  "onenote_get_page",
  {
    title: "Get Page Content",
    description: "Get the complete content of a page, including HTML formatting",
    inputSchema: z.object({
      page_id: z.string().optional().describe("Page ID or title (searches by title if not found by ID)")
    })
  },
  async (params) => {
    try {
      await ensureGraphClient();
      const pagesResponse = await graphClient.api('/me/onenote/pages').get();

      let targetPage;
      if (params.page_id) {
        targetPage = pagesResponse.value.find(p => p.id === params.page_id);
        if (!targetPage) {
          targetPage = pagesResponse.value.find(p =>
            p.title && p.title.toLowerCase().includes(params.page_id.toLowerCase())
          );
        }
        if (!targetPage) {
          throw new Error(`Page with ID or title "${params.page_id}" not found`);
        }
      } else {
        if (pagesResponse.value.length === 0) {
          throw new Error("No pages found");
        }
        targetPage = pagesResponse.value[0];
      }

      const url = `https://graph.microsoft.com/v1.0/me/onenote/pages/${targetPage.id}/content`;
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status} ${response.statusText}`);
      }

      const content = await response.text();
      return {
        content: [{
          type: "text",
          text: content
        }]
      };
    } catch (error) {
      console.error("Error getting page:", error);
      throw new Error(`Failed to get page: ${error.message}`);
    }
  }
);

server.registerTool(
  "onenote_create_page",
  {
    title: "Create Page",
    description: "Create a new page in a section with HTML content",
    inputSchema: z.object({
      section_name: z.string().optional().describe("Name of the section (optional, uses first section if not provided)"),
      title: z.string().describe("Title of the page"),
      content: z.string().describe("HTML content for the page body")
    })
  },
  async (params) => {
    try {
      await ensureGraphClient();
      const sectionsResponse = await graphClient.api(`/me/onenote/sections`).get();

      if (sectionsResponse.value.length === 0) {
        throw new Error("No sections found");
      }

      let sectionId;
      if (params.section_name) {
        const section = sectionsResponse.value.find(s =>
          s.displayName.toLowerCase().includes(params.section_name.toLowerCase())
        );
        if (!section) {
          throw new Error(`Section "${params.section_name}" not found`);
        }
        sectionId = section.id;
      } else {
        sectionId = sectionsResponse.value[0].id;
      }

      const html = `<!DOCTYPE html>
<html>
  <head>
    <title>${params.title}</title>
  </head>
  <body>
    ${params.content}
  </body>
</html>`;

      const response = await graphClient
        .api(`/me/onenote/sections/${sectionId}/pages`)
        .header("Content-Type", "application/xhtml+xml")
        .post(html);

      return {
        content: [{
          type: "text",
          text: JSON.stringify(response, null, 2)
        }]
      };
    } catch (error) {
      console.error("Error creating page:", error);
      throw new Error(`Failed to create page: ${error.message}`);
    }
  }
);

server.registerTool(
  "onenote_search_pages",
  {
    title: "Search Pages",
    description: "Search for pages across all notebooks by title",
    inputSchema: z.object({
      query: z.string().describe("Search query to match against page titles")
    })
  },
  async (params) => {
    try {
      await ensureGraphClient();
      const response = await graphClient.api(`/me/onenote/pages`).get();

      const searchTerm = params.query.toLowerCase();
      const filteredPages = response.value.filter(page => {
        return page.title && page.title.toLowerCase().includes(searchTerm);
      });

      return {
        content: [{
          type: "text",
          text: JSON.stringify(filteredPages, null, 2)
        }]
      };
    } catch (error) {
      console.error("Error searching pages:", error);
      throw new Error(`Failed to search pages: ${error.message}`);
    }
  }
);

server.registerTool(
  "onenote_get_notebook_toc",
  {
    title: "Get Notebook Table of Contents",
    description: "Generate a Table of Contents for a notebook showing all sections and pages",
    inputSchema: z.object({
      notebook_name: z.string().optional().describe("Name of the notebook (optional, uses first notebook if not provided)")
    })
  },
  async (params) => {
    try {
      await ensureGraphClient();
      const notebooksResponse = await graphClient.api('/me/onenote/notebooks').get();
      const notebooks = notebooksResponse.value;

      if (notebooks.length === 0) {
        return {
          content: [{ type: "text", text: "No notebooks found." }]
        };
      }

      let notebook;
      if (params.notebook_name) {
        const searchName = params.notebook_name.toLowerCase();
        notebook = notebooks.find(n =>
          n.displayName.toLowerCase().includes(searchName)
        );
        if (!notebook) {
          const available = notebooks.map(n => n.displayName).join(', ');
          throw new Error(`Notebook "${params.notebook_name}" not found. Available: ${available}`);
        }
      } else {
        notebook = notebooks[0];
      }

      const sectionsResponse = await graphClient.api(`/me/onenote/notebooks/${notebook.id}/sections`).get();
      const sections = sectionsResponse.value;

      let totalPages = 0;
      const tocSections = [];

      for (const section of sections) {
        const pagesResponse = await graphClient.api(`/me/onenote/sections/${section.id}/pages`).get();
        const pages = pagesResponse.value;
        totalPages += pages.length;

        tocSections.push({
          name: section.displayName,
          pageCount: pages.length,
          pages: pages.map(p => ({
            title: p.title,
            id: p.id,
            created: p.createdDateTime,
            modified: p.lastModifiedDateTime
          }))
        });
      }

      const lines = [];
      lines.push(`# ${notebook.displayName}`);
      lines.push('');
      lines.push(`> ${sections.length} sections, ${totalPages} pages`);
      lines.push('');
      lines.push('---');
      lines.push('');

      for (const section of tocSections) {
        lines.push(`## ${section.name} (${section.pageCount} pages)`);
        lines.push('');
        if (section.pages.length === 0) {
          lines.push('*(empty section)*');
        } else {
          for (const page of section.pages) {
            const modified = new Date(page.modified).toLocaleDateString();
            lines.push(`- **${page.title}** *(${modified})*`);
          }
        }
        lines.push('');
      }

      const tocData = {
        notebook: notebook.displayName,
        stats: { sections: sections.length, pages: totalPages },
        sections: tocSections
      };

      return {
        content: [
          { type: "text", text: lines.join('\n') },
          { type: "text", text: "\n---\nJSON Data:\n" + JSON.stringify(tocData, null, 2) }
        ]
      };
    } catch (error) {
      console.error("Error generating TOC:", error);
      throw new Error(`Failed to generate TOC: ${error.message}`);
    }
  }
);

// Connect to stdio and start server
async function main() {
  try {
    const transport = new StdioServerTransport();
    await server.connect(transport);

    console.error('OneNote MCP Server started successfully.');
    console.error('Use the "onenote_authenticate" tool to start authentication,');
    console.error('or use "onenote_save_token" if you already have a token.');

    process.on('SIGINT', () => {
      process.exit(0);
    });

    process.on('uncaughtException', (error) => {
      console.error('Uncaught exception:', error);
      process.exit(1);
    });

    process.on('unhandledRejection', (reason, promise) => {
      console.error('Unhandled rejection at:', promise, 'reason:', reason);
      process.exit(1);
    });
  } catch (error) {
    console.error('Fatal error starting server:', error);
    console.error('Stack:', error.stack);
    process.exit(1);
  }
}

main();

main();
main();
main();
main();
main();
main();
main();
main();
main();
main();
main();
main();
main();
