"""Build the data the prototype visualization reads, src/lib/flu-onset/data.json.

    python3 scripts/build_viz_data.py

Baseline: CDC's published national ILINet baseline for each season (see CDC_BASELINE below).
Seasons before 2007-08, whose CDC reports are no longer online, fall back to an estimate in the
same spirit: mean plus two standard deviations of wILI in the low weeks of the three seasons
before it, leaving out 2008-09 and 2009-10 because of the 2009 pandemic.
Onset: the first of three weeks in a row at or above the baseline, with wILI rounded to one
decimal, the rule CDC's FluSight forecasting challenge used.
"""
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
nat = pd.read_csv(ROOT / "data/raw/ilinet_wili_nation.csv", parse_dates=["reference_time"])
nat = nat[["reference_time", "value"]].rename(columns={"reference_time": "week_end", "value": "wili"})
nat = nat.sort_values("week_end").reset_index(drop=True)
nat["season"] = nat["week_end"].map(lambda d: d.year if d.month >= 10 else d.year - 1)
first = nat.groupby("season")["week_end"].transform("min")
nat["w"] = (nat["week_end"] - first).dt.days // 7  # 0-based week of season

NW = 53

# CDC national baselines, % of visits.
# 2007-08 to 2019-20: data/raw/flusight_wili_baseline.csv, from github.com/cdcepi/FluSight-forecasts
# 2020-21: 2.6, CDC figure as cited in Delaware's weekly influenza report, 2022 week 1 (secondary source)
# 2021-22: 2.5, MMWR 71(29), "Influenza Activity ... 2021-22 Season"
# 2022-23: 2.5, CDC 2022-23 season technical report
# 2023-24: 2.9, FluView week 5 of 2024
# 2024-25: 3.0, CDC 2024-25 season summary
# 2025-26: 3.1, CDC FluView methods page
# 2026-27: 2.9, FluView week 42 of 2026
fs = pd.read_csv(ROOT / "data/raw/flusight_wili_baseline.csv", index_col=0)
CDC_BASELINE = {int(c[:4]): float(fs.loc["National", c].iloc[0] if hasattr(fs.loc["National", c], "iloc") else fs.loc["National", c]) for c in fs.columns}
CDC_BASELINE.update({2020: 2.6, 2021: 2.5, 2022: 2.5, 2023: 2.9, 2024: 3.0, 2025: 3.1, 2026: 2.9})
PANDEMIC = {2008, 2009}


def thanksgiving_week(season, start):
    nov1 = date(season, 11, 1)
    thu = nov1 + timedelta(days=(3 - nov1.weekday()) % 7 + 21)
    sat = thu + timedelta(days=2)
    return (sat - start).days // 7


def low_weeks(g):
    g = g.sort_values("w")
    return pd.concat([g.head(4), g.tail(3)])["wili"]


seasons = sorted(nat["season"].unique())
out = []
for s in seasons:
    g = nat[nat["season"] == s].sort_values("w")
    # The 2009 pandemic ran from spring 2009 into the 2009-10 season, so neither counts as low weeks.
    pool = [p for p in seasons if p < s and p not in PANDEMIC]
    prior = pool[-3:] if pool else [p for p in seasons if p not in PANDEMIC][1:4]
    lows = pd.concat([low_weeks(nat[nat["season"] == p]) for p in prior])
    est = float(lows.mean() + 2 * lows.std())
    base = CDC_BASELINE.get(int(s), round(est, 1))
    vals = [None] * NW
    for w, v in zip(g["w"], g["wili"]):
        if w < NW:
            vals[int(w)] = round(float(v), 3)
    above = [v is not None and round(v, 1) >= base for v in vals]
    onset = next((i for i in range(NW - 2) if all(above[i:i + 3])), None)
    # The season still running cannot have three weeks yet if it crossed recently. Its start is the
    # first week of the run it is in now, marked provisional until a third week confirms it.
    last = max(i for i, v in enumerate(vals) if v is not None)
    provisional = False
    if onset is None and int(s) == seasons[-1] and above[last]:
        onset = last
        while onset > 0 and above[onset - 1]:
            onset -= 1
        provisional = True
    known = [v for v in vals if v is not None]
    peak_w = int(np.nanargmax([v if v is not None else np.nan for v in vals]))
    start = g["week_end"].iloc[0].date()
    out.append({
        "season": int(s),
        "label": f"{s}–{str(s + 1)[-2:]}",
        "start": start.isoformat(),
        "weeks": vals,
        "baseline": round(base, 2),
        "baselineSource": "cdc" if int(s) in CDC_BASELINE else "estimate",
        "onset": onset,
        "provisional": provisional,
        "peakWeek": peak_w,
        "peak": max(known),
        "above": int(sum(above)),
        "thanksgiving": thanksgiving_week(int(s), start),
        "partial": len(known) < 52,
    })

cur = out[-1]
meta = {"latest": nat["week_end"].max().date().isoformat(), "currentWeek": max(i for i, v in enumerate(cur["weeks"]) if v is not None)}
(ROOT / "src/lib/flu-onset/data.json").write_text(json.dumps({"meta": meta, "seasons": out}, ensure_ascii=False))
for d in out:
    print(d["label"], "base", d["baseline"], "onset", d["onset"], "peakW", d["peakWeek"], "peak", round(d["peak"], 2), "above", d["above"], "tg", d["thanksgiving"])
print(meta)
