# Skill Audit

Read your recent Claude Code sessions for recurring friction, then recommend conservative changes to your skills and configuration. Report-only: it proposes, it never edits.

## Problem

If you build and maintain a library of personal Claude Code skills, the same friction tends to show up again and again: you correct the same preference across sessions, the wrong skill fires and you redirect it, you re-explain a procedure you have explained before, or a rule that used to be followed quietly stops being followed after a model upgrade. Each instance is small, so none of them gets fixed, and the friction compounds.

The hard part is not noticing one annoyance. It is seeing the pattern across weeks of sessions, separating a genuine gap from a rule that already exists but was not followed, and resisting the urge to "fix" everything with new rules that add clutter without adding adherence.

## Approach

The skill reads your session transcripts over a time window, extracts the turns where you pushed back or repeated yourself, and looks for friction that recurs across multiple sessions. A one-off correction is noise; the same correction in four sessions is a signal.

Two design commitments keep it honest. First, it is **report-only**: it has no Edit or Write tool, so it physically cannot change your configuration. It proposes; you decide; the edits happen later as a separate, deliberate step. Second, before recommending anything it **verifies the current state** of the relevant file. A recurring problem usually means one of three things, and they need different responses: the rule does not exist (a real gap), the rule exists but was not followed (an enforcement problem, not a content edit), or the plumbing is misconfigured (a config fix). Skipping that check is how an audit manufactures busywork, so the skill treats it as mandatory.

It also remembers across runs. Two small state files record what you have already declined and what prior audits have already fixed, so the same rejected idea does not resurface every week.

## The Flow

1. **Read state.** Load the declined-findings file and the changes ledger so the run does not re-propose something you already rejected or already fixed.
2. **Enumerate transcripts.** List the session JSONL files in the window (default 7 days, or a day count you pass), grouped by project, skipping internal subagent transcripts and the current session.
3. **Extract and scan.** Pull the human-authored turns, ignore tool noise and system messages, and look for corrections, redirects, reprompts, and permission friction. For large volumes, fan out one read-only subagent per project cluster.
4. **Synthesize.** Pool the findings, dedup, rank by evidence, and drop one-offs.
5. **Verify.** For each candidate, open the actual skill, CLAUDE.md, protocol, or settings file and classify it as a missing rule, an enforcement gap, or a config fix.
6. **Sweep for consistency.** Alongside the transcript scan, check each family of skills that shares a standard for a rule stated in more than one file, a dated attribution older than a later decision on the same subject, a reference file nothing points at, and a pointer to a file that does not exist. Transcripts show what already went wrong; this shows what will go wrong the next time a shared standard changes.
7. **Filter.** Remove anything already declined or already fixed, noting recurrence instead.
8. **Report and stop.** Present a ranked report with verbatim evidence quotes, a recommended action class, and a confidence level for each finding, capped to a short list. Then ask which to act on. Nothing is edited.

## Usage

**Trigger phrases:** `skill audit`, `audit my skills`, `audit recent sessions`, `audit skills`, `skill opportunities`, `audit recent work`

**Good uses:**
- A periodic review of where your skills and rules are causing repeated friction
- The first run right after a model upgrade, to catch rules that quietly stopped being followed (invoke under the strongest available model for this case)
- Deciding whether a recurring annoyance is worth a new skill or a tightened existing one
- Right after a session that edited several skills, which is when a standard gets restated somewhere new and is cheapest to catch

**Not good uses:**
- Auditing a project's source code or a shared team repo (the skill is scoped to your personal configuration only)
- Expecting it to make the changes for you (it is report-only by design)

**Tips:**
- Pass a wider window (for example, `30`) for a less frequent, deeper review.
- After you rule on the findings, record declines and applied fixes in the two state files so future runs stay clean.
- Treat "recommend nothing" as a good outcome, not a failed run.

## Installation

1. Copy `SKILL.md` to `~/.claude/skills/skill-audit/SKILL.md`.
2. Restart Claude Code (or start a new session).
3. The skill activates on any trigger phrase above. It creates its two state files (`declined.md`, `changes.md`) in its own folder on first use.

## Output

A ranked, report-only analysis in the session. Each finding carries a title, a friction category, the sessions it appeared in, one to three verbatim quotes as evidence, a recommended action class, and a confidence level. No files are changed. After you decide, the declined-findings file and the changes ledger are updated by hand as a separate step.

## Design Rationale

**Report-only, enforced by tool scope.** The skill is granted no Edit or Write tool. This is not a convention you have to trust; it is a capability boundary. The audit cannot edit your configuration even if it wanted to, which keeps the propose-then-decide separation real.

**Verify before recommending.** The single most valuable step is checking the current state of a file before proposing a change to it. Most recurring problems are enforcement gaps, not missing rules, and re-adding a rule that already exists makes the configuration worse, not better.

**Recurrence over severity.** The skill ranks by how often friction repeats across sessions, not by how irritating any single instance felt. Patterns are fixable; one bad moment usually is not.

**Memory across runs.** Without the declined and changes files, every run would resurface the same rejected ideas. Recording decisions makes the audit converge over time instead of nagging.

**A bias toward no change.** New rules have a cost: they crowd the configuration and dilute the rules that matter. The skill is explicitly told to prefer no change, to narrow broad ideas, and to cap how much it proposes per run.
