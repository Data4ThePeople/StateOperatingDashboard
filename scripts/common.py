"""Shared paths and HTTP helpers. Every script imports from here; paths resolve from this file."""
import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/.claude/d4tp-process"))
try:
    from d4tp_env import get_key, load_env  # noqa: E402
except ImportError:  # outside Data 4 The People's machines, keys come from the environment
    def load_env(*args, **kwargs):
        pass

    def get_key(name):
        if not os.environ.get(name):
            sys.exit(f"Set {name} in the environment.")
        return os.environ[name]

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
DIST = ROOT / "dist"

STATE = "39"          # Ohio

load_env()


def user_agent():
    """Browser-like User-Agent with a contact address. The address lives in the central .env
    (D4TP_CONTACT_EMAIL), not in this repo."""
    return f"Mozilla/5.0 (Macintosh) Data4ThePeople research {get_key('D4TP_CONTACT_EMAIL')}"


def get(url, tries=4, timeout=120, data=None, headers=None):
    h = {"User-Agent": user_agent()}
    h.update(headers or {})
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=timeout).read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def cached(path, url, **kw):
    """Fetch once into data/raw; later runs read the saved file."""
    path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(get(url, **kw))
        (path.parent / "pulled.txt").write_text(dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC") + "\n")
    return path.read_bytes()


def bls_series(ids, start, end, folder):
    """BLS API v2. Twenty years per request, so long spans go in pieces. Returns
    {series_id: [(year, period, value, footnote_codes)]} sorted by date. A dash value stays a dash."""
    out = {i: [] for i in ids}
    y = start
    while y <= end:
        y2 = min(y + 19, end)
        path = RAW / folder / f"{'_'.join(ids)[:80]}_{y}_{y2}.json"
        if not path.exists():
            body = json.dumps({"seriesid": ids, "startyear": str(y), "endyear": str(y2),
                               "registrationkey": get_key("BLS_API_KEY")}).encode()
            path.parent.mkdir(parents=True, exist_ok=True)
            raw = get("https://api.bls.gov/publicAPI/v2/timeseries/data/", data=body,
                      headers={"Content-Type": "application/json"})
            res = json.loads(raw)
            if res.get("status") != "REQUEST_SUCCEEDED":
                raise SystemExit(f"BLS request failed: {res.get('message')}")
            path.write_bytes(raw)
            (path.parent / "pulled.txt").write_text(dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC") + "\n")
        res = json.loads(path.read_bytes())
        for s in res["Results"]["series"]:
            for o in s["data"]:
                codes = "".join(f.get("code", "") for f in o.get("footnotes", []) if f)
                out[s["seriesID"]].append((int(o["year"]), o["period"], o["value"], codes))
        y = y2 + 1
    for i in out:
        out[i].sort()
        keys = [(a, b) for a, b, _, _ in out[i]]
        if len(keys) != len(set(keys)):
            raise SystemExit(f"duplicate keys in {i}")
    return out


def write_csv(name, header, rows):
    PROC.mkdir(parents=True, exist_ok=True)
    with open(PROC / name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote data/processed/{name}: {len(rows)} rows")


def read_csv(name):
    with open(PROC / name, newline="") as f:
        return list(csv.DictReader(f))


def write_json(name, obj):
    """Write a processed layer. Keys are 5-digit county FIPS strings ("39001")."""
    (PROC / name).parent.mkdir(parents=True, exist_ok=True)
    (PROC / name).write_text(json.dumps(obj, separators=(",", ":")))
    print(f"wrote data/processed/{name}")


def census(url_path, params, cache_name):
    """Census Data API, cached. url_path like '2024/acs/acs5'. Returns list of dicts."""
    import urllib.parse
    q = dict(params)
    q["key"] = get_key("CENSUS_API_KEY")
    url = f"https://api.census.gov/data/{url_path}?" + urllib.parse.urlencode(q, safe=":,*")
    path = RAW / "census" / cache_name
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(get(url))
    rows = json.loads(path.read_bytes())
    return [dict(zip(rows[0], r)) for r in rows[1:]]
