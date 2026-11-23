# How Early Is This Flu Season? US Influenza Onset, 1997–2026

Work in progress, started November 23, 2026.

## The question

The 2026–27 flu season in the United States started early. By the week ending November 7, CDC reported high or very high flu activity in seven states. This study asks two things:

1. How early is this season's start compared with every season since 1997?
2. Does an early start predict a larger or longer season?

## Data

| Layer | Source | Notes |
|---|---|---|
| National and HHS regions, 1997–2026 | CDC ILINet through the Delphi Epidata V5 API | Population-weighted percentage of outpatient visits for influenza-like illness (wILI), weekly |
| States, 2010–2026 | CDC ILINet through the Delphi Epidata V5 API | Unweighted ILI percentage, weekly |

`scripts/download_data.py` downloads both into `data/raw`.

## Plan

- Define onset as the first week of a season that wILI stays at or above CDC's national baseline for that season for at least three weeks in a row.
- Measure each season's onset week, peak week, peak height and length above baseline.
- Place 2026–27 in that distribution, nationally and by region.
- Test whether onset week relates to peak height and season length, and treat the 2009 pandemic and the 2020–21 season apart.
- Note which subtype led each season, using CDC's public health laboratory data, as a possible explanation.

## Limitations to check

- ILINet counts visits for symptoms, not confirmed flu, so other viruses such as RSV and COVID-19 add to it.
- The number of reporting providers has grown since 1997.
- The newest weeks are revised as late reports arrive.

## Run it

```
pip install -r requirements.txt
python3 scripts/download_data.py
jupyter lab notebooks/analysis.ipynb
```
