"""Download the raw data the notebook uses into data/raw.

    python3 scripts/download_data.py

- CDC ILINet, population-weighted percentage of outpatient visits for influenza-like
  illness (wILI), national and by HHS region, from 1997, through the Delphi Epidata V5 API
- CDC ILINet, unweighted ILI percentage by state, from 2010

Delphi's legacy /epidata/fluview/ endpoint stopped at September 22, 2026. The V5
snapshot endpoint returns the latest release of every week.
"""
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
V5 = "https://delphi.cmu.edu/epidata/v5/snapshot/?source=fluview_ilinet&signal={signal}&geo_type={geo}&limit=-1"
PULLS = [
    ("wili", "nation", "ilinet_wili_nation.csv"),
    ("wili", "hhs", "ilinet_wili_hhs.csv"),
    ("ili", "state", "ilinet_ili_state.csv"),
]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "flu-season-onset"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    log = {"downloaded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "files": {}}
    for signal, geo, name in PULLS:
        url = V5.format(signal=signal, geo=geo)
        body = get(url)
        (RAW / name).write_bytes(body)
        log["files"][name] = url
        print(f"{signal} {geo}: data/raw/{name} ({body.count(b'\n') - 1} rows)")
    (RAW / "download.json").write_text(json.dumps(log, indent=2))


if __name__ == "__main__":
    main()
