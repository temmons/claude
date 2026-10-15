"""Match web-found listing addresses (data/listings_found.csv) to candidate parcels by house number + street."""
import re
import sys

import pandas as pd

SUF = r"\b(ST|STREET|AVE|AVENUE|RD|ROAD|DR|DRIVE|LN|LANE|CT|COURT|PL|PLACE|BLVD|PKWY|CIR|WAY|TER|TRL|HWY|RTE|ROUTE|ILLINOIS)\b"


def key(addr):
    a = re.sub(r"[^A-Z0-9 ]", " ", str(addr).upper().replace("SAINT ", "ST "))
    m = re.match(r"\s*([0-9]+[NSEW]?[0-9]*)\s+(.*)", a)
    if not m:
        return None
    d = re.match(r"\s*([NSEW])\b", m.group(2))
    street = re.sub(r"\b[NSEW]\b", " ", m.group(2))
    street = re.sub(SUF, " ", street)
    words = street.split()
    return f"{m.group(1)} {words[0]}|{d.group(1) if d else ''}" if words else None


def match(cands, listings_csv):
    L = pd.read_csv(listings_csv)
    L["k"] = L.address.map(key)
    c = cands.assign(k=cands.PROPADDRL1.map(key), city=cands.PROPADDRL2.fillna("").str.upper())
    hits = []
    for _, r in L.dropna(subset=["k"]).iterrows():
        base, d = r.k.split("|")
        ck = c.k.fillna("|")
        same = (ck.str.split("|").str[0] == base) & ((d == "") | ck.str.endswith("|") | ck.str.endswith("|" + d))
        m = c[same & c.city.str.contains(r.town.upper().split()[0])]
        for pin in m.PIN:
            hits.append(dict(PIN=pin, listing_url=r.source_url, listing_price=r.price, listing_status=r.get("status", "listed"), listing_note=r.note))
        L.loc[_, "matched_PINs"] = ", ".join(m.PIN) if len(m) else ""
    L["matched_PINs"] = L.matched_PINs.fillna("")
    return pd.DataFrame(hits).drop_duplicates("PIN"), L.drop(columns="k")


if __name__ == "__main__":
    import geopandas as gpd
    cands = gpd.read_parquet(sys.argv[1])
    h, L = match(cands, sys.argv[2])
    print(len(h), "candidate parcels matched")
    print(L[L.matched_PINs != ""][["address", "town", "matched_PINs"]].to_string())
