# Methodology: Structured AI Environments

This document explains the design principles behind the skills, templates, and workflows in this repository. It is not a tutorial; it is the reasoning behind the approach. Read this if you want to understand why the skills are built the way they are, not just how to use them.

## The Problem with Ad-Hoc AI Usage

Most knowledge workers interact with AI the same way every time: open a chat, write a prompt, get a response, close the chat. The next time they need similar work done, they start from scratch. This approach has predictable failure modes:

- **Corrections are forgotten.** You teach the AI to avoid a mistake in one session; the next session, it makes the same mistake.
- **Quality varies.** Output quality depends on how much context you remember to provide and how carefully you prompt. On a busy day, quality drops.
- **Repetitive work stays repetitive.** If you create the same type of document every week, you rewrite the same prompting instructions every week.
- **Context is wasted.** Long sessions fill the AI's context window with old conversation turns, degrading performance on new work.

A structured AI environment addresses these by separating persistent configuration from individual conversations.

## The Four-Layer Model

The skills in this repository are built on a four-layer architecture. Each layer serves a distinct purpose, and the interaction between layers is what makes the system more than the sum of its parts.

### Layer 1: Rules (CLAUDE.md)

**What it is:** A markdown file loaded into every conversation. It contains declarative instructions: writing standards, routing tables, delivery gates, and workflow protocols.

**Why it matters:** Rules are the cheapest form of persistent context. They cost one file read at session start and apply to every task in that session. A well-designed CLAUDE.md means you never need to re-explain your formatting preferences, citation style, or quality standards.

**Design principle:** Rules should be declarative, not procedural. "Always use Oxford commas" is a rule. "Step 1: check for Oxford commas, Step 2: add them if missing" is a procedure that belongs in a skill. A CLAUDE.md that grows too large becomes a liability; the AI loses track of critical instructions buried in noise.

### Layer 2: Reinforcement (Memories)

**What it is:** Structured notes that persist across sessions, capturing corrections, preferences, project context, and reference pointers.

**Why it matters:** Memories are how the system learns from mistakes. When you correct the AI once ("do not reduce font size to fit content; reduce content instead"), that correction is saved as a feedback memory and applied to all future sessions. Without memories, the same correction must be repeated every time.

**Design principle:** Memories complement rules. Rules declare the standard; memories capture the exceptions and edge cases discovered through use. A memory saying "integration tests must hit a real database, not mocks, because of the Q3 migration incident" carries context that a rule alone cannot.

### Layer 3: Execution (Skills)

**What it is:** Procedural workflow files that the AI loads on demand when a task matches the skill's triggers. Each skill specifies its own model, effort level, and step-by-step process.

**Why it matters:** Skills solve the repetition problem. Instead of re-explaining a multi-step workflow every time you create a slide deck or analyze student responses, you encode the workflow once. The AI loads it when relevant and follows the defined steps, including quality gates and audit steps that you might forget to request in an ad-hoc prompt.

**Design principle:** Skills are loaded on demand, not all at once. This keeps the context window clean. A user with 40 skills only loads the one or two relevant to the current task. Skills should be self-contained: each skill file includes everything the AI needs to execute that workflow, including references to style guides and audit checklists.

### Layer 4: Enforcement (Audit Agents)

**What it is:** Post-hoc quality checks built into skill workflows. After the AI produces output, an audit step reviews the output against defined criteria and flags defects.

**Why it matters:** AI output is confidently wrong often enough that automated checking is essential. A single-pass compilation of a LaTeX slide deck will often produce overlay positioning errors, font size violations, or citation formatting issues. The audit step catches these before the user sees them.

**Design principle:** Enforcement is separate from execution because the AI that produced the output is often blind to its own mistakes. Audit criteria should be explicit and checkable (font size minimums, citation format, content overflow), not subjective ("make it look good").

## How the Layers Interact

The four layers form a priority hierarchy:

1. **Rules** set the boundaries (always loaded, highest priority)
2. **Memories** refine the rules with learned corrections (loaded on demand)
3. **Skills** execute within those boundaries (loaded per task)
4. **Audit agents** verify compliance after execution (embedded in skills)

A correction discovered during an audit can become a memory (Layer 2) or, if it recurs, a rule (Layer 1). This feedback loop means the system improves with use.

## Skill Design Pattern

Every skill in this repository follows a common pattern:

1. **Frontmatter** declares metadata: name, description, when_to_use, model, and effort level. The `description` is what Claude reads to decide whether to load a skill at all, so the phrases that should invoke it belong there; `when_to_use` refines that choice in prose, by naming what belongs to this skill rather than to a neighboring one.
2. **Context loading** reads any prerequisite files (style guides, reference materials, project state)
3. **Execution steps** define the procedural workflow
4. **Quality gates** specify audit criteria and fix cycles
5. **Output** defines what the skill produces and where it goes

Skills reference style guides rather than embedding formatting rules. This means updating a color palette or font standard in one place propagates to all skills that reference it.

## Context Management

The AI's context window is a finite resource. Every instruction, file read, conversation turn, and skill file consumes space. When the window fills, the AI either drops earlier context (losing important instructions) or compacts by summarizing its own progress (losing details).

Effective context management strategies:

- **Load skills on demand.** Do not put procedural steps in CLAUDE.md if they belong in a skill.
- **Use handoffs between sessions.** A structured handoff captures key decisions, file paths, and next steps so the next session starts with relevant context rather than re-reading everything.
- **Separate planning from execution.** Plan the approach in one session, then execute in a fresh session with clean context.
- **Keep CLAUDE.md concise.** Rules that are never used should be removed. Verbose explanations should become skills or memories.

## When to Use Skills vs. Ad-Hoc Prompting

Skills are worth the investment when:

- You perform the same type of task more than twice
- The task has quality criteria that you tend to forget or skip under time pressure
- The task involves multiple steps that must happen in a specific order
- Output consistency matters (the same type of document should look the same every time)

Ad-hoc prompting is fine when:

- The task is genuinely one-time
- You are exploring or brainstorming, not producing a deliverable
- The task is simple enough that a single prompt produces acceptable output

## Feedback Memory in Practice

The most underrated component of a structured AI environment is feedback memory. Here is how it works in practice:

1. You notice the AI made a mistake (reduced font size instead of reducing content)
2. You correct the AI in the conversation
3. The correction is saved as a feedback memory with context on why the correction matters
4. In every future session, the AI checks its feedback memories and applies the correction proactively

Over time, the system accumulates a library of learned corrections specific to your work. This is not generic AI improvement; it is customized to your standards, your domain, and your recurring failure modes.
