import requests
import json
from pathlib import Path

def arcgis_to_geojson_feature(feature):
    geometry = feature.get("geometry")
    attributes = feature.get("attributes")

    if not geometry or not attributes:
        return None

    # Handle polygon geometry
    if "rings" in geometry:
        geojson_geom = {
            "type": "Polygon",
            "coordinates": geometry["rings"]
        }
    elif "paths" in geometry:
        geojson_geom = {
            "type": "LineString",
            "coordinates": geometry["paths"][0]
        }
    elif "x" in geometry and "y" in geometry:
        geojson_geom = {
            "type": "Point",
            "coordinates": [geometry["x"], geometry["y"]]
        }
    else:
        return None

    return {
        "type": "Feature",
        "geometry": geojson_geom,
        "properties": attributes
    }

def fetch_all_features():
    base_url = "https://services1.arcgis.com/KbxwQRRfWyEYLgp4/arcgis/rest/services/BLM_Natl_Land_Use_Plans_Approved_2022/FeatureServer/1/query"
    all_features = []
    offset = 0
    page_size = 1000

    print("[INFO] Fetching approved land use plans…")

    while True:
        params = {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": page_size
        }

        resp = requests.get(base_url, params=params)
        resp.raise_for_status()
        data = resp.json()
        arcgis_features = data.get("features", [])

        if not arcgis_features:
            break

        for f in arcgis_features:
            converted = arcgis_to_geojson_feature(f)
            if converted:
                all_features.append(converted)

        offset += page_size
        print(f"[INFO] Retrieved {len(arcgis_features)} more features…")

    return {
        "type": "FeatureCollection",
        "features": all_features
    }

def main():
    output_path = Path("data/outputs/approved_land_use_plans.geojson")
    geojson = fetch_all_features()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(geojson, f)
    print(f"[DONE] Wrote {len(geojson['features'])} features to {output_path}")

if __name__ == "__main__":
    main()
