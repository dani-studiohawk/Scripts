import psycopg2
import geojson
from shapely.geometry import shape
from shapely import wkb

# Replace with your Supabase connection string
conn = psycopg2.connect("postgresql://postgres.qszyffifotylrcvxwkdk:2jFU6bePL_7*4Fe@aws-0-eu-west-2.pooler.supabase.com:6543/postgres")
cur = conn.cursor()

# Load your GeoJSON file
with open(r'G:\My Drive\Workflow\Resources\Geolocation Files\Geojson\sa1_2021.geojson') as f:
    gj = geojson.load(f)

for feature in gj['features']:
    props = feature['properties']
    sa1_code = props.get('SA1_CODE_2021')
    change_flag = props.get('CHANGE_FLAG_2021')
    change_label = props.get('CHANGE_LABEL_2021')
    sa2_code = props.get('SA2_CODE_2021')
    sa2_name = props.get('SA2_NAME_2021')
    sa3_code = props.get('SA3_CODE_2021')
    sa3_name = props.get('SA3_NAME_2021')
    sa4_code = props.get('SA4_CODE_2021')
    sa4_name = props.get('SA4_NAME_2021')
    gccsa_code = props.get('GCCSA_CODE_2021')
    gccsa_name = props.get('GCCSA_NAME_2021')
    state_code = props.get('STATE_CODE_2021')
    state_name = props.get('STATE_NAME_2021')
    aus_code = props.get('AUS_CODE_2021')
    aus_name = props.get('AUS_NAME_2021')
    area_sqkm = props.get('AREA_ALBERS_SQKM')
    asgs_loci_uri = props.get('ASGS_LOCI_URI_2021')
    
    # Skip if sa1_code is missing
    if not sa1_code:
        print("Skipping feature with missing SA1_CODE_2021")
        continue
    
    geom = shape(feature['geometry'])
    wkb_geom = geom.wkb  # Convert to WKB for PostGIS

    cur.execute("""
        INSERT INTO sa1_2021_boundaries (
            sa1_code_2021, change_flag_2021, change_label_2021, 
            sa2_code_2021, sa2_name_2021, sa3_code_2021, sa3_name_2021,
            sa4_code_2021, sa4_name_2021, gccsa_code_2021, gccsa_name_2021, 
            state_code_2021, state_name_2021, aus_code_2021, aus_name_2021, 
            area_albers_sqkm, asgs_loci_uri_2021, geometry
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(%s::geometry, 4326))
    """, (
        sa1_code, change_flag, change_label,
        sa2_code, sa2_name, sa3_code, sa3_name,
        sa4_code, sa4_name, gccsa_code, gccsa_name,
        state_code, state_name, aus_code, aus_name,
        area_sqkm, asgs_loci_uri, wkb_geom
    ))

    print(f"Uploaded {sa1_code}")

conn.commit()
cur.close()
conn.close()

print("Upload complete!")
