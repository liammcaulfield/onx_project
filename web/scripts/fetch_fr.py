#!/usr/bin/env python3
"""
fetch_usfs_open_fr.py
Pull Forest Service Federal Register notices that are STILL OPEN for public comment.
Output → data/raw/usfs_open_comments_YYYY-MM-DD.csv
"""

import csv, datetime as dt, pathlib, requests, sys

BASE = "https://www.federalregister.gov/api/v1/documents.json"
AGENCY  = "forest-service"          # you could also use agency_ids[]=31
PER_PAGE = 100
FIELDS = [
    "document_number","title","type","publication_date",
    "comments_close_on","comment_url","html_url","docket_ids"
]

def page_query(page: int) -> list[dict]:
    params = [
        ("per_page", PER_PAGE),
        ("order", "newest"),
        ("conditions[agencies][]", AGENCY),
        ("conditions[type][]", "NOTICE"),     # add PRORULE or RULE if you need them too
        ("page", page)
    ]
    # one fields[]= param **per field**  – that’s what the FR API expects
    params.extend([("fields[]", f) for f in FIELDS])
    r = requests.get(BASE, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def fetch_open_docs(today: dt.date):
    docs, page = [], 1
    while True:
        data = page_query(page)
        for d in data["results"]:
            end = d.get("comments_close_on")
            if end and dt.date.fromisoformat(end) >= today:
                d["days_left"] = (dt.date.fromisoformat(end) - today).days
                docs.append(d)
        if not data.get("next_page_url"):
            break
        page += 1
    return docs

def write_csv(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"✓ saved {len(rows)} open Forest Service dockets → {path}")

def main():
    today = dt.date.today()
    docs = fetch_open_docs(today)
    if not docs:
        sys.exit("No Forest Service comment periods are currently open.")
    out = pathlib.Path("data/raw") / f"usfs_open_comments_{today}.csv"
    write_csv(docs, out)

if __name__ == "__main__":
    main()
