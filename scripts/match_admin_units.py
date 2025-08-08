#!/usr/bin/env python3
"""
match_admin_units.py
────────────────────
Enrich the Federal-Register notice CSV with a column listing the
National Forest administrative units that appear in the notice title.

USAGE (from project root)
  python scripts/match_admin_units.py \
         data/raw/usfs_open_comments_2025-08-07.csv \
         data/boundaries/Forest_Administrative_Boundaries_(Feature_Layer).geojson
"""
import sys, re, csv, json, pathlib, pandas as pd

################################################################################
# 1.  read inputs --------------------------------------------------------------
################################################################################
notice_csv  = pathlib.Path(sys.argv[1])
boundary_fp = pathlib.Path(sys.argv[2])     # .geojson **or** .csv is fine

df = pd.read_csv(notice_csv)

# boundary file can be GeoJSON **or** the flat CSV ArcGIS export
if boundary_fp.suffix.lower() == ".geojson":
    with open(boundary_fp, "r", encoding="utf-8") as fh:
        bdy_json = json.load(fh)
    forest_names = [f["properties"]["FORESTNAME"] for f in bdy_json["features"]]
else:                                       # flat CSV fallback
    forest_names = pd.read_csv(boundary_fp)["FORESTNAME"].tolist()

################################################################################
# 2.  build simple lookup table ------------------------------------------------
################################################################################
# strip “National Forest(s)” so we catch titles that list several forests
def simplify(name: str) -> str:
    return re.sub(r"\s+National\s+Forest[s]?", "", name, flags=re.I).strip().lower()

canonical  = {name: simplify(name) for name in forest_names}

################################################################################
# 3.  match each title to zero/one/many forests --------------------------------
################################################################################
def match_title(title: str) -> list[str]:
    low = title.lower()
    hits = []
    for full, simp in canonical.items():
        if simp and simp in low:
            hits.append(full)
        elif full.lower() in low:
            hits.append(full)
    return sorted(set(hits))                # deduplicate & keep stable order

df["admin_units"] = df["title"].apply(match_title)

################################################################################
# 4.  write output -------------------------------------------------------------
################################################################################
out_csv = notice_csv.with_name(notice_csv.stem + "_with_units.csv")
df.to_csv(out_csv, index=False)
print(f"✓ wrote {out_csv} with admin_units column")
