"""Flag candidate parcels that are really multi-unit or non-residential sites.

Signals (any one flags the parcel):
  * declared use on the most recent PTAX-203 transfer declaration (fetch_use.py):
    apartment building, office, retail, commercial, industrial or other
  * subdivision name in the legal description says townhouse/townhome/condo/duplex/two-flat
  * county address points: 2+ house numbers within 6 of each other on the same street
    (side-by-side duplex), or 3+ points at one address (multi-unit building)

Usage: python flag_multiunit.py WORK_DIR ADDRESSPOINTS_PARQUET
Writes WORK_DIR/_multiunit_flags.csv (PIN, reason).
"""
import sys

import geopandas as gpd
import pandas as pd

WORK, AP = sys.argv[1], sys.argv[2]
c = gpd.read_parquet(f"{WORK}/_candidates.parquet")
reasons = {}


def add(pins, why):
    for p in pins:
        reasons.setdefault(p, []).append(why)


# 1. Declared use at last transfer.
use = pd.read_csv(f"{WORK}/_use.csv", dtype=str)
USE = {"D": "apartment building (6 units or less)", "E": "apartment building (over 6 units)", "F": "office",
       "G": "retail", "H": "commercial building", "I": "industrial building", "K": "other non-residential"}
for _, r in use[use.current_use.fillna("").str.match(r"[DEFGHIK] ")].iterrows():
    units = f", {r.current_units} units" if isinstance(r.current_units, str) and r.current_units.strip() else ""
    add([r.pin], f"declared use at last sale: {USE[r.current_use[0]]}{units}")

# 2. Subdivision name.
leg = (c.LEGALDES1.fillna("") + " " + c.LEGALDES2.fillna("")).str.upper()
sub = leg.str.extract(r"(TOWN ?HOUSE|TOWNSHOUSE|TOWN ?HOME|TWNHM|TWNHS|CONDO|DUPLEX|TWO ?FLAT|2 ?FLAT)")[0]
add(c.PIN[sub.notna()], "subdivision name indicates attached/multi-unit housing")

# 3. Address points inside the parcel.
a = gpd.read_parquet(AP)
j = gpd.sjoin(a[["STREET_NUM", "STREET_NAME", "PROPADDRL1", "geometry"]], c[["PIN", "geometry"]], predicate="within")
j["num"] = pd.to_numeric(j.STREET_NUM.str.extract(r"(\d+)")[0], errors="coerce")
for pin, g in j.groupby("PIN"):
    for _, s in g.groupby("STREET_NAME"):
        nums = sorted(s.num.dropna().unique())
        if len(nums) >= 2 and min(b - a for a, b in zip(nums, nums[1:])) <= 6:
            add([pin], "two adjoining street addresses on one lot (likely duplex)")
            break
    if g.groupby("PROPADDRL1").size().max() >= 3:
        add([pin], "3+ address points at one address (likely multi-unit)")

out = pd.DataFrame([(p, "; ".join(dict.fromkeys(r))) for p, r in reasons.items()], columns=["PIN", "multiunit_reason"])
out.to_csv(f"{WORK}/_multiunit_flags.csv", index=False)
m = c[["PIN", "current_use"]].merge(out, on="PIN")
print(len(out), "flagged")
print(m.groupby("current_use").size())
