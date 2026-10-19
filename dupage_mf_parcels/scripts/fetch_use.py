"""Fetch the declared property use (PTAX-203 transfer declaration) for each candidate PIN.

The DuPage County Property Lookup portal's Conveyance page shows, for each recorded
transfer, the seller/buyer-declared "Current Primary Use" and "Intended Primary Use"
(Residence, Apartment building <=6 units with unit count, Apartment building >6 units,
Land/lot only, ...). That separates 2-6 flats and small apartment buildings, which the
assessor classes as residential "R", from detached houses.

Usage: python fetch_use.py WORK_DIR [PIN ...]
Caches raw results in WORK_DIR/use_cache.jsonl, writes WORK_DIR/_use.csv.
"""
import html
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

URL = "https://propertylookup.dupagecounty.gov/Datalets/Datalet.aspx?UseSearch=no&pin={pin}&mode=conveyance"
WORK = Path(sys.argv[1])
CACHE = WORK / "use_cache.jsonl"
_local = threading.local()


def session():
    # One session per thread: the portal serializes requests that share an ASP.NET session cookie.
    if not hasattr(_local, "s"):
        _local.s = requests.Session()
        _local.s.headers["User-Agent"] = "Mozilla/5.0 (parcel research)"
    return _local.s


def text(page):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", page, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def field(t, label, stop):
    m = re.search(re.escape(label) + r"\s*(.*?)\s*" + stop, t)
    return m.group(1).strip() if m else ""


def parse(page):
    t = text(page)
    if "Conveyance Details" not in t:
        return {}
    cur = re.search(r"Current Primary Use:\s*(.*?)\s*Specify/No of Units:\s*(.*?)\s*Intended Primary Use:", t)
    intd = re.search(r"Intended Primary Use:\s*(.*?)\s*Specify/No of Units:\s*(.*?)\s*Significant Change Date:", t)
    return dict(
        n_conveyances=int(field(t, "Conveyance Details 1 of", r"\s") or 0) if re.search(r"Conveyance Details 1 of \d+", t) else 1,
        current_use=cur.group(1) if cur else "", current_units=cur.group(2) if cur else "",
        intended_use=intd.group(1) if intd else "", intended_units=intd.group(2) if intd else "",
        building_type=field(t, "Building Type:", "Building Removal Date:"),
        recorded=field(t, "Recorded Date:", "Asmt to Sale Ratio:"),
    )


def get(pin):
    err = ""
    for i in range(4):
        try:
            r = session().get(URL.format(pin=pin), timeout=60)
            r.raise_for_status()
            if "PARCEL NUMBER" not in r.text:
                raise RuntimeError("no parcel header")
            time.sleep(0.25)
            return {"pin": pin, **parse(r.text)}
        except Exception as e:
            err = str(e)
            time.sleep(2 ** i)
    return {"pin": pin, "error": err}


if __name__ == "__main__":
    pins = sys.argv[2:] or pd.read_parquet(WORK / "_candidates.parquet", columns=["PIN"]).PIN.tolist()
    if len(sys.argv) > 2:
        for p in pins:
            print(get(p))
        sys.exit()
    done = set()
    if CACHE.exists():
        done = {json.loads(l)["pin"] for l in CACHE.open() if '"error"' not in l}
    todo = [p for p in pins if p not in done]
    print(f"{len(todo)} to fetch, {len(done)} cached", file=sys.stderr)
    with CACHE.open("a") as fh, ThreadPoolExecutor(4) as ex:
        for i, res in enumerate(ex.map(get, todo), 1):
            fh.write(json.dumps(res) + "\n")
            if i % 50 == 0:
                fh.flush()
                print(i, file=sys.stderr)
    recs = {}
    for line in CACHE.open():
        d = json.loads(line)
        if "error" in d and d["pin"] in recs:
            continue
        recs[d["pin"]] = d
    pd.DataFrame(list(recs.values())).to_csv(WORK / "_use.csv", index=False)
    print("wrote", len(recs), file=sys.stderr)
