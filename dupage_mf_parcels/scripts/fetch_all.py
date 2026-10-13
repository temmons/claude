"""Download county parcels and every municipal zoning layer listed in sources.py."""
import os
import sys

from arcgis_fetch import fetch_layer
from sources import SOURCES

PARCELS = "https://gis.dupageco.org/arcgis/rest/services/DuPage_County_IL/ParcelsWithRealEstateCC/FeatureServer/0"
PARCEL_FIELDS = ",".join([
    "PIN", "ACREAGE", "PROPADDRL1", "PROPADDRL2", "PROPCITY", "PROPZIP", "PROPAPT", "BILLNAME",
    "MUNICIPALITY", "REA017_PROP_CLASS", "REA017_FCV_LAND", "REA017_FCV_IMP", "REA017_FCV_TOTAL",
    "EXEMPTCODE", "GIS_Prop_Class", "LEGALDES1", "LEGALDES2", "TAXCODE"])

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
only = sys.argv[2:]
if not only or "parcels" in only:
    fetch_layer(PARCELS, f"{out}/parcels.geojson", out_fields=PARCEL_FIELDS, chunk=1000, workers=8)
for town, s in SOURCES.items():
    if only and town not in only:
        continue
    path = f"{out}/zoning_{town.replace(' ', '_')}.geojson"
    try:
        fetch_layer(s["url"], path, where=s.get("where", "1=1"),
                    out_fields="PIN," + s["field"] if s.get("join") == "pin" else "*")
    except Exception as e:
        print(f"FAILED {town}: {e}", file=sys.stderr)
