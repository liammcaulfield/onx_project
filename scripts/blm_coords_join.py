#!/usr/bin/env python
import argparse, csv, pathlib, re, zipfile, tempfile, shutil, unicodedata
import geopandas as gpd

# ──── helper ──────────────────────────────────────────────────────────
def norm(text: str) -> str:
    """Upper-case, remove punctuation & generic words so names match."""
    t = unicodedata.normalize("NFKD", text).upper()
    t = re.sub(r"[^A-Z ]", "", t)
    return re.sub(r"\b(FIELD|DISTRICT|STATE|OFFICE|FO|DO)\b", "", t).strip()

# ──── CLI args ───────────────────────────────────────────────────────
ap = argparse.ArgumentParser()
ap.add_argument("-z", "--zip", required=True, help=".gdb.zip file")
ap.add_argument("-i", "--csv-in",  default="blm_active_projects.csv")
ap.add_argument("-o", "--csv-out", default="blm_projects_with_coords.csv")
args = ap.parse_args()

ZIP = pathlib.Path(args.zip).expanduser()
CSV_IN  = pathlib.Path(args.csv_in)
CSV_OUT = pathlib.Path(args.csv_out)

# ──── unzip & load polygons ──────────────────────────────────────────
tmp = tempfile.mkdtemp()
try:
    with zipfile.ZipFile(ZIP) as z:
        z.extractall(tmp)
    gdb = str(next(pathlib.Path(tmp).glob("*.gdb")))

    layer = "blm_natl_admu_field_poly_webpub"
    gdf = gpd.read_file(gdb, layer=layer, engine="pyogrio").to_crs(4326)

    gdf["KEY"] = gdf["ADMU_NAME"].apply(norm)
    gdf = gdf.drop_duplicates(subset="KEY", keep="first")
    gdf["Latitude"]  = gdf.geometry.centroid.y
    gdf["Longitude"] = gdf.geometry.centroid.x
    lookup = gdf.set_index("KEY")[["Latitude", "Longitude"]].to_dict("index")

    # ──── merge with CSV ──────────────────────────────────────────
    with CSV_IN.open(newline='', encoding="utf-8-sig") as f:
        rdr    = csv.reader(f)
        header = next(rdr)
        lead_i = header.index("Lead Office")

        out_rows = []
        for r in rdr:
            lat = lon = ""
            match = lookup.get(norm(r[lead_i]))
            if match:
                lat, lon = match["Latitude"], match["Longitude"]
            out_rows.append(r + [lat, lon])

    with CSV_OUT.open("w", newline='', encoding="utf-8") as f:
        csv.writer(f).writerows([header + ["Latitude", "Longitude"]] + out_rows)

    print(f"✅  wrote {CSV_OUT}  ({len(out_rows)} rows)")

finally:
    shutil.rmtree(tmp)
