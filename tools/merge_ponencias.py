"""Merge E-Library and SC-website scan results into one clean ponencia index for a topic.

Usage:
    python tools/merge_ponencias.py <SURNAME> <topic_id> <crawl_dir> [<pdf_dir>] [--cutoff YYYY-MM-DD] [--start YYYY-MM-DD]

<crawl_dir> is the output of find_ponencias_elib.py (elib_index.jsonl + html/).
<pdf_dir>   is the output of scan_sc_pdfs.py (pdf_index.jsonl + txt/), optional.

Writes:
    topics/<topic_id>/ponencias-index.json      one row per decision, sorted by date
    .cache/<topic_id>/<case id>.txt             full text of each decision (input for digesting)
Existing "status" values in the index are kept, so re-running never loses progress.
"""
import sys, re, json, html
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
HEADER_RE = re.compile(r"\[\s*(.+?),\s*((?:" + MONTHS + r")\s+\d{1,2}\s*,\s*\d{4})\s*\]", re.S)
DIV_RE = re.compile(r"\b(EN BANC|FIRST DIVISION|SECOND DIVISION|THIRD DIVISION|SPECIAL [A-Z ]*DIVISION)\b")
PONENTE_LINE = re.compile(r"\n\s*([A-Z][A-Z\-\.,' ]{2,40}?),\s*((?:C\.\s*)?J\.?)\s*\*?\s*[:;]")


def iso(d):
    return datetime.strptime(re.sub(r"\s+", " ", d.replace(" ,", ",")), "%B %d, %Y").strftime("%Y-%m-%d")


def court_name(div):
    div = re.sub(r"\s+", " ", div or "").upper()
    if div == "EN BANC":
        return "En Banc"
    for n in ("FIRST", "SECOND", "THIRD"):
        if n in div:
            return n.title() + " Division"
    return div.title()


def slug(docket):
    s = docket.lower()
    s = re.sub(r"\(.*?\)|\[.*?\]", " ", s)
    s = s.replace("g.r.", "gr").replace("a.m.", "am").replace("a.c.", "ac").replace("b.m.", "bm")
    s = re.sub(r"\bnos?\.?\b", " ", s)
    s = re.split(r"\band\b|,|&", s)[0]
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "case"


def html_text(h):
    h = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</h\d>", "\n", h)
    t = html.unescape(re.sub(r"<[^>]+>", " ", h))
    t = re.sub(r"[ \t\r\f\v]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n\n", t)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(zip(sys.argv[1::1], sys.argv[2::1]))
    surname, topic_id, crawl_dir = args[0], args[1], Path(args[2])
    pdf_dir = Path(args[3]) if len(args) > 3 else None
    cutoff = opts.get("--cutoff", "9999-12-31")
    start = opts.get("--start", "0000-01-01")
    cache = ROOT / ".cache" / topic_id
    cache.mkdir(parents=True, exist_ok=True)
    rows = []

    for line in open(crawl_dir / "elib_index.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if surname not in r.get("ponente", ""):
            continue
        t = html_text(open(crawl_dir / "html" / f"{r['elib_id']}.html", encoding="utf-8").read())
        m = DIV_RE.search(t)
        body = t[m.start():] if m else t
        hm = HEADER_RE.search(body[:3000])
        if not hm:
            print("could not read header for", r["url"])
            continue
        pm = PONENTE_LINE.search(body)
        title = re.sub(r"\s+", " ", body[hm.end():pm.start()] if pm else "").strip()
        title = re.sub(r"\s*(D\s*E\s*C\s*I\s*S\s*I\s*O\s*N|R\s*E\s*S\s*O\s*L\s*U\s*T\s*I\s*O\s*N)\s*$", "", title)
        kind = "Resolution" if pm and re.search(r"R\s*E\s*S\s*O\s*L\s*U\s*T\s*I\s*O\s*N\s*$", body[hm.end():pm.start()].strip()) else "Decision"
        cut = re.search(r"\n\s*(Source:\s*Supreme Court E-Library|This page was dynamically generated)", body)
        rows.append(dict(docket=re.sub(r"\s+", " ", hm.group(1)).strip(), date=iso(hm.group(2)),
                         court=court_name(m.group(1) if m else ""), kind=kind, title=title[:600],
                         source="SC E-Library", url=r["url"], text=body[:cut.start()] if cut else body))

    if pdf_dir and (pdf_dir / "pdf_index.jsonl").exists():
        for line in open(pdf_dir / "pdf_index.jsonl", encoding="utf-8"):
            r = json.loads(line)
            if surname not in r.get("ponente", ""):
                continue
            t = open(pdf_dir / "txt" / f"{r['id']}.txt", encoding="utf-8", errors="replace").read()
            rows.append(dict(docket=r["docket"] or r["title"], date=iso(r["date"]), court=court_name(r.get("division")),
                             kind="Resolution" if re.search(r"R\s*E\s*S\s*O\s*L\s*U\s*T\s*I\s*O\s*N", t[:6000]) and not re.search(r"D\s*E\s*C\s*I\s*S\s*I\s*O\s*N", t[:6000]) else "Decision",
                             title=r["title"], source="SC Website (PDF)", url=r["pdf"], text=t))

    rows = [r for r in rows if start <= r["date"] <= cutoff]
    rows.sort(key=lambda r: (r["date"], r["docket"]))
    # one row per (docket, date); E-Library copy wins because it was added first
    seen, uniq = set(), []
    for r in rows:
        key = (slug(r["docket"]), r["date"])
        if key not in seen:
            seen.add(key)
            uniq.append(r)

    index_path = ROOT / "topics" / topic_id / "ponencias-index.json"
    old = {}
    if index_path.exists():
        old = {x["id"]: x for x in json.loads(index_path.read_text(encoding="utf-8"))}
    out = []
    for r in uniq:
        cid = f"{slug(r['docket'])}-{r['date'].replace('-', '')}"
        (cache / f"{cid}.txt").write_text(r.pop("text"), encoding="utf-8")
        r["id"] = cid
        r["text_path"] = f".cache/{topic_id}/{cid}.txt"
        r["status"] = old.get(cid, {}).get("status", "pending")
        if (ROOT / "topics" / topic_id / "cases" / f"{cid}.json").exists():
            r["status"] = "digested"
        out.append(r)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    by_court = {}
    for r in out:
        by_court[r["court"]] = by_court.get(r["court"], 0) + 1
    print(f"{len(out)} ponencias -> {index_path.relative_to(ROOT)}; by court: {by_court}")


if __name__ == "__main__":
    main()
