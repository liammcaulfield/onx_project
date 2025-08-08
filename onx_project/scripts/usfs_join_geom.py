#!/usr/bin/env python3
"""
merge_forest_centroids_into_comments.py
───────────────────────────────────────
Add lat/lon coordinates to each row in the USFS comments CSV based on forest centroid matches.
"""

import pandas as pd

# Paths
COMMENTS_CSV = "data/outputs/usfs_open_comments_2025-08-07.csv"
CENTROIDS_CSV = "data/processed/usfs_selected_forests.csv"
OUTPUT_CSV = "data/processed/usfs_comments_with_coords.csv"

# Load files
comments_df = pd.read_csv(COMMENTS_CSV)
centroids_df = pd.read_csv(CENTROIDS_CSV)

# Normalize names
comments_df.columns = comments_df.columns.str.strip()
centroids_df.columns = centroids_df.columns.str.strip()
comments_df["admin unit"] = comments_df["admin unit"].astype(str).str.strip()
centroids_df["FORESTNAME"] = centroids_df["FORESTNAME"].astype(str).str.strip()

# Create lookup dictionary of centroids
centroid_lookup = centroids_df.set_index("FORESTNAME")[["lon", "lat"]].to_dict("index")

# Prepare lists for coordinates
lons = []
lats = []

for admin_unit in comments_df["admin unit"]:
    # Split by comma if there are multiple forests
    forests = [f.strip() for f in admin_unit.split(",")]

    # Average coordinates of all matching forests
    matched_coords = [centroid_lookup.get(f) for f in forests if f in centroid_lookup]

    if matched_coords:
        avg_lon = sum(c["lon"] for c in matched_coords) / len(matched_coords)
        avg_lat = sum(c["lat"] for c in matched_coords) / len(matched_coords)
    else:
        avg_lon = None
        avg_lat = None

    lons.append(avg_lon)
    lats.append(avg_lat)

# Add columns
comments_df["lon"] = lons
comments_df["lat"] = lats

# Save
comments_df.to_csv(OUTPUT_CSV, index=False)
print(f"✅ Saved enriched comments → {OUTPUT_CSV}")
