# BAR REVIEW — project guide for Claude

Reviewer materials for a Philippine law graduate preparing for the **2027 Bar Examinations**.
Every topic ends up in one interactive reviewer app (`reviewer/index.html`, published as an Artifact).

## The exam this is for (verified from Bar Bulletin No. 1-2027, Sept 16, 2026)

- **Bar Chairperson:** Associate Justice Ricardo R. Rosario. Dates: Sept 5, 8, 12, 2027. Electronic, local testing centers.
- **Coverage cutoff:** laws, rules, issuances in force and jurisprudence promulgated **as of June 30, 2026**.
  Only the **doctrines and dispositions in the main opinion** are examinable (not separate opinions).
- **Format:** 20 essay problems per subject, 5% each (a problem may have up to two questions). Tests whether a
  beginning lawyer can state the governing principle, apply it to facts, and explain the reasoning.
  Criminal Law: no computing exact penalty periods. Computations: basic arithmetic only.
- **Subjects (use these exact strings in data files):**
  | Subject | Weight |
  |---|---|
  | `Political and Public International Law` | 15% |
  | `Commercial and Taxation Laws` | 20% |
  | `Civil Law and Land Titles and Deeds` | 20% |
  | `Labor Law and Social Legislation` | 10% |
  | `Criminal Law` | 10% |
  | `Remedial Law, Legal and Judicial Ethics` | 25% (includes Practical Exercises) |
- The full official syllabus is in [reference/2027-bar-bulletin-1-and-syllabus.txt](reference/2027-bar-bulletin-1-and-syllabus.txt)
  (PDF beside it). Map every case to the closest syllabus heading there.

## How the user works

- The user writes each request as a numbered prompt file in the project root (`1.md`, `2.md`, …). Each prompt = one **topic**.
- Talk to the user in Taglish (match their language). Write all reviewer content in **English** (the language of the Bar).
- The user wants complete, exam-ready output, readable in the interactive reviewer.

## Accuracy rules (non-negotiable)

This is exam material. A wrong G.R. number, date, holding or ponente is worse than a missing case.

1. **Never digest from memory.** Every digest is written from the full text of the decision, fetched from an official
   source in the same session: SC E-Library (elibrary.judiciary.gov.ph), the SC website PDF (sc.judiciary.gov.ph), or LawPhil.
2. Copy docket number, date of promulgation, ponente, and **En Banc / Division** from the decision header itself.
3. **Doctrine** = the ratio decidendi of the main opinion, stated as a rule a bar examinee can apply. If the Court
   only reiterated settled doctrine, say "reiterated" and name the doctrine. Never take doctrine from a separate opinion.
4. Facts, issues and ruling must be traceable to the decision. Quote sparingly and exactly, in quotation marks.
   No invented facts, numbers, names, or citations. If something can't be verified, leave it out and say so in `notes`.
5. Respect the cutoff: only decisions promulgated on or before the topic cutoff (June 30, 2026 for the 2027 Bar).
6. If the decision was later modified on reconsideration and that resolution is in the index, cross-reference it in `notes`.
7. Minors and VAWC/child-abuse victims appear as XXX/YYY/AAA in the decisions. Keep them anonymized the same way.

## Default case-digest format (from `1.md`)

Every case digest has: Bar subject and specific topic · Doctrine · Facts · Issues · Ruling · En Banc or Division ·
three Bar Exam questions, each with a suggested answer using **ALAC** (Answer, Legal basis, Application, Conclusion).

**Bar questions:** write them like real Bar problems. A short fact pattern with fictional names (not the actual
parties), then one direct question (or two closely related ones). Across the three questions: one tests the core
doctrine directly, one changes a fact to test the limits of the doctrine, one connects it to a related rule or a
different subject the case touches. Each must be answerable from the decision's doctrine plus basic law.

**ALAC suggested answers:**
- **Answer:** the direct conclusion first ("Yes, the dismissal is valid." / "No. …").
- **Legal basis:** the rule, with the statute/rule provision and the case name and G.R. No. it comes from.
- **Application:** apply the rule to the question's own facts, step by step.
- **Conclusion:** one sentence restating the answer.
Suggested answers must agree with the Court's ruling. Never contradict the main opinion.

## Files

```
1.md, 2.md, …                    user's prompts, one per topic (keep them)
CLAUDE.md                        this guide
reference/                       2027 Bar Bulletin No. 1 + syllabus (PDF and text)
tools/                           pipeline scripts (see below)
topics/NN-slug/
  topic.json                     topic metadata: id, title, description, prompt file, cutoff
  ponencias-index.json           every source decision for the topic, with status pending|digested|skipped
  cases/<case-id>.json           one digest per file (schema below)
  DIGESTS.md                     generated: the whole topic as one printable Markdown file
reviewer/
  template.html                  the reviewer app (edit this, never index.html)
  index.html                     generated by tools/build.py; this is what gets published
.cache/                          downloaded decision texts (re-creatable, never edit by hand)
```

### Case file schema (`topics/NN-slug/cases/<id>.json`)

```json
{
  "id": "gr-235316-20211201",                 // = file name; slug of docket + promulgation date
  "short_title": "Municipality of Makati v. Municipality of Taguig",
  "full_title": "MUNICIPALITY OF MAKATI (NOW CITY OF MAKATI), PETITIONER, VS. ...",
  "docket": "G.R. No. 235316",
  "date": "2021-12-01",                        // promulgation date, ISO
  "ponente": "Rosario, J.",
  "court": "Third Division",                   // exactly: En Banc | First Division | Second Division | Third Division
  "decision_type": "Decision",                 // or "Resolution"
  "subject": "Political and Public International Law",   // one of the six exact subject strings
  "syllabus_topic": "XI. Local Governments > ... ",       // path of headings from the 2027 syllabus
  "topics": ["Boundary disputes between LGUs", "Res judicata"],   // 2-5 short specific topics
  "other_subjects": [{"subject": "Remedial Law, Legal and Judicial Ethics", "syllabus_topic": "..."}],  // optional
  "doctrine": "Rule statement(s). Separate paragraphs with a blank line.",
  "facts": "Concise facts needed to understand the ruling.",
  "issues": ["Whether ...", "Whether ..."],
  "ruling": "Answer each issue in order, with the Court's reasoning. **Bold** the key holding.",
  "disposition": "What the Court ordered (the fallo), summarized.",
  "bar_questions": [ {"q": "Fact pattern + question", "alac": {"answer": "", "legal_basis": "", "application": "", "conclusion": ""}} ],  // exactly 3
  "sources": [{"label": "SC E-Library", "url": "https://..."}],
  "notes": "",                                 // optional caveats (shown collapsed at the bottom of the digest)
  "superseded_by": {"id": "gr-246027-20250128", "label": "Reversed", "summary": "..."}   // only when a later ruling reversed/set aside this one
}
```
Text fields accept light Markdown: blank line = new paragraph, `**bold**`, `*italic*`, lines starting with `- ` = bullets.

## Workflow for a new topic

1. Read the new prompt file. Create `topics/NN-slug/topic.json` (copy the shape of `topics/01-rosario-ponencias/topic.json`).
   If the prompt asks for a different output format than the default digest, record it in `topic.json` → `format_notes`
   and update this file if the format becomes a new standard.
2. **Build the source list** before writing anything.
   For "ponencias of Justice X" topics, run the pipeline (outputs go to the scratchpad or `.cache/`, not the topic folder):
   ```
   python tools/find_ponencias_elib.py <crawl_dir> <SURNAME> 2020-10 2026-06      # E-Library, ponente from each decision
   python tools/list_sc_posts.py <sc_dir>                                          # every SC website post
   python tools/select_sc_candidates.py <sc_dir>/sc_posts.jsonl <crawl_dir>/elib_index.jsonl <sc_dir>/cand.json 2020-10-01 2026-06-30
   python tools/scan_sc_pdfs.py <sc_dir>/cand.json <pdf_dir> <SURNAME>              # fills E-Library gaps from SC PDFs
   python tools/merge_ponencias.py <SURNAME> <topic_id> <crawl_dir> <pdf_dir> --cutoff 2026-06-30
   ```
   The E-Library lags behind the SC website by months, which is why the SC PDF pass exists. Use a browser-like
   User-Agent (the scripts already do); plain requests to sc.judiciary.gov.ph get HTTP 403.
   For subject topics (e.g. "recent cases on Rule 65"), search the official sources and record each decision in
   `ponencias-index.json` with the same fields before digesting.
3. **Digest in parallel batches.** Balance batches by text size (about 250,000 characters of decision text per
   subagent; one very long En Banc case can be a batch by itself) and keep related rulings (a decision and its
   resolution on reconsideration) in the same batch. Point every subagent to [tools/digest-brief.md](tools/digest-brief.md),
   which carries the rules, the schema and the example digest. Mark the rows `digested` in the index when done.
4. **Check quality.** Run `python tools/build.py --check`: besides the schema, it cross-checks each digest's date,
   court, docket and source URL against `ponencias-index.json` (which came from the decision headers). Then spot-check
   at least one case per batch against the decision text: the doctrine, and that the ALAC answers agree with the ruling.
5. **Build and publish.** `python tools/build.py` regenerates `DIGESTS.md`, `reviewer/index.html` (Artifact
   fragment) and `site/` (standalone lazy-loading website for Netlify). Then publish both (the website goes live by
   committing and pushing to GitHub):
   - Republish `reviewer/index.html` to the **same** Artifact URL (below). The `sample` capability carries forward,
     so "Grade my answer" keeps working. Never create a second reviewer artifact for a new topic: topics are tabs
     in the same app.
   - Website (Netlify) and GitHub: use only the user's **personal** accounts. This machine also holds **work**
     accounts (Netlify CLI, git credentials, global git email), so never infer the account from an email or a name.
     A browser login does not change a CLI login. Before any deploy, push, or account-touching command, show the exact
     account the tool will use (`netlify status`, the remote URL, the commit author) and get the user's confirmation.

## Reviewer app

- Published Artifact: https://claude.ai/artifact/1Zjnor3wUfjsYFcVja9Uxg (private to the owner until shared from its Share menu).
  Update it by publishing `reviewer/index.html` with `url` set to this link; read it first with the Artifact tool if
  this session has not published it.
- Modes: **Digests** (filter by subject, En Banc/Division, status; search) and **Practice** (bar questions one at a
  time, write an answer, reveal the ALAC suggested answer, optional AI grading through the `sample` capability).
- GitHub repo: https://github.com/jaysi17/bar2027-rosario-ponencias (public). This repo has its own commit identity
  (`git config user.email` = the jaysi17 noreply address) and the remote URL carries `jaysi17@` so the right stored
  credential is used. Do not change either. `.cache/` and `.netlify/` stay out of git.
- Public website: https://bar2027-rosario-ponencias.netlify.app, on the user's personal Netlify, **deployed
  automatically from the GitHub repo** (publish dir `site/`, no build command). To update it: build, commit, push.
  No Netlify CLI needed (and the CLI on this machine is a work account).
- The website build is **lazy**: `site/index.html` embeds only the case list (~30 KB compressed); each digest is
  `site/data/<hash>/<topic>/<id>.json` (~5 KB), fetched when opened; `search.json` loads when the search box is used.
  The Netlify edge serves this user's region slowly (~15 KB/s measured), so keep the first page small. The Artifact
  build (`reviewer/index.html`) still embeds everything. The footer carries the credit "Made by JC Medenilla" and the AI-assisted disclaimer; keep both.
  "Grade my answer" only works inside the Claude Artifact; on the website it hides itself.
- Welcome note on open (approved wording; keep it light, not alarming): unofficial, not the only reviewer, arranged by
  a powerful AI model. The AI mention stays a plain phrase inside the paragraph, not highlighted or boxed (user's choice).
  It shows on every visit until "Don't show this again" (`bar27:welcome-hidden`); the footer link "About this
  reviewer" reopens it.
- Header navigation is two nav links (Digests, Practice) with icons, not a toggle. A "Practice here" callout points at
  Practice after the welcome note closes, until its X or Practice is clicked (`bar27:practice-tip-closed`).
- Focus reading (wider screens): "Hide" in the case-list header hides the filters and list; a slim sticky "Show cases"
  tab on the left brings them back; shortcut F; remembered in `bar27:focus`. Controls that hide the list must sit on
  the list, never on the reading pane (the user found that confusing). Previous/Next case buttons end every digest.
- Approve-before-ship: for visible UI changes, the user wants a local mockup (screenshots in `mockups/`, gitignored)
  and approval before anything is pushed or published.
- Light/dark toggle in the header; the choice is saved in browser storage (`bar27:theme`), otherwise it follows the device.
- Progress (reviewed/mastered marks, practice marks, drafts) lives in the viewer's browser storage only.
- Design tokens are at the top of `reviewer/template.html`. Keep the look consistent when adding features.

## Topics so far

| # | Topic folder | Prompt | Status |
|---|---|---|---|
| 1 | `topics/01-rosario-ponencias` | `1.md` — case digests of Justice Rosario's ponencias up to June 30, 2026 | 89 of 89 digested (Oct 13, 2026); how the list was built: `COVERAGE.md` |
