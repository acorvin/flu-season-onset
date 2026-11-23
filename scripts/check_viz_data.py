"""Check data.json against the raw ILINet file and against figures CDC has published.

    python3 scripts/check_viz_data.py

Exits with an error if any check fails.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
d = json.loads((ROOT / "src/lib/flu-onset/data.json").read_text())
S = {s["season"]: s for s in d["seasons"]}
raw = pd.read_csv(ROOT / "data/raw/ilinet_wili_nation.csv", parse_dates=["reference_time"]).set_index("reference_time")["value"]
fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


def week(s, w):
    return pd.Timestamp(s["start"]) + pd.Timedelta(weeks=w)


# 1. Every weekly value in the picture is the raw value for that date.
bad = [(s["label"], w) for s in S.values() for w, v in enumerate(s["weeks"]) if v is not None and abs(raw[week(s, w)] - v) > 0.001]
check("every weekly value matches the raw CDC file", not bad)

# 2. Seasons start on the Saturday ending MMWR week 40.
check("every season starts in the first week of October", all(pd.Timestamp(s["start"]).month == 10 and pd.Timestamp(s["start"]).day <= 10 for s in S.values()))

# 3. Onset: first of three weeks at or above the baseline, recomputed here independently.
def onset(s):
    up = [v is not None and round(v, 1) >= s["baseline"] for v in s["weeks"]]
    return next((i for i in range(len(up) - 2) if all(up[i:i + 3])), None)
check("onsets match the three-week rule", all(onset(s) == s["onset"] for s in S.values() if not s["provisional"]))

# 4. Against CDC's own statements.
cdc = [
    ("2009-10 peak 7.7% in the week ending Oct 24, 2009", lambda: round(S[2009]["peak"], 1) == 7.7 and week(S[2009], S[2009]["peakWeek"]).date().isoformat() == "2009-10-24"),
    ("2017-18 peak 7.5% in the week ending Feb 3, 2018", lambda: round(S[2017]["peak"], 1) == 7.5 and week(S[2017], S[2017]["peakWeek"]).date().isoformat() == "2018-02-03"),
    ("2021-22 peak in the week ending Jan 1, 2022 (CDC: 4.8%)", lambda: week(S[2021], S[2021]["peakWeek"]).date().isoformat() == "2022-01-01" and abs(S[2021]["peak"] - 4.8) < 0.15),
    ("2022-23 above the 2.5% baseline for 21 weeks", lambda: S[2022]["above"] == 21),
    ("2023-24 above the 2.9% baseline from week 44 (ending Nov 4, 2023)", lambda: week(S[2023], S[2023]["onset"]).date().isoformat() == "2023-11-04"),
    ("2024-25 peak 7.9% (CDC season summary)", lambda: round(S[2024]["peak"], 1) in (7.8, 7.9)),
    ("2011-12 never had three weeks above its baseline", lambda: S[2011]["onset"] is None),
    ("2020-21 never rose above its baseline", lambda: S[2020]["onset"] is None and S[2020]["above"] == 0),
]
for name, f in cdc:
    check("CDC: " + name, f())

# 5. The findings stated on the single-particle page.
cur = S[max(S)]
past = [s for k, s in S.items() if 2007 <= k < cur["season"]]
earlier = sorted(s["label"] for s in past if s["onset"] is not None and s["onset"] < cur["onset"])
same = [s["label"] for s in past if s["onset"] == cur["onset"]]
n = d["meta"]["currentWeek"]
rank = sorted([s for k, s in S.items() if k >= 2007], key=lambda s: -(s["weeks"][n] or -1)).index(cur) + 1
print(f"     this season crossed {week(cur, cur['onset']).date()} (provisional: {cur['provisional']}), "
      f"{len(earlier)} of {len(past)} began earlier {earlier}, same week {same}, rank {rank} at week {n + 1} ({cur['weeks'][n]:.2f}%)")
check("this season crossed in the week ending Nov 7, 2026", week(cur, cur["onset"]).date().isoformat() == "2026-11-07")
check("this season's last two weeks are above 2.9%", all(round(v, 1) >= 2.9 for v in cur["weeks"][5:7]))

raise SystemExit(f"{len(fails)} checks failed" if fails else 0)
