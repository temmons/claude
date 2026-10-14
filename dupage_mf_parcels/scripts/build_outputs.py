"""Build the Excel workbook and the web map data from analyze.py results."""
import json
import sys
from datetime import date

import geopandas as gpd
import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from sources import NO_GIS_ZONING, SOURCES
from zoning_classes import CLASSES, LABELS

WORK, OUT = sys.argv[1], sys.argv[2]
c = gpd.read_parquet(f"{WORK}/_candidates.parquet").to_crs(4326)
cov = pd.read_csv(f"{WORK}/_coverage.csv")

c["address"] = c.PROPADDRL1.fillna("").str.strip()
c["city_zip"] = c.PROPADDRL2.fillna("").str.strip()
c["maps_link"] = "https://www.google.com/maps/search/?api=1&query=" + c.lat.astype(str) + "," + c.lon.astype(str)
side = "vacant lot owned by the owner of an adjoining improved parcel (likely side yard)"
c["flag_text"] = c.structure_type_note.fillna("")
c.loc[c.vacant_side_lot_flag, "flag_text"] = (c.flag_text + "; " + side).str.strip("; ")

# Most recent recorded sale (fetch_sales.py) and lookup links.
try:
    sales = pd.read_csv(f"{WORK}/_sales.csv", dtype={"PIN": str})
    c = c.merge(sales, on="PIN", how="left")
except FileNotFoundError:
    for k in ["last_sale_date", "last_sale_price", "last_sale_doc_type", "last_sale_buyer"]:
        c[k] = None
c["last_sale_date"] = pd.to_datetime(c.last_sale_date, format="%m/%d/%Y", errors="coerce")
c.loc[c.last_sale_date.dt.year < 1950, "last_sale_date"] = pd.NaT  # 01/01/1900 is a placeholder in the county data
c["last_sale_price"] = pd.to_numeric(c.last_sale_price.astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce")
c["record_link"] = "https://propertylookup.dupagecounty.gov/Datalets/Datalet.aspx?UseSearch=no&mode=sales&pin=" + c.PIN
city = c.city_zip.str.replace(r"\s+IL\s+", " IL ", regex=True)
c["listing_link"] = ("https://www.zillow.com/homes/" + (c.address + " " + city).str.replace(r"[^A-Za-z0-9 ]", "", regex=True).str.strip().str.replace(r"\s+", "-", regex=True) + "_rb/")
c.loc[c.address.str.len() < 3, "listing_link"] = None

cols = {
    "PIN": "PIN",
    "address": "Property address",
    "city_zip": "City / ZIP",
    "MUNICIPALITY": "Municipality",
    "current_use": "Current use",
    "zoning_category": "Zoning category",
    "zoning_raw": "Zoning district (as mapped)",
    "zoning_code": "Base district",
    "zoning_note": "District description",
    "zoning_basis": "Classification basis",
    "acres": "Lot acres",
    "lot_sqft": "Lot sq ft",
    "building_footprint_sqft": "Building footprint sq ft",
    "REA017_PROP_CLASS": "Assessor class",
    "REA017_FCV_LAND": "Assessed land $",
    "REA017_FCV_IMP": "Assessed building $",
    "REA017_FCV_TOTAL": "Assessed total $",
    "market_value_est": "Est. market value $ (3x assessed)",
    "BILLNAME": "Taxpayer name",
    "last_sale_date": "Last sale date",
    "last_sale_price": "Last sale price $",
    "last_sale_doc_type": "Last sale deed type",
    "last_sale_buyer": "Last sale buyer",
    "listing_link": "Check for sale (Zillow)",
    "record_link": "County sales record",
    "flag_text": "Flags",
    "lat": "Latitude",
    "lon": "Longitude",
    "maps_link": "Map link",
}
tbl = c[list(cols)].rename(columns=cols)
tbl["Taxpayer name"] = tbl["Taxpayer name"].fillna("").str.strip()
tbl = tbl.sort_values(["Municipality", "Zoning category", "Current use", "Lot acres"], ascending=[True, True, True, False])

summary = (c.assign(n=1)
           .pivot_table(index="MUNICIPALITY", columns=["current_use"], values=["n", "acres"], aggfunc="sum", fill_value=0))
summary.columns = [f"{u} – {'parcels' if m == 'n' else 'acres'}" for m, u in summary.columns]
summary = summary[[k for k in ["Vacant land – parcels", "Vacant land – acres", "Single-family home – parcels", "Single-family home – acres"] if k in summary]]
for cat, lab in LABELS.items():
    summary[f"{lab} – parcels"] = c[c.zoning_cat == cat].groupby("MUNICIPALITY").size()
summary = summary.fillna(0)
summary.loc["TOTAL"] = summary.sum()
summary = summary.round(2).reset_index().rename(columns={"MUNICIPALITY": "Municipality"})

zrows = [dict(Municipality=t, District=d, Category=LABELS[v[0]], Basis=v[1], Description=v[2])
         for t, ds in CLASSES.items() for d, v in ds.items()]
zt = pd.DataFrame(zrows)

cov = cov.rename(columns={"MUNICIPALITY": "Municipality", "parcels": "Parcels in county layer",
                          "zoning_matched": "Parcels matched to a zoning district",
                          "zoned_for_apartments": "Parcels in an apartment-allowing district",
                          "zoning_source": "Zoning source"})
cov["Zoning source"] = cov["Zoning source"].fillna("")
cov.loc[cov.Municipality == "Uninc", "Municipality"] = "Unincorporated DuPage"

today = date.today().isoformat()
readme = [
    ("DuPage County parcels zoned for apartments, currently vacant or single-family", ""),
    ("Built", today),
    ("", ""),
    ("WHAT IS INCLUDED", ""),
    ("Zoning", "Parcels in (a) a multi-family residential district or (b) a commercial / downtown / mixed-use district whose code allows dwelling units (often above the ground floor, some by special use). See the 'Zoning districts' sheet for every district counted and why."),
    ("Zoning categories", "Multi-family (apartments) = district permits apartment/condo buildings. Multi-family (townhouse/attached) = 'general residence' style districts where multi-unit housing is mainly townhouses/attached, apartments limited. Commercial/mixed-use allowing apartments = business districts that allow residential units."),
    ("Current use: Vacant land", "Assessed building value = $0, assessed land value >= $1,000, taxable class (residential, commercial, industrial, farm), lot >= 2,500 sq ft. Excludes exempt/public land, utility corridors (ComEd, Nicor, etc.), homeowner-association/common areas, and land-only PINs of existing apartment complexes."),
    ("Current use: Single-family home", "Assessor class R (residential) with building value > $0, lot >= 3,000 sq ft, not a condo unit (stacked PINs or unit numbers in the address), and not part of an attached building. Townhouses/duplex halves are removed using FEMA/ORNL USA Structures building footprints: a footprint spread across 3+ parcels, or split at least 25/75 between two parcels, is treated as attached."),
    ("", ""),
    ("FLAGS", ""),
    ("review: house footprint crosses a lot line", "The house footprint overlaps a neighboring parcel by 10–25%. Usually mapping offset, sometimes a duplex. Check before relying on it."),
    ("building footprint present", "Vacant by assessment, but a building footprint sits on the lot. Often new construction not yet assessed, or a garage/shed."),
    ("vacant lot owned by the owner of an adjoining improved parcel", "Likely a side yard or extra lot held with a house or business next door."),
    ("", ""),
    ("SOURCES", ""),
    ("Parcels & assessment", "DuPage County GIS, ParcelsWithRealEstateCC: https://gis.dupageco.org/arcgis/rest/services/DuPage_County_IL/ParcelsWithRealEstateCC/FeatureServer/0 (assessed values are 1/3 of market value)."),
    ("Zoning", "Each municipality's own published zoning layer, plus DuPage County unincorporated zoning. Layer URLs are on the 'Coverage' sheet."),
    ("Sales", "Most recent recorded transfer from the DuPage County Property Lookup portal (https://propertylookup.dupagecounty.gov), Sales page per PIN. Includes non-market transfers (quitclaim, trustee and other deeds, often at $0 or $10); check the deed type before treating a price as market value."),
    ("Deed type codes", "WD warranty deed, SW special warranty deed, TD trustee's deed, ED executor's deed, QC quitclaim deed, TR trust transfer, BI beneficial interest assignment, OT other. WD/SW sales are usually market sales."),
    ("For sale", "No free, permitted source of active listings exists (listings come from the MLS; Zillow/Redfin/LoopNet prohibit automated collection). 'Check for sale' opens a Zillow search for the address. Vacant parcels without a street address have no link."),
    ("Building footprints", "USA Structures (FEMA/ORNL), FIPS 17043: https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/USA_Structures_View/FeatureServer/0"),
    ("District rules", "Municipal zoning codes (via Zoneomics code mirror and municipal PDFs) and district names/descriptions in the towns' GIS layers."),
    ("", ""),
    ("LIMITATIONS", ""),
    ("Towns not covered", "No public GIS zoning layer was found for: " + ", ".join(NO_GIS_ZONING) + ". Their zoning is only available as PDF maps, so their parcels are not analyzed. Addison (~11,700 parcels) and Hinsdale (~5,700) are the largest gaps."),
    ("Planned developments", "PUD/PD overlays whose uses are set by an individual ordinance (e.g. Aurora PDD, Bartlett PD, Bloomingdale Stratford PD, Warrenville SD) are not counted, even though some allow apartments."),
    ("Small multi-unit buildings", "The assessor classes some 2–4 unit buildings as residential (R). Where the footprint dataset doesn't tag them multi-family they can appear as 'single-family home'."),
    ("Zoning classification", "District calls marked 'inferred' follow the district's name and were not confirmed in the code text. Verify with the municipality before acting on any parcel."),
    ("Clarendon Hills", "That town's layer stores generalized class names (e.g. 'Multi-Family Residential', 'General Sale') instead of district codes; they are mapped to R-3 and the downtown B districts."),
    ("Data currency", "Layers downloaded " + today + ". Zoning layers are updated by each town on its own schedule and may lag recent rezonings."),
]
rm = pd.DataFrame(readme, columns=["Item", "Detail"])

xlsx = f"{OUT}/DuPage_apartment_zoned_vacant_or_SF_parcels.xlsx"
with pd.ExcelWriter(xlsx, engine="openpyxl") as xw:
    rm.to_excel(xw, sheet_name="Read me", index=False)
    tbl.to_excel(xw, sheet_name="Parcels", index=False)
    summary.to_excel(xw, sheet_name="Summary by town", index=False)
    zt.to_excel(xw, sheet_name="Zoning districts", index=False)
    cov.to_excel(xw, sheet_name="Coverage", index=False)
    head = PatternFill("solid", fgColor="1F3A5F")
    for ws in xw.book.worksheets:
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = head
            cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.freeze_panes = "A2"
        for i, col in enumerate(ws.columns, 1):
            width = max(len(str(v.value or "")) for v in list(col)[:300])
            ws.column_dimensions[get_column_letter(i)].width = min(max(10, width + 2), 60)
    ws = xw.book["Read me"]
    ws.column_dimensions["A"].width = 48
    ws.column_dimensions["B"].width = 120
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
        if row[0].value and row[0].value.isupper():
            row[0].font = Font(bold=True)
    ws = xw.book["Parcels"]
    ws.auto_filter.ref = ws.dimensions
    for name, text in [("Map link", "map"), ("Check for sale (Zillow)", "check listing"), ("County sales record", "sales record")]:
        link_col = list(cols.values()).index(name) + 1
        for r in range(2, ws.max_row + 1):
            cell = ws.cell(r, link_col)
            if cell.value:
                # HYPERLINK formulas instead of hyperlink objects: Google Sheets imports them reliably.
                cell.value = '=HYPERLINK("%s","%s")' % (cell.value.replace('"', "%22"), text)
                cell.font = Font(color="0563C1", underline="single")
    dcol = list(cols.values()).index("Last sale date") + 1
    for r in range(2, ws.max_row + 1):
        ws.cell(r, dcol).number_format = "yyyy-mm-dd"
    ws.column_dimensions[get_column_letter(dcol)].width = 12
    money = [list(cols.values()).index(k) + 1 for k in cols.values() if k.endswith("$") or "$ (" in k]
    for r in range(2, ws.max_row + 1):
        for m in money:
            ws.cell(r, m).number_format = "#,##0"
    xw.book["Summary by town"].auto_filter.ref = xw.book["Summary by town"].dimensions
    xw.book["Zoning districts"].auto_filter.ref = xw.book["Zoning districts"].dimensions
tbl.to_csv(f"{OUT}/DuPage_apartment_zoned_vacant_or_SF_parcels.csv", index=False, date_format="%Y-%m-%d")
print("wrote", xlsx, len(tbl), "rows")

# ---------------------------------------------------------------- map data
m = c[["PIN", "address", "MUNICIPALITY", "current_use", "zoning_cat", "zoning_raw", "acres",
       "REA017_FCV_TOTAL", "flag_text", "last_sale_date", "last_sale_price", "last_sale_doc_type", "listing_link", "geometry"]].copy()
m["last_sale_date"] = m.last_sale_date.dt.strftime("%Y-%m-%d")
m["last_sale_price"] = m.last_sale_price.astype("Int64").astype(str).replace("<NA>", "")
m["geometry"] = m.to_crs(3435).simplify(1.5).to_crs(4326)
m = m.rename(columns={"MUNICIPALITY": "town", "current_use": "use", "zoning_cat": "cat", "zoning_raw": "zone",
                      "REA017_FCV_TOTAL": "av", "flag_text": "flags",
                      "last_sale_date": "sd", "last_sale_price": "sp", "last_sale_doc_type": "st", "listing_link": "zl"})
m["use"] = m.use.map({"Vacant land": "V", "Single-family home": "S"})
m["town"] = m.town.replace({"Uninc": "Unincorporated"})
m["av"] = m.av.fillna(0).astype(int)
gj = json.loads(m.to_json(drop_id=True))


def rnd(o):
    if isinstance(o, float):
        return round(o, 6)
    if isinstance(o, list):
        return [rnd(x) for x in o]
    return o


for f in gj["features"]:
    f["geometry"]["coordinates"] = rnd(f["geometry"]["coordinates"])
    f["properties"] = {k: v for k, v in f["properties"].items() if v not in ("", None)}
with open(f"{WORK}/map_data.json", "w") as fh:
    json.dump(gj, fh, separators=(",", ":"))
not_cov = cov[cov["Zoning source"].isin(["none found"])][["Municipality", "Parcels in county layer"]]
with open(f"{WORK}/map_meta.json", "w") as fh:
    json.dump({"built": today, "not_covered": not_cov.values.tolist(),
               "covered": sorted(set(SOURCES) - {"Uninc"}) + ["Unincorporated DuPage"]}, fh)
print("map features", len(gj["features"]))
