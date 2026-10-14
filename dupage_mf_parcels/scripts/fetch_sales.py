"""Fetch recorded sales for each candidate PIN from the DuPage County Property Lookup portal.

Usage: python fetch_sales.py WORK_DIR
Reads WORK_DIR/_candidates.parquet, caches raw results in WORK_DIR/sales_cache.jsonl
(re-runs skip PINs already fetched), writes WORK_DIR/_sales.csv with the most recent sale.
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

URL = "https://propertylookup.dupagecounty.gov/Datalets/Datalet.aspx?UseSearch=no&pin={pin}&mode=sales"
WORK = Path(sys.argv[1])
CACHE = WORK / "sales_cache.jsonl"
_local = threading.local()


def session():
    # One session per thread: the portal serializes requests that share an ASP.NET session cookie.
    if not hasattr(_local, "s"):
        _local.s = requests.Session()
        _local.s.headers["User-Agent"] = "Mozilla/5.0 (parcel research)"
    return _local.s


def parse(page):
    """Return the rows of the 'Sales' table as dicts, newest first."""
    m = re.search(r"id=['\"]Sales['\"].*?</table>", page, flags=re.S | re.I)
    if not m:
        return []
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(0), flags=re.S | re.I):
        cells = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", c))).strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S | re.I)]
        if len(cells) >= 6 and re.match(r"\d{2}/\d{2}/\d{4}", cells[0]):
            rows.append(dict(date=cells[0], price=cells[1], doc_type=cells[2], doc_no=cells[3],
                             seller=cells[4], buyer=cells[5]))
    return rows


def get(pin):
    for i in range(4):
        try:
            r = session().get(URL.format(pin=pin), timeout=60)
            r.raise_for_status()
            if "PARCEL NUMBER" not in r.text:
                raise RuntimeError("no parcel header")
            time.sleep(0.25)
            return {"pin": pin, "sales": parse(r.text)}
        except Exception as e:
            err = str(e)
            time.sleep(2 ** i)
    return {"pin": pin, "error": err}


pins = pd.read_parquet(WORK / "_candidates.parquet", columns=["PIN"]).PIN.tolist()
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
out = []
for pin, d in recs.items():
    s = (d.get("sales") or [None])[0]
    out.append(dict(PIN=pin, last_sale_date=s and s["date"], last_sale_price=s and s["price"],
                    last_sale_doc_type=s and s["doc_type"], last_sale_seller=s and s["seller"],
                    last_sale_buyer=s and s["buyer"], n_sales_on_record=len(d.get("sales") or []),
                    sales_lookup_error=d.get("error")))
pd.DataFrame(out).to_csv(WORK / "_sales.csv", index=False)
print("wrote", len(out), file=sys.stderr)
