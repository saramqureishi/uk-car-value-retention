# Tableau Public dashboard - build guide

Tableau Public is free and runs on Windows (you confirmed you're on Windows).
It's also honestly on your CV. This builds a small, clean dashboard an RV team
would actually find useful.

## Data sources to connect
From the `output/` folder, connect these CSVs (Text file connection):
- `clean_cars.csv`        - the row-level data
- `rv_matrix_all.csv`     - model x age % retained + n + low_confidence flag
- `total_annual_depreciation.csv` - fuel x mileage-scenario %/yr
- `procurement_2yr_ranking.csv`   - best value-retainers by segment

## Sheet 1 - Depreciation curve by fuel
- Columns: `age`  Rows: median of `retained` (from clean_cars)
- Colour: `fuel`
- Title: "Median value retention by fuel (proxy, 2020 data)"
- Add a caption: "Not model-adjusted - see the regression finding."

## Sheet 2 - Total annual loss by mileage scenario
- Use `total_annual_depreciation.csv`
- Columns: `scenario`  Rows: `total_pct_per_year`  Colour: `fuel`
- Bar chart. Shows the rental 15k/20k scenarios losing value fastest.

## Sheet 3 - RV matrix heatmap
- Use `rv_matrix_all.csv`
- Columns: the age columns (age0_pct..age3_pct)  Rows: `model`
- Colour by % retained; add `*_n` to tooltip.
- Filter: exclude `low_confidence = True` (or show them greyed) so thin cells
  don't mislead. Mention this filter on the dashboard.

## Sheet 4 - Procurement: best 2-year holds by segment
- Use `procurement_2yr_ranking.csv`
- Rows: `segment` then `model` (sorted by `retained_2yr`)
- Columns: `retained_2yr`  Label with `n`
- Horizontal bars, one small multiple per segment.

## Dashboard assembly
- Combine the 4 sheets. Add one text box with the key honesty line:
  "Asking prices, 2020 snapshot. 'Retained %' is a proxy, not residual value.
  Hybrid advantage not statistically confirmed once model is controlled for."
- Publish to Tableau Public and put the link in the GitHub README.

## If you were on a Mac
Power BI Desktop is Windows-only, so Tableau Public (or Tableau on Mac) is the
right choice there too. You're on Windows, so either works; this guide uses
Tableau because it's already on your CV.
