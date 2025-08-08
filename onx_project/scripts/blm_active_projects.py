import os
import csv
import time
from playwright.sync_api import sync_playwright

def extract_project_urls(page):
    import time

    page.goto('https://eplanning.blm.gov/eplanning-ui/search?filterSearch={"open":true,"active":true}')
    page.wait_for_timeout(5000)  # Wait for initial load

    project_urls = set()
    previous_count = -1

    while True:
        # Find all cells in the Project Name column
        project_name_cells = page.query_selector_all('div[col-id="projectName"] a')

        for cell in project_name_cells:
            href = cell.get_attribute('href')
            if href:
                full_url = "https://eplanning.blm.gov" + href
                project_urls.add(full_url)

        # Scroll down a bit to load next set of rows
        page.mouse.wheel(0, 500)
        time.sleep(0.5)

        # Stop if no new links are found after scroll
        if len(project_urls) == previous_count:
            break
        previous_count = len(project_urls)

    print(f"Found {len(project_urls)} project URLs.")
    return list(project_urls)


def extract_coords_from_project(page, url):
    print(f"Processing project: {url}")
    try:
        page.goto(url)
        page.wait_for_selector('esri-view-root', timeout=15000)
        time.sleep(5)  # Wait for map to fully load

        coords = page.evaluate('''() => {
            const views = window.require("esri/views/MapView").instances;
            if (!views || views.length === 0) return null;
            const graphics = views[0].graphics.items;
            if (!graphics || graphics.length === 0) return null;
            const coord = graphics[0].geometry;
            return { lat: coord.latitude, lon: coord.longitude };
        }''')
        if coords:
            print(f"Coords found: {coords['lat']}, {coords['lon']}")
            return coords['lat'], coords['lon']
        else:
            print("No coords found.")
            return None, None
    except Exception as e:
        print(f"Failed to extract coords for {url}: {e}")
        return None, None

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Step 1: Extract Project URLs from Search Page
        project_urls = extract_project_urls(page)

        # Step 2: Visit each project and get coordinates
        output_rows = []
        for url in project_urls:
            lat, lon = extract_coords_from_project(page, url)
            output_rows.append({'Project URL': url, 'Latitude': lat, 'Longitude': lon})

        # Step 3: Write Output CSV
        with open('blm_projects_with_coords.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Project URL', 'Latitude', 'Longitude'])
            writer.writeheader()
            writer.writerows(output_rows)

        print("✅ Done! Data written to blm_projects_with_coords.csv")

        browser.close()

if __name__ == "__main__":
    main()
