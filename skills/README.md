# Skills Catalog

Each skill is a self-contained workflow that Claude Code loads on demand when your request matches its triggers. Most install by copying `SKILL.md` to `~/.claude/skills/<skill-name>/SKILL.md`; the two flagged exceptions install differently per their READMEs.

## Available Skills

### Content Creation

| Skill | What It Does |
|-------|-------------|
| [beamer](beamer/) | Generate, edit, audit, or convert-to-PPTX LaTeX Beamer slide decks with TikZ figures and a four-step compile-audit-fix cycle |
| [slides-content](slides-content/) | End-to-end pipeline: source document (PDF, markdown, text) to compiled presentation slides |
| [diagram-pdf](diagram-pdf/) | Generate standalone TikZ diagrams (pipelines, hierarchies, cycles, hub-and-spoke, thematic) compiled to PDF, with an independent audit agent |

### Analysis

| Skill | What It Does |
|-------|-------------|
| [ai-council](ai-council/) | Pressure-test a decision or argument through a structured five-advisor deliberation |
| [ai-council-deep](ai-council-deep/) | Interactive variant of ai-council with three user checkpoints for high-stakes decisions |
| [analyze-reply](analyze-reply/) | Fact-check a forwarded article, essay, or email, then draft a reply in your voice |

### Knowledge Management

| Skill | What It Does |
|-------|-------------|
| [split-pdf](split-pdf/) | Split and deeply read academic PDFs in 4-page chunks to avoid shallow comprehension |
| [summary-academic](summary-academic/) | Summarize an academic paper into a fixed nine-section, citation-backed structure |
| [summary-general](summary-general/) | Summarize a news article, blog post, video, or podcast, keeping the statistics and flagging weak claims |
| [knowledge-base](knowledge-base/) | Process, index, summarize, search, query, and health-check a personal document library, and build slides from any item |
| [knowledge-base-update](knowledge-base-update/) | Sync the knowledge-base index with disk; run a periodic health check |

### Process Guides

| Skill | What It Does |
|-------|-------------|
| [writing-voice-guide](writing-voice-guide/) *(process guide)* | How to create a consistent writing voice layer for your AI environment |
| [handoff-resume](handoff-resume/) *(protocol)* | Session continuity protocol for carrying project context across Claude Code sessions |
| [git-sync](git-sync/) *(recipe)* | Version your `~/.claude` environment with Git and sync two machines through a private GitHub repository |

### Administration

| Skill | What It Does |
|-------|-------------|
| [skill-audit](skill-audit/) | Audit recent session transcripts for recurring friction, sweep your skill files for a rule stated in more than one place, and recommend conservative, report-only changes |

## Dependencies

Some skills reference [style guides](../style-guides/) for formatting rules. If you install a skill that references a style guide, install the style guide too, or replace the reference with your own formatting standards.

## Customization

These skills are starting points. Adapt them to your own workflows:

- Change trigger phrases to match how you naturally ask for things
- Adjust quality gate criteria to match your standards
- Replace style guide references with your own formatting rules
- Add or remove pipeline steps as needed
