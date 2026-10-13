"""Inline map data into map_template.html -> standalone HTML map."""
import sys
from pathlib import Path

WORK, OUT = Path(sys.argv[1]), Path(sys.argv[2])
here = Path(__file__).parent
html = (here / "map_template.html").read_text()
for key, fn in [("__PARCELS__", "map_data.json"), ("__MUNI__", "muni.json"), ("__ROADS__", "roads.json"), ("__META__", "map_meta.json")]:
    html = html.replace(key, (WORK / fn).read_text().replace("</", "<\\/"))
html = html.replace("/*__LEAFLET_CSS__*/", (WORK / "leaflet.css").read_text())
OUT.write_text(html)
print(OUT, round(OUT.stat().st_size / 1e6, 2), "MB")
