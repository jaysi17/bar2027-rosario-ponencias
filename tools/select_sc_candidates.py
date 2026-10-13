"""Pick SC-website decision posts that the E-Library crawl did not already cover.

Usage: python tools/select_sc_candidates.py <sc_posts.jsonl> <elib_index.jsonl> <out cand.json> <start YYYY-MM-DD> <end YYYY-MM-DD>

Drops non-decision posts (no promulgation date or no PDF), separate opinions, and anything whose
G.R./A.M. number already appears in the E-Library index. The result feeds scan_sc_pdfs.py.
"""
import sys, re, json
from datetime import datetime


def nums(s):
    return set(re.findall(r"\d{5,6}", s or ""))


def parse(s):
    try:
        return datetime.strptime(re.sub(r"\s+", " ", s.replace(" ,", ",")), "%B %d, %Y")
    except ValueError:
        return None


def main():
    posts_path, elib_path, out_path, start, end = sys.argv[1:6]
    lo, hi = datetime.fromisoformat(start), datetime.fromisoformat(end)
    elib = set()
    for line in open(elib_path, encoding="utf-8"):
        elib |= nums(json.loads(line).get("docket", ""))
    keep = []
    for line in open(posts_path, encoding="utf-8"):
        p = json.loads(line)
        d = parse(p["date"])
        if not d or not (lo <= d <= hi) or not p["pdf"]:
            continue
        if re.search(r"(concurring|dissenting|separate)\s+opinion|^(opinion|separate|dissent|concurr)", p["title"].lower()):
            continue
        n = nums(p["docket"]) or nums(p["slug"])
        if n and n & elib:
            continue
        keep.append(p)
    json.dump(keep, open(out_path, "w", encoding="utf-8"))
    print(len(keep), "candidate PDFs ->", out_path)


if __name__ == "__main__":
    main()
