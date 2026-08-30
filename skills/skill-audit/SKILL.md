---
name: skill-audit
description: Audit recent Claude Code session transcripts for recurring friction (repeated corrections, routing misfires, repeated reprompts, enforcement gaps, post-upgrade regressions) and sweep your skill files for a standard stated in more than one place, orphaned reference files, and broken pointers, then recommend conservative changes to your personal skills, CLAUDE.md, protocols, or settings. Report-only: it proposes, it never edits. Prefers no change. Triggers on "skill audit", "audit my skills", "audit recent sessions".
when_to_use: Use when the user asks for a skill audit, an audit of their skills, an audit of recent sessions or recent work, or a review of where their own configuration is causing repeated friction. Use it also for the first run after a model upgrade, when the point is catching rules that quietly stopped being followed, and after a session that edited several skills, when a shared standard has most likely been restated somewhere new.
allowed-tools: Bash, Read, Glob, Grep, Agent
model: sonnet
argument-hint: [days, default 7]
---

# Skill Audit

Audit recent Claude Code session transcripts for recurring friction and recommend conservative changes to your personal configuration. This skill **proposes only; it never edits anything**. Prefer no change. "Recommend nothing" is a valid and common result.

## Argument
- No argument: scan the last **7 days**.
- A number: scan that many days (for example, `14`).

## Model
Runs on a mid-tier model by default, which is sufficient given the report-only design and the mandatory verification step below. For the run right after a model upgrade, when catching regressions is the point, invoke under the strongest available model.

## Report-only contract
This skill reads transcripts and configuration and produces a report. It does not change any file. After you rule on the findings, the actual edits and the two log updates (below) are made as a separate, deliberate step outside this skill.

## State files (in this skill's folder)
- `declined.md`: findings you have ruled "do not pursue." **Read this first, every run.** Do not re-recommend a matching item. If the friction still recurs, note it as "previously declined, still occurring," without re-proposing the fix.
- `changes.md`: the ledger of changes prior audits have driven. **Read this too.** Do not re-flag something already fixed; if it recurs despite a fix, say so, because the fix may not have held.

Both files ship with this skill, already carrying their headers and column names, and both start with no rows. If one is missing, say so in the report and continue the run; do not create it, because this skill writes nothing.

## Procedure

### Phase 0: Read state
Read `declined.md` and `changes.md` in this skill's folder so the run knows what has been declined and what has already been fixed.

### Phase 1: Enumerate transcripts
Session transcripts are JSONL files under `~/.claude/projects/<encoded-project-dir>/`. List the ones in the window:
```bash
find ~/.claude/projects -maxdepth 2 -name "*.jsonl" -mtime -<days> -type f -exec stat -f '%Sm %z %N' -t '%Y-%m-%d' {} + | sort -r
```
The `stat` form above is the BSD one macOS ships, and it is the recipe here because it depends only on `stat`, not on which `find` implementation is on your path.

Scan **top-level** session files. A session's subagent transcripts and tool results sit in a per-session subfolder beside it (`<session-id>/subagents/` and `<session-id>/tool-results/`), which the `-maxdepth 2` above already excludes. They are internal and low signal; leave them out unless a main thread points at one.

**Skip the current session's own transcript** to avoid self-reference. The running session id is in `$CLAUDE_CODE_SESSION_ID`, and it is the transcript filename stem, so exclude `<that id>.jsonl`:
```bash
[ -n "$CLAUDE_CODE_SESSION_ID" ] && echo "exclude: $CLAUDE_CODE_SESSION_ID.jsonl"
```
If that variable is empty in your environment, fall back to modification time: the live transcript is the one file in the current project's directory whose `stat` timestamp advances between two listings taken a few seconds apart. Exclude that file instead.

Group the remaining files by their project directory and gauge total volume.

### Phase 2: Extract and scan
If the volume is small (a few small files), read and scan directly. If it is large (several files, or more than a few MB), **fan out one read-only subagent per project cluster**: merge directories that hold only tiny stubs, and split any single directory whose files exceed about 15 MB across two agents.

Sample one real user record first to confirm the jq path. The first line of a transcript is a metadata record with no `message` key, so selecting on the record type has to come before taking the first result:
```bash
jq -c 'select(.type=="user")' <file> | head -1 | jq '.message | keys'
```
Then give each agent the friction schema below and this extraction recipe:
```bash
# human-authored turns only
jq -rc 'select(.type=="user") | (.message.content // .content) | if type=="string" then . else (map(select(.type?=="text")|.text)|join("\n")) end' <file> 2>/dev/null
```
Ignore noise: tool results, and lines beginning with `<command-`, `<system-reminder`, `<local-command`, `Caveat:`, or `[Request interrupted`. Also grep skill invocations and permission denials to assess routing. Each agent returns structured findings with verbatim user quotes (under about 25 words each), tagged with the file basename.

### Phase 3: Synthesize
Pool the findings. The strongest signal is friction that **recurs across multiple sessions or clusters**. Dedup, rank by evidence, and drop one-offs. A single unusual correction is noise, not a skill opportunity.

### Phase 4: Verify before recommending (mandatory)
For every candidate fix, open the relevant skill, CLAUDE.md, protocol, or settings file and confirm the current state **before** proposing anything. Decide which case each finding is:
- The rule does not exist: a genuine gap; an edit may help.
- The rule already exists but was not followed: an **adherence or enforcement gap**, not a content edit. Do not propose re-adding a rule that is already there.
- The plumbing is broken or misconfigured (wrong path, stale config): a config fix.

This step is what keeps the audit from manufacturing busywork. Skipping it is not allowed.

### Phase 5: Consistency sweep
Transcripts show what went wrong in a session. This sweep shows what will go wrong later: **a standard stated in more than one place drifts the first time it changes.**

**Skip this phase unless you maintain several skills that share a standard.** With two or three skills there is no family for a standard to drift across, and the checks below return noise rather than findings. Say in the report that the sweep was skipped and why.

Where it does apply, check each family of skills that shares a standard for four things:

1. **Duplicated rules.** Is a rule stated in more than one SKILL.md or reference file, rather than stated once and pointed at? Grep a distinctive phrase from each shared standard and count the files it lands in. More than one is a finding.
2. **Stale attributions.** If you date the rules in your skills, look for one whose date is older than a later decision on the same subject. Skip this check if you do not use dated attributions; a rule with no date cannot be checked this way.
3. **Orphaned reference files.** If your skills keep files in a `references/` subfolder, look for one that no SKILL.md points at. Nothing reads it, so nobody notices it has gone stale, and a later session can read a retired rule as current.
4. **Broken pointers.** A SKILL.md naming a reference file, script, or sibling skill that does not exist.

**Sweep finding format.** A sweep finding has no frequency across sessions, no verbatim quote, and no friction category, so it is written short, about two lines:
```
<kind: duplicated rule, stale attribution, orphaned file, or broken pointer>
Files: <path>, <path>   Target: <the duplicated phrase, the orphaned file, or the missing target>
```
Give each sweep finding whichever action class from the list below fits the file the defect sits in: a skill file is `update-skill:<name>`, CLAUDE.md is `update-claude-md`, and a protocol, a settings file, or a hook is `config-fix`.

**The fix for a duplicated rule is to collapse it to one file and point at it, never to synchronize the copies.**

### Phase 6: Filter against declined.md and changes.md
Remove from the recommendation list anything matching a `declined.md` entry (note the recurrence instead) or already fixed per `changes.md` (note if it recurred anyway). This filter covers sweep findings from Phase 5 exactly as it covers transcript findings.

### Phase 7: Report and stop
Present one ranked report holding both kinds of finding, already filtered by Phase 6.

For each transcript finding: title, type, frequency (which sessions, by file basename), one to three verbatim evidence quotes, the active skill if any, the recommended action class, and confidence.

For each sweep finding, use the short two-line format defined in Phase 5. Do not ask a sweep finding for a frequency, a quote, or a friction category; it has none.

Cap the recommendations: at most one or two new-skill ideas and a short list of updates per run; if a run wants more, say what was held back. End by asking which to act on. **Do not edit anything.**

### Post-report (outside this skill, after you rule)
- For each finding you decline, append a row to `declined.md` (date, finding, category, reason).
- For each change actually made, append a row to `changes.md` pointing at the record that holds the diff.

## Friction categories
- **repeated-correction**: you repeat an instruction or preference across or within sessions.
- **routing-misfire**: the wrong skill or no skill fired and you redirected, or you had to name a skill that should have been automatic.
- **repeated-reprompt**: you re-issue the same request because the output missed.
- **repeated-workflow-explanation**: you re-explain the same procedure.
- **tool-permission-friction**: the same command or tool repeatedly denied or re-prompted.

Give special weight to **regressions**: an established rule or workflow that quietly stopped being followed. That is where a model upgrade does its damage, and it is the case that most often maps to enforcement rather than to a new rule.

**Run the audit after a session that edited several skills.** That is when a standard gets restated somewhere new, and it is the cheapest moment for Phase 5 to catch it.

## Action classes
Map each surviving finding to exactly one:
- `promote-to-memory`: a cross-project preference worth a persistent memory entry.
- `update-skill:<name>`: a specific personal skill needs tightened or added text.
- `update-claude-md`: a routing or global-rule gap.
- `config-fix`: settings.json, a path, a hook, or other plumbing.
- `no-action`: recurring but already governed, or not worth a change.

## Scope guardrails
- Your own personal skills (the `~/.claude/skills/` directory), CLAUDE.md, protocols, settings, hooks, and memory only. **Never skills you installed from a shared or third-party repo**, and never propose changes to a project's own code or repo configuration.
- Prefer no change. Narrow beats broad. If a recommendation sounds like "a skill for all of X," shrink it or drop it.
- Read-only throughout. The skill is granted no Edit or Write tool, and the report-only contract binds its Bash tool too: Bash is here to list, sample, and read files, never to write one.

## Session log
This is a utility audit. Do not write a project session log. The report is the output; the record of any change later made, plus the two state files, are the durable trail.
