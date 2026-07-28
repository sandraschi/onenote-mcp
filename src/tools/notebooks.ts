/**
 * Notebook management tools for OneNote MCP Server
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { ensureGraphClient, getAccessToken } from '../services/graph-client.js';
import { ListNotebooksInputSchema, GetNotebookInputSchema, GetNotebookTOCInputSchema } from '../schemas/index.js';
import type { ListNotebooksInput, GetNotebookInput, GetNotebookTOCInput } from '../schemas/index.js';
import { formatErrorResponse } from '../services/error-handler.js';
import { CHARACTER_LIMIT } from '../constants.js';
import type { Notebook, TOCData, TOCSection } from '../types.js';

/**
 * Register notebook tools
 */
export function registerNotebookTools(server: McpServer): void {
  server.registerTool(
    "onenote_list_notebooks",
    {
      title: "List Notebooks",
      description: `List all OneNote notebooks accessible to the authenticated user.

This tool retrieves all notebooks from your OneNote account, including their IDs, names, and metadata.

Returns:
  JSON array of notebook objects with:
  - id: Unique notebook identifier
  - displayName: Notebook name
  - self: API endpoint for this notebook
  - sectionsUrl: URL to list sections in this notebook
  - sectionGroupsUrl: URL to list section groups

Examples:
  - Use when: "Show me all my OneNote notebooks"
  - Use when: "What notebooks do I have?"
  - Use when: "List my notebooks"

Error Handling:
  - Returns error if not authenticated
  - Returns error if API request fails`,
      inputSchema: ListNotebooksInputSchema,
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: true
      }
    },
    async (params: ListNotebooksInput) => {
      try {
        const client = await ensureGraphClient();
        const response = await client.api("/me/onenote/notebooks").get() as { value: Notebook[] };
        
        let result = JSON.stringify(response.value, null, 2);
        
        // Check character limit
        if (result.length > CHARACTER_LIMIT) {
          const truncated = response.value.slice(0, Math.max(1, Math.floor(response.value.length / 2)));
          result = JSON.stringify({
            notebooks: truncated,
            truncated: true,
            total: response.value.length,
            shown: truncated.length,
            message: `Response truncated from ${response.value.length} to ${truncated.length} notebooks. Use filters or pagination to see more.`
          }, null, 2);
        }
        
        return {
          content: [{
            type: "text",
            text: result
          }]
        };
      } catch (error) {
        console.error("Error listing notebooks:", error);
        return formatErrorResponse(error);
      }
    }
  );

  server.registerTool(
    "onenote_get_notebook",
    {
      title: "Get Notebook",
      description: `Get details of a specific notebook by name or return the first notebook.

This tool retrieves detailed information about a specific notebook. If no name is provided, returns the first notebook.

Args:
  - notebook_name (string, optional): Name of the notebook (partial match supported)

Returns:
  JSON object with notebook details:
  - id: Unique notebook identifier
  - displayName: Notebook name
  - self: API endpoint
  - sectionsUrl: URL to list sections
  - sectionGroupsUrl: URL to list section groups
  - links: Links to open notebook in OneNote clients

Examples:
  - Use when: "Get details of my Work notebook"
  - Use when: "Show me information about the Projects notebook"
  - Use when: "Get the first notebook"

Error Handling:
  - Returns error if notebook not found
  - Returns error if not authenticated`,
      inputSchema: GetNotebookInputSchema,
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: true
      }
    },
    async (params: GetNotebookInput) => {
      try {
        const client = await ensureGraphClient();
        const response = await client.api(`/me/onenote/notebooks`).get() as { value: Notebook[] };
        
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
        return formatErrorResponse(error);
      }
    }
  );

  server.registerTool(
    "onenote_get_notebook_toc",
    {
      title: "Get Notebook Table of Contents",
      description: `Generate a Table of Contents for a notebook showing all sections and pages.

This tool creates a comprehensive overview of a notebook's structure, including all sections and their pages. The output includes both a human-readable markdown format and structured JSON data.

Args:
  - notebook_name (string, optional): Name of the notebook (optional, uses first notebook if not provided)

Returns:
  Two-part response:
  1. Markdown-formatted table of contents with:
     - Notebook name and statistics
     - Sections with page counts
     - Page titles with modification dates
  2. JSON data with complete structure:
     - notebook: Notebook name
     - stats: Section and page counts
     - sections: Array of sections with pages

Examples:
  - Use when: "Show me the table of contents for my Work notebook"
  - Use when: "Generate a TOC for the Projects notebook"
  - Use when: "List all sections and pages in my first notebook"

Error Handling:
  - Returns error if notebook not found
  - Returns error if not authenticated`,
      inputSchema: GetNotebookTOCInputSchema,
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: true
      }
    },
    async (params: GetNotebookTOCInput) => {
      try {
        const client = await ensureGraphClient();
        const notebooksResponse = await client.api('/me/onenote/notebooks').get() as { value: Notebook[] };
        const notebooks = notebooksResponse.value;
        
        if (notebooks.length === 0) {
          return {
            content: [{ type: "text", text: "No notebooks found." }]
          };
        }
        
        let notebook: Notebook;
        if (params.notebook_name) {
          const searchName = params.notebook_name.toLowerCase();
          notebook = notebooks.find(n => 
            n.displayName.toLowerCase().includes(searchName)
          )!;
          if (!notebook) {
            const available = notebooks.map(n => n.displayName).join(', ');
            throw new Error(`Notebook "${params.notebook_name}" not found. Available: ${available}`);
          }
        } else {
          notebook = notebooks[0];
        }
        
        const sectionsResponse = await client.api(`/me/onenote/notebooks/${notebook.id}/sections`).get() as { value: Array<{ id: string; displayName: string }> };
        const sections = sectionsResponse.value;
        
        let totalPages = 0;
        const tocSections: TOCSection[] = [];
        
        for (const section of sections) {
          const pagesResponse = await client.api(`/me/onenote/sections/${section.id}/pages`).get() as { value: Array<{ id: string; title: string; createdDateTime: string; lastModifiedDateTime: string }> };
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
        
        // Format as markdown
        const lines: string[] = [];
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
        
        const tocData: TOCData = {
          notebook: notebook.displayName,
          stats: { sections: sections.length, pages: totalPages },
          sections: tocSections
        };
        
        let markdownResult = lines.join('\n');
        let jsonResult = JSON.stringify(tocData, null, 2);
        
        // Check character limit
        const combinedLength = markdownResult.length + jsonResult.length;
        if (combinedLength > CHARACTER_LIMIT) {
          // Truncate if needed
          const maxMarkdown = Math.floor(CHARACTER_LIMIT * 0.6);
          const maxJson = CHARACTER_LIMIT - maxMarkdown - 100; // Reserve space for truncation message
          
          if (markdownResult.length > maxMarkdown) {
            markdownResult = markdownResult.substring(0, maxMarkdown) + '\n\n*(Content truncated due to size limits)*';
          }
          if (jsonResult.length > maxJson) {
            jsonResult = JSON.stringify({
              ...tocData,
              truncated: true,
              message: `JSON data truncated. Original size: ${JSON.stringify(tocData).length} characters.`
            }, null, 2).substring(0, maxJson);
          }
        }
        
        return {
          content: [
            { type: "text", text: markdownResult },
            { type: "text", text: "\n---\nJSON Data:\n" + jsonResult }
          ]
        };
      } catch (error) {
        console.error("Error generating TOC:", error);
        return formatErrorResponse(error);
      }
    }
  );
}



























