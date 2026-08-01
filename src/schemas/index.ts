/**
 * Zod validation schemas for OneNote MCP Server tools
 */

import { z } from 'zod';

// Authentication schemas
export const AuthenticateInputSchema = z.object({}).strict();

export const SaveTokenInputSchema = z.object({
  token: z.string().min(1, "Token cannot be empty").describe("The Microsoft Graph access token to save")
}).strict();

// Notebook schemas
export const ListNotebooksInputSchema = z.object({}).strict();

export const GetNotebookInputSchema = z.object({
  notebook_name: z.string().optional().describe("Name of the notebook (partial match supported)")
}).strict();

// Section schemas
export const ListSectionsInputSchema = z.object({
  notebook_name: z.string().optional().describe("Name of the notebook (optional)")
}).strict();

// Page schemas
export const ListPagesInputSchema = z.object({
  section_name: z.string().optional().describe("Name of the section (optional, uses first section if not provided)")
}).strict();

export const GetPageInputSchema = z.object({
  page_id: z.string().optional().describe("Page ID or title (searches by title if not found by ID)")
}).strict();

export const CreatePageInputSchema = z.object({
  section_name: z.string().optional().describe("Name of the section (optional, uses first section if not provided)"),
  title: z.string().min(1, "Title cannot be empty").max(200, "Title must not exceed 200 characters").describe("Title of the page"),
  content: z.string().min(1, "Content cannot be empty").describe("HTML content for the page body")
}).strict();

export const SearchPagesInputSchema = z.object({
  query: z.string().min(1, "Query cannot be empty").max(200, "Query must not exceed 200 characters").describe("Search query to match against page titles")
}).strict();

export const GetNotebookTOCInputSchema = z.object({
  notebook_name: z.string().optional().describe("Name of the notebook (optional, uses first notebook if not provided)")
}).strict();

// Type exports
export type AuthenticateInput = z.infer<typeof AuthenticateInputSchema>;
export type SaveTokenInput = z.infer<typeof SaveTokenInputSchema>;
export type ListNotebooksInput = z.infer<typeof ListNotebooksInputSchema>;
export type GetNotebookInput = z.infer<typeof GetNotebookInputSchema>;
export type ListSectionsInput = z.infer<typeof ListSectionsInputSchema>;
export type ListPagesInput = z.infer<typeof ListPagesInputSchema>;
export type GetPageInput = z.infer<typeof GetPageInputSchema>;
export type CreatePageInput = z.infer<typeof CreatePageInputSchema>;
export type SearchPagesInput = z.infer<typeof SearchPagesInputSchema>;
export type GetNotebookTOCInput = z.infer<typeof GetNotebookTOCInputSchema>;
