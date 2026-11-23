# How Early Is Flu in the US This Year?

Every US flu season since 2007–08 inside one flu virus particle. Each season is a ring, the oldest at the center and this season on the outside, and each week is a point on its ring. When doctor visits for flu-like illness rise above CDC's baseline for that season, the week becomes a spike, so each flu season swells out of its ring.

**[See the page](https://acorvin.github.io/flu-season-onset/)**

## What it found

As of CDC's report for the week ending November 14, 2026:

- **This season crossed CDC's national baseline of 2.9% in the week ending November 7, 2026,** and stayed above it the next week. A season counts as begun after three weeks in a row above the baseline, so this start is provisional until the week ending November 21 is reported.
- **Only 3 of the 19 seasons since 2007–08 began earlier:** 2009–10, the H1N1 pandemic, then 2022–23 and 2023–24. 2019–20 began the same week.
- **By the week ending November 14, 3.8% of outpatient visits were for flu-like illness,** the third highest level at that point of any season since 2007–08, behind 2022–23 (5.7%) and 2009–10 (5.2%).
- 2011–12 never had three weeks above its baseline, and 2020–21 never rose above it at all.

## Data

| Layer | Source | Notes |
|---|---|---|
| National, 1997–2026 | CDC ILINet through the Delphi Epidata V5 API | Population-weighted percentage of outpatient visits for influenza-like illness (wILI), weekly |
| HHS regions, 1997–2026 | CDC ILINet through the Delphi Epidata V5 API | Downloaded for the regional analysis still to come |
| States, 2010–2026 | CDC ILINet through the Delphi Epidata V5 API | Unweighted ILI percentage, downloaded for the state analysis still to come |
| National baselines, 2007–08 to 2019–20 | [CDC FluSight forecasts](https://github.com/cdcepi/FluSight-forecasts), `wILI_Baseline.csv` | `data/raw/flusight_wili_baseline.csv` |
| National baselines, 2020–21 to 2026–27 | CDC FluView reports, season summaries and MMWR | Listed with their sources in `scripts/build_viz_data.py` |

`scripts/download_data.py` downloads the ILINet files into `data/raw`. Delphi's legacy FluView endpoint stopped at September 22, 2026, so the script uses the V5 snapshot endpoint.

## Method

- **Seasons** run from MMWR week 40, the first week of October, to week 39 of the next year.
- **Baseline.** Each season is measured against CDC's published national baseline for that season. CDC sets it each year from the weeks without flu in the three seasons before.
- **Start.** A season begins with the first of three weeks in a row at or above its baseline, with wILI rounded to one decimal. This is the rule CDC's FluSight forecasting challenge used.
- **The picture.** A ring is drawn as a circle until a week rises above the baseline, and then it swells outward by how far above. Every other ring is drawn half a week on so the spikes of neighboring seasons do not line up. The figures in the side panel are exact.
- **Checks.** `scripts/check_viz_data.py` recomputes every weekly value and every start from the raw file and compares them with figures CDC has published, such as the 2009–10 peak of 7.7% on October 24, 2009, the 2017–18 peak of 7.5% on February 3, 2018, and 21 weeks above baseline in 2022–23.

## What to keep in mind

- ILINet counts doctor visits for fever with a cough or sore throat, not confirmed flu. Other viruses add to it. The 2021–22 peak in the week ending January 1, 2022 came largely from COVID-19's Omicron wave, and the highest week of 2008–09, in September 2009, is the start of the 2009 pandemic's autumn wave, which ran into 2009–10.
- CDC's archived report for 2020–21 is no longer online. Its baseline of 2.6% comes from a Delaware state report quoting CDC.
- The network has grown since 1997, and CDC's baseline has risen from 2.0% to around 3%. Measuring each season against its own baseline accounts for that.
- The newest weeks are revised as late reports arrive.
- The notebook in `notebooks/` covers 1997 onward. Seasons before 2002–03 have no summer weeks, because the network reported only from October to May.

## Still to do

- Test whether an early start relates to a higher peak or a longer season.
- Repeat the comparison for HHS regions and states.
- Add which subtype led each season, from CDC's public health laboratory data, which starts in 2016–17.

## Run it

```
pip install -r requirements.txt
python3 scripts/download_data.py
python3 scripts/build_viz_data.py
python3 scripts/check_viz_data.py
npm install
npm run dev
```

`npm run build` writes the page to `docs/`, which GitHub Pages serves.
