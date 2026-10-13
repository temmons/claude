"""Find DuPage parcels zoned for apartments whose current use is vacant land or a single-family home.

Inputs (from fetch_all.py): <data>/parcels.parquet (or parcels.geojson) and <data>/zoning_<Town>.geojson
Outputs: <out>/dupage_mf_candidates.geojson, <out>/_candidates.parquet, <out>/_coverage.csv
"""
import re
import sys

import geopandas as gpd
import pandas as pd

from sources import NO_GIS_ZONING, SOURCES
from zoning_classes import LABELS, classify

DATA, OUT = sys.argv[1], sys.argv[2]
FT = 3435  # NAD83 / Illinois East (ftUS)

# ---------------------------------------------------------------- parcels
try:
    parcels = gpd.read_parquet(f"{DATA}/parcels.parquet")
except Exception:
    parcels = gpd.read_file(f"{DATA}/parcels.geojson").drop(columns=["SHAPE"], errors="ignore")
parcels = parcels[parcels.geometry.notna() & ~parcels.geometry.is_empty].copy()
pf = parcels.to_crs(FT)
parcels["lot_sqft"] = pf.area.round(0)
parcels["pt"] = pf.representative_point()
# Condo units are mapped as stacked copies of one polygon: count PINs sharing a centroid.
cen = pf.centroid
parcels["n_stacked_pins"] = parcels.groupby([cen.x.round(0), cen.y.round(0)]).PIN.transform("count")

# ---------------------------------------------------------------- zoning join
rows = []
for town, src in SOURCES.items():
    z = gpd.read_file(f"{DATA}/zoning_{town.replace(' ', '_')}.geojson")
    sub = parcels[parcels.MUNICIPALITY == town]
    if src.get("join") == "pin":
        z["PINN"] = z["PIN"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(10)
        z = z[z[src["field"]].notna()].drop_duplicates("PINN")
        j = sub[["PIN"]].merge(z[["PINN", src["field"]]], left_on="PIN", right_on="PINN", how="left")
        j.index = sub.index
        raw = j[src["field"]]
    else:
        z = z[z.geometry.notna()].to_crs(FT)
        z = z[z[src["field"]].notna() & (z[src["field"]].astype(str).str.strip().isin(["", "0", "None", "N/A", "NONE"]) == False)]
        pts = gpd.GeoDataFrame(index=sub.index, geometry=sub["pt"], crs=FT)
        j = gpd.sjoin(pts, z[[src["field"], "geometry"]], how="left", predicate="within")
        j = j[~j.index.duplicated(keep="first")]
        raw = j[src["field"]]
    out = pd.DataFrame({"zoning_raw": raw.astype("string").str.strip()}, index=sub.index)
    out["zoning_source"] = src["url"]
    rows.append(out)
zj = pd.concat(rows)
parcels = parcels.join(zj)
cls = [classify(t, r) if pd.notna(r) else ("", None, None, None)
       for t, r in zip(parcels.MUNICIPALITY, parcels.zoning_raw)]
parcels[["zoning_code", "zoning_cat", "zoning_basis", "zoning_note"]] = pd.DataFrame(cls, index=parcels.index)

# ---------------------------------------------------------------- current use
pc = parcels.REA017_PROP_CLASS
imp = parcels.REA017_FCV_IMP.fillna(0)
land = parcels.REA017_FCV_LAND.fillna(0)
addr = parcels.PROPADDRL1.fillna("").astype(str)
owner = parcels.BILLNAME.fillna("").astype(str)
common_owner = owner.str.contains(r"\b(ASSN|ASSOC|ASSOCIATION|HOMEOWNER|HOMEOWNERS|HMEOWNRS|HOA|COMMON|CONDO|TOWNHOME|ROWHOME|OWNERS)\b", regex=True)
public_owner = owner.str.contains(r"\b(VILLAGE OF|CITY OF|COUNTY|STATE OF|PARK DIST|FOREST PRESERVE|SCHOOL|SCH DIST|DIST NO|SANITARY|RAILROAD|RAILWAY|METRA|TOLLWAY|IL DEPT|ILLINOIS DEPT|UNITED STATES|TOWNSHIP|LIBRARY|FIRE PROT|COMMONWEALTH EDISON|COMED|NICOR|NORTHERN ILLINOIS GAS|PIPE ?LINE|AMERITECH|ILLINOIS BELL|WATER COMMISSION)\b", regex=True)
condo_like = (parcels.n_stacked_pins > 1) | addr.str.contains(r"#|\bUNIT\b|\bAPT\b", regex=True)

# M/A/N/L are multi-unit residential classes: a land-only PIN there is usually part of an existing complex.
taxable_classes = {"R", "C", "I", "F", "K"}
vacant = (imp == 0) & (land >= 1000) & pc.isin(taxable_classes) & ~common_owner & ~public_owner & (parcels.lot_sqft >= 2500)
single_family = (pc == "R") & (imp > 0) & ~condo_like & (parcels.lot_sqft >= 3000)

parcels["current_use"] = None
parcels.loc[vacant, "current_use"] = "Vacant land"
parcels.loc[single_family, "current_use"] = "Single-family home"
cand = parcels[parcels.zoning_cat.notna() & parcels.current_use.notna()].copy()

# Building footprints (FEMA/ORNL USA Structures) separate detached houses from
# townhouse/duplex units, which the assessor also classes as residential "R".
# A footprint shared by 3+ parcels, or split at least 30/70 between 2 parcels,
# is an attached building; small slivers come from imagery/parcel misalignment.
# Splits between 10% and 25% are ambiguous and are kept but flagged for review.
bld = gpd.read_parquet(f"{DATA}/structures.parquet").to_crs(FT)
bld = bld[bld.SQFEET >= 400]
cf = cand.to_crs(FT)
bsel = gpd.sjoin(bld, cf[["geometry"]], predicate="intersects").index.unique()
bs = bld.loc[bsel].reset_index(names="bid")
pu = parcels[["PIN", "geometry"]].to_crs(FT)
pu = pu[parcels.n_stacked_pins == 1]
psel = gpd.sjoin(pu, bs[["geometry"]], predicate="intersects").index.unique()
ov = gpd.overlay(bs[["bid", "PRIM_OCC", "geometry"]], pu.loc[psel], how="intersection", keep_geom_type=True)
ov["a"] = ov.area
ov["share"] = ov.a / ov.groupby("bid").a.transform("sum")
sig = ov[ov.share >= 0.08]
g = sig.groupby("bid").agg(n=("PIN", "nunique"), mins=("share", "min"))
attached_bids = g[(g.n >= 3) | ((g.n == 2) & (g.mins >= 0.25))].index
attached_pins = set(sig[sig.bid.isin(attached_bids)].PIN)
maybe_bids = g[(g.n == 2) & (g.mins >= 0.10) & (g.mins < 0.25)].index
maybe_pins = set(sig[sig.bid.isin(maybe_bids)].PIN) - attached_pins
main = ov[ov.share >= 0.5]  # the parcel holding most of a building
mf_bldg_pins = set(main[main.PRIM_OCC == "Multi - Family Dwelling"].PIN)
bldg_pins = set(main.PIN)
bldg_sqft = (ov[ov.share >= 0.5].groupby("PIN").a.sum()).round(0)

is_sf = cand.current_use == "Single-family home"
cand["building_footprint_sqft"] = cand.PIN.map(bldg_sqft)
cand["structure_type_note"] = ""
cand.loc[is_sf & cand.PIN.isin(attached_pins), "structure_type_note"] = "attached (townhouse/duplex)"
cand.loc[is_sf & cand.PIN.isin(mf_bldg_pins), "structure_type_note"] = "building tagged multi-family"
cand.loc[(cand.current_use == "Vacant land") & cand.PIN.isin(bldg_pins), "structure_type_note"] = "building footprint present"
drop = is_sf & (cand.structure_type_note != "")
cand.loc[is_sf & ~drop & cand.PIN.isin(maybe_pins), "structure_type_note"] = "review: house footprint crosses a lot line (possible duplex)"
dropped = cand[drop]
dropped.drop(columns=["pt"]).to_crs(4326).to_parquet(f"{OUT}/_excluded_attached.parquet")
cand = cand[~drop]
print(f"excluded {len(dropped)} attached/multi-unit residential parcels", file=sys.stderr)

# Vacant lot owned by the owner of an adjoining improved parcel (likely a side yard).
vac = cand[cand.current_use == "Vacant land"]
improved = parcels[(imp > 0)][["BILLNAME", "geometry"]].to_crs(FT)
vg = vac[["BILLNAME", "geometry"]].to_crs(FT)
vg["geometry"] = vg.buffer(3)
t = gpd.sjoin(vg, improved, how="inner", predicate="intersects")
side = t[t.BILLNAME_left.str.strip() == t.BILLNAME_right.str.strip()].index.unique()
cand["vacant_side_lot_flag"] = cand.index.isin(side)

# ---------------------------------------------------------------- output
cand["zoning_category"] = cand.zoning_cat.map(LABELS)
cand["acres"] = (cand.lot_sqft / 43560).round(3)
cand["market_value_est"] = (cand.REA017_FCV_TOTAL.fillna(0) * 3).round(0)  # DuPage assesses at 1/3 of market value
pt = cand.pt.to_crs(4326)
cand["lat"], cand["lon"] = pt.y.round(6), pt.x.round(6)
cand = cand.drop(columns=["pt"]).set_geometry("geometry")
cand = cand.sort_values(["MUNICIPALITY", "zoning_cat", "current_use", "lot_sqft"], ascending=[True, True, True, False])
cand.to_file(f"{OUT}/dupage_mf_candidates.geojson", driver="GeoJSON")
cand.to_parquet(f"{OUT}/_candidates.parquet")

# Coverage summary for every municipality in the parcel layer.
cov = parcels.groupby(parcels.MUNICIPALITY.fillna("(none)")).agg(
    parcels=("PIN", "size"),
    zoning_matched=("zoning_raw", lambda s: int(s.notna().sum())),
    zoned_for_apartments=("zoning_cat", lambda s: int(s.notna().sum())),
)
cov["zoning_source"] = [SOURCES[m]["url"] if m in SOURCES else ("none found" if m in NO_GIS_ZONING else "") for m in cov.index]
cov.to_csv(f"{OUT}/_coverage.csv")
print(cand.groupby(["MUNICIPALITY", "current_use"]).size().unstack(fill_value=0).to_string())
print("TOTAL", len(cand))
print(cov.to_string())
