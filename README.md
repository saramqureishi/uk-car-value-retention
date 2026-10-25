# UK Used-Car Value Retention Analysis

A small, honest data project: **how fast do UK cars lose value, and do hybrids
really hold value better than petrol and diesel?** Built as a worked example for
a Graduate Residual Value Analyst role, with a focus on honest methods, clear
limitations and decision-ready outputs.

> **Important:** the data is ~99k UK dealer **asking-price** listings from around
> 2020. These are not auction/wholesale values and there is no new-price field,
> so "value retained" is a **proxy** (price as a % of the same model's near-new
> median). It is never called "residual value". Only 6 pure EVs are in the data,
> so EV conclusions come only from cited published sources, not from this data.

## Headline findings
- Cars lose roughly **8-10% of value per year** from age alone (model held constant).
- Including real annual mileage, total loss is about **13%/yr** at typical use and
  about **19%/yr** at rental-style 20,000 miles/yr.
- The "hybrids hold value better" story is **~60% a brand effect** (hybrids are
  mostly Toyotas). The like-for-like hybrid edge is **not statistically clear**
  (95% CI about -0.3% to +3.6%, clustered by model). So the data **cannot confirm**
  a hybrid advantage.
- A **simple baseline forecasts as well as a gradient-boosted model** for ageing a
  known car, so the transparent method wins here.

See **[SUMMARY.md](SUMMARY.md)** for the one-page write-up with cited sources.

## How to run
```bash
python3 -m venv venv
./venv/bin/pip install pandas numpy scikit-learn statsmodels matplotlib openpyxl

# then, in order:
./venv/bin/python step1_clean.py            # clean + data-quality log
./venv/bin/python step2_hedonic.py          # regression, gap decomposition, honest CI
./venv/bin/python step2b_same_model_charts.py  # supporting charts (PNG)
./venv/bin/python step3_forward_test.py     # forward test vs naive baseline
./venv/bin/python step4_rv_matrix.py        # RV matrix + procurement ranking (xlsx)
```
Each script has a header comment explaining what it does and why.

## What's in here
| File | What it produces |
|------|------------------|
| `step1_clean.py` | `clean_cars.csv`, `data_quality_log.csv` (every removal rule + n) |
| `step2_hedonic.py` | per-fuel %/yr, raw-vs-like-for-like gap decomposition, model-clustered CI |
| `step2b_same_model_charts.py` | same-model petrol-vs-hybrid charts with sample sizes |
| `step3_forward_test.py` | forward-test error vs a naive baseline, on % retained |
| `step4_rv_matrix.py` | `rv_matrix.xlsx` (matrix + mileage bands + procurement ranking) |
| `pipeline/snowflake_setup.sql` | optional ELT: raw -> staging -> mart in Snowflake |
| `pipeline/s3_setup.md` | optional: land raw data in S3, load into Snowflake |
| `dashboard/tableau_guide.md` | how to build the Tableau Public dashboard |
| `step5_reconcile.py` | side-by-side matrix vs regression retention, gap explained |
| `SUMMARY.md` | one-page summary with cited "what's changed since 2020" |
| `CHEAT_SHEET.md` | plain-English guide to explaining the project in an interview |

## Method notes (the honest bits)
- **Model fixed effects** separate the *fuel* effect from the *brand/model* effect.
- **Cluster bootstrap by model** (not by row) gives honest confidence intervals,
  because listings of one model are not independent.
- **Forward test** (train age 0-3, predict 4-5) mirrors the real forecasting job,
  and is compared against a naive baseline so we know if the model adds value.
- **Low-confidence cells** (n below 10) are flagged in the RV matrix, never hidden.

## Limitations
- **Baseline understates depreciation from new.** The 100% reference is the
  median of 0-1 year old listings, which is really a ~1-year-old, ~5k-mile car
  (age-0 cars sit *above* it, e.g. ~120%). So these figures **miss the first-year
  drop from the showroom price** and understate total depreciation for a buyer of
  new cars.
- Asking prices, not trade/auction values.
- 2020 snapshot; the market has shifted a lot since (see SUMMARY.md, cited).
- Proxy baseline mixes trims/generations within a model.
- Few models sold as both petrol and hybrid, so the fuel comparison is thin.

## Reconciling the two retention numbers
The matrix shows strong models at ~88% at 2yr; the regression implies ~81%
(fleet average, age-only). The gap is because the matrix is for hand-picked
value-holding models while the regression is the all-model average. Use the
matrix for "which model to buy", the regression for "typical fleet %/yr". See
`output/reconciliation_matrix_vs_regression.csv` and SUMMARY.md.
