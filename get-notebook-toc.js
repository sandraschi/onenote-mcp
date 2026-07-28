/**
 * Generate Table of Contents for a OneNote Notebook
 * 
 * Creates a hierarchical TOC showing all sections and pages
 * with optional metadata (created date, modified date, page count)
 * 
 * Usage: node get-notebook-toc.js [notebook-name] [--format=md|json|tree]
 */

import { readFileSync, existsSync } from 'fs';
import https from 'https';

const TOKEN_FILE = '.access-token.txt';

function getAccessToken() {
    if (!existsSync(TOKEN_FILE)) {
        console.error('No access token found. Run authentication first.');
        process.exit(1);
    }
    return readFileSync(TOKEN_FILE, 'utf8').trim();
}

async function graphRequest(endpoint) {
    const token = getAccessToken();
    
    return new Promise((resolve, reject) => {
        const options = {
            hostname: 'graph.microsoft.com',
            path: `/v1.0/me/onenote/${endpoint}`,
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        };

        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                if (res.statusCode === 200) {
                    resolve(JSON.parse(data));
                } else {
                    reject(new Error(`API error ${res.statusCode}: ${data}`));
                }
            });
        });

        req.on('error', reject);
        req.end();
    });
}

async function getNotebooks() {
    const response = await graphRequest('notebooks');
    return response.value || [];
}

async function getSections(notebookId) {
    const response = await graphRequest(`notebooks/${notebookId}/sections`);
    return response.value || [];
}

async function getPages(sectionId) {
    const response = await graphRequest(`sections/${sectionId}/pages`);
    return response.value || [];
}

async function buildNotebookTOC(notebook) {
    const toc = {
        notebook: {
            id: notebook.id,
            name: notebook.displayName,
            created: notebook.createdDateTime,
            modified: notebook.lastModifiedDateTime,
            sections: []
        },
        stats: {
            sectionCount: 0,
            pageCount: 0
        }
    };

    const sections = await getSections(notebook.id);
    toc.stats.sectionCount = sections.length;

    for (const section of sections) {
        const pages = await getPages(section.id);
        toc.stats.pageCount += pages.length;

        toc.notebook.sections.push({
            id: section.id,
            name: section.displayName,
            created: section.createdDateTime,
            modified: section.lastModifiedDateTime,
            pages: pages.map(p => ({
                id: p.id,
                title: p.title,
                created: p.createdDateTime,
                modified: p.lastModifiedDateTime,
                order: p.order
            })).sort((a, b) => a.order - b.order)
        });
    }

    return toc;
}

function formatAsMarkdown(toc) {
    const lines = [];
    const nb = toc.notebook;
    
    lines.push(`# ${nb.name}`);
    lines.push('');
    lines.push(`> ${toc.stats.sectionCount} sections, ${toc.stats.pageCount} pages`);
    lines.push(`> Last modified: ${new Date(nb.modified).toLocaleDateString()}`);
    lines.push('');
    lines.push('---');
    lines.push('');

    for (const section of nb.sections) {
        lines.push(`## ${section.name}`);
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

    return lines.join('\n');
}

function formatAsTree(toc) {
    const lines = [];
    const nb = toc.notebook;
    
    lines.push(`${nb.name}/`);
    
    const sectionCount = nb.sections.length;
    nb.sections.forEach((section, si) => {
        const isLastSection = si === sectionCount - 1;
        const sPrefix = isLastSection ? '└── ' : '├── ';
        const sIndent = isLastSection ? '    ' : '│   ';
        
        lines.push(`${sPrefix}${section.name}/`);
        
        const pageCount = section.pages.length;
        section.pages.forEach((page, pi) => {
            const isLastPage = pi === pageCount - 1;
            const pPrefix = isLastPage ? '└── ' : '├── ';
            lines.push(`${sIndent}${pPrefix}${page.title}`);
        });
    });

    lines.push('');
    lines.push(`(${toc.stats.sectionCount} sections, ${toc.stats.pageCount} pages)`);
    
    return lines.join('\n');
}

async function main() {
    const args = process.argv.slice(2);
    let notebookName = null;
    let format = 'md';

    for (const arg of args) {
        if (arg.startsWith('--format=')) {
            format = arg.split('=')[1];
        } else if (!arg.startsWith('-')) {
            notebookName = arg;
        }
    }

    try {
        const notebooks = await getNotebooks();
        
        if (notebooks.length === 0) {
            console.log('No notebooks found.');
            return;
        }

        // Find matching notebook or use first one
        let notebook;
        if (notebookName) {
            notebook = notebooks.find(n => 
                n.displayName.toLowerCase().includes(notebookName.toLowerCase())
            );
            if (!notebook) {
                console.error(`Notebook "${notebookName}" not found.`);
                console.log('Available notebooks:');
                notebooks.forEach(n => console.log(`  - ${n.displayName}`));
                return;
            }
        } else {
            // Show all notebooks if none specified
            console.log('Available notebooks:');
            notebooks.forEach(n => console.log(`  - ${n.displayName}`));
            console.log('\nGenerating TOC for first notebook...\n');
            notebook = notebooks[0];
        }

        console.error(`Building TOC for "${notebook.displayName}"...`);
        const toc = await buildNotebookTOC(notebook);

        switch (format) {
            case 'json':
                console.log(JSON.stringify(toc, null, 2));
                break;
            case 'tree':
                console.log(formatAsTree(toc));
                break;
            case 'md':
            default:
                console.log(formatAsMarkdown(toc));
                break;
        }

    } catch (error) {
        console.error('Error:', error.message);
        if (error.message.includes('401')) {
            console.error('Token expired. Please re-authenticate.');
        }
    }
}

main();

