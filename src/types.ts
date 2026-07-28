/**
 * TypeScript type definitions for OneNote MCP Server
 */

import { Client } from '@microsoft/microsoft-graph-client';

// Microsoft Graph API types
export interface Notebook {
  id: string;
  displayName: string;
  self: string;
  sectionsUrl: string;
  sectionGroupsUrl: string;
  links?: {
    oneNoteClientUrl?: { href: string };
    oneNoteWebUrl?: { href: string };
  };
}

export interface Section {
  id: string;
  displayName: string;
  pagesUrl: string;
  self: string;
  parentNotebook?: {
    id: string;
    displayName: string;
    self: string;
  };
}

export interface Page {
  id: string;
  title: string;
  createdDateTime: string;
  lastModifiedDateTime: string;
  self: string;
  contentUrl: string;
  content?: string;
}

export interface GraphClientResult {
  type: 'token' | 'device_code';
  client: Client;
}

export interface TOCSection {
  name: string;
  pageCount: number;
  pages: Array<{
    title: string;
    id: string;
    created: string;
    modified: string;
  }>;
}

export interface TOCData {
  notebook: string;
  stats: {
    sections: number;
    pages: number;
  };
  sections: TOCSection[];
}



























