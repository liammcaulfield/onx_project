import json
import pandas as pd

# --- Load the files ---
geojson_path = "data/outputs/usfs_selected_forests.geojson"
csv_path = "data/processed/usfs_comments_with_coords.csv"
output_path = "data/processed/usfs_merged.geojson"

with open(geojson_path, 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)

df_csv = pd.read_csv(csv_path)

# --- Normalize and prepare multi-forest matching ---
def get_forest_list(admin_units):
    if pd.isna(admin_units):
        return []
    return [name.strip().lower() for name in admin_units.split(';')]

df_csv['forest_list'] = df_csv['admin unit'].apply(get_forest_list)

# --- Assign matching data ---
for feature in geojson_data['features']:
    forest_name = feature['properties'].get('FORESTNAME', '').strip().lower()

    matched_row = None
    for _, row in df_csv.iterrows():
        if forest_name in row['forest_list']:
            matched_row = row
            break

    if matched_row is not None:
        feature['properties']['title'] = matched_row.get('title', '')
        feature['properties']['type'] = matched_row.get('type', '')
        feature['properties']['comments_close_on'] = matched_row.get('comments_close_on', '')
        feature['properties']['days_left'] = matched_row.get('days_left', '')
        feature['properties']['html_url'] = matched_row.get('html_url', '')

# --- Save the new GeoJSON ---
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(geojson_data, f, indent=2)

print(f"✅ Merged GeoJSON written to: {output_path}")
