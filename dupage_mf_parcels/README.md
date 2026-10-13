# DuPage County: apartment-zoned parcels that are vacant or single-family

Parcels in DuPage County, IL that are **zoned multi-family, or commercial/mixed-use that allows apartments**, and whose **current use is vacant land or a single-family home**.

## Outputs (`output/`)
| File | What it is |
|---|---|
| `DuPage_apartment_zoned_vacant_or_SF_parcels.xlsx` | Parcel list (PIN, address, zoning, use, lot size, assessed value, owner, flags, map link), summary by town, the zoning-district classification table, coverage by municipality, and method notes |
| `dupage_apartment_zoned_parcels_map.html` | Standalone interactive map (open in a browser); filter by use, zoning category, town, acreage, PIN/address |
| `dupage_mf_candidates.geojson` | Parcel polygons with all attributes, for GIS |

## Method
1. **Parcels/assessment**: DuPage County `ParcelsWithRealEstateCC` (gis.dupageco.org).
2. **Zoning**: each town's own published zoning layer, plus the county's unincorporated zoning (sources in `scripts/sources.py`). Parcels get the district under their interior point (Aurora joins by PIN).
3. **Which districts allow apartments**: `scripts/zoning_classes.py`, from municipal code text or the district names in each town's layer. Three categories: multi-family (apartments), multi-family (townhouse/attached), and commercial/mixed-use allowing dwelling units.
4. **Current use**:
   - *Vacant*: assessed building value $0, taxable class, not public, utility, HOA, or apartment-complex land.
   - *Single-family*: assessor class R with a building, not a condo. Townhouse/duplex units are removed using FEMA/ORNL USA Structures footprints that span parcels.

## Not covered
Addison, Hinsdale, Itasca, Winfield, Oakbrook Terrace, Wayne, and the DuPage slivers of Bolingbrook, Chicago, St. Charles, Elk Grove, Lemont, Schaumburg, and Batavia. These publish zoning only as PDF maps. Planned-development districts are not counted.

## Rerun
```
pip install geopandas pyarrow requests openpyxl
cd scripts
python fetch_all.py DATA_DIR                 # parcels + zoning layers
python -c "from arcgis_fetch import fetch_layer; ..."   # structures, municipal boundaries, roads (see build notes in analyze.py / build_map.py)
python analyze.py DATA_DIR WORK_DIR
python build_outputs.py WORK_DIR ../output
python build_map.py WORK_DIR ../output/dupage_apartment_zoned_parcels_map.html
```
`analyze.py` expects `DATA_DIR/structures.parquet` (USA Structures, `FIPS='17043'`, saved as parquet). `build_map.py` expects `muni.json`, `roads.json`, and `leaflet.css` in `WORK_DIR`.
