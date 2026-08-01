# onenote-mcp User Guide — Natural Language Tutorials

This guide teaches you, the user, how to get the most out of the OneNote MCP server. It is
written conversationally, task by task. You do not need to read it top to bottom — jump to
whatever you are trying to do. The assistant will use the underlying tools automatically;
this document is your map of what is possible and how to ask for it.

---

## 1. Your First Connection

### 1.1 Signing in

Before any OneNote content is accessible, the server needs permission to act as you. The
first time you use any notebook tool, the assistant will (or you can ask it to) run the
device code login. Here is what happens:

1. The server contacts Microsoft and gets a short code plus a web address.
2. You open https://microsoft.com/devicelogin on any device — phone, tablet, another PC.
3. You enter the code shown by the assistant.
4. You pick the Microsoft account that owns the notebooks you want to access and approve
   the permission request.
5. The assistant confirms "Authentication successful", and from then on every tool call
   works silently in the background.

You only need to do this once per machine, until the token expires. If you ever see
authentication errors, simply ask: "Please re-authenticate my OneNote connection."

### 1.2 Alternative: paste a token yourself

If you already have a Microsoft Graph access token (for example from Graph Explorer,
`az account get-access-token --resource https://graph.microsoft.com`, or a corporate
script), you can hand it to the assistant:

> "Save this access token: eyJ0eXA..."

The assistant persists it via the `onenote_save_access_token` tool, and you are in.

### 1.3 Verify you are connected

Ask: "Show me my notebooks." You should see a numbered list. If the list is empty, your
account has no OneNote notebooks yet — the next section shows how to think about that.

---

## 2. Understanding Your Notebooks

OneNote organizes content in three levels. Think of it like a real notebook:

- **Notebook** — the binder. Most people have a handful: "Personal", "Work", "Projects",
  "Journal". You open and close them like real binders.
- **Section** — the tab dividers inside a binder. "Meeting Notes", "Ideas", "Budget",
  "Class Notes" are typical section names.
- **Page** — an actual sheet of notes inside a tab. A page is one dated or titled note:
  "2026-08-01 standup", "Project Alpha charter", "Shopping list".

The assistant addresses each level with an ID. IDs look like `0-ABC123...` and are
unique. You will rarely need to type IDs yourself — the assistant carries them between
steps. But when you see them, know that they are the handle used to navigate.

### Typical question → tool mapping

| You ask | The assistant runs |
|---------|-------------------|
| "What notebooks do I have?" | onenote_list_notebooks |
| "What's inside my Work notebook?" | onenote_list_sections |
| "What pages are in my Meeting Notes?" | onenote_list_pages |
| "Show me the page about the Q3 plan" | onenote_get_page |
| "Find everything about the migration" | onenote_search_pages |
| "Give me the full structure of Projects" | onenote_get_notebook_toc |

---

## 3. Reading Your Notes

### 3.1 Browsing the tree

The simplest read workflow is drill-down:

1. "List my notebooks" → you see Personal, Work, Projects...
2. "Show the sections in Work" → you see Meetings, Reports, HR...
3. "What pages are in Meetings?" → you see dated meeting notes.
4. "Open the standup from August 1" → you get the full page content.

The assistant renders page content as clean markdown: headings, bullets, tables, and
checklists — even though OneNote stores everything as HTML. It converts for you.

### 3.2 Searching instead of browsing

When you know roughly what a note is about but not where it lives, search is faster:

> "Find my notes about the database migration."
> "What did I write about the Vienna apartment?"
> "Do I have anything on the new pricing model?"

The assistant runs a full-text search across all notebooks and returns matching pages
with titles and dates. You can then open the best hits.

Search tips:

- Use distinctive words. "Report" matches everything; "Q3 capacity report" is targeted.
- If you get nothing, try a broader term — OneNote search is simple full-text matching,
  not a smart engine.
- Recent edits may take a few minutes to appear in search.

### 3.3 Reading a table of contents

For a complete map of one notebook:

> "Give me the structure of my Projects notebook."

The assistant walks every section and page and returns an outline with page counts per
section and modification dates per page. This is the fastest way to see everything in a
notebook at a glance. On very large notebooks it takes a few seconds — normal.

---

## 4. Writing and Saving Notes

### 4.1 Creating a page

The core write operation: creating a page inside a notebook.

> "Save this: meeting with design on Thursday 10am, decide on the new onboarding flow."
> "Create a page in Work with my Q3 goals."
> "Write up my trip plan for Lisbon."

The assistant picks the notebook (or asks you), then creates a page with your content
formatted as proper HTML: headings for structure, bullet lists for items, checkboxes for
tasks. Inside OneNote it looks native — synced to all your devices.

To be explicit about where things go:

> "Create the page in my Journal notebook."
> "Put it in Work, section Meetings."

### 4.2 Authoring rich content

You can dictate as much structure as you like and the assistant will encode it:

- Headings: "Start with a heading 'Goals', then..."
- Lists: "Bullet list of the three options"
- Tables: "Make a table with columns Team, Owner, Status"
- Tasks: "Checklist of action items with the owner in parentheses"
- Code: "Paste this Python snippet in a code block"

Example request:

> "Create a page in Projects called 'Alpha kickoff'. Structure: an overview paragraph,
> a table of stakeholders, a checkbox list of immediate actions, and a code block with
> the connection string example."

### 4.3 Append or consolidate

The server has no edit tool yet — it writes new pages. To evolve a note, create a new
dated page and reference the old one, or ask the assistant to search first and then
create a consolidated page. A good habit:

> "Find my Alpha notes, then create a single summary page with the key points and
> links to the source page titles."

---

## 5. Everyday Workflows

### 5.1 Meeting minutes

After every meeting, ask:

> "Take minutes: attendees Sandra, Tom, Ines. Agenda: Q3 roadmap, headcount. Decisions:
> ship the beta end of August. Actions: Tom drafts the migration plan, Ines checks the
> budget, Sandra schedules the review."

The assistant creates a page with the standard minutes structure — attendees, agenda,
decisions, and an action-item checklist you can tick off in OneNote.

### 5.2 Daily journal

> "Journal entry for today: mostly focused on the onboarding flow; blocked on the auth
> decision; read two papers on retrieval. Tomorrow: prototype the dashboard."

Keep one notebook ("Journal"), one page per day. The assistant titles pages with the
date so they sort naturally.

### 5.3 Weekly review

> "Run my weekly review: show me what changed this week and create a review page."

The assistant collects recently modified pages across your notebooks, summarizes the
week, and writes a "Week of ..." review page with open loops as checkboxes.

### 5.4 Research and reading

> "Clip this article: [URL]. Summary of the argument, three key quotes, and follow-ups."

The assistant builds a structured clipping page. Over time your "Clippings" section
becomes a searchable personal knowledge base:

> "Find my clips about agent memory."

### 5.5 To-do and habit tracking

> "Create a page 'October habits' with daily checkboxes: morning walk, one hour of
> German, no phone after 10pm."

Review periodically with "How did my habits do this month?" — the assistant finds the
page and summarizes the checked state.

### 5.6 Project tracking

> "Set up a page for the app redesign: goals, scope, team, backlog as checkboxes."

Weekly: "Update my app redesign page with what got done this week." The assistant finds
the page (search by title), and you create a refreshed status page or a progress note.

### 5.7 Travel planning

> "Create a Lisbon trip page: flights (booked), hotel (booked, link below), packing
> checklist, day-by-day plan."

[Hotel confirmation link]. The assistant builds the page with a booking link and a
packing checklist.

---

## 6. Advanced Patterns

### 6.1 Cross-notebook synthesis

OneNote content is fragmented by nature. The assistant is good at pulling it together:

> "Synthesize everything I have about the warehouse move into one page: decisions,
> dates, open questions."

It searches, reads the relevant pages, and writes a single consolidated page — with the
source pages named so you can audit the synthesis.

### 6.2 Structure-first navigation for big notebooks

If your notebooks are huge, full TOC walks get slow. Ask targeted questions instead:

> "Which sections in Work have pages modified this month?"

The assistant walks the TOC but only reports the relevant subset.

### 6.3 Template reuse

Develop your own templates by asking for them once, then referencing the pattern:

> "Create another kickoff page like the Alpha one, for the Beta project."

The assistant reads the Alpha page structure and replicates it with Beta's content.

### 6.4 Batch capture

Dump many small notes at once:

> "Create these pages in Inbox: 'Buy milk' (shopping list item), 'Read the LangChain
> post' (reading queue), 'Book dentist' (errands)."

Each becomes its own page, searchable independently.

---

## 7. The Webapp (Browser Interface)

If you run the webapp (http://localhost:10906 in development), you get a graphical
mirror of the MCP surface:

- **Dashboard** — live backend status, tool count, uptime, and Graph auth state.
- **Notebooks** — tree browser: notebooks → sections → pages, with a page viewer that
  renders the HTML content safely, plus search and a create-page form.
- **Chat** — the assistant with personality presets; conversation history persists in
  your browser (last 100 messages).
- **Logging** — a live ring buffer of server activity (filter, search, export).
- **Settings** — device-code sign-in and the LLM provider selector.
- **Status / Tools / Apps / Help** — diagnostics, the tool catalog, fleet apps, and
  usage documentation.

The webapp talks to the same backend as the MCP clients, so anything you see there
reflects the same data the assistant works with.

---

## 8. Troubleshooting

### "The assistant says I'm not authenticated"

Run the device-code login again (ask "authenticate me"). Tokens expire; this is normal.

### "My notebook list is empty"

Your Microsoft account has no OneNote notebooks. Create one in the OneNote app or web
client first, then refresh ("list my notebooks again").

### "I get 'not found' errors"

An ID may be stale or mistyped. Ask the assistant to re-run discovery from the top
("list my notebooks again, then drill into Work"). IDs change only if the item is moved
or deleted.

### "Search returns nothing"

OneNote search is literal full-text. Try fewer or more distinctive words, and remember
brand-new pages may take minutes to index.

### "Page content looks odd"

OneNote HTML can be messy (nested tables, embedded media). Ask the assistant to
"extract the key points as a clean summary" — it converts HTML to structured markdown.

### "The server won't start"

- Check port 10907 is free (another process may be holding it).
- The HTTP target must be `onenote_mcp.server:http_app` — never the raw FastMCP object
  (that produces `'FastMCP' object is not callable`).
- Check `MCP_TRANSPORT` and `ONENOTE_PORT` environment variables.

---

## 9. Safety and Privacy

- The server can read everything in your OneNote and write new pages. It has no delete
  tools — content is never destroyed by the assistant.
- Tokens are treated as secrets: never paste them into public chats or log files.
- When you ask the assistant to save sensitive content (health, finances), it writes it
  to your notebooks like any other note — you control what goes where.
- You can revoke access anytime at https://account.microsoft.com/consent — the server
  will simply start prompting for authentication again.

---

## 10. Quick Reference Card

| Goal | Ask | Tool |
|------|-----|------|
| Sign in | "Authenticate OneNote" | authenticate |
| Save a token | "Save this token: ..." | onenote_save_access_token |
| See notebooks | "Show my notebooks" | onenote_list_notebooks |
| Notebook details | "Details of notebook X" | onenote_get_notebook |
| See sections | "Sections in X" | onenote_list_sections |
| See pages | "Pages in section X" | onenote_list_pages |
| Read a page | "Open page X" | onenote_get_page |
| Save a note | "Save this to notebook X" | onenote_create_page |
| Find notes | "Find notes about X" | onenote_search_pages |
| Notebook map | "Structure of notebook X" | onenote_get_notebook_toc |
| Tool list | "What can you do?" | onenote_help |
| Stop server | "Shut down the server" | shutdown_server |

---

## 11. What the Assistant Does Not Do (Yet)

- **No editing in place** — existing pages cannot be modified; you create new pages or
  consolidated versions.
- **No deletion** — by design. Remove content manually in the OneNote app.
- **No section targeting on create** — new pages land in the notebook's default section.
  (Section-level creation is on the roadmap; until then, create in the notebook and move
  pages manually if needed.)
- **No section groups** — folder-like section groups are not surfaced in listings.
- **No attachments or binary media** — images by URL or data URI work; binary uploads
  are not exposed.

These are roadmap items. Everything else — browse, read, search, write, synthesize,
organize — works today.

---

## 12. Walkthrough: Your First Hour

If you are brand new to the OneNote MCP server, here is a complete first-hour script.
Follow along; each step takes under a minute.

### Step 1 — Connect (2 minutes)

Ask: "Please authenticate OneNote." Open the link the assistant prints, enter the code,
approve. Then ask: "Show my notebooks" and confirm you see your real notebooks. If you
have none, create one in the OneNote app (File → New Notebook, name it "Test") and ask
again.

### Step 2 — Explore (5 minutes)

Ask: "What sections are in my Test notebook?" Then: "Create a page in Test titled
'First note' with a bullet list of three things you learned today." Open the OneNote app
or web client and watch the page appear — usually within seconds thanks to sync.

### Step 3 — Search (5 minutes)

Add a second page: "Create a page in Test called 'Groceries' with a checkbox list: milk,
eggs, coffee." Then ask: "Find my note about groceries." Watch the assistant find it
via search even though you never told it where it lives.

### Step 4 — Synthesize (5 minutes)

Ask: "Find all my pages in Test, summarize what they contain, and create a 'Test — all
my notes' summary page." The assistant walks the TOC, reads both pages, and writes a
consolidated page. You now have a searchable personal knowledge base pattern you can
reuse for real projects.

### Step 5 — Structure (2 minutes)

Ask: "Give me the full structure of my Test notebook." You get a TOC: sections, page
counts, modification dates. This is the "map" view you will use constantly.

### Step 6 — Habits (5 minutes)

Set up a real workflow: "Create a page 'Daily log' in Test with a checkbox list: wrote
three sentences, moved one task forward, read one page of a book." Tomorrow, ask: "Log
today's entry" and let the assistant create the next day's page.

### Step 7 — Clean up (2 minutes)

Delete the Test notebook in the OneNote app (or keep it as a sandbox — your call).

---

## 13. Walkthrough: Realistic Project Session

Scenario: you manage a small software project and want to keep it in OneNote. Here is a
full session, from zero to a maintained project notebook.

### Setup (5 minutes)

1. "Create a notebook for the project" — do this in OneNote itself (name it "Orbit").
2. "List my notebooks" — confirm Orbit exists.
3. "Create a page in Orbit: 'Charter' with headings Goals, Scope, Non-goals, and a
   stakeholders table (Name, Role, Contact)."
4. "Create a page in Orbit: 'Backlog' with checkbox items: login flow, dashboard,
   export, notifications."

### Daily (2 minutes per day)

- "Log today: did the login flow, blocked on the export library decision." (creates a
  dated progress page)
- "Add to backlog: fix the settings page validation."

### Weekly (10 minutes)

1. "Run my weekly review for Orbit: what changed this week?"
2. The assistant lists pages modified in the last 7 days.
3. "Create a 'Week of <date> — Orbit review' page: wins, blockers, next week
   priorities." The assistant builds it from the week's pages.

### Monthly (15 minutes)

1. "Synthesize everything in Orbit into a status report: what shipped, what is
   blocked, open risks."
2. The assistant searches and reads the relevant pages and writes one consolidated
   report page.
3. You copy the report into an email or share it — done.

### Crisis mode

Forgot what you decided in March? "Find my Orbit decisions about the export format."
Search finds the page; the assistant quotes the decision and the date.

---

## 14. Walkthrough: Research Corpus

Scenario: you are researching a topic (say, "retrieval-augmented generation") and want
OneNote to be your reading-notes hub.

1. Create a "Research" notebook in the OneNote app.
2. "Create a page in Research: 'RAG reading queue' with checkbox items" — add papers as
   you find them: "RAG survey 2024", "RAG vs fine-tuning benchmark".
3. When you read a paper: "Clip into Research: [title], authors, one-paragraph
   summary, three key quotes, follow-up questions." The assistant creates a clipping
   page.
4. Weekly: "Find my RAG clips from this month and create a synthesis page." The
   assistant aggregates.
5. Before a meeting: "Brief me on RAG: what have I read, and what are the open
   questions?" The assistant searches, reads the synthesis, and answers conversationally.

The pattern generalizes to any domain: feed it clips, get syntheses on demand.

---

## 15. Walkthrough: Personal Lifehacks

### Grocery and errands

"Create a page 'Shopping' with a checkbox list: milk, eggs, coffee, dish soap."
Check items off in the OneNote app as you buy them. Ask "What's on my shopping list
that I haven't bought?" and the assistant reports unchecked items.

### Packing lists

"Create a 'Lisbon packing' page with checkboxes: passport, charger, adapters,
medication, comfortable shoes." On trip day: "Show my Lisbon packing list."

### Gift ideas

"Create a page 'Gift ideas' with a table: person, idea, status, budget." Before any
birthday: "What gift ideas do I have for Tom?" — search finds the table.

### Bill tracking

"Create a 'Bills' page with a table: bill, amount, due date, paid (checkbox)." Monthly:
"What bills are due this week?" The assistant searches and lists due items.

### Reading queue

"Add to my reading queue: the LangChain documentation, an article on vector
databases." Then "What's in my reading queue?" — checked items show progress.

---

## 16. Language and Tone

You can talk to the assistant as if it were a human note-keeping partner. Natural
phrases work:

- "Jot this down: ..."
- "Remember that ..."
- "File this under projects: ..."
- "What do I have on ...?"
- "Save a note about ..."

There is no command syntax to memorize. If the assistant is unsure which notebook or
section to use, it asks one short question and proceeds. If it cannot find something,
it says so honestly and suggests a broader search.

## 17. Frequently Asked Questions

**Q: Does this work with my corporate OneDrive account?**
A: Yes — any Microsoft account that has OneNote notebooks works, as long as the
organization allows app sign-in. If your org requires admin consent, contact your IT
admin with the app registration details.

**Q: Is my data sent to a cloud service beyond Microsoft?**
A: The server talks only to graph.microsoft.com. No third-party service sees your
content. The token file and logs stay on your machine.

**Q: Can the assistant see my password?**
A: No. Only the Graph access token is stored, and the assistant is instructed never to
echo it.

**Q: What happens if I revoke access?**
A: The next tool call fails with an authentication error; you can re-authenticate at
any time.

**Q: Can I use it on multiple machines?**
A: Yes — each machine runs its own server instance and its own token file. Content is
shared via OneDrive sync.

**Q: How do I move pages between sections?**
A: The server does not move pages yet. Do it in the OneNote app; the server picks up
the new location on the next listing.

**Q: How do I delete a notebook?**
A: In the OneNote app. The server never deletes anything.

**Q: The webapp shows "Offline"**
A: The backend on port 10907 is not running or is running old code. Restart it with
the fleet launcher or `uv run python -m onenote_mcp --http`, and ensure the ASGI
target is `http_app`.

**Q: Can I use it with Claude Desktop / Cursor?**
A: Yes. Add a stdio MCP entry pointing at `uv run python -m onenote_mcp`, or an HTTP
entry at `http://127.0.0.1:10907/mcp` when the server runs in HTTP mode.

**Q: Does the server work offline?**
A: No — OneNote content lives in the Microsoft cloud. You need network access to
graph.microsoft.com.

**Q: What if I have hundreds of pages?**
A: The tools are stateless and fast per call. TOC generation is the only N+1
operation; prefer search for large corpora.

## 18. Glossary

- **Access token** — a short-lived credential the server uses to call Microsoft Graph
  on your behalf.
- **Device code flow** — the sign-in method where you enter a code on a web page.
- **Graph API** — Microsoft's REST API for Microsoft 365 data, including OneNote.
- **Notebook** — top-level OneNote container (the "binder").
- **Section** — a tab inside a notebook.
- **Page** — an individual note inside a section.
- **TOC (table of contents)** — a structural overview of one notebook.
- **Ring buffer** — the in-memory log store (last 2000 entries) exposed in the webapp.
- **MCP** — Model Context Protocol, the standard the server speaks to assistants.
- **stdio / HTTP transports** — the two ways assistants connect: via a local process
  pipe or via an HTTP endpoint.

## 19. Getting Help

- The assistant's `onenote_help` tool lists everything it can do.
- The webapp Help page documents architecture, ports, and environment variables.
- `llms-full.txt` in the repository root is the machine-readable reference.
- The repository issue tracker collects bugs and feature requests; report problems
  with the server version and the exact error text.

---

*End of user guide. Happy note-taking!*

---

## 20. Walkthrough: Home Renovation Project

Scenario: you are managing a kitchen renovation and want every detail in OneNote.

### Setup
1. Create a "Renovation" notebook in the OneNote app.
2. "Create a page 'Kitchen — scope': headings Scope, Budget, Timeline; a budget table
   (item, estimate, actual, paid); a checkbox list of materials."
3. "Create a page 'Kitchen — contractors': table (company, contact, quote, status)."

### During the project
- "Add to materials: cabinet pulls, under-cabinet lighting, backsplash tiles."
- "Log today: electrician finished the wiring, plumber postponed to Friday."
- "Update the budget table: actual for cabinets is 4200, paid."

### Weekly
- "What changed in my renovation notebook this week?" — the assistant reports modified
  pages.
- "Create a status page for week 12: what got done, what is behind, next week."

### Closeout
- "Synthesize the whole renovation: total spend vs budget, outstanding items, lessons
  learned." One consolidated page you can keep forever.

---

## 21. Walkthrough: Job Search

### Setup
1. "Create a page 'Job search — applications' with a table: company, role, date,
   status, notes."
2. "Add rows: Acme senior engineer applied March 2; Globex data lead applied March 5."

### Per role
- "Create a page 'Acme — senior engineer': job summary, timeline table (step, date,
   outcome), interview prep notes."
- After an interview: "Log the Acme technical interview: asked about system design,
   I struggled with the caching part; follow up on the distributed systems topic."

### Weekly
- "What is the status of my applications?" — the assistant reads the table and
  summarizes.
- "Create a prep page for my Globex interview: research points, likely questions,
   my talking points."

---

## 22. Walkthrough: Language Learning with OneNote

### Setup
1. Create a "Languages" notebook, "German" section.
2. "Create a page 'German — vocabulary' with a table: word, reading, meaning,
   example sentence."
3. "Add words: der Termin (appointment), verschieben (to postpone), die Besprechung
   (meeting)."

### Daily practice
- "Create a page 'German — 2026-08-01 practice' with a checkbox list of exercises:
   write five sentences with new vocabulary, read one news headline, listen to one
   episode."
- "Quiz me: pick five random words from my German vocabulary table."

### Review
- "Summarize my German vocabulary: how many words, which topics are missing?" The
   assistant counts rows and suggests categories.

---

## 23. Walkthrough: Blog and Newsletter Drafting

### Setup
1. Create a "Writing" notebook.
2. "Create a page 'Newsletter — issue 12': outline with headings Intro, Deep dive,
   Links, Closing."

### Drafting
- "Write the Intro paragraph: hook about retrieval pipelines, two sentences on the
   newsletter, a teaser for the deep dive."
- "Add the Deep dive section: the three takeaways from the RAG survey, with a
   table comparing approaches."
- "Add the Links section as a bullet list of five resources."

### Publishing
- "Convert my newsletter page to clean markdown." The assistant extracts the HTML
   content and renders it as markdown for your publishing tool.

---

## 24. Walkthrough: Travel with a Family Member

### Setup
1. "Create a 'Lisbon trip' page: flights table (date, route, airline, time), hotel
   section with the booking link, packing checklist, day-by-day plan."
2. Share the notebook with your travel partner via OneNote's sharing (in the app).

### Before the trip
- "Add to the packing list: passports for both, phone chargers, travel adapter."
- "What still needs booking for Lisbon?" — the assistant reads the page and lists
   unchecked items.

### During the trip
- "Log day 2: Alfama walking tour, pastel de nata at the old bakery, booked the
   evening fado show."

### After
- "Create a 'Lisbon — after action' page: what went well, what to skip next time,
   favorite spots."

---

## 25. Walkthrough: Tracking Household Documents

### Setup
1. Create a "Home" notebook.
2. "Create a page 'Documents — inventory' with a table: document, location, expiry,
   notes." Add rows: passport (safe, 2031), warranty laptop (email), rental contract
   (archive).

### Maintenance
- "Remind me what expires this year" — the assistant filters by expiry.
- "Add the new car insurance policy: location email, expiry March next year."

---

## 26. Walkthrough: Fitness Log

### Setup
1. Create a "Fitness" notebook.
2. "Create a page 'Fitness — 2026-08' with a table: date, activity, duration, notes,
   and a goals checkbox list."

### Daily
- "Log today: 40-minute run, felt strong, pace 5:30."
- "Add to goals: three strength sessions this week."

### Monthly
- "Create a fitness review for July: total sessions, trends, what to adjust."
   The assistant aggregates the table rows into a summary page.

---

## 27. Walkthrough: Event Planning (Birthday)

### Setup
1. "Create a page 'Birthday — Sandra 40th': guest table (name, RSVP, dietary,
   plus-one), budget table, ideas list."
2. "Add guests: Tom, Ines, Markus."

### Coordination
- "Update RSVP: Tom confirmed, Ines maybe." (The assistant appends or you update in
   the app.)
- "Add a budget row: venue 1200, catering 800, cake 150."

### Execution
- "Show me the guest list with RSVP status." — one call, up-to-date table.

---

## 28. Walkthrough: Code Snippets Library

### Setup
1. Create a "Snippets" notebook, "Python" section.
2. "Create a page 'Python — httpx retry wrapper': code block with the implementation,
   usage example, gotchas (timeout handling, stream reuse)."

### Daily use
- "Find my snippet for retry logic." — search finds the page; the assistant extracts
   the code block.
- "Add a snippet: PowerShell — kill process by port, with usage and notes."
   OneNote preserves code formatting, so snippets stay readable on every device.

---

## 29. Walkthrough: Smart Home Manual

### Setup
1. Create a "Smart Home" notebook.
2. "Create a page 'Living room devices': table (device, model, host, app), automation
   rules list, troubleshooting notes."

### Troubleshooting
- "My living room lights stopped working — what do I have in the manual?" The
   assistant finds the page and walks the troubleshooting steps.
- "Add a note: after the router update, the Hue bridge needed a restart."

---

## 30. Putting It All Together

By now you have seen the full vocabulary of the server:

- **Discover** — list notebooks, sections, pages; get a TOC.
- **Read** — open pages, parse HTML into clean markdown.
- **Find** — search across everything.
- **Write** — create structured pages with headings, lists, tables, checkboxes, code.
- **Synthesize** — consolidate scattered notes into one page.
- **Track** — use checkboxes and tables as living status boards.

The assistant handles the mechanics; you provide intent. The most effective users
develop personal conventions — a "Daily log" page, a "Queue" page, a naming scheme —
because OneNote search and the assistant both work best with consistent structure.

Start small: one notebook, one workflow, one week. Expand as the habit forms. OneNote
is your long-term memory; this server is the way your assistant participates in it.

*End of user guide. Happy note-taking!*
