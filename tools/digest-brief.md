# Brief for digest subagents

You are writing case digests for a Philippine law graduate reviewing for the **2027 Bar Examinations**
(Bar Chair: Justice Ricardo R. Rosario; jurisprudence cutoff June 30, 2026; only doctrines and dispositions
in the **main opinion** are examinable; every subject is 20 essay problems answered in ALAC form).
Read `CLAUDE.md` in the project root first; its accuracy rules and schema bind you.

## Your inputs

- A list of case ids. For each id, the metadata row is in `topics/<topic>/ponencias-index.json`
  (docket, date, court, kind, title, url) and the full decision text is at `.cache/<topic>/<id>.txt`.
- The 2027 syllabus: `reference/2027-bar-bulletin-1-and-syllabus.txt`. Use Grep on it to find the closest heading.
- A finished example of the expected quality and shape:
  `topics/01-rosario-ponencias/cases/gr-234345-20210622.json`. Match its depth and tone.

## Steps for each case

1. Read the **entire main opinion** (use Read with offset/limit for long files). Stop at "SO ORDERED." plus the
   votes line; separate/concurring/dissenting opinions that follow are not examinable and must not feed the doctrine.
   Footnotes at the end may be skimmed for citations.
2. Confirm the ponente line reads ROSARIO, J. If it does not, do not write a digest; report it.
3. Confirm the docket, promulgation date and court (En Banc / First / Second / Third Division) from the header.
   Use the court exactly as one of: `En Banc`, `First Division`, `Second Division`, `Third Division`
   (a "Special Third Division" is `Third Division`; mention "Special" in `notes`).
4. Pick the **one** most examinable bar subject (exact string from CLAUDE.md) and the syllabus heading path,
   e.g. `"XII. Election Law > E. Remedies and Jurisdiction > 1. Petition to Deny Due Course or Cancel Certificate of Candidacy"`.
   Put other subjects the case meaningfully teaches in `other_subjects` (with their syllabus paths).
5. Write `topics/<topic>/cases/<id>.json` following the schema in CLAUDE.md. Use UTF-8 and valid JSON
   (escape inner double quotes as \").

## Writing rules

- **short_title:** how a reviewee would cite it. "Municipality of Makati v. Municipality of Taguig",
  "People v. Badillo", "People v. XXX" (keep anonymized names as written), "Usama v. Judge Tomarong",
  "Re: Dropping from the Rolls of Miras", "SEC v. 1Accountants Party-List (Resolution)" for a resolution on MR.
- **doctrine:** 1-3 short paragraphs of rules a bar examinee can apply, with the statutory/rule provision.
  Bold the core holding. Say "reiterated" when the Court applied settled doctrine; say when the Court
  abandoned, clarified, or laid down a new rule or guideline. If the case lays down guidelines, list them.
- **facts:** only facts that matter to the ruling, 2-5 paragraphs, with dates and amounts as stated.
- **issues:** phrase each as "Whether ...", in the Court's order.
- **ruling:** answer each issue in order, numbered and bolded ("**1. Yes, ...**"), with the reasoning the Court
  actually used. Short exact quotes in quotation marks are welcome; never invent a quote.
- **disposition:** summarize the fallo (petition granted/denied, what was affirmed/reversed, penalties, damages, interest).
- **bar_questions:** exactly 3. Fictional names, realistic fact pattern, one question (or two closely related
  sub-questions labeled (a) and (b)). Q1 tests the core doctrine head-on. Q2 changes a fact to probe the limits or an
  exception the Court discussed. Q3 links the case to a related rule or another subject it touches
  (procedure, ethics, evidence, damages, etc.). In criminal cases do not ask for computation of penalty periods.
- **ALAC:** `answer` = direct conclusion first. `legal_basis` = rule + provision + this case's name, G.R. No. and date
  (other cases only if the decision itself relied on them). `application` = apply the rule to the question's own facts.
  `conclusion` = one sentence. The suggested answers must agree with the Court's ruling.
- English only. Plain, precise language. No filler.

## Accuracy

Everything must come from the decision text you read. Never fill gaps from memory. If something is unclear in the
text (garbled OCR, missing pages), say so in `notes` and keep to what is legible. Copy the `url` from the index row
into `sources` with label "SC E-Library" or "SC Website (PDF)" as the row's `source` says.

## When done

Run `python tools/build.py --check` from the project root. Fix any error that names your files (ignore errors in
files that are not yours). Do not edit any other file (not the index, not CLAUDE.md, not the template).
Reply with one line per case: `id | subject | one-sentence doctrine | any doubt`.
