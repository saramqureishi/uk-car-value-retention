"""
Day 1-2 - Hedonic value-retention regression, MODEL fixed effects, honest CIs.

Conceptual model (identical interpretation to C(model) dummies):
  log(price) ~ age + mileage + engineSize + C(transmission)
               + C(fuel) + age:C(fuel) + [model fixed effect]

Implementation note (speed + correctness):
  Instead of creating hundreds of C(model) dummy columns (slow), we apply the
  WITHIN-MODEL transformation: subtract each model's mean from logprice and
  from every predictor. This is the standard fixed-effects estimator and gives
  the SAME age / fuel:age coefficients as C(model) dummies, because it controls
  for everything constant within a model (its baseline price, trim mix, etc).

Age = 2020 - year  (dataset collected ~2020; stated assumption).

Uncertainty, the key honesty point:
  Listings of one model are not independent. We therefore bootstrap by
  RESAMPLING WHOLE MODELS (cluster bootstrap). We also show the naive row-level
  CI for contrast, to demonstrate how row resampling understates uncertainty.

HOW TO RUN
  Run step1_clean.py first, then:
      ../venv/bin/python step2_hedonic.py
  Needs: pandas, numpy (statsmodels NOT required - we use a fast fixed-effects
  within-transform via numpy.linalg.lstsq).
  Prints: per-fuel annual depreciation, the raw-vs-like-for-like gap
  decomposition, total depreciation at several mileage scenarios, and the
  honest (model-clustered) bootstrap CI. Writes CSVs into ./output.
"""

import numpy as np
import pandas as pd
from pathlib import Path

OUT = Path(__file__).parent / "output"
cars = pd.read_csv(OUT / "clean_cars.csv")
cars = cars[cars["fuel"].isin(["Petrol", "Diesel", "Hybrid"])].copy()
cars["logprice"] = np.log(cars["price"])

# design: numeric + fuel dummies + transmission dummies + fuel*age
cars["is_diesel"] = (cars["fuel"] == "Diesel").astype(float)
cars["is_hybrid"] = (cars["fuel"] == "Hybrid").astype(float)
cars["age_diesel"] = cars["age"] * cars["is_diesel"]
cars["age_hybrid"] = cars["age"] * cars["is_hybrid"]
cars["auto"] = (cars["transmission"] == "Automatic").astype(float)
cars["semi"] = (cars["transmission"] == "Semi-Auto").astype(float)

XCOLS = ["age", "mileage", "engineSize", "auto", "semi",
         "is_diesel", "is_hybrid", "age_diesel", "age_hybrid"]
YCOL = "logprice"


def within_transform(df, group_col="model"):
    """Subtract per-group means (fixed effects). group_col lets the bootstrap
    pass a per-draw cluster id so duplicated models are demeaned separately."""
    g = df.groupby(group_col)
    out = df.copy()
    for c in XCOLS + [YCOL]:
        out[c] = df[c] - g[c].transform("mean")
    return out


def fit_fe(df, group_col="model"):
    """OLS on within-transformed data; returns coefficient dict."""
    w = within_transform(df, group_col)
    X = w[XCOLS].to_numpy()
    y = w[YCOL].to_numpy()
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return dict(zip(XCOLS, beta))


def pct_per_year(slope):
    return (np.exp(slope) - 1) * 100


# ----------------------------------------------------- point estimates
b = fit_fe(cars)
age_petrol = b["age"]
age_diesel = b["age"] + b["age_diesel"]
age_hybrid = b["age"] + b["age_hybrid"]

print("Value change per EXTRA YEAR of age (model held constant, within-model FE):")
print(f"  Petrol : {pct_per_year(age_petrol):+.1f}% / yr")
print(f"  Diesel : {pct_per_year(age_diesel):+.1f}% / yr")
print(f"  Hybrid : {pct_per_year(age_hybrid):+.1f}% / yr")

shared = (set(cars.loc[cars.fuel == "Hybrid", "model"]) &
          set(cars.loc[cars.fuel == "Petrol", "model"]))
print(f"\nHybrid identified only from models sold as BOTH petrol & hybrid: "
      f"{len(shared)} models ({', '.join(sorted(shared))})")

# ----------------------------------------------------- naive row bootstrap
rng = np.random.default_rng(42)
gap = lambda bb: pct_per_year(bb["age"] + bb["age_hybrid"]) - pct_per_year(bb["age"])

row_gaps = []
for _ in range(500):
    s = cars.sample(len(cars), replace=True,
                    random_state=int(rng.integers(1e9)))
    try:
        row_gaps.append(gap(fit_fe(s)))
    except Exception:
        pass
row_gaps = np.array(row_gaps)
r_lo, r_hi = np.percentile(row_gaps, [2.5, 97.5])

# -------------------------------------------- honest cluster (by model) boot
models = cars["model"].unique()
by_model = {m: d for m, d in cars.groupby("model")}
mod_gaps = []
for _ in range(500):
    pick = rng.choice(models, size=len(models), replace=True)
    # give each drawn model a DISTINCT cluster id, so a model picked twice is
    # demeaned as two separate clusters (correct cluster bootstrap)
    parts = []
    for i, m in enumerate(pick):
        d = by_model[m].copy()
        d["_cid"] = f"{m}__{i}"
        parts.append(d)
    s = pd.concat(parts, ignore_index=True)
    if s["fuel"].nunique() < 3:
        continue
    try:
        mod_gaps.append(gap(fit_fe(s, group_col="_cid")))
    except Exception:
        pass
mod_gaps = np.array(mod_gaps)
m_lo, m_hi = np.percentile(mod_gaps, [2.5, 97.5])

point = gap(b)
sig = (m_lo > 0) or (m_hi < 0)

print("\nHYBRID vs PETROL: extra %/yr retained (positive = hybrid loses value slower)")
print(f"  point estimate                         : {point:+.2f} %/yr")
print(f"  95% CI  (naive, resample ROWS)         : [{r_lo:+.2f}, {r_hi:+.2f}]  <- too narrow, misleading")
print(f"  95% CI  (honest, resample MODELS)      : [{m_lo:+.2f}, {m_hi:+.2f}]  <- the one to trust")
print(f"  honest verdict: "
      f"{'clear - CI excludes 0' if sig else 'point estimate favours hybrids, but this data CANNOT CONFIRM a hybrid advantage (CI includes 0)'}")

# ---------- (2) how much of the RAW 3-yr gap is just model mix? -----------
# raw: median price of ~new (age<=1) vs 3yr old, per fuel -> retained %.
def raw_retained_at3(df):
    base = df[df.age <= 1].groupby("fuel")["price"].median()
    at3 = df[df.age == 3].groupby("fuel")["price"].median()
    return (at3 / base * 100)

raw = raw_retained_at3(cars)
raw_gap = raw["Hybrid"] - raw["Petrol"]          # the eye-catching ~13pt gap

# model-adjusted gap over 3 years, from the FE slopes (compounded)
adj_hybrid_3 = (1 + age_hybrid) ** 3 * 100   # age_* are log-slopes; use exp form
adj_hybrid_3 = np.exp(age_hybrid * 3) * 100
adj_petrol_3 = np.exp(age_petrol * 3) * 100
adj_gap = adj_hybrid_3 - adj_petrol_3            # like-for-like 3yr gap

explained = (raw_gap - adj_gap) / raw_gap * 100 if raw_gap else float("nan")
print("\n(2) Decomposing the raw 3-year hybrid-vs-petrol gap:")
print(f"  raw gap (median, mixes models) : {raw_gap:+.1f} percentage points")
print(f"  like-for-like gap (model held) : {adj_gap:+.1f} percentage points")
print(f"  share of raw gap explained by MODEL MIX : {explained:.0f}%")

# ---------- (3) TOTAL annual depreciation at realistic annual mileage -----
# Each year a car ages 1 yr AND accrues some miles. We DERIVE the "typical"
# annual mileage from the data itself (median miles / age), then also show
# RENTAL scenarios (fleets drive much harder than private owners).
tmp = cars[cars.age >= 1].copy()
tmp["mpy"] = tmp["mileage"] / tmp["age"]
DERIVED_TYPICAL_MPY = int(round(tmp["mpy"].median(), -2))  # data-derived, rounded to 100
MILEAGE_SCENARIOS = {
    f"typical (data-derived {DERIVED_TYPICAL_MPY:,}/yr)": DERIVED_TYPICAL_MPY,
    "rental 15,000/yr": 15000,
    "rental 20,000/yr": 20000,
}
mileage_slope = b["mileage"]  # log-price per mile

def total_annual_pct(age_slope, miles):
    # one year => +1 age and +miles; combine age effect and mileage effect
    return (np.exp(age_slope + mileage_slope * miles) - 1) * 100

print(f"\n(3) TOTAL value loss per year = age effect + mileage effect.")
print(f"    Annual mileage DERIVED from data: median {DERIVED_TYPICAL_MPY:,} miles/yr.")
rows3 = []
for label, miles in MILEAGE_SCENARIOS.items():
    print(f"  -- at {label} ({miles:,} miles/yr):")
    for fuel, sl in [("Petrol", age_petrol), ("Diesel", age_diesel), ("Hybrid", age_hybrid)]:
        v = total_annual_pct(sl, miles)
        print(f"       {fuel:7s}: {v:+.1f}% / yr")
        rows3.append({"scenario": label, "miles_per_year": miles,
                      "fuel": fuel, "total_pct_per_year": round(v, 2)})
pd.DataFrame(rows3).to_csv(OUT / "total_annual_depreciation.csv", index=False)

# ----------------------------------------------------- save
pd.DataFrame({
    "fuel": ["Petrol", "Diesel", "Hybrid"],
    "age_only_pct_per_year": [round(pct_per_year(age_petrol), 2),
                              round(pct_per_year(age_diesel), 2),
                              round(pct_per_year(age_hybrid), 2)],
    "total_pct_per_year_at_derived_mpy": [
        round(total_annual_pct(age_petrol, DERIVED_TYPICAL_MPY), 2),
        round(total_annual_pct(age_diesel, DERIVED_TYPICAL_MPY), 2),
        round(total_annual_pct(age_hybrid, DERIVED_TYPICAL_MPY), 2)],
}).to_csv(OUT / "hedonic_age_slopes.csv", index=False)

pd.DataFrame({
    "metric": ["raw_3yr_gap_pp", "likeforlike_3yr_gap_pp",
               "pct_of_raw_gap_explained_by_model_mix", "derived_typical_miles_per_year"],
    "value": [round(raw_gap, 1), round(adj_gap, 1), round(explained, 0),
              DERIVED_TYPICAL_MPY],
}).to_csv(OUT / "gap_decomposition.csv", index=False)

pd.DataFrame({
    "quantity": ["hybrid_minus_petrol_pct_per_year"],
    "point_estimate": [round(point, 2)],
    "ci_low_rows_naive": [round(r_lo, 2)],
    "ci_high_rows_naive": [round(r_hi, 2)],
    "ci_low_models_honest": [round(m_lo, 2)],
    "ci_high_models_honest": [round(m_hi, 2)],
    "significant_by_model": [sig],
}).to_csv(OUT / "hedonic_hybrid_gap_ci.csv", index=False)
print("\nSaved hedonic_age_slopes.csv and hedonic_hybrid_gap_ci.csv")
