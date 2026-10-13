"""Download every feature from an ArcGIS REST layer to GeoJSON (EPSG:4326)."""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0 (parcel research)"


def _req(url, params, tries=5):
    for i in range(tries):
        try:
            r = S.post(url, data=params, timeout=180)
            r.raise_for_status()
            d = r.json()
            if "error" in d:
                raise RuntimeError(d["error"])
            return d
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 ** i)


def fetch_layer(layer_url, out_path, where="1=1", out_fields="*", chunk=500, workers=6):
    meta = _req(layer_url, {"f": "json"})
    oid = next((f["name"] for f in meta.get("fields", []) if f["type"] == "esriFieldTypeOID"), None)
    ids = _req(layer_url + "/query", {"where": where, "returnIdsOnly": "true", "f": "json"})
    ids = sorted(ids.get("objectIds") or [])
    oid = ids and (meta.get("objectIdField") or oid or "OBJECTID")
    chunks = [ids[i:i + chunk] for i in range(0, len(ids), chunk)]

    def get(c):
        return _req(layer_url + "/query", {
            "objectIds": ",".join(map(str, c)), "outFields": out_fields,
            "outSR": 4326, "returnGeometry": "true", "geometryPrecision": 7, "f": "geojson"})["features"]

    feats = []
    with ThreadPoolExecutor(workers) as ex:
        for i, fs in enumerate(ex.map(get, chunks)):
            feats.extend(fs)
    with open(out_path, "w") as f:
        json.dump({"type": "FeatureCollection", "features": feats}, f)
    print(f"{layer_url} -> {out_path}: {len(feats)}/{len(ids)} features", file=sys.stderr)
    return len(feats)


if __name__ == "__main__":
    fetch_layer(sys.argv[1], sys.argv[2], *(sys.argv[3:4] or []))
