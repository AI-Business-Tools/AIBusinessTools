### 1. Process Inbox (`/kb` or "process inbox")

**This file is procedure Claude follows, not a checklist you work through.** It is written for the model: the flow, the subagent model and effort table, the agent prompts, the exit-code tables, and the report formats below are instructions Claude executes during a `kb` run. As a user you drop files into `aa-inbox/`, type `kb`, and read the report at the end. Read this file when you want to know what the run will do, or when you are adapting the skill to your own tools.

**Where this file's cross-references resolve.** This file is Mode 1 of the knowledge-base skill; `SKILL.md` is read first and stays loaded alongside it. Three blocks this mode uses are held in `SKILL.md` because other modes need them too: **Step 2 (extract citation metadata) and Step 3 (rename)**, under `## Citation metadata and naming`; the **frontmatter block** that Step 4b begins the summary with, under `## The frontmatter block`; and **Index Format**. The helper commands (`kb-index`, `kb-dup-check`, `kb-fetch-url`, `kb-recents`, `kb-search`) are defined once under `## Helper commands` there. Apply all of these from `SKILL.md`; they are not repeated here. "See Mode 5" below resolves to `references/slides.md`. Do not open any other mode file.

**When Mode 5 does NOT invoke this flow.** A `kb slides` run at the default deep tier, on a source that is NEW to the knowledge base, no longer runs this ingestion at all: the deck generator does the whole read and Mode 5 files the results afterwards. **That route is stated once, in `references/slides.md` under "THE NEW-SOURCE DEEP ROUTE", and is deliberately not restated here**; read it there rather than assuming this flow runs on a slide build. This flow still runs unchanged for every plain `kb` inbox run, for Mode 5's beamer path, for a URL target on any path, and for Mode 5's below-bar re-ingest of an already-filed item.

Scan `aa-inbox/` and `aa-blog/` for new files. Build a list of items with file types and page counts (for PDFs). Items from `aa-blog/` are processed with blog-specific overrides (see Blog Post Processing below).

**Processing levels:**

| Level | What it reads | Outputs | When to use |
|-------|-------------|---------|-------------|
| **full** | All pages via split-pdf agents | `_text.md` + `_summary.md` | Default for all items |
| **triage** | Pages 1-4 only (no splitting) | `_summary.md` only (no `_text.md`) | When prompted: "triage", "first pages only", "triage the big ones" |
| **lite** | Nothing in the PDF | `_summary.md` from companion `.txt` | Automatic when a companion `.txt` file exists |

**Default is full. Do not proactively ask whether to triage, even for large PDFs or large batches.** Triage activates only when the request includes "triage," "first pages only," "triage the big ones," or an equivalent explicit instruction. If the user does not include one of these triggers, process every item at **full** level and do not mention triage as an option. Lite is automatic when a companion `.txt` exists; do not ask about it.

**Companion .txt convention:** if a PDF has a matching-name `.txt` file (for example `Report.pdf` plus `Report.txt`), the system uses **lite** processing automatically: the `.txt` content provides the citation and description for `_summary.md`, and the PDF is filed unread. The `.txt` can contain a citation, description, URL, or any content to base the summary on. If the `.txt` contains a URL (line starting with `http`), fetch the URL for additional content; on fetch failure, see Source-fetch failure below (under Step 1).

**Agent-per-item architecture:** every inbox item is processed in its own subagent, regardless of file type. This is mandatory for all items, not just PDFs. The subagent architecture serves two purposes: (1) context isolation prevents image and content accumulation that can hit API request size limits, and (2) the agent prompt formulation step forces the parent to read and inline the correct summary skill format before launching the agent, which prevents improvised summaries that do not match the knowledge base's format standards.

**Before launching any agent, the parent must:**
1. Read the appropriate summary skill in full: your academic summary skill (for academic content) or your general summary skill (for non-academic content). If the batch contains both types, read both.
2. Inline the summary format instructions into each agent's prompt. Do not tell the agent to read skill files; include the format template directly.

**Flow:**

1a. **Parent: sort every line of a `.urls` file or `urls.txt` BEFORE anything else runs.** A line in one of those files is not always a URL, and what it turns out to be decides the processing level, the subagent model, and which summary template gets inlined, all of which the parent fixes before it launches anything (Flow steps 2 and 3, and the model table below). **So this sort is the parent's and never the reading agent's**: an agent that discovers a 60-page academic PDF behind a line it was launched for as "full, general / sonnet" reads it at the wrong tier against the wrong template, and this file's own agent-per-item rationale forbids it reading skill files to correct that.

**Normalize first, then sort.** Strip leading and trailing whitespace, then strip ONE matching pair of surrounding single or double quotes. **This is not optional and it is the case this rule exists for:** the motivating line was a quoted absolute path, and the unstripped string matches no file and no URL scheme, so an unnormalized test sends the very case this handles to branch 3. Skip a blank or whitespace-only line and a line whose first character is `#` **silently**, with no report: a trailing newline is the normal state of a text file, and `#` is how branch 3 parks a line it could not use.

Then each surviving line takes exactly one branch:

- **Branch 1, it begins `http://` or `https://`:** unchanged. It is a URL item, handled exactly as the routing table's `.urls` row describes.
- **Branch 2, it is an ABSOLUTE path to an existing, readable, regular file whose extension the Step 1 routing table covers:** it is a LOCAL SOURCE. **Copy it** (`cp`, never `mv`: the original may be a note you own inside another tool's folder, and moving it would take it out of your own filing) into `aa-inbox/` under its own basename, and from that point it is an ordinary inbox item, dup-checked, levelled, and routed by its real extension like any hand-dropped file. **Refuse the copy and take branch 3 when a file of that basename is already in `aa-inbox/`**; a plain `cp` overwrites silently, and the degenerate case is a line naming any file called `urls.txt`, which would clobber the drop target mid-run. **Clear the line the moment its copy is on disk in `aa-inbox/`**, not at the end of the run, so a run that dies after the copy does not re-copy over it next time. Name the origin path in the batch report, and write it into the copied file's own header as an `extract_note:` line (`Copied from <absolute origin path> on <date>. Not a fetch.`), because a batch report evaporates with the session and nothing else downstream records where the file came from. Where the copied file is markdown carrying its own `source:` or `url:` frontmatter (a web clipping does), lift that value into the summary's `url:` field, which also gives the duplicate check its highest-precision layer.
- **Branch 3, anything else:** a relative path, a directory, an unreadable file, a path that does not exist, an extension the routing table does not cover, a basename already sitting in `aa-inbox/`, a bare host, a DOI, a `file://` URL, or a typo. **Do not call `kb-fetch-url`, and never reach the Source-fetch failure rule below**: that rule ends by reconstructing an item from web-search excerpts and marking it `source_basis: excerpts`, which for a local path means replacing a document that may be sitting complete on disk with prose assembled from search results, and terminally gating the slide skills on it. Instead report the line in the batch report, **quoting the exact string that was tested** (so a path that failed on Unicode normalization, NFD against NFC on an accented name, is diagnosable in one look), and **retain it, rewritten in place as** `# unusable YYYY-MM-DD <reason>: <the original line>`. Nothing is lost, and the `#` stops every later run re-reporting it. **Accepted cost, stated so it is not met as a surprise:** `kb status` counts `urls.txt` toward the inbox backlog whenever the file is not empty, so a parked line shows as one pending item until it is deleted.

**In a `.urls` file rather than `urls.txt`,** a parked line means the file is left in place with the line retained, and is NOT moved after processing; only a `.urls` file whose every line was processed moves as the routing table says.

1. **Parent:** scans `aa-inbox/`, lists items, detects companion `.txt` files, and runs the duplicate check per item: `kb-dup-check "<candidate stem>" [--url <url>]`, passing the best available filename stem (the dropped name, or the prospective renamed stem if metadata is already evident) and the item's URL when known. `DUP` flags a probable duplicate (Step 5 leaves it in the inbox and reports); `NEAR` is a fuzzy hit to surface for the user's call; `ERROR` means the check could not complete, so treat the item as unverified and say so.

   **Without the script, run the targeted lookup instead:** `grep -i -F "<candidate stem>" index.md`, plus `grep -i -F "<url>" index.md` when the item's URL is known. A hit is a `DUP` (show the matched row), no hit is an `OK`, and a grep that cannot run, because `index.md` is missing or unreadable, is an `ERROR`. `NEAR` has no fallback; without the script the run detects exact duplicates and not near ones, and should say so once in the batch report. **Never eyeball-compare against a whole-file `index.md` read.** That prohibition is about reading the index into context and judging by eye; a `grep` for one stem reads back one line and is the sanctioned substitute, not a violation of it.
2. **Parent:** reads the appropriate summary skill or skills for the batch (academic, general, or both). For items from `aa-blog/`, the blog summary template (see Blog Post Processing) replaces the academic or general template. The parent also inlines the frontmatter template (see Step 4b) into every agent prompt, with `topic:` and `tags:` left blank for the parent to fill at filing, with `model:` pre-filled with the bare alias of the model the parent is about to launch the agent with (the parent is the only party that knows the launch model for certain; the agent copies the value out like every other field), and states the quoting rule explicitly (every free-text value double-quoted, embedded `"` escaped as `\"` and `\` as `\\`) so the agent quotes even values it composes itself.
3. **Parent:** for each item, launches an Agent to handle Steps 1 to 4 below. The agent prompt must inline the relevant instructions (file type routing, naming convention, summary format template from the summary skill), specify the processing level, and set the Agent tool's `model` parameter per the **Subagent model selection** table below. Do not tell the agent to read other skill files; include the instructions directly in the prompt.
4. **Agent:** processes the item at the specified level: full (split, read all, `_text.md` plus `_summary.md`), triage (read pages 1-4 only, `_summary.md`), lite (use companion content, `_summary.md`), or fast-extract (whole document mechanically extracted without a deep read, `_text.md` plus `_summary.md`; produced by other skills such as a lite slide build, not a level this skill itself chooses).
5. **Agent returns:** new filename, one-line content summary, content type (academic or general), any errors.
6. **Parent:** after all agents complete, reads each `_summary.md` to determine topic assignments, then presents the batch summary (Step 5).

**Subagent model selection** (pass via the Agent tool's `model` and `effort` parameters):

| Processing level / content | Model | Effort |
|---|---|---|
| lite (companion `.txt` exists) | `haiku` | (unspecified, inherits session) |
| triage (pages 1-4) | `sonnet` | (unspecified, inherits session) |
| blog post (any item from `aa-blog/`) | `sonnet` | (unspecified, inherits session) |
| full, general (news, reports, podcasts, videos) | `sonnet` | (unspecified, inherits session) |
| full, academic (papers, preprints, working papers, dissertations) | `opus` | `high` |

Use bare aliases so subagents auto-track the latest version of each tier. Academic items keep the strongest tier because incisive thesis and key-finding extraction on dense technical work is where the tier difference shows up. Everything else is template-driven and runs cleanly on a mid or small tier. The full-academic agent additionally pins `effort: high` explicitly rather than inheriting the session's ambient effort, which could otherwise run higher than a single document's transcription and summary needs; the model-tier reasoning above does not extend to needing maximum reasoning effort for that job.

For each item, the agent follows Steps 1 to 4:

#### Step 1: Identify file type and route

| Type | Extensions | Processing |
|------|-----------|------------|
| PDF | .pdf | full: split-pdf extraction. triage: read pages 1-4 only. lite: use companion `.txt` |
| Text-based documents | .md, .txt, .rtf | Read directly; generate `_summary.md` |
| Word documents | .docx, .doc | Run the visual content check (see below), then extract text via python-docx or textutil; generate `_summary.md` |
| HTML files | .html, .htm | Extract via trafilatura or an equivalent extractor; generate `_summary.md` |
| Images | .png, .jpg, .jpeg | Read image; extract text, data, and context; generate `_summary.md` |
| URL list | .urls | **Lines are sorted by the parent at Flow step 1a above, not here**, because a line may be a URL or a local file path and which it is decides the model and the summary template. For a branch-1 (URL) line, run `kb-fetch-url` (see The capture is written by script, below); on exit 2 or 3 see Source-fetch failure below, and on **exit 4 the line was never a URL**, so it is a branch-3 line and the Source-fetch failure rule does not apply to it. A branch-2 (local file) line has already been copied into `aa-inbox/` by the parent and is routed by its own extension in the rows above. |
| URL file (persistent) | `urls.txt` (exact name) | Same as .urls, but the file is **cleared of the lines that were processed** rather than moved, and a branch-3 line is retained in it as a `#` comment (Flow step 1a). This file stays in `aa-inbox/` as a persistent drop target. |
| LaTeX | .tex | Read directly; generate `_summary.md` |

##### Visual content check (Word and RTF only)

For `.docx`, `.doc`, and `.rtf` files, before extracting text, check whether the document embeds images, charts, or drawings that a text extraction will silently drop (a short script over the file's media parts does this; any equivalent check works).

- If the file carries no visual content: proceed silently to text extraction.
- Otherwise: include this line in the agent's report back to the parent, so it surfaces in the batch summary:
  > Visual content not viewed in `<filename>`: [what the check found]. Summary is text-only.

The agent continues with text extraction either way.

##### The capture is written by script, never by you (all URL paths)

**Run `kb-fetch-url "<url>" --out "aa-inbox/<stem>.md"`. Do not compose, summarize, paraphrase, or edit the source file's body. Ever.** For a non-PDF source the source file IS the text (that is why URL items get no `_text.md`), and the slide skills read it as their verification authority, so prose you write there does not read as yours downstream; it reads as the publication.

**If you have not built `kb-fetch-url`, URL ingestion still has a legal route, and it is narrow.** Fetch the page with the built-in web fetch tool and **save what it returns to `aa-inbox/<stem>.md` verbatim**, then disclose the method: add an `extract_note:` line to that file's header (`Captured with the built-in web fetch tool; kb-fetch-url is not installed. Not a mechanical extraction.`) and carry the same sentence into the summary's frontmatter as `capture_caveat:`. **The distinction that matters, stated so it cannot be blurred: saving retrieved page text verbatim is legal, and writing prose of your own from search results is not.** The second is a reconstruction, it is permitted only after a fetch has actually failed and captured nothing, and it is then marked `source_basis: excerpts` precisely so downstream skills refuse it (Source-fetch failure, below). Not having a script is not a failed fetch and authorizes nothing.

**Without the script you also lose the exit code that sets `source_basis` mechanically**, so set the field by hand from what came back, using the same tests the table below encodes: leave it out when the capture is the whole document, set `source_basis: partial` when what came back is visibly a fragment or is plainly a landing page standing in for the document, and set `source_basis: excerpts` only on a reconstruction after nothing could be captured. The rest of this section describes the script's behavior and applies when you have one.

The prohibition is stated this hard because the failure is not hypothetical. Two URL items were once filed with a model-written paraphrase in place of the article. Both agents had been given an instruction naming a mechanical route, both used a fetch tool instead and wrote the file by hand, and both cited reproduction limits for doing so. One disclosed it in the file, one did not. **The instruction was the problem: asking a model to emit five thousand words of someone else's text puts the compliant action and the correct action in opposition, and no wording resolves that.** A script removes the model from the write path, which is the only fix that holds.

The script prints extracted metadata (title, author, date, venue, word count) for your Step 2 and Step 3 work. **It does not settle the citation:** author comes back absent or malformed often (measured `None` on two of six live pages, and a semicolon-joined publisher-plus-author string on a third), and its date has been observed one day off. Confirm both before they reach the filename or the citation.

**Its exit code sets `source_basis` mechanically, so disclosure never depends on anyone remembering:**

| Exit | Meaning | What you do |
|---|---|---|
| 0 | Capture written | File normally, and omit `source_basis`. **If the output carries a `capture_caveat:` line, copy it verbatim into the summary's frontmatter as a `capture_caveat:` field** and name it in the batch report. A caveat records doubt; it does not gate anything. |
| 1 | **The script itself did not run to completion**: bad arguments, a missing dependency, or an unhandled error. Nothing was fetched and nothing was written | **Do NOT take the fallback and do NOT reach Source-fetch failure.** No fetch was attempted, so there is nothing to recover from, and reconstructing from web-search excerpts here would invent a body for a page nobody tried to read. The defect is in the invocation or the script, not in the source. Report the line quoting the exact string that was passed, name the script's own error output, and park it as a branch-3 line per Flow step 1a. Fix the call or the script and re-run; once it runs, the line is an ordinary branch-1 URL again. |
| 3 | Capture written, and KNOWN not to be the document: a landing page standing in for a paper, or a bot-check interstitial | File it, set `source_basis: partial`, and name it in the batch report. Where the note says the document is elsewhere (an arXiv or working-paper landing page), get the PDF and process that instead, which is the real fix. |
| 2 | Nothing captured, nothing written | Take the fallback below. |
| 4 | **The argument was never a web address** and nothing was attempted: a filesystem path, a bare host, a DOI, a `file://` URL, or a typo | **Do NOT take the fallback and do NOT reach Source-fetch failure.** Nothing failed to fetch, so there is nothing to recover from, and reconstructing from web-search excerpts here would replace a document that may be a readable file on disk. Treat it as a branch-3 line per Flow step 1a: report it quoting the exact string, and park it. Give your fetch script an explicit guard that produces this code; without one, a non-URL raises an unknown-scheme error out of the fetch and exits on an undocumented code, which leaves a reader to improvise toward exit 2 and the reconstruction. |

**Exit 3 is reserved for what is certain.** A metered publisher, where the same URL serves the whole article to one fetch and a teaser to the next, returns exit 0 with a caveat rather than a gate: stopping on every one of them was a false alarm often enough to train the reader to clear it unread, which is exactly when it would fail on the case that mattered.

**The fallback, which is sanctioned rather than forbidden.** A script exit of 2 means the host refused the fetch, and some hosts refuse only scripted requests: a site can return HTTP 403 to a script and the full article to an interactive fetch tool. So on exit 2, fetch with your fetch tool and write what it returns. Transcript sources, auth-walled documents, and JavaScript-rendered pages reach the knowledge base this way too and would otherwise stop being ingestible. **The method disclosure is mandatory:** add an `extract_note:` line to the source file's header naming it (`Captured via WebFetch after kb-fetch-url exited 2 (http-403). Not a mechanical extraction.`), and carry the same sentence into the summary's frontmatter as `capture_caveat:`. **`source_basis: partial` is set only if what came back is visibly a fragment** (it stops mid-argument, or it is plainly a teaser), not merely because the fallback was used: the case this rule is written around returns a faithful 4,029-word article that way. A capture obtained any other way is disclosed the same way. What is forbidden is not the fallback; it is an undisclosed one, and prose you wrote yourself in place of the article's text.

##### Source-fetch failure (all URL paths)

When a source URL will not fetch (timeout, block, paywall, dead link), in any mode that fetches URLs:

1. Retry once with the sanctioned fallback above (an interactive fetch tool, after `kb-fetch-url` has exited 2). Two failures end the fetch attempts; do not keep retrying. Never respond to a failed fetch by writing the article's text yourself; that is the one thing no exit code authorizes.
2. If a partial capture succeeded (an abstract, a preview, a page truncated mid-argument), process what was captured and set `source_basis: partial` in the frontmatter. **A capture that came back whole does not take the mark just because the fetch needed a second method:** what that owes is the method disclosure above, not an incompleteness claim, and marking a complete 4,000-word capture `partial` is the same false alarm the metered-host rule exists to avoid. If nothing was captured, reconstruct what the item is about from web-search excerpts and set `source_basis: excerpts`. **A reconstruction is the only case where you compose the body, and it is marked `excerpts` precisely so downstream skills refuse it.**
3. Either way, the summary body's first line after the citation must be a Source note naming what happened and what the content was built from, for example: `Source: URL fetch failed (site timeout). Content reconstructed from web search excerpts; no full source captured.`
4. The item still files normally (topic folder, index row, search index). A degraded record that is findable and marked beats an empty inbox slot; the marker is what makes it safe. Do not hold the item in the inbox.
5. Name the item in the batch report as excerpt-built or partial, so the user can decide whether to retry the capture later. In headless mode, write the basis into the result line.
6. When a later session captures the full source, replace the reconstruction (keeping a timestamped copy of the old artifacts), remove the `source_basis:` line, and regenerate the index.

**Both degraded values are load-bearing downstream, and both gate.** `excerpts` earns the harder treatment: a non-interactive deck generator and an unattended batch entry point refuse terminally, and an interactive generator confirms once, so a reconstruction is never presented as the publication. `partial` gates too, in the shape each skill's discipline allows: the non-interactive generator refuses with a `usepartial` escape, the interactive one confirms once, and the unattended one builds and flags into its result line. That protection only fires if this rule sets the field, so setting it is mandatory, not best-effort. The authoritative statement of who gates what is `SKILL.md`'s `source_basis` paragraph; this sentence and the one in `references/slides.md` follow it, and all three are edited together.

#### Step 4: Generate text and summary

For each file, generate two artifacts:

**4a. Full-text extraction (`_text.md`)** (PDF sources only)

During the split-read process, write the full text content to `<filename>_text.md` alongside the source file. Format:

```markdown
--- Page 1 ---

[Full text content of page 1]

[Figure 1: the figure's printed caption, verbatim]

--- Page 2 ---

[Full text content of page 2]

[Table 1: the table's printed caption, verbatim]
```

Include page markers (`--- Page N ---`), all body text, and annotations for images, figures, and tables (`[Figure N: caption]`, `[Table N: caption]`). This is a faithful transcription, not analysis. Non-PDF sources (markdown, text, HTML) do not need `_text.md` because the source file IS the text.

**A FIGURE ANNOTATION CARRIES THE PRINTED CAPTION. IT NEVER CARRIES A NUMBER YOU READ OFF THE PLOT.** This is the one rule in this section that has put wrong numbers on delivered slides, so it is stated as a prohibition rather than a preference.

- **Transcribe the caption the figure actually prints**, verbatim, exactly as you transcribe body text. A caption's own numbers (a figure number, a year range, a sample size, an axis unit, a value the caption itself states) are printed characters on the page, so they transcribe like any other characters.
- **Where you describe the figure beyond its caption, describe SHAPE AND DIRECTION, not values.** "Falls steeply through the 1950s, troughs in the late 1960s, and climbs after 1980 to end at its sample high" is a description this pipeline can use. "Falls to about +0.02 by 1975" is a measurement you took off a picture, and nothing downstream can tell the two apart once it is written.
- **Where a value genuinely cannot be avoided, mark it in the annotation itself: `near 3.1 (unverified)`.** The literal string `(unverified)` is what later stages and any figure-value audit key on, so a value written without it is indistinguishable from a transcribed one.
- **A TABLE is different and the difference is the point.** A table's cell values are printed characters, so transcribing them IS the faithful transcription asked for here. A figure's plotted values are printed nowhere; recovering one means measuring a pixel position against an axis, which is estimation wearing the costume of transcription.

**Why this is a prohibition, measured rather than assumed.** A 53-slide deck built from a 101-page paper shipped three slides carrying wrong numbers, and all three were transcribed FAITHFULLY out of this file: a slide read "ending near 1.55" from an annotation reading "about 1.55 at the end" (the endpoint is 2.75; 1.55 was the second-to-last vertex); another read "peaking near 1.5 to 1.6 around 1965, 1975, and 2019" (there is no 2019 observation, and the series ends near its sample low); a third read "to about 0.02 by 1975" (the value at 1975 is 0.086). Every later stage treated them as ground truth, because the slide pipeline names `_text.md` as its only verification authority. **The pipeline was verifying against the source of the error.** The obvious repair, letting a later stage re-read the figure and correct the number, was tried and FALSIFIED: the checking pass's own reading of one of those same figures was wrong by five years on the plateau it named, so the correction would have been applied and logged as verified. A value read off a plot is not reliable enough to carry an edit, which is why this rule stops the value being written rather than trying to fix it afterward.

For PDFs, use split-pdf to deep-read. For shorter documents (under 5 pages), read directly.

**Delete the split folder after writing `_text.md`, on every route, `kb slides` (Mode 5) included.** There is no retention exception. An earlier version of this rule held the folder on the slide path "for downstream re-extraction" and named a consumer that does not exist: nothing reads a split folder after ingestion. A deck generator's figure extractor takes the source PDF and a build directory, opens that one file, and knows nothing of chunks or page ranges; the Beamer workflow skips splitting outright whenever `_text.md` is already present, which on that path it always is. **That was searched rather than assumed:** no script, hook, or skill reads chunk files out of a directory it did not create in the same run, and every skill that reuses a split at all checks for the text extract FIRST, a check a filed item always satisfies. The retained folder was orphaned by construction besides: the split step writes it INSIDE a build folder named for the directory the source happened to be sitting in, so it stays behind in the inbox while the item itself moves on to its topic folder, with nothing linking the two.

**Why deleting is safe rather than a matter of taste, and the principle to reason from.** The chunks regenerate byte for byte in a few seconds, by a deterministic script, from an original the pipeline never deletes; nothing is lost that cannot be had back identically. Contrast a deck generator's own build-folder rule, which deletes slide renders and KEEPS extracted figures: that extractor keeps changing, so re-running it months from now yields different pictures from the same PDF. Delete what regenerates identically; keep what does not.

**Delete exactly one directory: the `split_<name>/` folder the split step itself created for this item, at the path the split step wrote it to.** Never by wildcard, never by recursion over a parent, never by any pattern that could match a folder this pipeline did not create. **Not deleted, on any route:** the source file, `_text.md`, `_summary.md`, the item's own folder, the parent build folder the split folder sat inside, and any generator's build folder. "Clean up the build folder" is the wrong instruction; the split folder is the target and nothing adjacent to it is. **Post-condition, checkable by any later run, and LOOK IN THE RIGHT PLACE:** the split folder is not at the top level of the directory the source sat in, and it is never in the item's topic folder at all. The split step writes `<containing folder>/<containing folder name>_build/split_<pdf stem>/`, one level down inside a build folder. So the check is that no `split_<pdf stem>` directory remains inside that `_build` folder, while the source file, `_text.md`, and `_summary.md` are all still in place in the item folder. Both halves together are the test: the negative half alone would also pass if the deletion took too much. **This location is written out because getting it wrong produces a check that cannot fail**, which is worse than no check. (Measured on one 85-page paper: the retained folder held 22 chunk PDFs at 11MB, beside a 5.3MB original that is never deleted. 22 is correct for 85 pages at four per chunk, 21 full chunks and a remainder.)

**4b. Structured summary (`_summary.md`)**

Generate a full structured summary following the format template inlined in the agent prompt by the parent (see Flow steps 2 and 3 above). The format comes from one of:
- Your academic summary skill, for academic papers, research articles, preprints, and working papers
- Your general summary skill, for news articles, blog posts, reports, videos, and podcasts

The agent does not read these files itself; the parent reads them before launch and inlines the format. Follow the inlined template exactly. **Begin the file with the frontmatter block held in `SKILL.md` under `## The frontmatter block`**, then the summary content.

#### Step 5: File items and report

**This step runs in the parent conversation** after all item agents have completed.

Read `topics.md` (if it exists) to understand existing categories, then determine the best-fit topic folder for each item. Do not read `index.md` into context for this; the topic descriptions plus each item's `_summary.md` carry the assignment signal, and a membership question is a `grep index.md` or `kb search`, never a whole-file read. **Do not pause for confirmation.** File each item into its best-fit folder immediately, update the index, recents, and search, and then report what was filed and invite redirection. The user corrects after the fact rather than approving before; see "Correcting a filing" below.

**Folder selection:**
- If an item clearly fits an existing topic folder, file it there.
- If no existing folder is a clear fit, file it into your overflow folder (for example, `other-articles/`) and flag it in the report so the user can redirect (including to a new folder). **Never auto-create a topic folder.** A new folder is created only when the user names one in a redirect.
- If an item was flagged `DUP` by the duplicate check (flow step 1), do **not** auto-file it. Leave it in `aa-inbox/`, report it as a probable duplicate of the existing entry, and wait for direction (file anyway, or discard). A `NEAR` hit files normally but is named in the report with its score and match so the user can redirect or discard after the fact.

**File each item:** create a per-document subfolder `<topic>/<stem>/` (where `<stem>` is the renamed filename without its extension) and move the source file, its `_text.md`, and its `_summary.md` into it (Pattern A; see Directory Structure). **As each item is filed, set the `topic:` frontmatter field in its `_summary.md` to the destination folder name, and set `tags:` to a single-element list matching that same topic** (for example, `tags: [AI-employment]`). After all items in the batch are filed, regenerate the index:

```bash
kb-index
```

The row's Summary cell renders from the `index_line` the agent already wrote; `index.md` is never hand-edited. Any warnings the command prints (missing frontmatter, topic drift, invalid date, duplicate rows) get relayed in the session's report and resolved, never silently absorbed.

**Without the script, regenerate the whole table yourself:** walk every `<topic>/*_summary.md` and `<topic>/*/*_summary.md`, render one row per file from its frontmatter, and write `index.md` in a single pass. **That is generation and is the correct fallback; appending or editing an individual row is what "never hand-edited" forbids** (see `SKILL.md`, Helper commands). Say in the report that the index was rebuilt by hand rather than by script, since the count-floor guard that protects against a truncated walk is the script's, not yours.

**Update `aa-recents/`** after all moves are complete. This folder holds symlinks to the most recently processed items (30 is a workable count), ranked by the `ingested:` date in each `_summary.md`'s frontmatter, descending, most recent first at rank `01`, with the summary's filesystem mtime as a tiebreaker for same-day ties (a summary lacking a valid `ingested:` field falls back to its mtime-derived date). Each symlink is named `NN - folder - basename.md` and carries its source file's mtime so sorting in a file browser reflects processing order, not rebuild date.

Rebuild by running the shared script:

```bash
kb-recents
```

The script validates all sources, wipes only the existing symlinks in `aa-recents/`, then creates the fresh set with `touch -h -r` applied so each symlink's mtime matches its source. It should exit nonzero without modifying anything if validation fails.

**Without the script, skip the rebuild and say so once in the report.** There is no hand fallback and no consequence: `aa-recents/` is a browse view, and the index, `kb search`, and `kb ask` all walk topic folders directly, so a stale or empty recents folder leaves the knowledge base fully correct.

**Refresh the search index.** After all moves and the recents rebuild are done, refresh the full-text database so the new items become findable via `kb search` and `kb ask` in this and future sessions:

```bash
kb-search reindex --incremental
```

An incremental run walks every topic folder but only re-reads and re-indexes items whose source files changed since the last reindex; everything else keeps its existing indexed row untouched, so this stays fast as the corpus grows. It should also prune rows whose files vanished from disk (stat-only, and guarded: nothing is pruned when the root is unreachable or when the vanish fraction exceeds a safety cap). Wall time is well under a minute. Best-effort; do not block the user-visible report on a reindex failure.

**Without a full-text index there is nothing to refresh:** skip this step silently, since `kb search` is then a `grep` over the same files and is current by definition.

**Report (after filing).** Present all filed items with the folder each landed in and the reason. **Always use the full renamed filename** (with date prefix) in the table; the date prefix is essential for sorting and identification.

> **Filed 3 items from inbox:**
>
> | # | Renamed file | Type | Filed to | Why |
> |---|---|---|---|---|
> | 1 | `2026-03-15 Autor. The Labor Market Impacts of AI.pdf` | 24pp PDF | **AI-employment/** | labor economics, AI impact on wages |
> | 2 | `2026-02-28 Mollick. Why Students Need AI Tutors.pdf` | 8pp PDF | **AI-teaching/** | AI in education, pedagogy |
> | 3 | `2025-12-01 Cowen. Economic Growth in 2026.md` | markdown | **other-articles/** | no clear existing-folder fit; filed to overflow (flagged) |
>
> Filed as above. To move any, say "move `<item>` to `<folder>`" and I will re-file.

**Rate usage report:** after the filed-items table, always include a rate usage report. This is mandatory regardless of whether items were processed by subagents or directly in the parent conversation.

Report each agent's item name, page count, token usage, and wall-clock time:

> **Rate usage:**
>
> | Agent | Item | Size | Tokens | Time |
> |-------|------|------|--------|------|
> | 1 | Core Memory Podcast | md | 42k | 2m |
> | 2 | Enterprise AI Market | 35pp | 99k | 9m |
> | 3 | Isik. Three Obstacles RAI | md | 28k | 1m |
> | | **Total** | | **169k** | **9m wall** |

Token counts come from the agent task notification `total_tokens` field. Wall time is the elapsed time from launch to the last agent completing (parallel agents share wall time). All items go through subagents, so this format applies to every run.

#### Correcting a filing

When the user redirects an item after it was auto-filed ("move `<item>` to `<folder>`", "that belongs in `<folder>`", or equivalent):

1. Move the item's per-document subfolder from its current topic folder into the named topic folder. (For a legacy flat item, move the source file, its `_summary.md`, and its `_text.md` if present.) If the named folder does not exist, create it (the user naming it is the approval) and add a one-line scope description to `topics.md`.
2. Update the **`topic:` field in the item's `_summary.md` frontmatter** to the new folder name. Leave any hand-added `tags:` entries alone; update the default topic tag only if it is still present unmodified. Then rerun `kb-index`; never edit an `index.md` row by hand.
3. Rebuild `aa-recents/` and refresh the search index (`kb-recents`, then `kb-search reindex --incremental`). The incremental reindex prunes the item's row under its **old** topic folder in the same run (its stored path no longer exists on disk), so the re-filed item appears once, under its new topic, immediately.

Sources are never deleted, so re-filing is fully reversible.

### Blog Post Processing (aa-blog/)

When processing items from `aa-blog/`, apply these overrides to Steps 1 to 5:

**Step 2 override (metadata):** author is always you. Extract the title and publication date from the content. If the publication date cannot be determined, use the file modification date. Blog posts may arrive in any format (md, html, pdf, docx, txt, and so on); apply the same file type routing as Step 1.

**Step 3 override (rename):** use the naming convention `YYYY-MM-DD AuthorName (blog). Title.ext`

The `(blog)` tag is mandatory. It distinguishes your own writing from external sources in topic folders and makes blog posts greppable across the entire knowledge base (`grep -r "(blog)" knowledge-base/`).

**Step 4 override (summary):** use this lighter template instead of the full academic or general summary. Blog posts are already condensed writing; a full structured summary would be redundant. The file still begins with the same frontmatter block as Step 4b, with `type: blog` and `authors:` set to your own name; the index generator renders the `[blog]` marker from `type: blog`, not from a hand-added tag.

```
# [Title]

**Author:** [Your name]
**Published:** YYYY-MM-DD
**URL:** [URL if known]
**Type:** blog

## Thesis
[1-2 sentences: the central argument or claim]

## Key Claims
- [claim 1]
- [claim 2]
- [claim 3-5]

## Sources Cited
- [source 1, Chicago Author-Date]
- [source 2]

## Context
[1-2 sentences: what prompted this post, what it responds to]
```

Do not use the academic or general summary skill for blog posts. Inline this template into the agent prompt instead.

**Step 5 override (index):** none needed. The generator appends `[blog]` to the Summary cell automatically from `type: blog` in the frontmatter. Blog posts are filed into existing topic folders alongside external sources, using the same topic suggestion process. They are not stored in a separate blog-only folder.

**No `_text.md` for blog posts.** The source file is the text. Only generate `_summary.md`.
