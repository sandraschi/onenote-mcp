/**
 * Section management tools for OneNote MCP Server
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { ensureGraphClient } from '../services/graph-client.js';
import { ListSectionsInputSchema } from '../schemas/index.js';
import type { ListSectionsInput } from '../schemas/index.js';
import { formatErrorResponse } from '../services/error-handler.js';
import { CHARACTER_LIMIT } from '../constants.js';
import type { Section, Notebook } from '../types.js';

/**
 * Register section tools
 */
export function registerSectionTools(server: McpServer): void {
  server.registerTool(
    "onenote_list_sections",
    {
      title: "List Sections",
      description: `List all sections in notebooks or sections within a specific notebook.

This tool retrieves all sections from your OneNote account. You can optionally filter by notebook name.

Args:
  - notebook_name (string, optional): Name of the notebook to list sections from

Returns:
  JSON array of section objects with:
  - id: Unique section identifier
  - displayName: Section name
  - pagesUrl: URL to list pages in this section
  - self: API endpoint for this section
  - parentNotebook: Parent notebook information (if filtered by notebook)

Examples:
  - Use when: "List all sections in my notebooks"
  - Use when: "Show me sections in my Work notebook"
  - Use when: "What sections are in the Projects notebook?"

Error Handling:
  - Returns error if notebook not found
  - Returns error if not authenticated`,
      inputSchema: ListSectionsInputSchema,
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: true
      }
    },
    async (params: ListSectionsInput) => {
      try {
        const client = await ensureGraphClient();
        let url = '/me/onenote/sections';
        
        if (params.notebook_name) {
          const notebooksResponse = await client.api('/me/onenote/notebooks').get() as { value: Notebook[] };
          const notebook = notebooksResponse.value.find(n => 
            n.displayName.toLowerCase().includes(params.notebook_name!.toLowerCase())
          );
          if (!notebook) {
            throw new Error(`Notebook "${params.notebook_name}" not found`);
          }
          url = `/me/onenote/notebooks/${notebook.id}/sections`;
        }
        
        const response = await client.api(url).get() as { value: Section[] };
        
        let result = JSON.stringify(response.value, null, 2);
        
        // Check character limit
        if (result.length > CHARACTER_LIMIT) {
          const truncated = response.value.slice(0, Math.max(1, Math.floor(response.value.length / 2)));
          result = JSON.stringify({
            sections: truncated,
            truncated: true,
            total: response.value.length,
            shown: truncated.length,
            message: `Response truncated from ${response.value.length} to ${truncated.length} sections. Use notebook filter to narrow results.`
          }, null, 2);
        }
        
        return {
          content: [{
            type: "text",
            text: result
          }]
        };
      } catch (error) {
        console.error("Error listing sections:", error);
        return formatErrorResponse(error);
      }
    }
  );
}



























