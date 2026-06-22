from __future__ import annotations

import html as _html
from . import report as _report

_MAX_COMMITS_GLOBAL = 15
_MAX_COMMITS_PROJECT = 5
_MAX_TOOLS_GLOBAL = 8
_MAX_TOOLS_PROJECT = 5

# Inlined from bhuvanesh_content_studio/design-system/foundation/tokens.css
# Bundled for portability — the report HTML is self-contained.
_TOKENS_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Mono:wght@400;700&display=swap');

:root {
  --ink:        #0F0F0F;
  --ink-soft:   #1A1A1A;
  --paper:      #F4F1EB;
  --bone:       #FFFFFF;
  --violet:     #5B21B6;
  --violet-2:   #A78BFA;
  --gray:       #9C9A9A;
  --gray-100:   #F8F7F7;
  --gray-900:   #0D0D0D;

  --glass-fill:        rgba(255,255,255,0.04);
  --glass-fill-2:      rgba(255,255,255,0.06);
  --glass-border:      rgba(255,255,255,0.08);
  --glass-border-2:    rgba(255,255,255,0.12);
  --accent-glow:       rgba(91,33,182,0.07);
  --accent-glow-2:     rgba(91,33,182,0.15);
  --accent-cta-shadow: rgba(91,33,182,0.35);

  --bg:        #0F0F0F;
  --bg-soft:   #1A1A1A;
  --bg-card:   rgba(255,255,255,0.04);
  --fg:        #FFFFFF;
  --fg-1:      rgba(255,255,255,0.92);
  --fg-2:      rgba(255,255,255,0.55);
  --fg-3:      rgba(255,255,255,0.30);
  --border:    rgba(255,255,255,0.08);
  --border-2:  rgba(255,255,255,0.12);
  --accent:    #5B21B6;
  --accent-fg: #FFFFFF;

  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'Space Mono', ui-monospace, 'SF Mono', Menlo, monospace;

  --lh-snug:  1.15;
  --lh-loose: 1.6;
  --ls-tight:    -0.02em;
  --ls-tightest: -0.05em;
  --ls-wide:      0.18em;

  --radius-sm:   8px;
  --radius-md:   16px;
  --radius-pill: 999px;

  --shadow-glass-sm: 0 8px 24px rgba(0,0,0,0.25);
  --shadow-brut:     6px 6px 0 #0D0D0D;
}

[data-style="brutalism"] {
  --bg:      #F4F1EB;
  --bg-soft: #FFFFFF;
  --bg-card: #FFFFFF;
  --fg:      #0D0D0D;
  --fg-1:    #0D0D0D;
  --fg-2:    rgba(13,13,13,0.7);
  --fg-3:    rgba(13,13,13,0.5);
  --border:  #0D0D0D;
}
"""

_PAGE_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: var(--font-sans);
  font-size: 16px;
  line-height: var(--lh-loose);
  color: var(--fg);
  background: var(--bg);
  -webkit-font-smoothing: antialiased;
  transition: background 0.22s, color 0.22s;
}

.stripe-top {
  height: 4px;
  background: linear-gradient(90deg, var(--accent), transparent 70%);
  position: sticky; top: 0; z-index: 100;
}
[data-style="brutalism"] .stripe-top { background: var(--accent); height: 6px; }

.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 64px;
  border-bottom: 1px solid var(--border);
}
.wordmark {
  font-family: var(--font-mono); font-weight: 700; font-size: 13px;
  letter-spacing: 0.12em; text-transform: uppercase; color: var(--fg-2);
}
.wordmark b { color: var(--accent); }

.toggle {
  font-family: var(--font-mono); font-weight: 700; font-size: 10px;
  letter-spacing: var(--ls-wide); text-transform: uppercase;
  background: transparent; color: var(--fg-2);
  border: 1px solid var(--border-2);
  padding: 8px 16px; border-radius: var(--radius-sm); cursor: pointer;
  transition: color 0.2s, border-color 0.2s;
}
.toggle:hover { color: var(--fg); border-color: var(--accent); }
[data-style="brutalism"] .toggle {
  border: 2px solid var(--border); border-radius: 0;
  box-shadow: 3px 3px 0 var(--border);
}

.wrap { max-width: 1100px; margin: 0 auto; padding: 64px 64px 96px; }

.page-header { margin-bottom: 64px; }
.eyebrow {
  font-family: var(--font-mono); font-weight: 700; font-size: 11px;
  letter-spacing: var(--ls-wide); text-transform: uppercase; color: var(--fg-3);
  margin-bottom: 12px;
}
.eyebrow .dot { color: var(--accent); margin: 0 8px; }
.page-header h1 {
  font-weight: 800; font-size: clamp(40px, 5.5vw, 56px);
  line-height: var(--lh-snug); letter-spacing: var(--ls-tightest); color: var(--fg);
}
.page-header h1 .accent { color: var(--accent); }

.stats-row {
  display: flex; gap: 48px; flex-wrap: wrap;
  margin-bottom: 64px; padding-bottom: 48px;
  border-bottom: 1px solid var(--border);
}
.stat .n {
  font-weight: 900; font-size: clamp(32px, 3.5vw, 40px);
  line-height: 1; letter-spacing: var(--ls-tight); color: var(--fg);
}
.stat .n .accent { color: var(--accent); }
.stat .l {
  font-family: var(--font-mono); font-size: 10px;
  letter-spacing: var(--ls-wide); text-transform: uppercase;
  color: var(--fg-3); margin-top: 4px;
}
.stat .note {
  font-size: 10px; color: var(--fg-3); margin-top: 2px;
  font-family: var(--font-mono);
}

.section { margin-bottom: 48px; }
.section-label {
  font-family: var(--font-mono); font-weight: 700; font-size: 11px;
  letter-spacing: var(--ls-wide); text-transform: uppercase;
  color: var(--fg-3); margin-bottom: 16px;
}

.card {
  background: var(--glass-fill); border: 1px solid var(--border);
  border-radius: var(--radius-md); backdrop-filter: blur(40px);
  box-shadow: var(--shadow-glass-sm); padding: 24px 32px;
}
[data-style="brutalism"] .card {
  background: var(--bone, #fff); border: 3px solid var(--border);
  border-radius: 0; box-shadow: var(--shadow-brut); backdrop-filter: none;
}

.card-stripe {
  height: 3px; border-radius: 2px 2px 0 0;
  background: linear-gradient(90deg, var(--accent), transparent);
  margin: -24px -32px 20px;
}
[data-style="brutalism"] .card-stripe {
  background: var(--accent); height: 5px; border-radius: 0;
}

/* Tools */
.tool-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.tag {
  display: inline-flex; align-items: center; gap: 6px;
  font-family: var(--font-mono); font-weight: 700; font-size: 10px;
  letter-spacing: var(--ls-wide); text-transform: uppercase;
  padding: 6px 14px; border-radius: var(--radius-pill);
  background: var(--glass-fill-2); color: var(--fg-2);
  border: 1px solid var(--border);
}
.tag .dot { color: var(--accent); font-size: 7px; }
.tag .tag-count { color: var(--fg-3); font-weight: 400; margin-left: 4px; }
.tag.top-tag { background: var(--accent-glow-2); color: var(--violet-2); border-color: transparent; }
.tag.top-tag .tag-count { color: var(--violet-2); opacity: 0.7; }
[data-style="brutalism"] .tag {
  border-radius: 0; border: 2px solid var(--border);
  background: var(--gray-100, #f8f7f7); color: var(--gray-900, #0d0d0d);
}
[data-style="brutalism"] .tag.top-tag {
  background: var(--accent); color: var(--bone, #fff);
  border-color: var(--border); box-shadow: 3px 3px 0 var(--border);
}
[data-style="brutalism"] .tag.top-tag .tag-count { color: rgba(255,255,255,0.7); }

/* Projects grid */
.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
  gap: 20px;
}
.project-card .card { height: 100%; }
.project-name {
  font-weight: 700; font-size: 18px;
  letter-spacing: var(--ls-tight); color: var(--fg); margin-bottom: 16px;
}
.project-stats-row { display: flex; gap: 24px; margin-bottom: 16px; flex-wrap: wrap; }
.ps .ps-v {
  font-weight: 800; font-size: 24px; line-height: 1;
  letter-spacing: var(--ls-tight); color: var(--fg);
}
.ps .ps-k {
  font-family: var(--font-mono); font-size: 9px;
  letter-spacing: var(--ls-wide); text-transform: uppercase;
  color: var(--fg-3); margin-top: 3px;
}

/* Commits */
.commit-list { display: flex; flex-direction: column; gap: 4px; margin-top: 12px; }
.commit-item {
  font-family: var(--font-mono); font-size: 11px; color: var(--fg-2);
  display: flex; gap: 8px; align-items: flex-start; line-height: 1.5;
}
.commit-hash { color: var(--accent); flex-shrink: 0; font-weight: 700; }
[data-style="brutalism"] .commit-hash { color: var(--violet); }

.commit-full-list { display: flex; flex-direction: column; }
.commit-full-item {
  font-family: var(--font-mono); font-size: 12px; color: var(--fg-2);
  display: flex; gap: 12px; align-items: baseline;
  padding: 10px 0; border-bottom: 1px solid var(--border);
}
.commit-full-item:last-of-type { border-bottom: none; }
.commit-full-hash { color: var(--accent); font-weight: 700; flex-shrink: 0; }
[data-style="brutalism"] .commit-full-hash { color: var(--violet); }
.commit-full-msg { color: var(--fg-1); line-height: 1.5; }
[data-style="brutalism"] .commit-full-msg { color: var(--gray-900, #0d0d0d); }
.commit-project-tag {
  flex-shrink: 0; font-size: 9px; padding: 2px 8px;
  border-radius: var(--radius-pill);
  background: var(--accent-glow-2); color: var(--violet-2);
  margin-left: auto; white-space: nowrap;
}
[data-style="brutalism"] .commit-project-tag {
  background: var(--accent); color: var(--bone, #fff); border-radius: 0;
}
.commit-more {
  font-family: var(--font-mono); font-size: 11px; color: var(--fg-3);
  padding: 10px 0; text-align: center; letter-spacing: 0.05em;
}

.no-data {
  font-family: var(--font-mono); font-size: 11px;
  color: var(--fg-3); font-style: italic; padding: 8px 0;
}

/* AI sections */
.ai-summary-text {
  font-size: 16px; line-height: var(--lh-loose);
  color: var(--fg-1); white-space: pre-wrap;
}
.ai-block { margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border); }
.ai-label {
  font-family: var(--font-mono); font-weight: 700; font-size: 9px;
  letter-spacing: var(--ls-wide); text-transform: uppercase;
  color: var(--fg-3); margin-bottom: 8px;
}
.ai-text { font-size: 13px; line-height: 1.65; color: var(--fg-2); white-space: pre-wrap; }
.ai-unavail { color: var(--fg-3); font-style: italic; font-size: 13px; }

/* Footer */
.page-footer {
  display: flex; align-items: center; justify-content: space-between;
  padding-top: 32px; border-top: 1px solid var(--border);
  font-family: var(--font-mono); font-size: 10px;
  letter-spacing: var(--ls-wide); text-transform: uppercase; color: var(--fg-3);
}
.page-footer .slash { color: var(--accent); }
"""


def _e(s: object) -> str:
    return _html.escape(str(s))


def _fmt(n: int) -> str:
    return f"{n:,}"


def _commit_hash(commit: dict) -> str:
    return (commit.get("meta", {}).get("commit", "") or "")[:8]


def _render_commit_list(commits: list, max_shown: int, show_project: bool) -> str:
    rows: list[str] = []
    shown = commits[:max_shown]
    for c in shown:
        h = _commit_hash(c)
        msg = _e(c.get("summary", ""))
        proj = _e(c.get("project", "") or "")
        proj_tag = (
            f'<span class="commit-project-tag">{proj}</span>'
            if show_project and proj else ""
        )
        rows.append(
            f'<div class="commit-full-item">'
            f'<span class="commit-full-hash">{h}</span>'
            f'<span class="commit-full-msg">{msg}</span>'
            f'{proj_tag}'
            f'</div>'
        )
    remaining = len(commits) - max_shown
    if remaining > 0:
        rows.append(
            f'<div class="commit-more">… and {remaining} more commit'
            f'{"s" if remaining > 1 else ""} not shown</div>'
        )
    return "\n".join(rows)


def _render_short_commits(commits: list, max_shown: int) -> str:
    if not commits:
        return '<div class="no-data">No commits tracked this period</div>'
    rows: list[str] = []
    shown = commits[:max_shown]
    for c in shown:
        h = _commit_hash(c)
        msg = _e(c.get("summary", ""))
        rows.append(
            f'<div class="commit-item">'
            f'<span class="commit-hash">{h}</span>'
            f'<span class="commit-msg">{msg}</span>'
            f'</div>'
        )
    remaining = len(commits) - max_shown
    if remaining > 0:
        rows.append(f'<div class="no-data">… and {remaining} more</div>')
    return "\n".join(rows)


def _render_tool_tags(tools, max_shown: int) -> str:
    tags: list[str] = []
    for i, (name, count) in enumerate(tools.most_common(max_shown)):
        cls = "tag top-tag" if i == 0 else "tag"
        tags.append(
            f'<span class="{cls}">'
            f'<span class="dot">●</span> {_e(name)}'
            f'<b class="tag-count">{_fmt(count)}</b>'
            f'</span>'
        )
    return "\n".join(tags)


def _render_project_card(project: str, proj_stats: dict, label: str,
                          engine_fn) -> str:
    sessions = len(proj_stats["sessions"])
    commits = proj_stats["commits"]
    prompts = proj_stats["prompts"]
    tool_use = proj_stats["tool_use"]
    duration = proj_stats["duration_min"]

    commit_html = _render_short_commits(commits, _MAX_COMMITS_PROJECT)

    ai_html = ""
    if engine_fn is not None:
        text = engine_fn(_report.build_project_ai_prompt(project, proj_stats, label))
        if text:
            ai_html = (
                f'<div class="ai-block">'
                f'<div class="ai-label">AI Explanation</div>'
                f'<div class="ai-text">{_e(text.strip())}</div>'
                f'</div>'
            )
        else:
            ai_html = '<div class="ai-block ai-unavail">AI explanation unavailable</div>'

    return (
        f'<div class="project-card">'
        f'<div class="card">'
        f'<div class="card-stripe"></div>'
        f'<div class="eyebrow">{_e(project)}</div>'
        f'<div class="project-stats-row">'
        f'<div class="ps"><div class="ps-v">{sessions}</div><div class="ps-k">Sessions</div></div>'
        f'<div class="ps"><div class="ps-v">{prompts}</div><div class="ps-k">Prompts</div></div>'
        f'<div class="ps"><div class="ps-v">{_fmt(tool_use)}</div><div class="ps-k">Tools</div></div>'
        f'<div class="ps"><div class="ps-v">{duration}</div><div class="ps-k">Min</div></div>'
        f'<div class="ps"><div class="ps-v">{len(commits)}</div><div class="ps-k">Commits</div></div>'
        f'</div>'
        f'<div class="commit-list">{commit_html}</div>'
        f'{ai_html}'
        f'</div>'
        f'</div>'
    )


def render_html(stats: dict, label: str, evs: list,
                engine_fn=None, detailed: bool = False) -> str:
    sessions = len(stats["sessions"])
    prompts = stats["prompts"]
    tool_use = stats["tool_use"]
    duration_min = stats["duration_min"]
    commits = stats["commits"]
    projects = stats["projects"]
    tools = stats["tools"]
    total_commits = len(commits)

    # AI session time note: accumulated across parallel AI sessions
    hours = duration_min // 60
    mins = duration_min % 60
    time_display = f"{hours}h {mins}m" if hours else f"{mins}m"

    # top tools
    tools_html = _render_tool_tags(tools, _MAX_TOOLS_GLOBAL) if tools else '<span class="no-data">No tool data</span>'

    # global commits
    commits_label = (
        f"Commits — {total_commits} total, showing {min(total_commits, _MAX_COMMITS_GLOBAL)}"
        if total_commits > _MAX_COMMITS_GLOBAL
        else f"Commits — {total_commits} total"
    )
    commits_html = _render_commit_list(commits, _MAX_COMMITS_GLOBAL, show_project=True)
    if not commits_html:
        commits_html = '<div class="no-data">No commits this period</div>'

    # AI summary
    ai_summary_html = ""
    if engine_fn is not None:
        text = engine_fn(_report.build_ai_prompt(stats, label))
        if text:
            ai_summary_html = (
                f'<div class="section">'
                f'<div class="section-label">AI Summary</div>'
                f'<div class="card">'
                f'<div class="card-stripe"></div>'
                f'<div class="ai-summary-text">{_e(text.strip())}</div>'
                f'</div>'
                f'</div>'
            )
        else:
            ai_summary_html = (
                '<div class="section">'
                '<div class="section-label">AI Summary</div>'
                '<div class="card ai-unavail">AI summary unavailable — engine not found or failed.</div>'
                '</div>'
            )

    # per-project cards
    projects_html = ""
    if detailed and projects:
        cards = [
            _render_project_card(p, _report.build_project_stats(evs, p), label, engine_fn)
            for p in sorted(projects.keys())
        ]
        projects_html = (
            f'<div class="section">'
            f'<div class="section-label">Projects — {len(projects)} active this period</div>'
            f'<div class="projects-grid">{"".join(cards)}</div>'
            f'</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>devlog // {_e(label)}</title>
<style>
{_TOKENS_CSS}
{_PAGE_CSS}
</style>
</head>
<body>
<div class="stripe-top"></div>

<div class="topbar">
  <div class="wordmark">devlog <b>//</b></div>
  <button class="toggle"
    onclick="document.body.dataset.style = document.body.dataset.style === 'brutalism' ? '' : 'brutalism'">
    Toggle Mode
  </button>
</div>

<div class="wrap">

  <header class="page-header">
    <div class="eyebrow">{_e(label.upper())}</div>
    <h1>Work Journal<span class="accent">.</span></h1>
  </header>

  <div class="stats-row">
    <div class="stat">
      <div class="n">{_fmt(sessions)}</div>
      <div class="l">Sessions</div>
    </div>
    <div class="stat">
      <div class="n">{_fmt(prompts)}</div>
      <div class="l">Human Prompts</div>
    </div>
    <div class="stat">
      <div class="n">{_fmt(tool_use)}</div>
      <div class="l">Tool Calls</div>
    </div>
    <div class="stat">
      <div class="n">{_e(time_display)}</div>
      <div class="l">AI Session Time</div>
      <div class="note">accumulated · may exceed 24h/day</div>
    </div>
    <div class="stat">
      <div class="n">{_fmt(total_commits)}</div>
      <div class="l">Commits</div>
    </div>
    <div class="stat">
      <div class="n">{len(projects)}</div>
      <div class="l">Projects</div>
    </div>
  </div>

  <div class="section">
    <div class="section-label">Top Tools</div>
    <div class="tool-tags">{tools_html}</div>
  </div>

  {ai_summary_html}

  {projects_html}

  <div class="section">
    <div class="section-label">{_e(commits_label)}</div>
    <div class="card">
      <div class="commit-full-list">{commits_html}</div>
    </div>
  </div>

  <footer class="page-footer">
    <span>devlog <span class="slash">//</span> {_e(label)}</span>
    <span>
      {_fmt(sessions)} sessions
      <span class="slash">·</span> {len(projects)} projects
      <span class="slash">·</span> {_fmt(total_commits)} commits
    </span>
  </footer>

</div>
</body>
</html>"""
