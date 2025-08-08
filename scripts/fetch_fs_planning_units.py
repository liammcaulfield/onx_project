import requests
import json
from pathlib import Path

BASE_URL = "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_LandManagementPlanningUnit_01/MapServer/0"
OUT_PATH = Path("data/outputs/fs_planning_units.geojson")
CHUNK_SIZE = 50

def get_all_object_ids():
    params = {
        "where": "1=1",
        "returnIdsOnly": "true",
        "f": "json"
    }
    r = requests.get(f"{BASE_URL}/query", params=params)
    r.raise_for_status()
    return r.json().get("objectIds", [])

def fetch_chunk(object_ids):
    params = {
        "objectIds": ",".join(map(str, object_ids)),
        "outFields": "*",
        "returnGeometry": "true",
        "f": "geojson"
    }
    r = requests.get(f"{BASE_URL}/query", params=params)
    r.raise_for_status()
    return r.json().get("features", [])

def main():
    print("[INFO] Getting OBJECTIDs…")
    object_ids = get_all_object_ids()
    print(f"[INFO] Found {len(object_ids)} records.")

    all_features = []

    for i in range(0, len(object_ids), CHUNK_SIZE):
        chunk_ids = object_ids[i:i + CHUNK_SIZE]
        print(f"[INFO] Fetching records {i + 1}–{i + len(chunk_ids)}")
        features = fetch_chunk(chunk_ids)
        all_features.extend(features)

    feature_collection = {
        "type": "FeatureCollection",
        "features": all_features
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(feature_collection, f)

    print(f"[DONE] Wrote {len(all_features)} features to {OUT_PATH}")

if __name__ == "__main__":
    main()
