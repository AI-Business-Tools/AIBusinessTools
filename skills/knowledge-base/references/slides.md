### 5. Slides (`kb slides <target> [beamer] [lite] [structure=...] [register=...] [plan=...]`)

**Where this file's cross-references resolve.** This file is Mode 5 of the knowledge-base skill; `SKILL.md` is read first and stays loaded alongside it. **Where Step 2's Case A, Case B below the bar, or Case C says to invoke the Mode 1 (Process Inbox) flow, read `references/inbox.md` at that point and run its Steps 1 to 5 with the overrides stated there; do not improvise the ingestion.** A Case B reuse at the bar, every `tier=lite` invocation, and every build on the new-source deep route below never invoke Mode 1: do not open `references/inbox.md` on those paths. **Where Step 5's file-after step cites "Mode 3's move sequence (Steps 3 to 5)", read `references/move.md` at that point, and only then.** The frontmatter block, Citation metadata and naming, Index Format, the helper commands, and the Integration index-update hook stay in `SKILL.md`. The headless overrides are in `references/slides-headless.md`, read only when the `headless` token is present.

Build a slide deck from a knowledge-base item, an inbox item, an external file path, or a URL. The workflow owns the knowledge-base side on every path: it resolves `<target>` to a single source file, selects the generator and tier, files the source into the knowledge base (file-first on the beamer path, on a URL target, and on an item that is already filed; **file-after on the lite tier and on the new-source deep route below**), verifies the filed record is at the reuse bar, then hands the source to the generator. The default deliverable is a native editable deck built by your deck generator at its deep-read tier.

**Triggers:** `kb slides <target>`, `slides from kb <target>`, `build slides from <target>`.

**Generator and tier selection** (from the invocation tokens):

- **Default (no engine token): your deck generator, deep-read tier; file-first on an already-filed item, file-after on a source new to the knowledge base** (the new-source deep route below). The deliverable is a native editable `.pptx` with a review render beside it.
- **`beamer`: the Beamer pipeline via [slides-content](../slides-content/), which in turn runs [beamer](../beamer/); file-first.** The deliverable is a Beamer `_slides.pdf`.
- **`lite`: your deck generator's lite tier (fast extract), file-after** (Step 5).
- **`deck` is an accepted synonym of plain `kb slides`** (the default generator already is the deck generator). Documented redundant; kept for muscle memory.
- **`beamer` and `lite` together is ambiguous** (there is no lite Beamer); ask which was meant.

You can also wire thin named entries (`kb slides lite`, `kb slides beamer`) as separate skills that route into this mode with `generator=` and `tier=` preset. Those entries carry pointers, not copies; all flow logic stays here.

**Tokens this workflow does not itself consume are stripped at Step 1 and forwarded verbatim.** Any generator-specific bareword your deck generator accepts (an audit pass, a fix pass, a report flag) must be stripped from `<target>` at Step 1 along with the tokens above, and **must never reach the name-fragment matcher**: `kb slides ransbotham voice` must not search for the fragment `ransbotham voice` and report not-found. Forward the ones present contiguous at the very end of the handoff string, which is where a bareword parser expects them. **A generator-specific token on the beamer path is a terminal refusal**, never a silent drop, for the same reason `plan=` is: the Beamer workflow has no such stage, so a forwarded token would vanish and the deck would build as though nothing had been asked for. Refuse by naming the token, the generator that owns it, and the two ways out (drop the `beamer` token, or drop the review token).

**The slide-path model pin.** Every Mode 1 ingestion this mode invokes, on any path (the beamer path's Case A and Case C, a URL target's Case A ingestion, the Case B re-ingest, and the headless flow, which inherits these steps by reference), launches the reading agent with `model: opus, effort: high` regardless of content type, and pre-fills `model: opus` in the inlined frontmatter template. This is an invocation-time override; it never touches Mode 1's content-type model table, which continues to govern plain `kb` inbox processing and every other non-slide caller. The pin applies only where a Mode 1 ingestion actually runs; the lite tier never triggers one (Step 2), so the pin never reaches it, and **the new-source deep route below runs no Mode 1 ingestion at all**, so the pin has nothing to apply to there. That route's reading model is unchanged rather than dropped: your deck generator's own deep tier should carry the identical pin in its own rule.

**No split-folder exception on this path.** The deep-read split folder is deleted once `_text.md` is written, exactly as on a plain `kb` run. This mode's Case A override list carried the opposite instruction until the retention rule was withdrawn, and the consumer it named does not exist. That was searched rather than assumed: no script, hook, or skill reads chunk files out of a directory it did not create in the same run, and every skill that reuses a split at all checks for the text extract FIRST, which a filed item always has. A deck generator's figure extractor opens the source PDF itself and knows nothing of chunks. The chunks regenerate byte for byte in seconds from an original nothing deletes, so both routes hold one rule. Mode 1's Step 4a owns the deletion, names the single directory that is removed, and lists what is not. **On the new-source deep route below the split folder is created by the deck generator rather than by Mode 1, and the same rule holds there rather than a second one:** whatever creates the folder deletes it once the text file is written, with the same bound on what may be deleted.

**THE NEW-SOURCE DEEP ROUTE: on a source that is NEW to the knowledge base, the default deck tier does the whole read and this workflow files the results afterwards. This block is the ONLY statement of the route.** Step 2, Step 4, Step 5, and `references/inbox.md` point here; none of them restates it, and a second statement anywhere else is a defect rather than a helpful reminder.

**When it applies, written as a test rather than a description, and all three conditions must hold.** The generator is the deck generator (no `beamer` token); the tier is the default deep-read tier (no `lite` token); and `<target>` resolved to a FILE ON DISK that is new to the knowledge base, meaning an item sitting in `aa-inbox/` or an external path that is not already under a topic folder.

**When it does not apply, each case unchanged and each for its own reason.** An **already-filed item (Case B) is untouched**: its `_text.md` and `_summary.md` are already paid for, the generator's reuse path is the right one, and a below-bar record still pays its Mode 1 upgrade read in place, because the generator reuses a filed record as-is and never rewrites one, which leaves this workflow as the only party that can upgrade a record. The **beamer path keeps file-first**, because the Beamer workflow produces no source brief and there is nothing to recover there. A **URL target keeps file-first**, because the Source-fetch failure contract that sets `source_basis: partial` or `source_basis: excerpts` lives in `references/inbox.md` Step 1 and nothing in the deck generator ever sets that field; routing a URL around Mode 1 would drop the one marker that stops a web-search reconstruction being presented as the publication. The **lite tier is untouched**, having always been file-after.

**What the route does.** Run the scripted duplicate check on the filename stem, `kb-dup-check "<stem>"`, and act on `DUP`, `NEAR`, and `ERROR` exactly as Case C states. On `OK`, run NO Mode 1 ingestion: continue to Step 3 with the source where it sits, hand it to the deck generator at the default tier (Step 4), and file the finished set at Step 5. **The one artifact this recovers is the source brief, and that is the whole of the change.** A deep tier is a full deep read of the same source by one strong reading agent at effort high, and it writes three artifacts in that single pass: `<content_name>_text.md`, `<content_name>_summary.md` carrying the frontmatter block at `level: full, model: opus` with `topic:` and `tags:` left blank, and the build folder's source brief, which is the fidelity checklist the finished deck is graded against. Mode 1's ingestion writes the first two and no brief (`references/inbox.md` Step 4 names `_text.md` and `_summary.md` and no third artifact), so a filed item reached the generator missing exactly one of the three, the generator took its reuse path, and that path launches a standalone agent that reads the whole extract over again to produce it. Reading the source once instead of twice is what this route buys. The record it files lands at the reuse bar (`level: full` AND `model: opus`), so the next `kb slides` on the same item takes the zero-reading-cost Case B reuse.

**The fallback is NOT removed, and the distinction is the point: this route removes a GUARANTEED duplicate read, never the safety net.** If the generator's reading agent does not produce a usable brief, the generator's own brief stage falls through to a standalone brief agent and the deck is still built against a checklist rather than briefless. That fall-through is the generator's rule and is not restated here.

**Where the build sits while it runs, and what a failure leaves behind.** The deck generator decides its own output directory from the source path and the disk, and this workflow neither computes nor passes that decision. An inbox item gets a per-document folder inside `aa-inbox/` with the source moved into it, which also takes it out of the inbox's top-level listing so a later `kb` run does not meet it a second time; an external source among unrelated files gets a folder of the same shape beside it. **The one case to STOP AND ASK on is an external source with a `CLAUDE.md` or `CLAUDE.local.md` beside it**, which is what a project folder looks like: the generator builds IN PLACE there, and Step 5's file-after step would then move that folder's source and artifacts into the knowledge base. Ask whether the source should be filed at all, and name the pure-generator alternative (invoke your deck generator directly on the path), which builds the deck and files nothing. **If the build fails before Step 5 the source and whatever artifacts exist are in that folder rather than where they started:** name the folder in the failure report and stop; `kb move <dir> <topic>` files it by hand when the user wants it filed.

`<target>` is one of:
- A URL (starts `http://` or `https://`)
- A filesystem path (absolute or relative) that exists
- A name fragment (everything else)

`structure=` and `register=` are optional. When present, forward verbatim to the selected generator (both the deck generator and `slides-content` accept them). `structure=` values: `mba` (default), `teaching`, `faculty`, `professional`, `consulting`, `working`; `academic` and `default` are deprecated aliases for the default structure (`mba`), and the legacy `audience=` is accepted as an alias for `structure=`. `register=` values: `business` (default), `technical`.

`plan=<path>` names a slide plan written as its own file, for the case where the plan already exists and the deck implements it. It rides to the deck generator in the same handoff argument string `structure=` and `register=` do, and the generator owns the whole contract: it resolves the path to absolute form, refuses the run when the file is unreadable, and hands the plan to its brief producer, whose transcribed slots then govern the deck. Two things this mode owes it. **Forward an ABSOLUTE path, double-quoted** (expand `~` and resolve a relative path against the invocation's own working directory before passing it), because the generator runs from a different directory than this workflow resolved in, and an unquoted value truncates at its first space. **`plan=` on the beamer path is a terminal refusal**, never a silent drop: the Beamer workflow has no plan input, so a forwarded token would vanish and the deck would build as though no plan existed. Refuse with `Refused: plan= is deck-only; the Beamer workflow has no plan input. Drop the beamer token to build the plan as a native PPTX deck, or drop plan= to build a Beamer deck from the source alone.` The plan file must not change between the handoff and the generator's own checks resolving each plan reference against it.

#### Step 1: Resolve `<target>` to a single source file

Resolve in this order:

1. **URL** -> write a staging file at `aa-inbox/slides-YYYY-MM-DD-HHMMSS.urls` containing just that URL (one line). Continue at Step 2 (treated as an inbox item).
2. **Existing path** -> use directly. Continue at Step 2.
3. **Name fragment** ->
   a. Run `kb-search search "<target>"`. **Read its count line before counting anything: a widened, any-word pass contributes ZERO hits, however many rows it returns.** If no record contains every word of the fragment and your search widens to any-word matching, that pass is a relevance ranking of most of the corpus (measured: one five-word query's any-word pass matched 2,346 of 3,086 indexed rows), which makes its top rows candidates for nothing. Never show those rows to the user as a candidate list, and never pick one. If your search reports its match mode, read it; if it does not, add one, because the counts in (c) are written against exact-match hits only.
   b. Independently `ls aa-inbox/` for filenames containing the fragment (case-insensitive substring match). **This half is unaffected by (a)'s test:** a substring match on filenames never widens.
   c. Combine results:
      - **0 hits:** report not found and exit. A widened search result is zero here, so a fragment matching nothing in the knowledge base and nothing in the inbox exits from this line, not from the one below.
      - **1 hit:** use that path; continue at Step 2.
      - **2 or more hits:** present a numbered list (path, topic, one-line snippet) and wait for the user to pick.

#### Step 2: Determine the case; file-first (beamer, a URL target, an already-filed item) or defer to file-after (the lite tier, and a new source at the default deck tier)

**Lite tier (`tier=lite`): never a deep read; the file-first cases below do not apply.** The lite tier's entire cost premise is that it never pays for a deep read (Step 5 states this), so it does not run the Case A, B, and C file-first or re-read logic. Instead:

- **Source already under a topic folder:** reuse its existing record as-is, whatever the `level:` and `model:` (a `fast-extract` record is exactly right for lite, and a richer record is reused without a re-read); never re-ingest. Continue to Step 3. The item is already filed, so Step 5's file-after step reduces to the index refresh.
- **New source (inbox item, external path, or URL):** run the scripted dup-check on the stem (`kb-dup-check "<stem>" [--url <url>]`) but do NOT file yet. `DUP`: present the existing entry and ask (build from it as an already-filed item, reusing its artifacts, or stop). `NEAR` and `ERROR`: surface and ask before proceeding. `OK`: continue to Step 3 with the source at its current location. The generator's lite tier builds beside the source (fast extract, `level: fast-extract`, blank `topic:` and `tags:`), and Step 5's file-after step files the finished set.

**Default deck tier, source NEW to the knowledge base: the new-source deep route above, not Case A or Case C below.** That route runs the dup-check, files nothing yet, and hands the source to the deck generator at the default tier, which reads it once and emits the brief in the same pass; Step 5's file-after step then files the finished set. The route block above states when it applies and when it does not, and this line does not restate it.

The cases below (A, B, and C) cover **the beamer path, a URL target, and every already-filed item**; a `tier=lite` invocation never reaches them, and a NEW source at the default deck tier takes the route above instead of Case A or Case C.

- **Case A (source is in `aa-inbox/`; reached by the beamer path, and by every URL target, whose staging `.urls` file Step 1 writes into `aa-inbox/`):** invoke the existing Mode 1 (Process Inbox) flow on this single item, with three overrides:
  1. **No split-folder override** (above): the split folder is deleted here as on every other route. This slot carried the opposite instruction until the retention rule was withdrawn and is deliberately left in place, rather than renumbered, so a reader who remembers the exception finds it withdrawn instead of merely absent.
  2. The Step 5 file-then-report behavior applies (single row): the item is auto-filed into its best-fit folder with no confirmation pause, exactly as in Mode 1. The "Correcting a filing" path is available if the user redirects.
  3. **The slide-path model pin** (above): the reading agent launches with `model: opus, effort: high` regardless of content type, and the inlined frontmatter template carries `model: opus` pre-filled.

  After the item is auto-filed, control falls through to Case B with the new in-topic path (the fresh record is at the bar, so Case B reuses it).

- **Case B (source is already in a topic folder):** run the re-read rule, not a skip. Read the item's `_summary.md` frontmatter and apply the **reuse bar**:
  - **Reuse** when `level: full` AND `model: opus`, or when the record carries the grandfather sentinel `model: grandfathered`. Continue to Step 3 with the record as-is; this is the zero-reading-cost path.
  - **Below the bar** (anything else, including every legacy record with no `model:` field and no `grandfathered` sentinel): **re-ingest in place with the model pin, before any build money is spent.** Run the Mode 1 single-item deep-read flow on the item where it sits (its own subagent, split-and-read for PDFs, direct read for non-PDF sources, the same summary formats). Nothing moves and nothing renames; the existing `topic:` and `tags:` carry into the fresh frontmatter; first preserve the replaced `_text.md` and `_summary.md` as timestamped copies in the item folder (the same convention Source-fetch failure item 6 uses when replacing a reconstruction). The new record lands at `level: full, model: opus`. Then regenerate the index, rebuild `aa-recents/`, and refresh the full-text index (the Mode 1 Step 5 commands). Name the upgrade in the run report (for example, "record upgraded from `full`/`sonnet` to `full`/`opus`", or "from `fast-extract` (no model recorded)"). Continue to Step 3.
  - **Exception:** a record carrying `source_basis: excerpts` is never re-ingested (there is no captured source to read deeper); the provenance gate at the generator handoff governs it instead. Continue to Step 3 with the record as-is.
  - **Exception, `partial`:** a record carrying `source_basis: partial` IS re-ingested when it is below the bar, but **the `source_basis: partial` line carries into the fresh frontmatter, alongside `topic:` and `tags:`.** Re-reading cannot restore text the capture never had, and the re-reading agent has no way to tell a 97-word teaser from a 97-word article, so a fresh record would come back clean and the gate at the generator would never fire. Preserving the line is what stops a below-bar upgrade laundering the mark away. Where a re-ingest genuinely captures the full source (a URL that fetches this time), remove the line deliberately, per the Source-fetch failure rule's item 6.

  **The grandfather sentinel, defined:** `model: grandfathered` is a closed-format `model:` value set only by a one-time bulk backfill on records filed before the `model:` field existed. It marks a pre-existing record (whose true reading model is unknown) as trusted for slide-path reuse and keeps the record's real `level:`; new filing never writes it. A legacy record with neither the bar nor the sentinel is below-bar and pays its one upgrade read on first slide use.

- **Case C (source is outside the knowledge base and outside `aa-inbox/`, an external path; reached by the beamer path only, since a NEW external source at the default deck tier takes the new-source deep route above):** file it first; do not build beside an unfiled source. Run the scripted duplicate check on the filename stem (`kb-dup-check "<stem>" [--url <url>]`) and act on the result:
  - **`DUP`:** the source is already in the knowledge base. Present the existing entry and ask: build from the existing entry (continue at Case B with it, reusing its paid-for artifacts), file this copy anyway, or stop. Never silently substitute the existing entry (a same-titled revision must not reuse the old artifacts unasked).
  - **`NEAR` or `ERROR`:** surface the hit (or the failed check) and ask before filing.
  - **`OK`:** run the Mode 1 single-item flow on the file **regardless of its location** (the same rule the headless mode uses), with the same three overrides as Case A including the model pin, and auto-file into the best-fit topic folder. Then fall through to Case B with the new in-topic path.

  Filing failures stop the run here, before any build money is spent. The no-filing escape is to invoke the deck generator directly on the path, not this mode.

#### Step 3: Existing-slides check (per generator)

Compute the prospective output directory: `<parent>/<content_name>/` where `<content_name>` is the source filename without extension.

Check for the engine-appropriate deliverable: `<output_dir>/<content_name>_slides.pptx` for the deck tiers (default and lite), `<output_dir>/<content_name>_slides.pdf` for the beamer path. **The headless path checks the `.pptx`**, stated here because it sets no `generator=` and would otherwise be ambiguous: the unattended entry point builds through the deck generator and its deliverable is the `.pptx`, with a `.pdf` review render beside it, so testing the `.pdf` would find the render and report a deck that was never built. (For an item still at Pattern B, also check the same filename directly in `<topic_folder>/`, since promotion has not happened yet.)

If the deliverable is found, ask:

> Slides already exist at `<path>` (last built YYYY-MM-DD HH:MM). Rebuild (timestamp backup of the existing deck, then regenerate) or skip?

- **Rebuild:** back up the existing deliverable as `<content_name>_slides YYYY-MM-DD-HHMMSS.<ext>` in the same folder, then continue to Step 4.
- **Skip:** exit with `Slides already at <path>. No rebuild.` Do not touch any file.

If none exists, continue.

#### Step 4: Hand off to the generator

Invoke the selected generator via the Skill tool, passing the resolved (filed) source path and any forwarded arguments.

**Default and lite (deck tiers):**

```
Skill(skill="<your deck generator>", args='<absolute path to source>[ tier=lite][ structure="<value>"][ register="<value>"][ template="<path>"][ plan="<absolute path>"][ report][ useexcerpts][ usepartial]')
```

The deck generator reuses the filed `_text.md` and `_summary.md` (its stage-level reuse rules), so on a filed item it skips its own extraction and summary stages, promotes Pattern B to Pattern A, and delivers the native editable `.pptx` with the review render beside it. **That reuse sentence describes an ALREADY-FILED item. On the new-source deep route the source is not filed and no `_text.md` exists, so the generator runs its own deep tier and writes all three artifacts, the text, the summary, and the build's source brief, in one reading pass;** the route block above is where that is stated, and nothing in the handoff string changes for it (the tier token is absent, which is what selects the deep tier). **The handoff string carries only the tokens listed above; never invent one.** `useexcerpts` and `usepartial` appear there only as the receipt for a Provenance answer the user already gave (see Provenance below); they are barewords and must stay contiguous at the very end, after `report`, which is where a bareword parser expects them. The generator strips the tokens it recognizes and treats whatever remains as the target, so an unrecognized `key=value` is swallowed into the target text and breaks resolution.

**Beamer path:**

```
Skill(skill="slides-content", args="<absolute path to source>[ structure=<value>][ register=<value>]")
```

(a legacy `audience=` is forwarded unchanged; `plan=` never appears here, having been refused above). `slides-content` reuses `_text.md` as its notes file and `_summary.md` if present, promotes Pattern B to Pattern A, and runs the `beamer` compilation cycle and audit.

**Provenance: THIS MODE ASKS, in plain language, before the handoff.** Both degraded values gate, not only `excerpts`, and **the user is never asked to type a token.**

Read `source_basis:` from the resolved item's `_summary.md` frontmatter at Step 2, where this mode already opens that file for the reuse bar, and act before Step 4's handoff:

- `full-text`, or the field absent: continue silently.
- `partial` or `excerpts`: **ask once, in ordinary words**, and continue only on an explicit yes:

  > The filed source for this item is incomplete (`source_basis: <value>`): <what the record's own Source note says is missing>. A deck built from it would present <part of the source as the whole | a web-search reconstruction as the publication>. Build it anyway, or stop so the source can be captured properly first?

  On a yes, append the matching bareword (`usepartial` or `useexcerpts`) to the generator handoff string. **That token is a receipt for an answer already given in plain English, never something the user types.** On a no, stop without building.

**Why the ask lives here and not in the engine.** A non-interactive deck generator is allowed no interactive pause, so its own provenance check is a terminal refusal; asking there would mean refusing, reporting, and re-running. This mode holds the conversation and reads the frontmatter anyway, so the question costs nothing extra and the engine never refuses on this path. The Beamer workflow keeps its own confirm for a direct invocation that does not come through here; when it does come through here, this ask is the single confirm for the run and the Beamer workflow does not ask again.

**A typed bareword is accepted as pre-authorization and skips the ask.** `usepartial` and `useexcerpts` are part of this mode's own invocation grammar: strip them at Step 1 with the other tokens, never let them reach the name-fragment matcher (`kb slides ransbotham usepartial` must not search for the fragment `ransbotham usepartial` and report not-found), and treat their presence as the yes.

The headless path (`references/slides-headless.md`) hands off to an unattended entry point instead, which cannot ask: it refuses terminally on `excerpts` and, on `partial`, builds and carries the flag into the result line the queue reports.

#### Step 5: Post-build sync and filing verification

After the generator reports completion, run the **Index-update hook for content skills** (see the Integration section of `SKILL.md`): ensure the document's `_summary.md` carries the frontmatter block, then run `kb-index`. The slide artifact does not get its own index entry; the source document's entry covers it.

**The file-after step: the lite tier, and the new-source deep route.** This step files a NEW source that was built before it was filed, which is both file-after paths and nothing else. A build on an item that was ALREADY filed is already in its topic folder under its citation stem, so it skips the rename, dup-check, and move below and reduces to the index, recents, and full-text refresh. The lite tier builds beside a new source because file-first would pay a deep read and destroy the tier's cost target; the new-source deep route builds beside a new source because the generator's own read is the only read, and it produces the source brief that a pre-ingest read does not. This is Mode 3's move sequence (Steps 3 to 5) invoked as a workflow step, with no confirmation pause and no model time.

**What exists on disk by the time this step runs**, all of it written by the generator, none of it by an ingestion: the source (moved by the generator into its output directory when the placement promoted it, otherwise still where it was), `<content_name>_text.md`, `<content_name>_summary.md` already carrying the frontmatter block with `topic:` and `tags:` blank, the `.pptx` and its review render, and `<content_name>_build/` holding the source brief, the extracted figures, and the build's records. **NO SUMMARY AGENT RUNS HERE, on either file-after path, and none is launched to compose one:** the deep route's reading agent wrote `_summary.md` in the knowledge base's own format during its single read, and the lite tier's summary agent wrote it at its own summary stage, so this step READS that file rather than commissioning another.

In order:

1. **Read the citation metadata off `<content_name>_summary.md`'s frontmatter** (`title:`, `authors:`, `date:`) and compose the citation stem `YYYY-MM-DD Last. Title` from it (Mode 3 Step 3's rule; these are the same fields Mode 1 Step 2 would have extracted from the source, already on disk and needing no model).
2. **Rename the source and every artifact to that stem**, per Mode 3 Step 3's per-artifact list (source, `_summary.md`, `_text.md`, `_slides.pptx`, the review render, the `_build/` folder).
3. **Re-run the scripted dup-check on the RENAMED stem** (`kb-dup-check "<renamed stem>" [--url <url from the frontmatter>]`).
4. **Pick the topic folder** by reading `topics.md` and the item's `_summary.md`; never auto-create a topic folder, and file to the overflow folder with a flag when nothing fits, exactly as Mode 1 Step 5 does.
5. **Move the source, metadata, deliverables, and build folder into `<topic>/<stem>/`** (Pattern A), with `mv` and never `cp`, then verify every file arrived.
6. **Set `topic:` and `tags:`** in the moved `_summary.md` (`tags:` defaulting to `[<topic>]`).
7. **Run the knowledge-base updates in this order:** `kb-index`, then `kb-recents`, then `kb-search reindex --incremental`. The last is best-effort and does not block the report.

A `DUP` at step 3 arrives after the deck already shipped: flag it loudly (deck delivered, filing blocked on the named existing entry, exact manual step stated) and never un-build.

**Post-build assertion (every filed path).** Verify the deliverable sits under the topic folder and the citation stem appears in `index.md` (a grep, per the index-first conventions). On a miss, report it with the exact manual step (`kb move <dir> <topic>`); do not self-heal.

If Case A or Case C ran, the inbox flow has already refreshed `aa-recents/` and the full-text index; a Case B re-ingest refreshed them during the upgrade; a Case B reuse needs no additional reindex; the lite tier and the new-source deep route refresh them in the file-after step above, which is the only place they are refreshed on either of those paths.
