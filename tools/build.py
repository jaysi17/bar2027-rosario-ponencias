"""Validate every topic's case digests, then build the readable Markdown and the reviewer app.

Usage (from the project root):
    python tools/build.py            # validate + build everything
    python tools/build.py --check    # validate only

Inputs:  topics/<topic>/topic.json and topics/<topic>/cases/*.json
Outputs: topics/<topic>/DIGESTS.md and reviewer/index.html (from reviewer/template.html)
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOPICS = ROOT / "topics"
TEMPLATE = ROOT / "reviewer" / "template.html"
OUTPUT = ROOT / "reviewer" / "index.html"          # page fragment for the Claude Artifact (it adds <head> itself)
SITE = ROOT / "site" / "index.html"                 # complete standalone page for static hosting (Netlify)
DATA_MARKER = "/*__REVIEWER_DATA__*/null"
BODY_START = '<div class="wrap">'
# What the Artifact skeleton normally supplies; a standalone page needs it in its own <head>.
SITE_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Case digests of Justice Ricardo R. Rosario's ponencias for the 2027 Philippine Bar Examinations, with ALAC practice questions.">
<meta name="author" content="JC Medenilla">
<link rel="canonical" href="https://bar2027-rosario-ponencias.netlify.app/">
<meta property="og:type" content="website">
<meta property="og:url" content="https://bar2027-rosario-ponencias.netlify.app/">
<meta property="og:title" content="Bar 2027 Case Reviewer">
<meta property="og:description" content="Digests of Justice Rosario's ponencias (up to June 30, 2026) with doctrine, facts, issues, ruling, and ALAC bar questions.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%2323408e'/%3E%3Ctext x='16' y='23' font-family='Georgia,serif' font-size='20' font-weight='700' text-anchor='middle' fill='%23fbe680'%3E%C2%A7%3C/text%3E%3C/svg%3E">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>
"""

SUBJECTS = [
    "Political and Public International Law",
    "Commercial and Taxation Laws",
    "Civil Law and Land Titles and Deeds",
    "Labor Law and Social Legislation",
    "Criminal Law",
    "Remedial Law, Legal and Judicial Ethics",
]
COURTS = ["En Banc", "First Division", "Second Division", "Third Division"]
REQUIRED = ["id", "short_title", "full_title", "docket", "date", "ponente", "court", "decision_type",
            "subject", "syllabus_topic", "topics", "doctrine", "facts", "issues", "ruling",
            "disposition", "bar_questions", "sources"]
ALAC = ["answer", "legal_basis", "application", "conclusion"]


def check_against_index(case, row):
    """The header facts of a digest must match the decision it was written from."""
    errs = []
    if row is None:
        return [f"id {case['id']!r} is not in ponencias-index.json"]
    if case["date"] != row["date"]:
        errs.append(f"date {case['date']} differs from the decision header {row['date']}")
    if case["court"] != row["court"]:
        errs.append(f"court {case['court']!r} differs from the decision header {row['court']!r}")
    if not set(re.findall(r"\d{3,}", row["docket"])) <= set(re.findall(r"\d{3,}", case["docket"])):
        errs.append(f"docket {case['docket']!r} does not match the decision header {row['docket']!r}")
    if row["url"] not in [s.get("url") for s in case["sources"]]:
        errs.append("sources must include the index url " + row["url"])
    return errs


def validate(case, path, cutoff):
    errs = []
    for k in REQUIRED:
        if k not in case or case[k] in ("", [], None):
            errs.append(f"missing '{k}'")
    if errs:
        return errs
    if case["subject"] not in SUBJECTS:
        errs.append(f"subject must be one of the six 2027 subjects, got {case['subject']!r}")
    for o in case.get("other_subjects", []):
        if o.get("subject") not in SUBJECTS:
            errs.append(f"other_subjects has unknown subject {o.get('subject')!r}")
    if case["court"] not in COURTS:
        errs.append(f"court must be one of {COURTS}, got {case['court']!r}")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", case["date"]):
        errs.append("date must be YYYY-MM-DD")
    elif cutoff and case["date"] > cutoff:
        errs.append(f"date {case['date']} is after the topic cutoff {cutoff}")
    if case["id"] != path.stem:
        errs.append(f"id {case['id']!r} must equal the file name {path.stem!r}")
    if not isinstance(case["issues"], list):
        errs.append("issues must be a list")
    qs = case["bar_questions"]
    if not isinstance(qs, list) or len(qs) != 3:
        errs.append("bar_questions must have exactly 3 items")
    else:
        for i, q in enumerate(qs, 1):
            if not q.get("q"):
                errs.append(f"bar_questions[{i}] missing 'q'")
            for part in ALAC:
                if not (q.get("alac") or {}).get(part):
                    errs.append(f"bar_questions[{i}].alac missing '{part}'")
    for s in case["sources"]:
        if not str(s.get("url", "")).startswith("https://"):
            errs.append("every source needs an https url")
    return errs


def md_case(c):
    out = [f"## {c['short_title']}", "",
           f"**{c['full_title']}**  ", f"{c['docket']} | {c['date']} | {c['court']} | {c['ponente']} | {c['decision_type']}", "",
           f"**Bar subject:** {c['subject']}  ", f"**Syllabus topic:** {c['syllabus_topic']}  ",
           f"**Specific topics:** {'; '.join(c['topics'])}"]
    for o in c.get("other_subjects", []):
        out.append(f"  \n**Also relevant to:** {o['subject']} ({o.get('syllabus_topic', '')})")
    if c.get("superseded_by"):
        out += ["", f"> **{c['superseded_by'].get('label', 'Superseded').upper()} — not the controlling rule.** {c['superseded_by']['summary']}"]
    out += ["", "### Doctrine", c["doctrine"], "", "### Facts", c["facts"], "", "### Issues"]
    out += [f"{i}. {x}" for i, x in enumerate(c["issues"], 1)]
    out += ["", "### Ruling", c["ruling"], "", "### Disposition", c["disposition"], "",
            "### En Banc or Division?", c["court"], "", "### Bar Exam Questions (ALAC)"]
    for i, q in enumerate(c["bar_questions"], 1):
        a = q["alac"]
        out += ["", f"**Q{i}.** {q['q']}", "", "**Suggested answer:**", "",
                f"- **Answer:** {a['answer']}", f"- **Legal basis:** {a['legal_basis']}",
                f"- **Application:** {a['application']}", f"- **Conclusion:** {a['conclusion']}"]
    if c.get("notes"):
        out += ["", f"> Note: {c['notes']}"]
    out += ["", "Sources: " + ", ".join(f"[{s['label']}]({s['url']})" for s in c["sources"]), "", "---", ""]
    return "\n".join(out)


def main():
    check_only = "--check" in sys.argv
    topics, all_errs = [], 0
    for tdir in sorted(p for p in TOPICS.iterdir() if p.is_dir()):
        meta_path = tdir / "topic.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        index_path = tdir / "ponencias-index.json"
        index = {r["id"]: r for r in json.loads(index_path.read_text(encoding="utf-8"))} if index_path.exists() else None
        cases = []
        for f in sorted((tdir / "cases").glob("*.json")):
            try:
                c = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                print(f"[{tdir.name}] {f.name}: invalid JSON: {e}")
                all_errs += 1
                continue
            errs = validate(c, f, meta.get("cutoff"))
            if not errs and index is not None:
                errs = check_against_index(c, index.get(c["id"]))
            for e in errs:
                print(f"[{tdir.name}] {f.name}: {e}")
            all_errs += len(errs)
            if not errs:
                cases.append(c)
        cases.sort(key=lambda c: (c["date"], c["docket"]), reverse=True)
        meta["cases"] = cases
        topics.append(meta)
        print(f"[{tdir.name}] {len(cases)} valid case(s)")

    if all_errs:
        print(f"\n{all_errs} problem(s) found. Fix them, then rebuild.")
        sys.exit(1)
    if check_only:
        return

    for t in topics:
        by_subject = {s: [c for c in t["cases"] if c["subject"] == s] for s in SUBJECTS}
        lines = [f"# {t['title']}", "", t.get("description", ""), "",
                 f"Cases digested: {len(t['cases'])}. Cutoff: {t.get('cutoff', '')}.", "", "## Contents", ""]
        for s, cs in by_subject.items():
            if cs:
                lines.append(f"- {s} ({len(cs)})")
        lines.append("")
        for s, cs in by_subject.items():
            if cs:
                lines += [f"# {s}", ""] + [md_case(c) for c in cs]
        (TOPICS / t["id"] / "DIGESTS.md").write_text("\n".join(lines), encoding="utf-8")

    data = {"subjects": SUBJECTS, "topics": topics}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8")
    if DATA_MARKER not in html:
        sys.exit(f"template is missing the data marker {DATA_MARKER}")
    page = html.replace(DATA_MARKER, payload)
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"Built {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size // 1024} KB)")

    # The website embeds only the case list and fetches each digest on demand (site/data/<hash>/<topic>/<id>.json),
    # so the first load is small even on slow connections. The hash in the folder name lets those files be cached forever.
    import hashlib, shutil
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:10]
    data_root = SITE.parent / "data"
    shutil.rmtree(data_root, ignore_errors=True)
    out_dir = data_root / digest
    search, site_topics = {}, []
    # Only what the list, the filters and the case header need; everything else loads with the digest.
    list_fields = ["id", "short_title", "docket", "date", "ponente", "court", "decision_type", "subject", "topics"]
    for t in topics:
        (out_dir / t["id"]).mkdir(parents=True, exist_ok=True)
        rows = []
        for c in t["cases"]:
            (out_dir / t["id"] / f"{c['id']}.json").write_text(json.dumps(c, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            row = {k: c[k] for k in list_fields if c.get(k)}
            if c.get("other_subjects"):
                row["other_subjects"] = [{"subject": o["subject"]} for o in c["other_subjects"]]
            if c.get("superseded_by"):
                row["superseded_by"] = {"id": c["superseded_by"]["id"], "label": c["superseded_by"].get("label", "")}
            row["nq"] = len(c["bar_questions"])
            rows.append(row)
            search[f"{t['id']}/{c['id']}"] = " ".join(
                [c["full_title"], c["syllabus_topic"], c["doctrine"]] + [o.get("syllabus_topic", "") for o in c.get("other_subjects", [])]).lower()
        site_topics.append({**{k: v for k, v in t.items() if k != "cases"}, "cases": rows})
    (out_dir / "search.json").write_text(json.dumps(search, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    site_payload = json.dumps({"subjects": SUBJECTS, "topics": site_topics, "base": f"data/{digest}"},
                              ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = html.replace(DATA_MARKER, site_payload)

    head_part, sep, body_part = page.partition(BODY_START)
    if not sep:
        sys.exit(f"template is missing {BODY_START!r}, needed to split <head> from <body> for the site build")
    head_part = head_part.replace('<meta charset="utf-8">', "", 1)
    SITE.parent.mkdir(exist_ok=True)
    SITE.write_text(SITE_HEAD + head_part.strip() + "\n</head>\n<body>\n" + sep + body_part + "\n</body>\n</html>\n", encoding="utf-8")
    print(f"Built {SITE.relative_to(ROOT)} ({SITE.stat().st_size // 1024} KB), ready for Netlify")


if __name__ == "__main__":
    main()
