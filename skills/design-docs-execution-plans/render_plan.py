#!/usr/bin/env python3
"""Render a Markdown execution plan into the styled HTML tracker.

The Markdown file is the source of truth. The HTML is regenerated from it.
Hero stats, per-milestone progress bars, status badges (Pending vs Complete),
and ToC counts are all computed at page load by the embedded script from
checkbox state. Do not hand-edit the HTML.

Usage:
    python3 render_plan.py PLAN.md [-o PLAN.html]

Expected Markdown shape (see SKILL.md for the full contract):

    # <Title>

    <One short paragraph stating the chosen design and constraints.>

    ## Status

    - 2026-05-11 — Plan created.

    ## Milestones

    ### Milestone 1: <Outcome>

    Toc: <short sidebar label>

    Goal: <one short sentence>

    Acceptance Criteria

    - <bullet>

    Checklist

    - [ ] <task>
    - [x] <completed task>

A checklist item may be followed by an indented fenced code block; the
renderer surfaces it as a collapsible "show command" disclosure attached
to that item.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

CSS = r"""
:root {
  --bg: #f7f6f3;
  --surface: #ffffff;
  --ink: #1a1a1a;
  --ink-2: #3d3d3d;
  --muted: #6b6b6b;
  --line: #e5e3dd;
  --line-2: #efedea;
  --accent: #2563eb;
  --accent-soft: #eff5ff;
  --done: #15803d;
  --warn: #b45309;
  --warn-soft: #fffbeb;
  --code-bg: #f3f1ec;
  --date: #7c3aed;
  --shadow: 0 1px 2px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.04);
  --radius: 10px;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }
}
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font: 15.5px/1.65 -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", "Helvetica Neue", sans-serif;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}
.skip-link {
  position: absolute;
  left: 1rem;
  top: 1rem;
  transform: translateY(-150%);
  background: var(--ink);
  color: white;
  padding: 0.45rem 0.7rem;
  border-radius: 6px;
  z-index: 10;
}
.skip-link:focus-visible {
  transform: translateY(0);
  outline: 3px solid var(--accent);
  outline-offset: 2px;
}
.layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  max-width: 1240px;
  margin: 0 auto;
  gap: 2rem;
  padding: 2rem;
}
@media (max-width: 920px) {
  .layout { grid-template-columns: 1fr; padding: 1rem; gap: 1rem; }
  nav.toc { position: static; max-height: none; border: 1px solid var(--line); border-radius: var(--radius); padding: 1rem; }
}
nav.toc {
  position: sticky;
  top: 1.5rem;
  align-self: start;
  max-height: calc(100vh - 3rem);
  overflow-y: auto;
  font-size: 0.88rem;
  padding: 1.25rem 1rem 1rem;
}
nav.toc h2 {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--muted);
  margin: 0 0 0.85rem;
  border: 0;
  font-weight: 600;
}
nav.toc ul { list-style: none; padding: 0; margin: 0; }
nav.toc > ul > li { margin-bottom: 0.15rem; }
nav.toc ul ul { padding-left: 0; margin-top: 0.25rem; }
nav.toc a {
  color: var(--ink-2);
  text-decoration: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.4rem 0.6rem;
  border-radius: 6px;
  transition: background 120ms, color 120ms;
}
nav.toc a:hover { color: var(--accent); background: var(--accent-soft); }
nav.toc a:focus-visible,
.totop:focus-visible,
details.collapse summary:focus-visible,
details.review-fold summary:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--accent) 35%, transparent);
  outline-offset: 2px;
}
nav.toc .toc-progress {
  font-family: ui-monospace, "SF Mono", Menlo, monospace;
  font-size: 0.72rem;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}
nav.toc .ms-link { padding-left: 1.1rem; font-size: 0.85rem; }
main { min-width: 0; }
.hero,
.section {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}
.hero {
  padding: 2rem 2.25rem;
  margin-bottom: 1.25rem;
}
.hero h1 {
  font-size: 1.85rem;
  margin: 0 0 0.5rem;
  font-weight: 650;
  letter-spacing: -0.015em;
}
.hero .lede {
  margin: 0;
  color: var(--ink-2);
  font-size: 1rem;
  line-height: 1.7;
}
.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--line-2);
}
.stat { flex: 1 1 130px; }
.stat-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  font-weight: 600;
}
.stat-value {
  font-size: 1.4rem;
  font-weight: 600;
  margin-top: 0.2rem;
  font-variant-numeric: tabular-nums;
}
.section {
  padding: 1.75rem 2rem 1.5rem;
  margin-bottom: 1.25rem;
}
.section.unframed {
  background: transparent;
  border: 0;
  border-radius: 0;
  padding: 0;
  box-shadow: none;
}
.section > h2:first-child,
.section > .ms-header:first-child { margin-top: 0; }
h2 {
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  margin: 0 0 1rem;
  border: 0;
  scroll-margin-top: 1rem;
}
.ms-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin: 0 0 0.4rem;
  scroll-margin-top: 1rem;
}
.ms-header h2 { margin: 0; font-size: 1.2rem; }
.ms-header .ms-num {
  font-family: ui-monospace, "SF Mono", Menlo, monospace;
  font-size: 0.78rem;
  color: var(--muted);
  margin-right: 0.5rem;
  font-weight: 500;
}
.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  white-space: nowrap;
}
.badge.pending {
  background: var(--warn-soft);
  color: var(--warn);
  border: 1px solid #fde68a;
}
.badge.pending::before { content: "○"; font-size: 0.72rem; }
.badge.done {
  background: #ecfdf5;
  color: var(--done);
  border: 1px solid #bbf7d0;
}
.badge.done::before {
  content: "●";
  font-size: 0.6rem;
}
.ms-progress {
  height: 4px;
  background: var(--line-2);
  border-radius: 999px;
  overflow: hidden;
  margin: 0.4rem 0 1.25rem;
}
.ms-progress-bar {
  height: 100%;
  background: var(--done);
  border-radius: 999px;
}
.goal { margin: 0 0 1.25rem; color: var(--ink-2); }
.goal strong { font-weight: 600; color: var(--ink); }
.subhead {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--muted);
  font-weight: 600;
  margin: 1.5rem 0 0.6rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.subhead::after {
  content: "";
  flex: 1;
  height: 1px;
  background: var(--line-2);
}
p { margin: 0.75rem 0; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
code {
  background: var(--code-bg);
  padding: 0.1em 0.4em;
  border-radius: 4px;
  font: 0.84em ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  color: #1f2937;
  word-break: break-word;
}
pre {
  background: var(--code-bg);
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
}
pre code { background: none; padding: 0; font-size: 0.86em; }
ul { padding-left: 1.4rem; margin: 0.5rem 0; }
li { margin: 0.3rem 0; }
.acceptance ul {
  list-style: none;
  padding-left: 0;
  display: grid;
  gap: 0.5rem;
}
.acceptance li {
  position: relative;
  padding: 0.6rem 0.85rem 0.6rem 2rem;
  background: var(--bg);
  border: 1px solid var(--line-2);
  border-radius: 8px;
  font-size: 0.95rem;
  margin: 0;
}
.acceptance li::before {
  content: "✓";
  position: absolute;
  left: 0.7rem;
  top: 0.55rem;
  color: var(--done);
  font-weight: 700;
  font-size: 0.95rem;
}
.checklist ul { list-style: none; padding-left: 0; }
.checklist li {
  display: grid;
  grid-template-columns: 16px minmax(0, 1fr);
  align-items: flex-start;
  column-gap: 0.65rem;
  row-gap: 0.35rem;
  padding: 0.45rem 0.75rem;
  border-radius: 6px;
  margin: 0.1rem 0;
  transition: background 120ms;
}
.checklist li:hover { background: var(--bg); }
.checklist .task-text {
  grid-column: 2;
  min-width: 0;
}
.checklist li > details.collapse {
  grid-column: 2;
  display: block;
  min-width: 0;
  width: 100%;
}
input[type="checkbox"] {
  grid-column: 1;
  appearance: none;
  width: 16px; height: 16px;
  border: 1.5px solid #c7c5bf;
  border-radius: 4px;
  flex-shrink: 0;
  margin-top: 0.32em;
  position: relative;
  background: var(--surface);
  cursor: default;
}
input[type="checkbox"]:checked { background: var(--done); border-color: var(--done); }
input[type="checkbox"]:checked::after {
  content: "✓";
  color: white;
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
  line-height: 1;
}
.timeline {
  list-style: none;
  padding: 0.5rem 0 0;
  margin: 0;
  position: relative;
}
.timeline::before {
  content: "";
  position: absolute;
  left: 7px;
  top: 0;
  bottom: 0.5rem;
  width: 2px;
  background: linear-gradient(to bottom, var(--line), var(--line-2));
}
.timeline li {
  position: relative;
  padding: 0.25rem 0 0.85rem 2rem;
  margin: 0;
  font-size: 0.94rem;
  color: var(--ink-2);
}
.timeline li::before {
  content: "";
  position: absolute;
  left: 2px;
  top: 0.55rem;
  width: 12px; height: 12px;
  border-radius: 50%;
  background: var(--surface);
  border: 2px solid var(--accent);
  box-shadow: 0 0 0 3px var(--surface);
}
.timeline .date {
  display: inline-block;
  font-family: ui-monospace, "SF Mono", Menlo, monospace;
  font-size: 0.78rem;
  color: var(--date);
  font-weight: 600;
  margin-right: 0.55rem;
  background: #f5f3ff;
  padding: 0.05rem 0.4rem;
  border-radius: 4px;
}
details.review-fold {
  border-top: 1px solid var(--line-2);
  margin-top: 1rem;
  padding-top: 0.75rem;
}
details.review-fold summary {
  cursor: pointer;
  color: var(--accent);
  font-weight: 600;
  font-size: 0.9rem;
}
details.review-fold summary::marker { color: var(--muted); }
details.collapse { display: inline; }
details.collapse summary {
  cursor: pointer;
  color: var(--accent);
  font-size: 0.88rem;
  list-style: none;
  display: inline;
}
details.collapse summary::-webkit-details-marker { display: none; }
details.collapse summary::before {
  content: "▸ ";
  display: inline-block;
  transition: transform 150ms;
}
details.collapse[open] summary::before { content: "▾ "; }
details.collapse[open] summary { display: block; margin-bottom: 0.4rem; }
details.collapse pre {
  margin: 0.4rem 0 0;
  font-size: 0.8rem;
  white-space: pre-wrap;
  word-break: break-all;
}
.totop {
  position: fixed;
  right: 1.5rem;
  bottom: 1.5rem;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 999px;
  width: 40px; height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
  text-decoration: none;
  box-shadow: var(--shadow);
  font-size: 1.1rem;
  opacity: 0;
  pointer-events: none;
  transition: opacity 200ms;
}
.totop.show { opacity: 1; pointer-events: auto; }
.totop:hover { color: var(--accent); }
"""

JS = r"""
const totop = document.getElementById('totop');
window.addEventListener('scroll', () => {
  totop.classList.toggle('show', window.scrollY > 500);
});

function updateProgress() {
  const milestones = [...document.querySelectorAll('#milestones > article.section[id]')];
  let totalTasks = 0;
  let doneTasks = 0;
  let doneMilestones = 0;

  milestones.forEach((milestone) => {
    const boxes = [...milestone.querySelectorAll('.checklist input[type="checkbox"]')];
    const done = boxes.filter((box) => box.checked).length;
    const total = boxes.length;
    const complete = total > 0 && done === total;
    const percent = total === 0 ? 0 : Math.round((done / total) * 100);

    totalTasks += total;
    doneTasks += done;
    if (complete) doneMilestones += 1;

    const progressBar = milestone.querySelector('.ms-progress-bar');
    if (progressBar) progressBar.style.width = `${percent}%`;

    const badge = milestone.querySelector('.badge');
    if (badge) {
      badge.textContent = complete ? 'Complete' : 'Pending';
      badge.classList.toggle('done', complete);
      badge.classList.toggle('pending', !complete);
    }

    const summary = milestone.querySelector('details.review-fold > summary');
    if (summary) summary.textContent = `Checklist ${done}/${total}`;

    const tocProgress = document.querySelector(`[data-ms-progress="${milestone.id}"]`);
    if (tocProgress) {
      tocProgress.textContent = `${done}/${total}`;
      tocProgress.classList.toggle('done', complete);
    }
  });

  const totalPercent = totalTasks === 0 ? 0 : Math.round((doneTasks / totalTasks) * 100);
  const statusCount = document.querySelectorAll('#status .timeline li').length;

  document.querySelector('[data-total-progress]').textContent = `${doneTasks}/${totalTasks}`;
  document.querySelector('[data-total-progress]').classList.toggle('done', doneTasks === totalTasks && totalTasks > 0);
  document.querySelector('[data-status-count]').textContent = String(statusCount);

  document.querySelector('[data-stat="milestones"]').textContent = `${doneMilestones} / ${milestones.length}`;
  document.querySelector('[data-stat="tasks"]').textContent = `${doneTasks} / ${totalTasks}`;
  document.querySelector('[data-stat="percent"]').textContent = `${totalPercent}%`;
  document.querySelector('[data-stat="status"]').textContent = String(statusCount);
}

updateProgress();
window.setTimeout(() => {
  window.location.reload();
}, 30000);
"""

INLINE_CODE_RE = re.compile(r"`([^`]+)`")
MILESTONE_HEADING_RE = re.compile(r"^###\s+Milestone\s+(\S+?):\s*(.*)$")
CHECKLIST_ITEM_RE = re.compile(r"^-\s+\[([ xX])\]\s+(.*)$")
STATUS_ENTRY_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\s*[—-]\s*(.*)$")
INDENTED_FENCE_RE = re.compile(r"^(\s{2,})```")


class PlanParseError(ValueError):
    pass


def parse_plan(text: str) -> dict:
    lines = text.splitlines()
    n = len(lines)
    i = 0

    plan: dict = {"title": "", "lede": "", "status": [], "milestones": []}

    while i < n and not lines[i].startswith("# "):
        i += 1
    if i >= n:
        raise PlanParseError("missing title line `# <Title>`")
    plan["title"] = lines[i][2:].strip()
    i += 1

    lede_lines: list[str] = []
    while i < n and not lines[i].startswith("#"):
        if lines[i].strip():
            lede_lines.append(lines[i].strip())
        i += 1
    plan["lede"] = " ".join(lede_lines)

    while i < n and not lines[i].startswith("## Milestones"):
        line = lines[i]
        if line.startswith("## Status"):
            i += 1
            while i < n and not lines[i].startswith("##"):
                stripped = lines[i].strip()
                if stripped.startswith("- "):
                    body = stripped[2:]
                    m = STATUS_ENTRY_RE.match(body)
                    if m:
                        plan["status"].append({"date": m.group(1), "body": m.group(2)})
                    else:
                        plan["status"].append({"date": "", "body": body})
                i += 1
        else:
            i += 1

    if i >= n:
        raise PlanParseError("missing `## Milestones` section")
    i += 1

    current: dict | None = None
    sub: str | None = None

    while i < n:
        line = lines[i]

        ms_match = MILESTONE_HEADING_RE.match(line)
        if ms_match:
            if current:
                plan["milestones"].append(current)
            current = {
                "number": ms_match.group(1),
                "title": ms_match.group(2).strip(),
                "toc": None,
                "goal": "",
                "acceptance": [],
                "checklist": [],
            }
            sub = None
            i += 1
            continue

        if current is None:
            i += 1
            continue

        stripped = line.strip()

        if stripped.startswith("Toc:"):
            current["toc"] = stripped[len("Toc:"):].strip()
            sub = None
            i += 1
            continue

        if stripped.startswith("Goal:"):
            current["goal"] = stripped[len("Goal:"):].strip()
            sub = "goal"
            i += 1
            continue

        if stripped == "Acceptance Criteria":
            sub = "acceptance"
            i += 1
            continue

        if stripped == "Checklist":
            sub = "checklist"
            i += 1
            continue

        if sub == "acceptance" and stripped.startswith("- "):
            current["acceptance"].append(stripped[2:])
            i += 1
            continue

        if sub == "checklist":
            cl_match = CHECKLIST_ITEM_RE.match(stripped)
            if cl_match:
                checked = cl_match.group(1).lower() == "x"
                item: dict = {
                    "checked": checked,
                    "text": cl_match.group(2),
                    "command": None,
                }
                i += 1

                j = i
                while j < n and lines[j].strip() == "":
                    j += 1
                fence_match = INDENTED_FENCE_RE.match(lines[j]) if j < n else None
                if fence_match:
                    indent = len(fence_match.group(1))
                    j += 1
                    cmd_lines: list[str] = []
                    while j < n:
                        if lines[j].lstrip().startswith("```") and lines[j].strip() == "```":
                            j += 1
                            break
                        cmd_lines.append(lines[j][indent:] if len(lines[j]) >= indent else lines[j])
                        j += 1
                    item["command"] = "\n".join(cmd_lines).rstrip()
                    i = j
                current["checklist"].append(item)
                continue

        i += 1

    if current:
        plan["milestones"].append(current)

    return plan


def inline_md(s: str) -> str:
    parts = INLINE_CODE_RE.split(s)
    out: list[str] = []
    for idx, part in enumerate(parts):
        if idx % 2 == 0:
            out.append(html.escape(part, quote=False))
        else:
            out.append(f"<code>{html.escape(part, quote=False)}</code>")
    return "".join(out)


def is_complete(milestone: dict) -> bool:
    total = len(milestone["checklist"])
    if total == 0:
        return False
    return all(it["checked"] for it in milestone["checklist"])


def render_html(plan: dict) -> str:
    total = sum(len(m["checklist"]) for m in plan["milestones"])
    done = sum(1 for m in plan["milestones"] for it in m["checklist"] if it["checked"])
    pct = round(100 * done / total) if total else 0
    ms_total = len(plan["milestones"])
    ms_done = sum(1 for m in plan["milestones"] if is_complete(m))
    status_count = len(plan["status"])

    first_open_idx = next(
        (idx for idx, m in enumerate(plan["milestones"]) if not is_complete(m)),
        None,
    )

    toc_milestones: list[str] = []
    for idx, m in enumerate(plan["milestones"], start=1):
        label = m["toc"] or m["title"]
        ms_t = len(m["checklist"])
        ms_d = sum(1 for it in m["checklist"] if it["checked"])
        toc_milestones.append(
            f'<li><a class="ms-link" href="#ms-{idx}">'
            f'<span>M{idx} - {html.escape(label, quote=False)}</span>'
            f'<span class="toc-progress" data-ms-progress="ms-{idx}">{ms_d}/{ms_t}</span></a></li>'
        )

    status_items: list[str] = []
    for entry in plan["status"]:
        if entry["date"]:
            status_items.append(
                f'<li><span class="date">{html.escape(entry["date"], quote=False)}</span>{inline_md(entry["body"])}</li>'
            )
        else:
            status_items.append(f"<li>{inline_md(entry['body'])}</li>")
    status_html = (
        '<ul class="timeline">' + "".join(status_items) + "</ul>"
        if status_items
        else '<p style="color: var(--muted); margin: 0;">No status entries yet.</p>'
    )

    ms_sections: list[str] = []
    for idx, m in enumerate(plan["milestones"], start=1):
        complete = is_complete(m)
        badge_class = "done" if complete else "pending"
        badge_label = "Complete" if complete else "Pending"
        ms_t = len(m["checklist"])
        ms_d = sum(1 for it in m["checklist"] if it["checked"])
        ms_pct = round(100 * ms_d / ms_t) if ms_t else 0
        open_attr = " open" if (idx - 1) == first_open_idx else ""

        accept_items = "".join(
            f"<li>{inline_md(b)}</li>" for b in m["acceptance"]
        )
        accept_html = (
            f'<div class="acceptance"><ul>{accept_items}</ul></div>'
            if accept_items
            else ""
        )

        checklist_items: list[str] = []
        for it in m["checklist"]:
            checked_attr = " checked" if it["checked"] else ""
            cmd_html = ""
            if it["command"]:
                cmd_html = (
                    '<details class="collapse"><summary>show command</summary>'
                    f'<pre><code>{html.escape(it["command"], quote=False)}</code></pre>'
                    "</details>"
                )
            checklist_items.append(
                f'<li><input type="checkbox" disabled{checked_attr}>'
                f'<span class="task-text">{inline_md(it["text"])}</span>'
                f"{cmd_html}</li>"
            )
        checklist_html = (
            f'<details class="review-fold"{open_attr}>'
            f"<summary>Checklist {ms_d}/{ms_t}</summary>"
            f'<div class="checklist"><ul>{"".join(checklist_items)}</ul></div>'
            "</details>"
        )

        ms_sections.append(
            f'<article class="section" id="ms-{idx}">'
            f'<div class="ms-header">'
            f'<h2><span class="ms-num">Milestone {idx}</span>{html.escape(m["title"], quote=False)}</h2>'
            f'<span class="badge {badge_class}">{badge_label}</span>'
            "</div>"
            f'<div class="ms-progress"><div class="ms-progress-bar" style="width:{ms_pct}%"></div></div>'
            f'<p class="goal"><strong>Goal:</strong> {inline_md(m["goal"])}</p>'
            '<div class="subhead">Acceptance Criteria</div>'
            f"{accept_html}"
            f"{checklist_html}"
            "</article>"
        )

    title_esc = html.escape(plan["title"], quote=False)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title_esc}</title>
<style>{CSS}</style>
</head>
<body>
<a class="skip-link" href="#main">Skip to main content</a>
<div class="layout">
<nav class="toc">
  <h2>Contents</h2>
  <ul>
    <li><a href="#status"><span>Status</span><span class="toc-progress" data-status-count>{status_count}</span></a></li>
    <li><a href="#milestones"><span>Milestones</span><span class="toc-progress" data-total-progress>{done}/{total}</span></a></li>
    <li>
      <ul>
        {"".join(toc_milestones)}
      </ul>
    </li>
  </ul>
</nav>
<main id="main">

<header class="hero">
  <h1>{title_esc}</h1>
  <p class="lede">{inline_md(plan["lede"])}</p>
  <div class="hero-meta">
    <div class="stat">
      <div class="stat-label">Milestones</div>
      <div class="stat-value" data-stat="milestones">{ms_done} / {ms_total}</div>
    </div>
    <div class="stat">
      <div class="stat-label">Tasks complete</div>
      <div class="stat-value" data-stat="tasks">{done} / {total}</div>
    </div>
    <div class="stat">
      <div class="stat-label">Overall progress</div>
      <div class="stat-value" data-stat="percent">{pct}%</div>
    </div>
    <div class="stat">
      <div class="stat-label">Status updates</div>
      <div class="stat-value" data-stat="status">{status_count}</div>
    </div>
  </div>
</header>

<section class="section" id="status">
  <h2>Status</h2>
  {status_html}
</section>

<section class="section unframed" id="milestones"><h2>Milestones</h2>

{"".join(ms_sections)}

</section>
</main>
</div>
<a href="#" class="totop" id="totop" title="Back to top" aria-label="Back to top">↑</a>
<script>{JS}</script>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("plan", type=Path, help="Path to the Markdown plan file")
    ap.add_argument("-o", "--output", type=Path, help="Output HTML path (default: sibling .html)")
    args = ap.parse_args()

    if not args.plan.is_file():
        print(f"error: plan file not found: {args.plan}", file=sys.stderr)
        return 2

    text = args.plan.read_text(encoding="utf-8")
    try:
        plan = parse_plan(text)
    except PlanParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    out = args.output or args.plan.with_suffix(".html")
    out.write_text(render_html(plan), encoding="utf-8")
    print(f"Wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
