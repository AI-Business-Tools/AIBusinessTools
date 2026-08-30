### 5. Slides (`kb slides <target> [beamer] [deck] [lite] [structure=...] [register=...] [plan=...]`)

**This file is procedure Claude follows, not a checklist you work through.** It is written for the model: the steps, agent parameters, model pins, token budgets, and handoff strings below are instructions Claude executes during a `kb slides` run. As a user you type `kb slides <target>` and read the result. Read this file when you want to know what the run will do, or when you are adapting the skill to your own tools.

**Where this file's cross-references resolve.** This file is Mode 5 of the knowledge-base skill; `SKILL.md` is read first and stays loaded alongside it. **Where Step 2's Case A, Case B below the bar, or Case C says to invoke the Mode 1 (Process Inbox) flow, read `references/inbox.md` at that point and run its Steps 1 to 5 with the overrides stated there; do not improvise the ingestion.** A Case B reuse at the bar, every `tier=lite` invocation, and every build on the new-source deep route below never invoke Mode 1: do not open `references/inbox.md` on those paths. **Where Step 5's file-after step cites "Mode 3's move sequence (Steps 3 to 5)", read `references/move.md` at that point, and only then.** The frontmatter block, Citation metadata and naming, Index Format, the helper commands, and the Integration index-update hook stay in `SKILL.md`. The headless overrides are in `references/slides-headless.md`, read only when the `headless` token is present.

Build a slide deck from a knowledge-base item, an inbox item, an external file path, or a URL. The workflow owns the knowledge-base side on every path: it resolves `<target>` to a single source file, selects the generator and tier, files the source into the knowledge base (file-first on the default Beamer route, on a URL target, and on an item that is already filed; **file-after on the deck generator's lite tier and on its new-source deep route below**), verifies the filed record is at the reuse bar, then hands the source to the generator. **The default deliverable is a compiled Beamer PDF built through [slides-content](../../slides-content/), which in turn runs [beamer](../../beamer/).** Both ship in this repository, so the default route works on a fresh install with nothing wired.

**Triggers:** `kb slides <target>`, `slides from kb <target>`, `build slides from <target>`.

#### Generator and tier selection (from the invocation tokens)

- **Default (no engine token): the Beamer route via `slides-content`, which runs `beamer`; file-first on every path.** The deliverable is `<content_name>_slides.pdf`, a compiled Beamer PDF, with an optional `<content_name>.pptx` that `slides-content` offers to produce at its own final step. This route needs no configuration.
- **`beamer`: the same route, named explicitly.** Accepted so an invocation can say which engine it means. It selects nothing the default does not already select.
- **`deck`: an OPTIONAL deck generator you supply, at its deep-read tier.** The deliverable is a native editable `.pptx` with a review render beside it. **No such generator ships in this repository.** See "The optional deck generator" below before using this token.
- **`lite`: the optional deck generator's lite tier (fast extract), file-after** (Step 5). Same prerequisite as `deck`.
- **`beamer` and `lite` together is ambiguous** (there is no lite Beamer); ask which was meant.

#### The optional deck generator

The `deck` and `lite` tokens hand off to a native PowerPoint generator that **this repository does not ship**. The handoff below is a placeholder naming `<your deck generator>`. Wire it only if you already have such a skill installed, by replacing that placeholder in Step 4 with your generator's skill name.

**If you have not supplied one, `deck` and `lite` do not work, and the run must say so rather than fail obscurely.** The test is mechanical: the Step 4 deck handoff still reads the literal placeholder `<your deck generator>`, unedited. When that is true and the invocation carries `deck` or `lite`, refuse before spending anything:

> `Refused: the deck and lite tokens need a native PowerPoint generator, and none is wired into this skill (the Step 4 handoff is still the <your deck generator> placeholder). Drop the token to build a Beamer PDF through slides-content, which is the default and needs no setup, or edit references/slides.md Step 4 to name your own generator.`

Everything below that is written for the deck generator (the new-source deep route, the lite tier, the file-after step, the `.pptx` existing-slides check, the `usepartial` and `useexcerpts` barewords, and `plan=`) is reachable only once that placeholder is replaced. On a fresh install none of it runs.

You can also wire thin named entries (`kb slides lite`, `kb slides beamer`) as separate skills that route into this mode with `generator=` and `tier=` preset. Those entries carry pointers, not copies; all flow logic stays here.

#### Moving a source that came from outside the knowledge base: ASK FIRST

**This block is the only statement of the rule.** Case C and Step 5's file-after step point here; neither restates it.

Filing moves a file. When the source came from outside the knowledge base, meaning `<target>` resolved to a path that is neither inside `aa-inbox/` nor already under a topic folder, **the move takes it out of the folder the user keeps it in**, and `kb slides ~/Documents/thesis.pdf` would otherwise silently empty that slot in Documents. So on that one class of source, after the destination topic folder is chosen and before anything is moved, ask once:

> `<source filename>` came from `<exact absolute origin path>`. Filing it moves it to `<exact absolute destination path>`, so it will no longer be in its original folder. Move it, copy it (leaving the original where it is), or stop without filing?

- **Move:** proceed with `mv`, the normal filing behavior.
- **Copy:** `cp` the source into the destination instead, leave the original untouched, and continue with the copy as the resolved source. This is the same reasoning `references/inbox.md` Flow step 1a branch 2 uses when it copies rather than moves a local path named in a `.urls` file: the original may be a document you keep inside another tool's folder.
- **Stop:** do not file. On the file-first path, the deck is not built either, and the no-filing escape is to invoke a generator directly on the path. On the file-after path the deck already exists; report where it sits and that nothing was filed.

**No confirmation for a source that was already inside the knowledge base.** An item in `aa-inbox/` was put there to be filed, and an item already under a topic folder is not moving at all. Both keep the no-pause behavior Mode 1 Step 5 defines. A URL target also keeps it: Step 1 writes its staging file into `aa-inbox/`, so it is an inbox item from that point on.

#### Forwarding and refusing tokens

**Tokens this workflow does not itself consume are stripped at Step 1 and forwarded verbatim.** Any generator-specific bareword your deck generator accepts (an audit pass, a fix pass, a report flag) must be stripped from `<target>` at Step 1 along with the tokens above, and **must never reach the name-fragment matcher**: `kb slides ransbotham voice` must not search for the fragment `ransbotham voice` and report not-found. Forward the ones present contiguous at the very end of the handoff string, which is where a bareword parser expects them. **A generator-specific token on the default Beamer route is a terminal refusal**, never a silent drop, for the same reason `plan=` is: `slides-content` has no such stage, so a forwarded token would vanish and the deck would build as though nothing had been asked for. Refuse by naming the token, the generator that owns it, and the two ways out (add the `deck` token, if you have wired a deck generator, or drop the review token).

**The slide-path model pin.** Every Mode 1 ingestion this mode invokes, on any path (the default route's Case A and Case C, a URL target's Case A ingestion, the Case B re-ingest, and the headless flow, which inherits these steps by reference), launches the reading agent with `model: opus, effort: high` regardless of content type, and pre-fills `model: opus` in the inlined frontmatter template. This is an invocation-time override; it never touches Mode 1's content-type model table, which continues to govern plain `kb` inbox processing and every other non-slide caller. The pin applies only where a Mode 1 ingestion actually runs; the lite tier never triggers one (Step 2), so the pin never reaches it, and **the new-source deep route below runs no Mode 1 ingestion at all**, so the pin has nothing to apply to there. That route's reading model is unchanged rather than dropped: a deck generator's own deep tier should carry the identical pin in its own rule.

**No split-folder exception on this path.** The deep-read split folder is deleted once `_text.md` is written, exactly as on a plain `kb` run. This mode's Case A override list carried the opposite instruction until the retention rule was withdrawn, and the consumer it named does not exist. That was searched rather than assumed: no script, hook, or skill reads chunk files out of a directory it did not create in the same run, and every skill that reuses a split at all checks for the text extract FIRST, which a filed item always has. `slides-content` skips splitting outright whenever `_text.md` is already present, and a deck generator's figure extractor opens the source PDF itself and knows nothing of chunks. The chunks regenerate byte for byte in seconds from an original nothing deletes, so both routes hold one rule. Mode 1's Step 4a owns the deletion, names the single directory that is removed, and lists what is not. **On the new-source deep route below the split folder is created by the deck generator rather than by Mode 1, and the same rule holds there rather than a second one:** whatever creates the folder deletes it once the text file is written, with the same bound on what may be deleted.

#### The new-source deep route (deck generator only)

**On a source that is NEW to the knowledge base, the optional deck generator's deep tier does the whole read and this workflow files the results afterwards. This block is the ONLY statement of the route.** Step 2, Step 4, Step 5, and `references/inbox.md` point here; none of them restates it, and a second statement anywhere else is a defect rather than a helpful reminder. **The route is unreachable until a deck generator is wired** (see "The optional deck generator" above); on a fresh install every new source takes Case A or Case C instead.

**When it applies, written as a test rather than a description, and all four conditions must hold.** A deck generator is wired; the invocation carries the `deck` token; the tier is that generator's default deep-read tier (no `lite` token); and `<target>` resolved to a FILE ON DISK that is new to the knowledge base, meaning an item sitting in `aa-inbox/` or an external path that is not already under a topic folder.

**When it does not apply, each case unchanged and each for its own reason.** An **already-filed item (Case B) is untouched**: its `_text.md` and `_summary.md` are already paid for, the generator's reuse path is the right one, and a below-bar record still pays its Mode 1 upgrade read in place, because a generator reuses a filed record as-is and never rewrites one, which leaves this workflow as the only party that can upgrade a record. The **default Beamer route keeps file-first**, because `slides-content` produces no source brief and there is nothing to recover there. A **URL target keeps file-first**, because the Source-fetch failure contract that sets `source_basis: partial` or `source_basis: excerpts` lives in `references/inbox.md` Step 1 and nothing in a deck generator ever sets that field; routing a URL around Mode 1 would drop the one marker that stops a web-search reconstruction being presented as the publication. The **lite tier is untouched**, having always been file-after.

**What the route does.** Run the duplicate check on the filename stem, `kb-dup-check "<stem>"` (**without the script:** `grep -i -F "<stem>" index.md`, and additionally `grep -i -F "<url>" index.md` when a URL is known, which is a targeted lookup, not the whole-file read the duplicate-check rule forbids; a hit is a `DUP`, no hit is an `OK`, and a grep that errors, on a missing or unreadable `index.md`, is an `ERROR`). Act on `DUP`, `NEAR`, and `ERROR` exactly as Case C states. On `OK`, run NO Mode 1 ingestion: continue to Step 3 with the source where it sits, hand it to the deck generator at the default tier (Step 4), and file the finished set at Step 5. **The one artifact this recovers is the source brief, and that is the whole of the change.** A deep tier is a full deep read of the same source by one strong reading agent at effort high, and it writes three artifacts in that single pass: `<content_name>_text.md`, `<content_name>_summary.md` carrying the frontmatter block at `level: full, model: opus` with `topic:` and `tags:` left blank, and the build folder's source brief, which is the fidelity checklist the finished deck is graded against. Mode 1's ingestion writes the first two and no brief (`references/inbox.md` Step 4 names `_text.md` and `_summary.md` and no third artifact), so a filed item reached the generator missing exactly one of the three, the generator took its reuse path, and that path launches a standalone agent that reads the whole extract over again to produce it. Reading the source once instead of twice is what this route buys. The record it files lands at the reuse bar (`level: full` AND `model: opus`), so the next `kb slides` on the same item takes the zero-reading-cost Case B reuse.

**The fallback is NOT removed, and the distinction is the point: this route removes a GUARANTEED duplicate read, never the safety net.** If the generator's reading agent does not produce a usable brief, the generator's own brief stage falls through to a standalone brief agent and the deck is still built against a checklist rather than briefless. That fall-through is the generator's rule and is not restated here.

**Where the build sits while it runs, and what a failure leaves behind.** The deck generator decides its own output directory from the source path and the disk, and this workflow neither computes nor passes that decision. An inbox item gets a per-document folder inside `aa-inbox/` with the source moved into it, which also takes it out of the inbox's top-level listing so a later `kb` run does not meet it a second time; an external source among unrelated files gets a folder of the same shape beside it. **The one case to STOP AND ASK on is an external source with a `CLAUDE.md` or `CLAUDE.local.md` beside it**, which is what a project folder looks like: the generator builds IN PLACE there, and Step 5's file-after step would then move that folder's source and artifacts into the knowledge base. Ask whether the source should be filed at all, and name the pure-generator alternative (invoke your deck generator directly on the path), which builds the deck and files nothing. **If the build fails before Step 5 the source and whatever artifacts exist are in that folder rather than where they started:** name the folder in the failure report and stop; `kb move <dir> <topic>` files it by hand when the user wants it filed.

#### Target and parameters

`<target>` is one of:
- A URL (starts `http://` or `https://`)
- A filesystem path (absolute or relative) that exists
- A name fragment (everything else)

`structure=` and `register=` are optional. When present, forward verbatim to the selected generator (`slides-content` accepts both, and a deck generator should). `structure=` values: `mba` (default), `teaching`, `faculty`, `professional`, `consulting`, `working`; `academic` and `default` are deprecated aliases for the default structure (`mba`), and the legacy `audience=` is accepted as an alias for `structure=`. `register=` values: `business` (default), `technical`.

`plan=<path>` names a slide plan written as its own file, for the case where the plan already exists and the deck implements it. **It is a deck-generator parameter and reaches nothing else.** It rides to the deck generator in the same handoff argument string `structure=` and `register=` do, and that generator owns the whole contract: it resolves the path to absolute form, refuses the run when the file is unreadable, and hands the plan to its brief producer, whose transcribed slots then govern the deck. Two things this mode owes it. **Forward an ABSOLUTE path, double-quoted** (expand `~` and resolve a relative path against the invocation's own working directory before passing it), because the generator runs from a different directory than this workflow resolved in, and an unquoted value truncates at its first space. **`plan=` without the `deck` token is a terminal refusal**, never a silent drop: `slides-content` has no plan input, so a forwarded token would vanish and the deck would build as though no plan existed. Refuse with `Refused: plan= is deck-only; the Beamer route through slides-content has no plan input. Add the deck token to build the plan as a native PPTX deck through your own deck generator, or drop plan= to build a Beamer deck from the source alone.` The plan file must not change between the handoff and the generator's own checks resolving each plan reference against it.

#### Step 1: Resolve `<target>` to a single source file

Resolve in this order:

1. **URL** -> write a staging file at `aa-inbox/slides-YYYY-MM-DD-HHMMSS.urls` containing just that URL (one line). Continue at Step 2 (treated as an inbox item).
2. **Existing path** -> use directly. Continue at Step 2.
3. **Name fragment** ->
   a. Run `kb-search search "<target>"`. **Read its count line before counting anything: a widened, any-word pass contributes ZERO hits, however many rows it returns.** If no record contains every word of the fragment and your search widens to any-word matching, that pass is a relevance ranking of most of the corpus (measured: one five-word query's any-word pass matched 2,346 of 3,086 indexed rows), which makes its top rows candidates for nothing. Never show those rows to the user as a candidate list, and never pick one. If your search reports its match mode, read it; if it does not, add one, because the counts in (c) are written against exact-match hits only. **Without the search script,** `grep -ril "<target>" <knowledge-base-root>/*/*_summary.md <knowledge-base-root>/*/*/*_summary.md` is the fallback; it cannot rank and cannot widen, so every hit it returns is an exact-substring hit and counts.
   b. Independently `ls aa-inbox/` for filenames containing the fragment (case-insensitive substring match). **This half is unaffected by (a)'s test:** a substring match on filenames never widens.
   c. Combine results:
      - **0 hits:** report not found and exit. A widened search result is zero here, so a fragment matching nothing in the knowledge base and nothing in the inbox exits from this line, not from the one below.
      - **1 hit:** use that path; continue at Step 2.
      - **2 or more hits:** present a numbered list (path, topic, one-line snippet) and wait for the user to pick.

#### Step 2: Determine the case; file-first (the default Beamer route, a URL target, an already-filed item) or defer to file-after (the deck generator's lite tier, and a new source at its deep tier)

**Lite tier (`tier=lite`, deck generator only): never a deep read; the file-first cases below do not apply.** The lite tier's entire cost premise is that it never pays for a deep read (Step 5 states this), so it does not run the Case A, B, and C file-first or re-read logic. Instead:

- **Source already under a topic folder:** reuse its existing record as-is, whatever the `level:` and `model:` (a `fast-extract` record is exactly right for lite, and a richer record is reused without a re-read); never re-ingest. Continue to Step 3. The item is already filed, so Step 5's file-after step reduces to the index refresh.
- **New source (inbox item, external path, or URL):** run the duplicate check on the stem (`kb-dup-check "<stem>" [--url <url>]`; **without the script,** the targeted `grep index.md` described under Case C) but do NOT file yet. `DUP`: present the existing entry and ask (build from it as an already-filed item, reusing its artifacts, or stop). `NEAR` and `ERROR`: surface and ask before proceeding. `OK`: continue to Step 3 with the source at its current location. The generator's lite tier builds beside the source (fast extract, `level: fast-extract`, blank `topic:` and `tags:`), and Step 5's file-after step files the finished set.

**Deck generator's deep tier, source NEW to the knowledge base: the new-source deep route above, not Case A or Case C below.** That route runs the duplicate check, files nothing yet, and hands the source to the deck generator at its deep tier, which reads it once and emits the brief in the same pass; Step 5's file-after step then files the finished set. The route block above states when it applies and when it does not, and this line does not restate it.

The cases below (A, B, and C) cover **the default Beamer route, a URL target, and every already-filed item**, which on a fresh install is every run there is. A `tier=lite` invocation never reaches them, and a NEW source at a wired deck generator's deep tier takes the route above instead of Case A or Case C.

- **Case A (source is in `aa-inbox/`; reached by the default Beamer route, and by every URL target, whose staging `.urls` file Step 1 writes into `aa-inbox/`):** invoke the existing Mode 1 (Process Inbox) flow on this single item, with three overrides:
  1. **No split-folder override** (above): the split folder is deleted here as on every other route. This slot carried the opposite instruction until the retention rule was withdrawn and is deliberately left in place, rather than renumbered, so a reader who remembers the exception finds it withdrawn instead of merely absent.
  2. The Step 5 file-then-report behavior applies (single row): the item is auto-filed into its best-fit folder with no confirmation pause, exactly as in Mode 1. The item is already inside the knowledge base, so the outside-source confirmation above does not apply here. The "Correcting a filing" path is available if the user redirects.
  3. **The slide-path model pin** (above): the reading agent launches with `model: opus, effort: high` regardless of content type, and the inlined frontmatter template carries `model: opus` pre-filled.

  After the item is auto-filed, control falls through to Case B with the new in-topic path (the fresh record is at the bar, so Case B reuses it).

- **Case B (source is already in a topic folder):** run the re-read rule, not a skip. Read the item's `_summary.md` frontmatter and apply the **reuse bar**:
  - **Reuse** when `level: full` AND `model: opus`, or when the record carries the grandfather sentinel `model: grandfathered`. Continue to Step 3 with the record as-is; this is the zero-reading-cost path.
  - **Below the bar** (anything else, including every legacy record with no `model:` field and no `grandfathered` sentinel): **re-ingest in place with the model pin, before any build money is spent.** Run the Mode 1 single-item deep-read flow on the item where it sits (its own subagent, split-and-read for PDFs, direct read for non-PDF sources, the same summary formats). Nothing moves and nothing renames; the existing `topic:` and `tags:` carry into the fresh frontmatter; first preserve the replaced `_text.md` and `_summary.md` as timestamped copies in the item folder (the same convention Source-fetch failure item 6 uses when replacing a reconstruction). The new record lands at `level: full, model: opus`. Then regenerate the index, rebuild `aa-recents/`, and refresh the full-text index (the Mode 1 Step 5 commands). Name the upgrade in the run report (for example, "record upgraded from `full`/`sonnet` to `full`/`opus`", or "from `fast-extract` (no model recorded)"). Continue to Step 3.
  - **Exception:** a record carrying `source_basis: excerpts` is never re-ingested (there is no captured source to read deeper); the provenance gate at the generator handoff governs it instead. Continue to Step 3 with the record as-is.
  - **Exception, `partial`:** a record carrying `source_basis: partial` IS re-ingested when it is below the bar, but **the `source_basis: partial` line carries into the fresh frontmatter, alongside `topic:` and `tags:`.** Re-reading cannot restore text the capture never had, and the re-reading agent has no way to tell a 97-word teaser from a 97-word article, so a fresh record would come back clean and the gate at the generator would never fire. Preserving the line is what stops a below-bar upgrade laundering the mark away. Where a re-ingest genuinely captures the full source (a URL that fetches this time), remove the line deliberately, per the Source-fetch failure rule's item 6.

  **The grandfather sentinel, defined:** `model: grandfathered` is a closed-format `model:` value set only by a one-time bulk backfill on records filed before the `model:` field existed. It marks a pre-existing record (whose true reading model is unknown) as trusted for slide-path reuse and keeps the record's real `level:`; new filing never writes it. A legacy record with neither the bar nor the sentinel is below-bar and pays its one upgrade read on first slide use.

- **Case C (source is outside the knowledge base and outside `aa-inbox/`, an external path; reached by the default Beamer route, and by any run where no deck generator is wired):** file it first; do not build beside an unfiled source. Run the duplicate check on the filename stem (`kb-dup-check "<stem>" [--url <url>]`) and act on the result:
  - **`DUP`:** the source is already in the knowledge base. Present the existing entry and ask: build from the existing entry (continue at Case B with it, reusing its paid-for artifacts), file this copy anyway, or stop. Never silently substitute the existing entry (a same-titled revision must not reuse the old artifacts unasked).
  - **`NEAR` or `ERROR`:** surface the hit (or the failed check) and ask before filing.
  - **`OK`:** run the Mode 1 single-item flow on the file **regardless of its location** (the same rule the headless mode uses), with the same three overrides as Case A, plus a fourth: **the outside-source confirmation above replaces Case A's no-pause filing.** Determine the best-fit topic folder as Mode 1 Step 5 does, then ask before the move, naming the exact origin path and the exact destination path. On a move or a copy, file and fall through to Case B with the new in-topic path. On a stop, build nothing and file nothing.

  **Without the duplicate-check script,** run the targeted lookup instead: `grep -i -F "<stem>" index.md`, plus `grep -i -F "<url>" index.md` when the item's URL is known. A hit is a `DUP` (show the matched row as the existing entry), no hit is an `OK`, and a grep that cannot run, because `index.md` is missing or unreadable, is an `ERROR`. `NEAR` has no fallback equivalent; a fuzzy match needs the script. **This is a targeted lookup on one stem, not the whole-file `index.md` read the duplicate-check rule forbids**, and it is the sanctioned substitute everywhere `kb-dup-check` is called.

  Filing failures stop the run here, before any build money is spent. The no-filing escape is to invoke `slides-content` directly on the path, not this mode.

#### Step 3: Existing-slides check (per generator)

Compute the prospective output directory: `<parent>/<content_name>/` where `<content_name>` is the source filename without extension.

Check for the engine-appropriate deliverable: **`<output_dir>/<content_name>_slides.pdf` for the default Beamer route**, `<output_dir>/<content_name>_slides.pptx` for a wired deck generator's tiers (deep and lite). **The headless path checks the `.pptx`**, stated here because it sets no `generator=` and would otherwise be ambiguous: the unattended entry point an adopter supplies builds through a deck generator and its deliverable is the `.pptx`, with a `.pdf` review render beside it, so testing the `.pdf` would find the render and report a deck that was never built. (For an item still at Pattern B, also check the same filename directly in `<topic_folder>/`, since promotion has not happened yet.)

If the deliverable is found, ask:

> Slides already exist at `<path>` (last built YYYY-MM-DD HH:MM). Rebuild (timestamp backup of the existing deck, then regenerate) or skip?

- **Rebuild:** back up the existing deliverable as `<content_name>_slides YYYY-MM-DD-HHMMSS.<ext>` in the same folder, then continue to Step 4.
- **Skip:** exit with `Slides already at <path>. No rebuild.` Do not touch any file.

If none exists, continue.

#### Step 4: Hand off to the generator

Invoke the selected generator via the Skill tool, passing the resolved (filed) source path and any forwarded arguments.

**Default (the Beamer route, and the `beamer` token):**

```
Skill(skill="slides-content", args="<absolute path to source>[ structure=<value>][ register=<value>]")
```

(a legacy `audience=` is forwarded unchanged; `plan=` never appears here, having been refused above). `slides-content` reuses `_text.md` as its notes file and `_summary.md` if present, promotes Pattern B to Pattern A, runs the `beamer` compilation cycle and audit, and delivers `<content_name>_slides.pdf`. At its own final step it offers to convert the deck to `<content_name>.pptx`; that offer is `slides-content`'s, not this mode's, and either answer is fine here.

**Deck generator (the `deck` and `lite` tokens), only once you have wired one:**

```
Skill(skill="<your deck generator>", args='<absolute path to source>[ tier=lite][ structure="<value>"][ register="<value>"][ template="<path>"][ plan="<absolute path>"][ report][ useexcerpts][ usepartial]')
```

**Replace `<your deck generator>` with your generator's skill name before using the `deck` or `lite` token; while it reads as written, both tokens are refused (see "The optional deck generator" above).** A deck generator reuses the filed `_text.md` and `_summary.md` (its stage-level reuse rules), so on a filed item it skips its own extraction and summary stages, promotes Pattern B to Pattern A, and delivers the native editable `.pptx` with the review render beside it. **That reuse sentence describes an ALREADY-FILED item. On the new-source deep route the source is not filed and no `_text.md` exists, so the generator runs its own deep tier and writes all three artifacts, the text, the summary, and the build's source brief, in one reading pass;** the route block above is where that is stated, and nothing in the handoff string changes for it (the tier token is absent, which is what selects the deep tier). **The handoff string carries only the tokens listed above; never invent one.** `useexcerpts` and `usepartial` appear there only as the receipt for a Provenance answer the user already gave (see Provenance below); they are barewords and must stay contiguous at the very end, after `report`, which is where a bareword parser expects them. The generator strips the tokens it recognizes and treats whatever remains as the target, so an unrecognized `key=value` is swallowed into the target text and breaks resolution.

**Provenance: THIS MODE ASKS, in plain language, before the handoff.** Both degraded values gate, not only `excerpts`, and **the user is never asked to type a token.**

Read `source_basis:` from the resolved item's `_summary.md` frontmatter at Step 2, where this mode already opens that file for the reuse bar, and act before Step 4's handoff:

- `full-text`, or the field absent: continue silently.
- `partial` or `excerpts`: **ask once, in ordinary words**, and continue only on an explicit yes:

  > The filed source for this item is incomplete (`source_basis: <value>`): <what the record's own Source note says is missing>. A deck built from it would present <part of the source as the whole | a web-search reconstruction as the publication>. Build it anyway, or stop so the source can be captured properly first?

  On a yes on the deck path, append the matching bareword (`usepartial` or `useexcerpts`) to the generator handoff string. **That token is a receipt for an answer already given in plain English, never something the user types.** On the default Beamer route there is no such token to append: record the answer in the run report instead, and name the provenance value beside the delivered deck so the deck is never handed on as though its source were complete. On a no, stop without building.

**Why the ask lives here and not in the engine.** `slides-content` and `beamer` read no provenance field and have no gate of their own, so **on the default route this ask is the only thing standing between a web-search reconstruction and a deck presented as the publication.** It is not a duplicate confirm and must not be skipped. On the deck path the reasoning is different but the placement is the same: a non-interactive generator is allowed no interactive pause, so its own provenance check is a terminal refusal, and asking there would mean refusing, reporting, and re-running. This mode holds the conversation and reads the frontmatter anyway, so the question costs nothing extra.

**A typed bareword is accepted as pre-authorization and skips the ask.** `usepartial` and `useexcerpts` are part of this mode's own invocation grammar on every route: strip them at Step 1 with the other tokens, never let them reach the name-fragment matcher (`kb slides ransbotham usepartial` must not search for the fragment `ransbotham usepartial` and report not-found), and treat their presence as the yes.

The headless path (`references/slides-headless.md`) hands off to an unattended entry point you supply, which cannot ask: it refuses terminally on `excerpts` and, on `partial`, builds and carries the flag into the result line the queue reports.

#### Step 5: Post-build sync and filing verification

After the generator reports completion, run the **Index-update hook for content skills** (see the Integration section of `SKILL.md`): ensure the document's `_summary.md` carries the frontmatter block, then run `kb-index`. The slide artifact does not get its own index entry; the source document's entry covers it.

**`slides-content` writes a `_summary.md` in its own format and does NOT add the frontmatter block.** On the default route, the hook's first half is real work rather than a formality: read the summary it produced, add the frontmatter block from `SKILL.md` in front of it if the block is absent, set `topic:` to the containing folder and `tags:` to `[<topic>]`, and only then regenerate the index. A summary without the block gets a degraded, flagged index row.

**The file-after step: the deck generator's lite tier, and its new-source deep route.** This step files a NEW source that was built before it was filed, which is both file-after paths and nothing else, and **both are reachable only once a deck generator is wired.** A build on an item that was ALREADY filed is already in its topic folder under its citation stem, so it skips the rename, duplicate check, and move below and reduces to the index, recents, and full-text refresh. The lite tier builds beside a new source because file-first would pay a deep read and destroy the tier's cost target; the new-source deep route builds beside a new source because the generator's own read is the only read, and it produces the source brief that a pre-ingest read does not. This is Mode 3's move sequence (Steps 3 to 5) invoked as a workflow step, with no model time and, for a source that was already inside the knowledge base, no confirmation pause. **For a source that came from outside the knowledge base, the outside-source confirmation above applies here too**, asked at sub-step 4 below once the destination folder is known.

**What exists on disk by the time this step runs**, all of it written by the deck generator, none of it by an ingestion: the source (moved by the generator into its output directory when the placement promoted it, otherwise still where it was), `<content_name>_text.md`, `<content_name>_summary.md` already carrying the frontmatter block with `topic:` and `tags:` blank, the `.pptx` and its review render, and `<content_name>_build/` holding the source brief, the extracted figures, and the build's records. **NO SUMMARY AGENT RUNS HERE, on either file-after path, and none is launched to compose one:** the deep route's reading agent wrote `_summary.md` in the knowledge base's own format during its single read, and the lite tier's summary agent wrote it at its own summary stage, so this step READS that file rather than commissioning another.

In order:

1. **Read the citation metadata off `<content_name>_summary.md`'s frontmatter** (`title:`, `authors:`, `date:`) and compose the citation stem `YYYY-MM-DD Last. Title` from it (Mode 3 Step 3's rule; these are the same fields Mode 1 Step 2 would have extracted from the source, already on disk and needing no model).
2. **Rename the source and every artifact to that stem**, per Mode 3 Step 3's per-artifact list (source, `_summary.md`, `_text.md`, `_slides.pptx`, the review render, the `_build/` folder).
3. **Re-run the duplicate check on the RENAMED stem** (`kb-dup-check "<renamed stem>" [--url <url from the frontmatter>]`; **without the script,** the targeted `grep index.md` described under Case C).
4. **Pick the topic folder** by reading `topics.md` and the item's `_summary.md`; never auto-create a topic folder, and file to the overflow folder with a flag when nothing fits, exactly as Mode 1 Step 5 does. **If the source came from outside the knowledge base, ask now**, naming the exact origin path and this destination, per the outside-source confirmation above.
5. **Move the source, metadata, deliverables, and build folder into `<topic>/<stem>/`** (Pattern A), with `mv` (or `cp` where the user chose to copy), then verify every file arrived.
6. **Set `topic:` and `tags:`** in the moved `_summary.md` (`tags:` defaulting to `[<topic>]`).
7. **Run the knowledge-base updates in this order:** `kb-index`, then `kb-recents`, then `kb-search reindex --incremental`. The last is best-effort and does not block the report. Where a helper is not wired, use its fallback from `SKILL.md`'s Helper commands table and say in the report which step ran by fallback.

A `DUP` at step 3 arrives after the deck already shipped: flag it loudly (deck delivered, filing blocked on the named existing entry, exact manual step stated) and never un-build.

**Post-build assertion (every filed path).** Verify the deliverable sits under the topic folder and the citation stem appears in `index.md` (a targeted grep, per the index-first conventions). On a miss, report it with the exact manual step (`kb move <dir> <topic>`); do not self-heal.

If Case A or Case C ran, the inbox flow has already refreshed `aa-recents/` and the full-text index; a Case B re-ingest refreshed them during the upgrade; a Case B reuse needs no additional reindex; the lite tier and the new-source deep route refresh them in the file-after step above, which is the only place they are refreshed on either of those paths.
