"""Crawl SC E-Library monthly decision lists and find decisions penned by a given justice.

Usage: python tools/find_ponencias_elib.py <outdir> <SURNAME> <start YYYY-MM> <end YYYY-MM>
Writes <outdir>/elib_index.jsonl (every decision seen, with ponente) and caches HTML in <outdir>/html/.
"""
import sys, os, re, json, time, html, urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            if i == tries - 1:
                print("FAIL", url, e, file=sys.stderr)
                return ""
            time.sleep(2 + 3 * i)


def text_of(h):
    h = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    t = re.sub(r"<[^>]+>", " ", h)
    t = html.unescape(t)
    return re.sub(r"[ \t\r\f\v]+", " ", t)


PONENTE_RE = re.compile(r"\n\s*([A-Z][A-Z\-\.,' ]{2,40}?),\s*((?:C\.\s*)?J\.?)\s*\*?\s*[:;]|\n\s*(PER CURIAM)\s*[:;]", re.M)
DIV_RE = re.compile(r"\b(EN BANC|FIRST DIVISION|SECOND DIVISION|THIRD DIVISION|SPECIAL [A-Z ]*DIVISION)\b")
DOCKET_RE = re.compile(r"((?:G\.R\.|A\.M\.|A\.C\.|B\.M\.|UDK|OCA I\.P\.I\.)[^\n\]]{0,80}?),\s*([A-Z][a-z]+ \d{1,2}, \d{4})")


def parse_decision(h):
    t = text_of(h)
    # cut at the start of the decision body to avoid nav noise
    m = DIV_RE.search(t)
    division = m.group(1) if m else ""
    body = t[m.start():] if m else t
    pm = PONENTE_RE.search(body)
    if pm and pm.group(3):
        ponente = "PER CURIAM"
    else:
        ponente = (pm.group(1).strip() + ", " + pm.group(2)) if pm else ""
    dm = DOCKET_RE.search(body)
    docket = dm.group(1).strip() if dm else ""
    date = dm.group(2) if dm else ""
    # title: text between docket line and ponente line, compressed
    title = ""
    if dm and pm and pm.start() > dm.end():
        title = re.sub(r"\s+", " ", body[dm.end():pm.start()]).strip()
        title = re.sub(r"^\]?\s*", "", title)
        title = re.sub(r"\s*(D E C I S I O N|DECISION|R E S O L U T I O N|RESOLUTION)\s*$", "", title)[:400]
    kind = "Resolution" if re.search(r"R\s*E\s*S\s*O\s*L\s*U\s*T\s*I\s*O\s*N", body[: (pm.start() if pm else 3000)]) else "Decision"
    return dict(division=division, ponente=ponente, docket=docket, date=date, title=title, kind=kind)


def month_iter(start, end):
    y, m = map(int, start.split("-"))
    ey, em = map(int, end.split("-"))
    while (y, m) <= (ey, em):
        yield y, m
        m += 1
        if m > 12:
            y, m = y + 1, 1


def main():
    outdir, surname, start, end = sys.argv[1:5]
    os.makedirs(os.path.join(outdir, "html"), exist_ok=True)
    links = []
    for y, m in month_iter(start, end):
        url = f"https://elibrary.judiciary.gov.ph/thebookshelf/docmonth/{MONTHS[m-1]}/{y}/1"
        h = get(url)
        ids = sorted(set(re.findall(r"showdocs/1/(\d+)", h)))
        print(f"{y}-{m:02d}: {len(ids)}", flush=True)
        links += [(f"{y}-{m:02d}", i) for i in ids]

    def work(item):
        ym, did = item
        path = os.path.join(outdir, "html", f"{did}.html")
        if os.path.exists(path) and os.path.getsize(path) > 5000:
            h = open(path, encoding="utf-8").read()
        else:
            h = get(f"https://elibrary.judiciary.gov.ph/thebookshelf/showdocs/1/{did}")
            if h:
                open(path, "w", encoding="utf-8").write(h)
        rec = parse_decision(h) if h else {}
        rec.update(listmonth=ym, elib_id=did, url=f"https://elibrary.judiciary.gov.ph/thebookshelf/showdocs/1/{did}")
        return rec

    out = open(os.path.join(outdir, "elib_index.jsonl"), "w", encoding="utf-8")
    hits = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        for n, rec in enumerate(ex.map(work, links), 1):
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if surname in rec.get("ponente", ""):
                hits += 1
            if n % 200 == 0:
                print(f"  processed {n}/{len(links)}; {surname} hits so far: {hits}", flush=True)
    out.close()
    print(f"DONE. total={len(links)} {surname}_hits={hits}")


if __name__ == "__main__":
    main()
