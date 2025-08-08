from pathlib import Path
import csv
import io
import time
from playwright.sync_api import sync_playwright

SEARCH_URL = (
    "https://eplanning.blm.gov/eplanning-ui/"
    "search?filterSearch=%7B\"open\":true,\"active\":true%7D"
)

OUT_FILE = Path("blm_active_projects.csv")   # final merged file

def download_page_csv(page):
    """click orange button, return csv text"""
    with page.expect_download() as dlinfo:
        page.locator('button:has-text("Download Results")').click()
    temp_path = dlinfo.value.path()
    return Path(temp_path).read_text(encoding="utf-8")

def ensure_100_rows(page):
    """set the 'Show ___ rows per page' dropdown to 100 if option exists"""
    dropdown = page.locator('select[aria-label*="rows per page"]')
    if dropdown.count():
        dropdown.select_option("100")  # silently ignored if 100 not in list
        time.sleep(1.0)

def merge_csv_texts(csv_texts):
    """merge multiple CSV strings (same header) into list-of-dict"""
    all_rows, header = [], None
    for txt in csv_texts:
        reader = csv.DictReader(io.StringIO(txt))
        if header is None:
            header = reader.fieldnames
        for row in reader:
            all_rows.append(row)
    return header, all_rows

def main():
    merged_csvs = []

    with sync_playwright() as p:
        browser  = p.chromium.launch(headless=True)
        context  = browser.new_context(accept_downloads=True)
        page     = context.new_page()

        print("→ opening search page …")
        page.goto(SEARCH_URL, wait_until="networkidle")
        page.wait_for_timeout(2500)

        # try to bump to 100 rows per page
        ensure_100_rows(page)

        page_no = 1
        while True:
            print(f"  • downloading page {page_no}")
            merged_csvs.append(download_page_csv(page))

            # is “Next Page” button disabled?
            next_btn = page.locator('button[aria-label="Next Page"]')
            if not next_btn.count() or next_btn.get_attribute("disabled"):
                break

            next_btn.click()
            page.wait_for_timeout(1200)   # wait grid redraw
            page_no += 1

        browser.close()

    hdr, rows = merge_csv_texts(merged_csvs)
    OUT_FILE.write_text(
        "\ufeff" +  # keep Excel happy (BOM)
        ",".join(hdr) + "\n" +
        "\n".join(
            ",".join(row[h] or "" for h in hdr)
            for row in rows
        ),
        encoding="utf-8"
    )

    print(f"✅ merged {len(rows)} rows → {OUT_FILE.resolve()}")

if __name__ == "__main__":
    # first-time users:   pip install playwright   &&   playwright install
    main()
