# Writing Voice Guide

How to create a consistent writing voice layer that other AI writing skills build on.

---

## Why a Writing Voice Layer

AI writing tools default to a generic professional register: polished, warm, slightly over-explained, and full of phrases like "I hope this finds you well" and "I wanted to reach out." That default is not your voice.

A writing voice layer is a skill file that defines your specific editorial identity and gives the AI a stable foundation to draw from every time it writes in your name. Without it, each writing session starts from scratch. The AI picks up cues from the current conversation, applies them inconsistently, and reverts to defaults when context runs out.

With a voice layer:

- Every email, blog post, and proposal sounds like the same person wrote it.
- Corrections you make once (remove intensifiers, stop apologizing, cut the filler opener) stay corrected across all future writing.
- Format-specific skills (email, blog, proposal) handle structure and mechanics. The voice layer handles how you think on the page.

The voice layer is not a style guide in the traditional sense. It is a set of executable rules the AI can apply to any draft.

---

## Start With a General Test, Not a List

The obvious way to build a voice layer is to enumerate: list the phrases you hate, list the habits you have, and hand the AI the list. That is a reasonable second step and a poor first one.

A list of banned phrases catches only the phrases on it. AI writing fails in a way that makes this a losing position: the failures are pattern completions from training data, so there is always another phrase that sounds like the ones you banned and is not on your list. You ban "truly transformative," and the next draft says "at scale." You ban that, and the next one says "where the real value lives." The list grows and never closes.

A general test asks the underlying question instead of matching known strings, so it catches the phrase nobody has named yet. Build the test first. Build the list second, as the backstop for cases the test alone lets through.

### The extraction test

The layer this guide grew out of states its general test as one question asked of every phrase in a deliverable, including titles, headers, column labels, bullets, callouts, section dividers, and annotations on a chart:

> What does a reader extract from this?

If the answer is a fact, a description, an action, or a relationship the reader can apply, the phrase passes. If the answer is a posture, a feeling, an attitude, or "nothing they do not already get from the surrounding content," the phrase fails and gets rewritten.

That is one formulation. Yours can differ, and the wording matters less than the property: the test has to be answerable about any phrase, by inspection, without consulting a list. A test phrased as "is this phrase on the banned list" is not a general test. A test phrased as "what would a reader do differently having read this" is.

Two things make a general test work in practice:

1. **It subsumes your specific rules.** Most named rules in a mature layer turn out to be instances of the general test. An intensifier fails because it conveys enthusiasm rather than information. A sales line fails because it tells the reader what to conclude instead of giving them something to conclude from. A phrase like "at scale" fails because it labels size without measuring it. Writing the test first, then deriving the rules from it, produces a layer that hangs together instead of a pile of preferences.
2. **It comes with worked examples.** The test is abstract, and an abstract test applied by an AI drifts. Anchor it with five or six short examples: the phrase, what a reader actually extracts from it, pass or fail, and the rewrite. Include at least one boundary case that looks like a failure and is not, because a test with only clear failures gets over-applied.

### The list, as backstop

Once the test exists, the enumerated inventory has a defined job: named patterns the test alone does not reliably catch, usually because they read as competent professional English. These are worth naming individually because recognition is cheaper than judgment, and because naming them gives you and the AI shared vocabulary for a correction.

Keep each entry short: the pattern name, one example, and where the boundary is. The boundary matters more than it looks. A rule against spatial metaphors that does not carve out the literal sense will start rewriting sentences about actual rooms.

---

## The Second Test: Does the Text Stand Alone

Extraction is one axis. Self-containment is a different one, and text can pass the first and fail the second.

Self-containment asks whether the information a phrase points to is reachable from the artifact itself. Can the reader stand on this sentence, or this slide, without recalling prior numbering, remembering an earlier conversation, or having read another document?

The clearest illustration is a phrase like "Question 1." It is precise, specific, and carries real information, so it passes an extraction test cleanly. It fails self-containment, because the reader cannot resolve it without holding the document's numbering in their head. That is exactly why the two tests have to stay separate. Fold self-containment into the extraction test and "Question 1" passes both.

Three failure forms are worth naming in your own layer:

1. **A bare pointer or cross-reference.** "Question 1," "as on slide 3," "the three modes from the previous slide," "per the attached." The referent lives in the reader's memory or in another artifact, not on the page.
2. **A concept used before it is defined.** A framework, term, or label invoked, then explained a paragraph or a slide later, or never.
3. **A finding that assumes the reader has read the source.** A result named without being restated, on the assumption the reader has the paper, the earlier email, or the prior slide in front of them.

The fix is always one of three: restate the referent inline, define the term on first use, or reorder so nothing is referenced before it is introduced.

Decide explicitly whether this test governs chat as well as deliverables. The bare "Question 1" habit shows up in conversation at least as often as in documents, and a layer that binds only finished files will not catch it.

---

## Generation Time and Audit Time

A voice layer gets applied twice, and the two applications are not the same work.

**Generation time is the primary defense.** The rules apply while the draft is being written, phrase by phrase, before anything is finished. This is where the general test does most of its work: pause on the slide title, the section header, or the leading bolded phrase, ask the question, and rewrite before continuing. Say this explicitly in the layer. An AI given a set of rules will otherwise treat them as an editing checklist and draft in its default voice first, which produces a draft that has to be substantially rewritten rather than one that was correct as written.

**Audit time is the backstop.** A separate pass over the finished text, checking it against the layer. The useful property here is independence: the audit is worth much more when it is run by something that did not write the text. A model reviewing its own draft tends to ratify it, because the same judgment that produced the phrase is being asked whether the phrase is good. Running the audit in a separate context, with the layer and the finished text but not the drafting conversation, catches things the writer will not.

A workable division of labor when the audit finds something: mechanical and unambiguous fixes get applied directly (a punctuation rule, a named pattern with one safe rewrite), and anything that requires a voice judgment gets surfaced for a human decision rather than silently rewritten.

Decide which of your outputs earn an audit pass. Auditing everything is expensive and trains you to ignore the result. One working example draws the line at audience: anything a person other than the writer will read gets the independent audit, and anything that stays internal does not. Where you draw it is your call, but draw it somewhere and write it down.

---

## What a Voice Layer Contains

A mature layer covers these areas, roughly in this order:

**1. Core voice description**
A short paragraph that characterizes the overall register: the relationship between writer and reader, the emotional temperature of the writing, and the implicit contract with the audience. Is your writing warm or cool, dense or expansive, confident or tentative? This is the north star the AI returns to when no specific rule applies.

**2. The general test**
The single question applied to every phrase, with worked examples, a boundary case, and a short statement of why a list alone is not sufficient. Placing this before the enumerated rules is deliberate: it tells the AI that the rules below are instances of one idea rather than a set of independent constraints.

**3. Self-containment**
The second axis, with its failure forms and its fixes, stated as a separate test rather than a subheading under the first.

**4. The named-pattern inventory**
The enumerated backstop. Patterns common in AI output that fail your voice, each with an example and a boundary. State whether it governs chat as well as deliverables.

**5. Editorial principles**
Named principles that govern how ideas are presented, not just how sentences are formatted. Common ground to cover:

- How much you explain compared with how much you trust the reader to infer
- Whether you sell your ideas or state them and let them speak
- How you balance confidence with intellectual honesty
- Which qualifications are necessary and which are hedging

**6. Tone rules**
Specific behaviors to prohibit or require. These are the most mechanically enforceable rules in the layer because they are close to binary. Categories worth covering:

- Opening conventions (what the first sentence must or must not do)
- Warmth conventions (how warmth is expressed, and what false substitutes to avoid)
- Apology and hedging conventions
- Gratitude conventions

**7. Formatting conventions**
Punctuation, capitalization, date and time formats, and other mechanics that appear consistently in your writing. These are the easiest rules to specify precisely and the easiest for an AI to apply reliably.

**8. Notes for the AI executor**
A section written directly to the AI that translates the principles into an operational checklist. The principles section explains your values; this section explains how to act on them. Include the generation-time instruction here explicitly, naming the surfaces where the general test gets applied before writing.

**9. Format-specific rules, if you choose to carry them**
See Notes on Scope below. One working example carries a whole section of slide-specific rules inside the voice layer rather than in the slide skill.

---

## How to Build Your Own

**Step 1: Audit your existing writing.**
Collect 10 to 20 samples of writing you consider representative of your best work. Include a range of formats: short replies, longer explanations, formal proposals, and casual notes. The goal is enough material to see patterns.

**Step 2: Write the general test.**
Read the samples and ask what your good writing is doing that generic professional writing is not. State it as one question you can ask about any phrase. Draft it, then try it on ten phrases from your samples and ten from AI output you have rejected. If it passes something you would cut, or cuts something you would keep, revise the wording. This step is worth more time than any other in this list.

**Step 3: Anchor the test with worked examples.**
Take five or six phrases, mostly real ones from drafts you have corrected. For each: the phrase, what a reader extracts from it, pass or fail, and the rewrite. Include one boundary case that looks like a failure but passes.

**Step 4: Write the self-containment test.**
Separately from step 2. Go back through your samples looking for pointers, cross-references, and terms used before definition. Name the failure forms you actually produce, not a generic list.

**Step 5: Identify the patterns the test misses.**
Now build the list. Go through AI output you have rejected and ask, for each phrase you cut, whether the general test would have caught it on first inspection. The ones that would have slipped through are your inventory. Each gets a name, an example, and a boundary.

**Step 6: Identify what you never do.**
Look for what is absent from your writing. Never use intensifiers? Never apologize unnecessarily? Never open with pleasantries? Prohibitions are easy to audit, which is why they are useful, but note that they are also the part of the layer with the shortest reach. They belong under the test, not in front of it.

**Step 7: Draft named principles.**
Write the patterns out as named rules with short titles, two to four words each. Titles make principles memorable and give you vocabulary for correcting the AI in conversation ("that is a selling sentence") instead of re-explaining the rule each time.

**Step 8: Write before and after examples.**
For each principle, one example that violates it and one that follows it, plus a sentence on the difference. Use real sentences from your own writing or from corrections you have made to AI output. Invented examples tend to be too obvious to be useful.

**Step 9: Write the generation-time instruction.**
Say explicitly, in the notes to the AI, that the tests apply while drafting rather than only in review, and name the surfaces: titles, headers, column labels, callouts, the leading phrase of a bullet, and chart annotations.

**Step 10: Test against new samples.**
Give the AI a writing task using only the voice layer as context. Compare the output to your audit samples. Where the output diverges, identify which rule is missing or poorly specified, and revise. Run the comparison in a fresh session so the layer is doing the work rather than the conversation.

**Step 11: Set up the audit pass.**
Decide which outputs get an independent review against the layer, and arrange for that review to run somewhere that did not produce the draft. Write down what the reviewer checks and what it is not responsible for; an audit with unbounded scope produces findings you will not act on.

**Step 12: Iterate.**
A voice layer is a living document. Add rules when you find new failure modes. Tighten rules when the AI finds loopholes. Remove rules that generate false positives, where the rule fires on correct writing and breaks it. When you add a specific rule, check first whether the general test already covers it and the real problem is that the test is not being applied.

---

## Integration with Other Skills

The voice layer is a foundation, not a standalone tool. It does not know how to structure an email, format a blog post, or organize a proposal. That work belongs to format-specific skills.

The integration pattern is simple: every format-specific writing skill reads the voice layer first, then applies its own structural rules. The voice layer handles how you sound; the format skill handles what goes where.

**Reading order:**

1. Voice layer (always first for any writing in your voice)
2. Format-specific skill (email, blog, proposal, forum reply)
3. Any domain-specific context (course materials, client background, topic notes)

**Practical consequence:** When you update a voice layer rule, the change propagates to every format-specific skill that reads it. You fix a problem once at the foundation and it does not reappear in any format.

**Skills that typically read a voice layer first:**

- Email drafting skills
- Blog and newsletter writing skills
- Consulting proposal and statement of work skills
- Forum and comment reply skills
- Any skill that produces writing attributed to a specific person

---

## Example Structure

The following skeleton shows how a voice layer SKILL.md can be organized. Replace bracketed placeholder text with your own content. The ordering is the point: the general test sits above the enumerated rules, and self-containment sits beside it as its own section.

```markdown
---
name: [your-handle]-writing-voice
description: [Your name]'s writing voice and editorial principles. Foundation layer
  for all writing in [your] voice. Read this skill before any format-specific writing
  skill.
triggers: write in [my] voice, apply [my] voice, [my] writing style
---

# [Your Name] Writing Voice

[One paragraph on what this file is and where it sits: the foundation layer that
format-specific skills read first. Say what it owns (how you think on the page) and
what it does not (structure and mechanics).]

---

## Core Voice

[Two to four sentences. Direct characterization: what the voice is and what it is
not. Dimensions to address: formal or casual, warm or cool, expansive or dense,
assertive or tentative.]

---

## [Your General Test]

[The one question, stated in a single line and set off so it is unmissable.]

[What a passing answer looks like and what a failing answer looks like.]

[One paragraph naming this as the master test and showing that two or three of the
specific rules below are instances of it.]

### Worked Examples

- **"[phrase]"** ([where it appeared]) [what a reader extracts, pass or fail, and
  the rewrite.]
- [Four to five more, at least one a boundary case that passes.]

### Why the Test Catches What a List Misses

[Two or three sentences on why enumeration alone cannot close: the failures are
pattern completions, so there is always a next phrase nobody has cataloged.]

---

## Self-Containment

[State it as a separate axis and say so explicitly, with the one example that
passes the general test and fails this one.]

[The failure forms you actually produce, numbered, each with examples.]

[The fixes: restate inline, define on first use, or reorder.]

[Scope: does this govern chat as well as deliverables?]

---

## [Named Pattern Inventory]

[One sentence establishing this as the backstop to the test above, not the primary
defense, and stating that it applies at generation time and at audit time.]

1. **[Pattern name]:** "[example]" [Boundary, where one is needed.]
2. **[Pattern name]:** "[example]"
[Continue. Expect this list to grow over time.]

### Not on this list (deliberate)

[Patterns you considered and rejected, with the reason. This section stops the list
from re-acquiring rules you have already decided against.]

---

## Editorial Principles

### [Principle Name 1]

[One paragraph: what it requires, what it prohibits, when it applies.]

**[Your name] writes:** "[Example that follows the principle]"

**Not:** "[Example that violates it]"

[One sentence on the difference.]

### [Principle Name 2]

[Repeat. Four to six principles is a common range.]

---

## Tone Rules

### [Category 1: e.g., Openers]

### [Category 2: e.g., Warmth]

### [Category 3: e.g., Hedging and Qualification]

---

## Formatting Conventions

### [Convention 1: e.g., Punctuation preference]

### [Convention 2: e.g., Time format]

### [Convention 3: e.g., Date format]

### [Convention 4: e.g., Emoji policy]

---

## [Citation and Reference Conventions]

[Optional, and common in layers that have been in use for a while. How sources are
named in running text, and what form a reference takes on first and later mention.]

---

## Notes for the AI Executor

When writing as [your name]:

1. **[Checklist item]:** [What to do after drafting.]

2. **[Checklist item]:** [What patterns to watch for and remove.]

3. **[Checklist item]:** [The default when choosing between a longer and a shorter
   version.]

4. **Apply [the general test] before writing any phrase.** [Name the surfaces:
   titles, section labels, column headers, callouts, the leading phrase of a bullet,
   chart annotations. State that this is the generation-time application and that
   audits are the backstop, not the primary defense.]

5. **Apply the self-containment test before writing any reference.** [Same shape:
   generation-time application, audit as backstop.]

---

## [Format-Specific Rules, e.g., Slides]

[Optional. See Notes on Scope. Rules that apply to one output format, kept here so
they travel with the voice rather than living in the format skill.]
```

---

## Notes on Scope

A voice layer should cover writing principles, not content expertise. It tells the AI how you write, not what you know. Domain knowledge belongs in separate context files or knowledge base entries that skills load alongside the voice layer.

**Where format-specific rules live is a real tradeoff, and it has two defensible answers.** A rule that only applies to slides, for example, can sit in the slide skill or in the voice layer.

Putting it in the format skill keeps the voice layer general and short. Every reader of the voice layer is reading rules that apply to them, and the slide rules are loaded only when slides are being built.

Putting it in the voice layer keeps the rule attached to the reasoning that produced it, and makes it reachable from every route that produces that format. That second point is what usually decides it in practice. If three different skills can generate slides, a rule living in one of them is enforced on one third of the output, while a rule in the voice layer is enforced on all of it. The cost is that the voice layer grows and that some of what it carries is irrelevant to any given read.

The layer this guide grew out of went the second way, deliberately, and now carries a full section of slide rules inside the voice layer. If your formats are produced by a single skill each, the first way is cheaper. If several skills produce the same format, or if the format-specific rules are really applications of your general test rather than mechanics, the second way holds up better.

**Expect the layer to grow, and know what growth costs.** A voice layer starts small and does not stay small. The working example behind this guide is roughly 33KB after regular use, and most of that growth came from three places: named patterns added each time an unnamed phrase got through, boundary carve-outs added each time a rule fired on writing that was fine, and worked examples added because an abstract rule was being applied inconsistently. All three are legitimate, and all three are load-bearing.

The cost is real, though. A file that is read at the start of every writing task is paid for on every writing task, and a long file dilutes attention across its own rules. Two habits keep it in bounds. Before adding a specific rule, check whether the general test already covers the case and the actual problem is that the test was not applied. When you add a boundary carve-out, put it with the rule it qualifies rather than in a separate exceptions section, so the rule and its limits are read together.

**A mature layer accumulates conventions beyond voice proper.** Citation format is the usual example: how a source is named in running text, whether the title or the author leads, and what a second mention looks like. Date and time formats, emoji policy, and reference conventions are the same kind of thing. These are not voice in the strict sense, but they are decisions that have to be made consistently across everything you write, and they have nowhere better to live. Letting them accumulate in the voice layer is normal and not a sign the file has lost focus.

The goal is a voice layer precise enough that the AI produces recognizably correct output on the first pass, and organized well enough that you can still find a rule in it after a year of additions.
