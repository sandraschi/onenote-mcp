/**
 * Error handling utilities for OneNote MCP Server
 */

/**
 * Handle API errors and return user-friendly error messages
 */
export function handleApiError(error: unknown): string {
  if (error instanceof Error) {
    // Check for specific error patterns
    const message = error.message.toLowerCase();

    if (message.includes('401') || message.includes('unauthorized')) {
      return "Error: Authentication failed. Please authenticate using the 'onenote_authenticate' tool or save a valid access token using 'onenote_save_token'.";
    }

    if (message.includes('403') || message.includes('forbidden')) {
      return "Error: Permission denied. Your access token may not have the required permissions. Please re-authenticate.";
    }

    if (message.includes('404') || message.includes('not found')) {
      return "Error: Resource not found. Please check the ID or name is correct.";
    }

    if (message.includes('429') || message.includes('rate limit')) {
      return "Error: Rate limit exceeded. Please wait before making more requests.";
    }

    if (message.includes('timeout') || message.includes('timed out')) {
      return "Error: Request timed out. Please try again.";
    }

    if (message.includes('network') || message.includes('connection')) {
      return "Error: Network error. Please check your internet connection and try again.";
    }

    // Return the original error message if no specific pattern matches
    return `Error: ${error.message}`;
  }

  return `Error: Unexpected error occurred: ${String(error)}`;
}

/**
 * Format error response for MCP
 */
export function formatErrorResponse(error: unknown): { content: Array<{ type: string; text: string }> } {
  return {
    content: [{
      type: "text",
      text: handleApiError(error)
    }]
  };
}
