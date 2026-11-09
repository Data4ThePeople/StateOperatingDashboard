"""Build dist/oh10/index.html from scripts/oh10_template.html and data/processed/oh10/{data,geo}.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "data/processed/oh10/data.json").read_text())
geo = json.loads((ROOT / "data/processed/oh10/geo.json").read_text())
geo.pop("split", None)
html = (ROOT / "scripts/oh10_template.html").read_text()
assert html.count("__DATA__") == 1 and html.count("__GEO__") == 1
html = html.replace("__DATA__", json.dumps(data, separators=(",", ":"))).replace("__GEO__", json.dumps(geo, separators=(",", ":")))
out = ROOT / "dist/oh10/index.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html)
print(f"wrote dist/oh10/index.html ({len(html)//1024} KB), {len(data['metrics'])} measures, {sum(v['in_district'] for v in geo['tracts'].values())} tracts")
