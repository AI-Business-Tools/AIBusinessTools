# The survey spec

The intermediate file between a written survey and a `.qsf`. The model writes it; `build_qsf.py` reads it. It exists because deciding what Qualtrics question type a written question is takes judgment, and expanding that decision into 40KB of cross-referenced JSON does not. Splitting the two puts each on the side of the line it belongs on.

It is plain JSON, not YAML: YAML needs a package installed, and a spec that needs an install is a spec that fails on a machine that does not have it.

## Table of contents
1. File shape
2. Question types
3. Fields every question accepts
4. Skip logic
4a. Carry-forward and piped text
3a. Randomizing choices
4b. Hidden fields (embedded data)
5. Worked example
6. What the spec deliberately cannot express

The sections are numbered by subject and are listed above in the order they appear, which is why 3a sits after 4a.

---

## 1. File shape

```json
{
  "survey_name": "Pre-session survey",
  "blocks": [
    {
      "name": "Section 1: About you",
      "questions": [ { "...": "one question object" } ]
    }
  ]
}
```

`survey_name` becomes the survey's name in Qualtrics, and an optional `survey_description` beside it becomes the description. `qsf_read.py` does not carry a description back out, so a rebuilt survey loses one it had; section 6 records that. Blocks appear in the order listed, and that order drives both the on-screen order and the export column prefixes (`Q1.1`, `Q1.2`, `Q2.1`), so it is not cosmetic.

**One block per section of the written survey** is the default. A survey with no sections gets one block named after the survey. Blocks are the only grouping Qualtrics has, and they set the export column prefixes, so they are worth matching to the survey's own sections even where nothing depends on them.

**Page breaks** are a question entry, not a block property: `{"type": "page_break"}` anywhere in a `questions` array. Qualtrics shows everything between two page breaks on one screen. A block with no page breaks is one long screen; the builder does not insert them for you, because how much a respondent sees at once is a design decision, not a formatting one.

**How the survey ends.** Omit `end_of_survey` and the survey ends with Qualtrics' own end-of-survey message. That is the right answer for anything a respondent reaches from a plain link: a client pre-session survey, a workshop survey, an audience poll.

**A survey launched from another system is the exception.** Where a learning-management system or portal launches the survey and expects the respondent handed back to it afterwards, the survey has to redirect, and the address is whatever that system documents:

```json
"end_of_survey": {
  "termination": "Redirect",
  "redirect_url": "<the address that system expects>"
}
```

Write it only for those surveys; leave `end_of_survey` out otherwise, which is the common case.

`redirect_url` is required whenever `termination` is `"Redirect"`. Omit it and the builder falls back to whatever address the profile inherited and says so in the build report, and `validate_qsf.py` fails a file that redirects to nothing at all. The address belongs to the survey rather than to the profile: a redirect nobody chose is a redirect nobody checks, and a survey sent to the wrong place only reveals it after someone has finished it.

`qsf_read.py` writes this field, with the address, whenever it reads a survey whose ending is not the default, so reading a survey that redirects and rebuilding it keeps that ending without anything being restated.

## 2. Question types

### descriptive

Text shown to the respondent that collects no answer. Survey intros, section preambles, instructions.

```json
{ "type": "descriptive", "text": "Please complete by Friday. It takes about 15 minutes." }
```

### choice

Multiple choice, the workhorse.

```json
{
  "type": "choice",
  "text": "Which best describes your company's industry?",
  "select": "single",
  "layout": "vertical",
  "choices": [
    "Manufacturing",
    "Retail",
    { "text": "Other (please describe)", "write_in": true }
  ]
}
```

- `select`: `"single"` (default) or `"multi"`.
- `layout`: `"vertical"` (default), `"horizontal"`, `"columns"`, `"dropdown"`, `"select"`, or `"multiselect"`. Horizontal suits a short agree-disagree scale, columns a long list that would otherwise run down the page, and dropdown a very long one like a country picker.
- `choices`: a list of strings, or objects for a choice that needs more than its text. `{"text": "...", "write_in": true}` attaches a write-in box to that one choice, which is how "Other (please describe)" works.
- `max_choices` and `min_choices`: multi-select only. `max_choices: 3` is the "Choose up to 3" instruction, enforced by Qualtrics rather than left as words in the question.

A single-answer choice question whose choices are an agree-disagree or satisfaction scale is still `select: "single"`. Qualtrics has no separate Likert type for one statement; the matrix type below is for several statements sharing one scale.

### matrix

A grid: several statements down the side, one shared scale across the top. Use it wherever the written survey repeats the same answer options under a list of items.

```json
{
  "type": "matrix",
  "text": "How recently have you used each of the following?",
  "select": "single",
  "rows": ["Tool A", "Tool B", "Tool C"],
  "columns": ["Never heard of", "Heard of, never used", "Used in the past month"]
}
```

- `select`: `"single"` (default, one answer per row) or `"multi"` (checkboxes, several per row).
- `rows` are the statements, `columns` the scale points. Both display in the order given.

**Recognizing a matrix is the most common judgment call in a run.** A written survey shows it as a list of items each followed by the same set of boxes. Six items with a six-point scale is one matrix question, not six choice questions, and getting that wrong produces a survey that works but is tedious to answer and awkward to analyze.

### text

A written answer.

```json
{ "type": "text", "text": "Which other tools have you used?", "size": "essay" }
```

- `size`: `"line"` (single line, for a name or a number), `"box"` (a few lines), `"essay"` (default, a large box), or `"form"`.
- `"form"` takes a `fields` list instead of collecting one answer, and gives each field its own labeled input:
  ```json
  { "type": "text", "size": "form", "text": "Your details", "fields": ["First name", "Last name", "Company"] }
  ```

### slider

A dragged bar. One bar per row.

```json
{
  "type": "slider",
  "text": "How much of your week goes to each?",
  "rows": ["Client work", "Admin"],
  "min": 0,
  "max": 100,
  "decimals": 0,
  "grid_lines": 10
}
```

### nps

The 0-to-10 recommend question, with Qualtrics' own scoring attached.

```json
{ "type": "nps", "text": "How likely are you to recommend us to a colleague?" }
```

### rank

Drag into order.

```json
{ "type": "rank", "text": "Rank these in order of priority.", "choices": ["Cost", "Speed", "Quality"] }
```

### constant_sum

Numbers that add to a total.

```json
{ "type": "constant_sum", "text": "Split 100 points across these.", "choices": ["A", "B", "C"], "total": 100 }
```

### page_break

```json
{ "type": "page_break" }
```

## 3. Fields every question accepts

| Field | Default | What it does |
|---|---|---|
| `id` | auto | A label for this question inside the spec, used as a skip target and in the readback. Not the Qualtrics QID, which the builder mints. Use the number from the written survey (`"Q8"`) so the readback lines up against the source. |
| `required` | `"request"` | **The default is "request"**, what Qualtrics calls Request Response: the respondent is prompted once if they skip and can continue anyway. `true` blocks them until they answer. `false` makes it silently skippable, and is what a question the survey marks "Optional:" gets. If your default is request response on anything not marked optional, this field is usually omitted and written only to mark a question optional. |
| `randomize` | none | Shuffles the choices. See below. |
| `skip` | none | See below. |
| `html` | `false` | Set true to pass `text` through as HTML instead of escaping it. Needed only for formatting the builder cannot infer; `qsf_read.py` never sets it, so rich text in a survey read back from Qualtrics comes back as plain prose. |
| `export_tag` | auto | The question's column name in the response export. Written by `qsf_read.py` so a rebuilt survey keeps the columns any existing analysis already refers to; a survey written from scratch omits it and the builder names columns `Q<block>.<position>`. Do not set it by hand unless you are matching an export that already exists. |

`type` and `text` are required on every question except `page_break`.

## 4. Skip logic

```json
{
  "type": "choice",
  "id": "Q14",
  "text": "Did you complete the interview?",
  "choices": ["Yes", "I started it and did not finish", "No"],
  "skip": [ { "when": "No", "to": "Q18" } ]
}
```

- `when` is the exact text of one of this question's own choices.
- `to` is `"end_of_block"`, `"end_of_survey"`, the `name` of the **immediately following** block, or the `id` of a later question. A block two or more further on is refused, the same way a distant question is. When a name and an id are the same string, the block wins.
- `condition` is `"selected"` (the default), `"not_selected"`, or `"displayed"`. The last fires because the question was shown at all rather than on any answer, so it takes no `when`.

**A question target must be reachable, and Qualtrics is narrow about what that means.** `"to": "Q18"` builds only when question 18 is in the same block as the question skipping to it, or is the first question of the very next block. Anything further is refused at build time, in Qualtrics' own words: "Invalid Skip Logic: cannot find destination in the block." A written instruction like "skip to question 18" therefore maps onto `"to": "Q18"` only when the survey's blocks already fall that way. When they do not, splitting the block so question 18 starts one is not a stylistic choice, it is what makes the skip possible, and `"to": "<that block's name>"` then expresses it.

A question can carry several skips, and they are evaluated in the order written:

```json
"skip": [
  { "when": "Yes", "to": "Section 4" },
  { "when": "No",  "to": "end_of_survey" },
  { "when": "Not sure", "condition": "not_selected", "to": "end_of_block" }
]
```

## 4a. Carry-forward and piped text

A question can show what the respondent picked earlier. Write `${answers:Q3}` in any question text or choice text, where `Q3` is another question's `id`:

```json
{
  "type": "matrix",
  "id": "Q7",
  "text": "Rate each person you named.",
  "rows": ["${answers:Q3}"],
  "columns": ["Poor", "Fair", "Good", "Excellent"]
}
```

The builder rewrites the reference to the Qualtrics id it minted for `Q3`. **Never write a raw `QID` number into the spec**: the spec's ids and Qualtrics' ids are different things, and the whole point of the rewrite is that a rebuild re-points every reference instead of leaving it aimed at ids from the survey it came from. A reference to an id that does not exist in the spec is refused at build time rather than shipped.

The longer form works too, for the pipe types `${answers:...}` does not cover, and takes the same spec ids:

```json
"text": "You said ${q://Q3/ChoiceTextEntryValue} was the main obstacle. Say more."
```

Embedded-data pipes (`${e://Field/...}`) pass through untouched; they name a field rather than a question.

## 3a. Randomizing choices

Shuffling the answer options removes the advantage the top of a list has. It applies to a choice question's options and to a matrix's rows.

```json
{ "randomize": true }                                  // every choice moves
{ "randomize": { "except_last": 3 } }                  // all but the last three move
{ "randomize": { "fixed": ["Other (please describe)"] } }   // that one stays put, the rest move
```

**Pinning is usually the point.** A barriers question ending in "Nothing is standing in the way", "I do not know", and "Other (please describe)" reads as a mistake once those are shuffled into the middle, so the useful form is nearly always `except_last`. `fixed` names the exact choice text instead, for a list whose stay-put options are not all at the end.

**Never randomize an ordered list.** A scale (Strongly agree to Strongly disagree), a size band, a frequency, or anything a respondent reads as a sequence loses its meaning when shuffled. The builder does not check this, because it cannot tell an ordered list from an unordered one; it is a judgment made when the spec is written.

## 4b. Hidden fields (embedded data)

Fields the survey records with every response without asking for them, supplied by whatever launched it. A survey launched from a learning-management system typically carries the respondent's email and an institutional id this way, and **they are what attach a response to a person**; a survey that loses them still works and comes back anonymous.

```json
{
  "survey_name": "Team member evaluation",
  "embedded_data": [
    { "field": "user_email" },
    { "field": "sis_user_id" },
    { "field": "cohort", "source": "custom", "value": "spring" }
  ],
  "blocks": [ "..." ]
}
```

- `source` is `"recipient"` (the default: the value arrives from the panel or the launch URL, and Qualtrics shows "Value will be set from Panel or URL") or `"custom"` (this survey sets it, and `value` says to what).
- Question text can pipe one in with `${e://Field/user_email}`. The builder leaves those alone, and the validator fails a file that pipes a field the survey never declares.

**Reading an existing survey back recovers these**, so a course survey revised through this skill keeps identifying students. It did not always: a rebuild used to drop them silently, which is the defect this section exists to prevent.

## 5. Worked example

A three-question survey covering a section break, a grid, a write-in, and a skip.

```json
{
  "survey_name": "Workshop pre-read check",
  "blocks": [
    {
      "name": "Before we start",
      "questions": [
        { "type": "descriptive", "text": "Six questions, about four minutes." },
        {
          "type": "choice",
          "id": "Q1",
          "text": "Did you read the pre-read?",
          "choices": ["Yes, all of it", "Parts of it", "No"],
          "required": true,
          "skip": [ { "when": "No", "to": "Wrap up" } ]
        },
        { "type": "page_break" },
        {
          "type": "matrix",
          "id": "Q2",
          "text": "How clear was each section?",
          "rows": ["The opening case", "The framework", "The worked example"],
          "columns": ["Not clear", "Somewhat clear", "Very clear"],
          "required": "request"
        }
      ]
    },
    {
      "name": "Wrap up",
      "questions": [
        {
          "type": "choice",
          "id": "Q3",
          "text": "What would you like more of?",
          "select": "multi",
          "max_choices": 2,
          "choices": ["Cases", "Frameworks", "Hands-on work", { "text": "Something else", "write_in": true }]
        }
      ]
    }
  ]
}
```

## 6. What the spec deliberately cannot express

Named here so a run does not go looking for them, and so anything a written survey asks for that lands in this list gets said out loud rather than dropped.

- **Display logic**, meaning showing or hiding a question based on an earlier answer. Only skip logic, which jumps forward, is supported. A survey that needs a question shown conditionally gets it built and the condition added by hand in Qualtrics. None of the five exports profiled uses display logic, which is why it stays out.
- **Quotas and contact lists.** These belong to the survey's distribution rather than its content. Embedded data itself IS supported; see section 4b.
- **Loop and merge**, where a block repeats once per item.
- **Themes and branding.** The builder copies whatever theme the profile carries; see `qsf-format.md`.
- **The survey's description**, which `build_qsf.py` writes from `survey_description` but `qsf_read.py` does not read back, so a rebuild drops one the original had.
- **Formatting inside question and choice text.** The readback strips every tag, so bold, italics, and links come back as plain prose and a rebuild does not restore them. Paragraph and line structure IS preserved: `<p>`, `<li>`, and their kin become line breaks rather than being run together, and a rebuild re-emits them as the `<div>` paragraphs Qualtrics' own editor writes. What is lost is the bullet or number in front of a list item, so a bulleted list rebuilds as separate lines without bullets. The `html` field can put any of it back by hand.
- **Block-level options**, meaning a block's own `BlockLocking`, `RandomizeQuestions`, and `BlockVisibility` settings. A rebuild emits none of them, so a block set to randomize its questions comes back not doing so. All three are at their defaults in every export profiled here, but `RandomizeQuestions` will not be in general; check it after rebuilding a survey that used it.

Anything on this list that a written survey asks for gets said out loud rather than dropped. A construct the spec cannot carry is not made safe by going unmentioned: the survey is built without it and the gap is named, so it can be added in the Qualtrics builder.
