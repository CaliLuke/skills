---
name: dev-session-to-blog-notes
description: Turn development session transcripts into blog-writing notes. Use to summarize a coding session, extract a narrative arc from Claude Code or Codex transcripts, combine sessions, or draft BLOG-NOTES.md for a technical post.
---

# Development Session to Blog Notes

Transform development session transcripts into structured notes for writing blog posts about the development process.

## When to Use

- User asks to summarize "our session" or "what we built"
- User wants to write a blog post about a development project
- User wants to capture the narrative arc of a coding session
- Multiple sessions need to be combined into a coherent story

## Session Transcript Locations

Claude Code stores session transcripts at:

```text
~/.claude/projects/<project-path-encoded>/<session-id>.jsonl
```

Codex session storage can vary by local setup. Search under `~/.codex` if the user asks for Codex transcripts.

Each line is a JSON object representing a conversation turn.

## The Process

### Step 1: Locate Transcripts

```bash
# Find transcript files for a project
ls -la ~/.claude/projects/-Users-*/<project-name>*/

# Check size before reading
wc -l ~/.claude/projects/.../<session-id>.jsonl
```

### Step 2: Extract Session Narrative

Check transcript size before reading. For very large sessions, use `rg`, `jq`, or small scripts to extract user messages, tool results, and key assistant turns without loading the whole file into context.

Use subagents only when the user explicitly asks for delegated or parallel agent work. When subagents are authorized, give each agent a bounded transcript path and ask for raw narrative findings rather than a polished final answer:

```typescript
Task({
  description: "Extract blog narrative from dev session",
  subagent_type: "general-purpose",
  prompt: `Read the session transcript at ${transcriptPath}

This is a JSONL file of a Claude Code development session.
Project context: ${projectDescription}

Extract a narrative for a blog post:

**Story Arc:**
1. What was the initial goal/problem?
2. What approaches were tried first?
3. What failed and why?
4. What was the turning point or key insight?
5. What was the final solution?

**Debugging Stories:**
- Interesting bugs discovered
- How they were diagnosed
- The "aha" moment when the fix became clear

**Human-AI Collaboration Moments:**
- Times the user course-corrected the AI
- Frustration points that led to better solutions
- Direct quotes showing the dynamic

**Technical Details:**
- Key code snippets that illustrate the solution
- Architecture decisions made
- Tools or techniques that proved valuable

Return a chronological narrative with specific details and quotes.`,
});
```

### Step 3: Handle Multiple Sessions

If the project spans multiple sessions and the user explicitly authorizes parallel agent work, spawn parallel agents:

```typescript
// Spawn agents in parallel for each session
Task({
  description: "Extract session 1 narrative",
  prompt: `...session 1 path...`,
  subagent_type: "general-purpose",
});

Task({
  description: "Extract session 2 narrative",
  prompt: `...session 2 path...`,
  subagent_type: "general-purpose",
});

// Then synthesize the results into a unified narrative
```

Without explicit subagent authorization, process each transcript sequentially with targeted extraction commands and synthesize locally.

### Step 4: Synthesize into Blog Notes

After receiving subagent summaries, create structured notes:

```markdown
# Blog Notes: [Project Name]

## Title Ideas

- ...

## The Hook

What problem was being solved? Why should readers care?

## Act Structure

1. **Setup**: Initial goal, tools involved
2. **Conflict**: What went wrong, what was tried
3. **Turning Point**: The key insight
4. **Resolution**: The working solution
5. **Lesson**: What was learned

## Key Quotes

Direct exchanges that show the collaboration dynamic

## Technical Highlights

Code snippets, architecture diagrams, before/after comparisons

## Lessons Learned

Actionable takeaways for readers
```

## Extraction Prompt Template

```text
Read the session transcript at [PATH].

This is a JSONL file from a Claude Code session building [PROJECT DESCRIPTION].

I need to write a blog post about this development process. Extract:

1. **Chronological narrative**: What happened in order, including false starts
2. **Emotional beats**: Frustration points, breakthroughs, satisfaction moments
3. **Direct quotes**: User messages that capture the collaboration dynamic (include the sharp/frustrated ones - they're authentic)
4. **Technical turning points**: The specific bugs, the specific fixes, the code that mattered
5. **Pivots**: When the approach fundamentally changed and why

Format as a story outline I can expand into a blog post, not a dry summary.
Include specific details - file names, error messages, line numbers mentioned.
```

## What Makes Good Blog Content

From development sessions, look for:

- **The mess before the solution** - Readers relate to struggle
- **Explicit course corrections** - "no, that's wrong" moments are gold
- **The debugging detective story** - Following clues to find a bug
- **Strategic retreats** - When abandoning an approach was the right call
- **Visual validation** - Screenshots, before/after comparisons
- **The one-line fix** - Satisfying resolutions to complex problems

## Output Location

Write notes to the project root:

```text
/path/to/project/BLOG-NOTES.md
```

## Example: Site Sucker Project

Input: 5000+ line transcript across multiple sessions

Extraction prompt focused on:

- MCP integration struggles
- The pivot from Penpot plugin to CLI
- The negative margin bug discovery
- Visual debugging with bounding box overlay

Output: Structured notes with 7-act narrative, memorable quotes, technical diagrams, and suggested blog post structure.
