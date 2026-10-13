"""Download SC website decision PDFs, extract text with pdftotext, and record the ponente line.

Usage: python tools/scan_sc_pdfs.py <cand.json> <outdir> [SURNAME]
Writes <outdir>/pdf_index.jsonl and keeps full text in <outdir>/txt/<post id>.txt (PDFs are deleted after extraction).
"""
import sys, os, re, json, time, subprocess, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
PONENTE_RE = re.compile(r"^\s*([A-Z][A-Z\-\.,' ]{2,40}?),\s*((?:C\.\s*)?J\.?)\s*\*?\s*[:;]|^\s*(PER\s+CURIAM)\s*[:;]", re.M)
DIV_RE = re.compile(r"\b(EN\s+BANC|FIRST\s+DIVISION|SECOND\s+DIVISION|THIRD\s+DIVISION|SPECIAL\s+[A-Z ]*DIVISION)\b")


def fetch(url, path):
    url = urllib.parse.quote(url, safe=":/?&=%")
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
                f.write(r.read())
            return True
        except Exception as e:
            err = e
            time.sleep(3 + 4 * i)
    print("FAIL", url, err, file=sys.stderr, flush=True)
    return False


def main():
    cand = json.load(open(sys.argv[1], encoding="utf-8"))
    outdir = sys.argv[2]
    surname = sys.argv[3] if len(sys.argv) > 3 else "ROSARIO"
    os.makedirs(os.path.join(outdir, "txt"), exist_ok=True)
    os.makedirs(os.path.join(outdir, "pdf"), exist_ok=True)

    def work(p):
        txt_path = os.path.join(outdir, "txt", f"{p['id']}.txt")
        if not (os.path.exists(txt_path) and os.path.getsize(txt_path) > 200):
            pdf_path = os.path.join(outdir, "pdf", f"{p['id']}.pdf")
            if not fetch(p["pdf"], pdf_path):
                return dict(p, ponente="", division="", error="download")
            subprocess.run(["pdftotext", "-enc", "UTF-8", pdf_path, txt_path], capture_output=True)
            try:
                os.remove(pdf_path)
            except OSError:
                pass
        t = open(txt_path, encoding="utf-8", errors="replace").read() if os.path.exists(txt_path) else ""
        head = t[:20000]
        m = PONENTE_RE.search(head)
        if m and m.group(3):
            pon = "PER CURIAM"
        elif m:
            pon = re.sub(r"\s+", " ", m.group(1)).strip() + ", " + m.group(2)
        else:
            pon = ""
        d = DIV_RE.search(head)
        return dict(p, ponente=pon, division=re.sub(r"\s+", " ", d.group(1)) if d else "", chars=len(t))

    out = open(os.path.join(outdir, "pdf_index.jsonl"), "w", encoding="utf-8")
    hits = 0
    with ThreadPoolExecutor(max_workers=5) as ex:
        for n, r in enumerate(ex.map(work, cand), 1):
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
            if surname in r.get("ponente", ""):
                hits += 1
            if n % 50 == 0:
                print(f"processed {n}/{len(cand)}; {surname} hits {hits}", flush=True)
    out.close()
    print("DONE", len(cand), surname, "hits", hits)


if __name__ == "__main__":
    main()
