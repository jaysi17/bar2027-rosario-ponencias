"""List all decision posts on sc.judiciary.gov.ph via the WordPress REST API.

Usage: python tools/list_sc_posts.py <outdir>
Writes <outdir>/sc_posts.jsonl with: id, slug, title, docket, date (promulgation), pdf, uploaded.
"""
import sys, os, re, json, html, time, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
API = "https://sc.judiciary.gov.ph/wp-json/wp/v2/posts?per_page=100&page={}&_fields=id,slug,title,content,date"


def get(url):
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read().decode("utf-8", "replace"), dict(r.headers)
        except urllib.error.HTTPError as e:
            if e.code == 400:
                return "[]", {}
            time.sleep(3 + 5 * i)
        except Exception:
            time.sleep(3 + 5 * i)
    return "[]", {}


DATE_RE = re.compile(r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\s*,\s*\d{4})")


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    out = open(os.path.join(outdir, "sc_posts.jsonl"), "w", encoding="utf-8")
    page, n = 1, 0
    while True:
        body, hdr = get(API.format(page))
        posts = json.loads(body)
        if not posts:
            break
        if page == 1:
            print("total posts:", hdr.get("X-WP-Total"), "pages:", hdr.get("X-WP-TotalPages"), flush=True)
        for p in posts:
            c = p["content"]["rendered"]
            txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", c)))
            title = html.unescape(re.sub(r"<[^>]+>", "", p["title"]["rendered"]))
            pdfs = re.findall(r'href="([^"]+\.pdf)"', c)
            dm = DATE_RE.search(txt)
            docket = ""
            km = re.search(r"((?:G\.R\.|A\.M\.|A\.C\.|B\.M\.|UDK|OCA)[^\[]{0,80}?)\.?\s+" + (re.escape(dm.group(1)) if dm else r"$"), txt)
            if km:
                docket = km.group(1).strip()
            um = re.search(r"Date Uploaded:\s*([\d/]+)", txt)
            out.write(json.dumps(dict(id=p["id"], slug=p["slug"], title=title, docket=docket,
                                      date=re.sub(r"\s+,", ",", dm.group(1)) if dm else "",
                                      pdf=pdfs[0] if pdfs else "", uploaded=um.group(1) if um else "",
                                      posted=p["date"]), ensure_ascii=False) + "\n")
            n += 1
        print("page", page, "cum", n, flush=True)
        page += 1
        time.sleep(0.5)
    out.close()
    print("DONE", n)


if __name__ == "__main__":
    main()
