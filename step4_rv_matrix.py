"""
Day 3 - Build the decision-ready outputs an RV team actually uses:

  1. RV MATRIX  : rows = model, columns = age 0,1,2,3 (the ages a rental fleet
                  cares about), cells = median % RETAINED vs that model's
                  near-new price. We SHOW n per cell and FLAG low-confidence
                  cells (n below a threshold), so nobody quotes a number built
                  on a handful of cars.
  2. MILEAGE BANDS: same matrix split into normal vs HIGH-mileage cars
                  (rental cars rack up miles), because a 2-yr/40k car is worth
                  much less than a 2-yr/12k car.
  3. PROCUREMENT VIEW: within each size segment, rank models by value retained
                  per year for a 2-YEAR hold. Turns the analysis into a buy
                  recommendation.

Honesty labels:
  - % retained here is a PROXY (asking prices, no true new-price data).
  - Low-n cells are flagged, never hidden.

HOW TO RUN
  Run step1_clean.py first, then:
      ../venv/bin/python step4_rv_matrix.py
  Needs pandas, numpy. Writes output/rv_matrix.xlsx (several sheets) and
  a couple of CSVs for the dashboard.
"""

import numpy as np
import pandas as pd
from pathlib import Path

OUT = Path(__file__).parent / "output"
cars = pd.read_csv(OUT / "clean_cars.csv")
cars = cars[cars["fuel"].isin(["Petrol", "Diesel", "Hybrid"])].copy()

MIN_N = 10          # minimum listings per cell to trust it
HIGH_MILEAGE = 15000  # miles/yr threshold that flags a "rental-style" hard-used car

# ---- % retained vs each model's near-new (age<=1) median -------------------
baseline = (cars[cars.age <= 1].groupby("model")["price"].median()
            .rename("base_price"))
cars = cars.merge(baseline, on="model", how="inner")
cars["retained"] = cars["price"] / cars["base_price"] * 100
cars = cars[(cars.retained > 5) & (cars.retained <= 120)]
cars["miles_per_year"] = cars["mileage"] / cars["age"].clip(lower=1)
cars["mileage_band"] = np.where(cars.miles_per_year >= HIGH_MILEAGE,
                                f"high (>= {HIGH_MILEAGE:,}/yr)",
                                f"normal (< {HIGH_MILEAGE:,}/yr)")

# ---------------------------------------------------------- 1. RV MATRIX
def build_matrix(df):
    """median % retained + n, for ages 0-3, per model."""
    d = df[df.age.between(0, 3)]
    med = d.pivot_table(index="model", columns="age",
                        values="retained", aggfunc="median").round(1)
    cnt = d.pivot_table(index="model", columns="age",
                        values="retained", aggfunc="count")
    med.columns = [f"age{int(c)}_pct" for c in med.columns]
    cnt.columns = [f"age{int(c)}_n" for c in cnt.columns]
    out = med.join(cnt)
    # flag low-confidence: any age cell with n < MIN_N
    n_cols = [c for c in out.columns if c.endswith("_n")]
    out["low_confidence"] = (out[n_cols].fillna(0) < MIN_N).any(axis=1)
    return out.sort_index()

matrix = build_matrix(cars)
low = int(matrix["low_confidence"].sum())
print(f"RV matrix: {len(matrix)} models, {low} flagged low-confidence "
      f"(a cell with n < {MIN_N}).")

# mileage-banded matrices
mat_normal = build_matrix(cars[cars.mileage_band.str.startswith("normal")])
mat_high = build_matrix(cars[cars.mileage_band.str.startswith("high")])

# ------------------------------------------------- 2. PROCUREMENT RANKING
# crude but transparent size segment from model/brand heuristics.
SEGMENT = {
    # small hatch
    "A1": "Small", "Polo": "Small", "Fiesta": "Small", "Corsa": "Small",
    "Yaris": "Small", "Aygo": "Small", "Up": "Small", "i10": "Small",
    "i20": "Small", "A Class": "Small", "1 Series": "Small",
    # family / medium
    "A3": "Medium", "Golf": "Medium", "Focus": "Medium",
    "Astra": "Medium", "Auris": "Medium", "Corolla": "Medium",
    "3 Series": "Medium", "C Class": "Medium", "A4": "Medium",
    "Passat": "Medium", "Mondeo": "Medium", "Octavia": "Medium",
    # SUV
    "Q3": "SUV", "Q5": "SUV", "X1": "SUV", "X3": "SUV", "X5": "SUV",
    "GLC Class": "SUV", "GLE Class": "SUV", "Tucson": "SUV", "Kona": "SUV",
    "RAV4": "SUV", "C-HR": "SUV", "Kuga": "SUV", "Tiguan": "SUV",
    "Puma": "SUV", "Karoq": "SUV", "Kadjar": "SUV",
}
cars["segment"] = cars["model"].map(SEGMENT).fillna("Other")

# value retained at a 2-year hold, per model (needs enough 2yr listings)
two_yr = (cars[cars.age == 2].groupby(["segment", "model"])
          .agg(retained_2yr=("retained", "median"),
               n=("retained", "size")).reset_index())
two_yr = two_yr[two_yr.n >= MIN_N]  # only trust well-populated models
two_yr["rank_in_segment"] = (two_yr.groupby("segment")["retained_2yr"]
                             .rank(ascending=False).astype(int))
two_yr = two_yr.sort_values(["segment", "rank_in_segment"])

# ---- RANK STABILITY via bootstrap (point 3) --------------------------------
# resample the 2yr cars WITH REPLACEMENT many times; each time, see which model
# ranks #1 in its segment. A model that is #1 in most resamples is "consistently
# strong"; one that flips around is not. We report how often each top pick wins,
# so we present them as consistently strong rather than as a precise %.
age2 = cars[cars.age == 2].copy()
rng = np.random.default_rng(42)
B = 300
win_counts = {}  # (segment, model) -> times ranked #1
for _ in range(B):
    s = age2.sample(len(age2), replace=True,
                    random_state=int(rng.integers(1e9)))
    agg = (s.groupby(["segment", "model"])
           .agg(r=("retained", "median"), n=("retained", "size")).reset_index())
    agg = agg[agg.n >= MIN_N]
    for seg, g in agg.groupby("segment"):
        if seg == "Other" or g.empty:
            continue
        winner = g.sort_values("r", ascending=False).iloc[0]["model"]
        win_counts[(seg, winner)] = win_counts.get((seg, winner), 0) + 1

print("\nProcurement view - CONSISTENTLY STRONG value-retainers for a 2-year hold")
print("(how often each model ranked #1 in its segment across", B, "bootstraps):")
stability_rows = []
for seg in sorted(set(k[0] for k in win_counts)):
    picks = sorted([(m, c) for (s, m), c in win_counts.items() if s == seg],
                   key=lambda x: -x[1])
    top_m, top_c = picks[0]
    print(f"  {seg:7s}: {top_m} (top in {top_c/B*100:.0f}% of resamples)")
    for m, c in picks:
        stability_rows.append({"segment": seg, "model": m,
                               "pct_resamples_ranked_1": round(c / B * 100, 0)})

# --------------------------------------------------------------- SAVE
xlsx = OUT / "rv_matrix.xlsx"
with pd.ExcelWriter(xlsx, engine="openpyxl") as xw:
    matrix.to_excel(xw, sheet_name="RV_matrix_all")
    mat_normal.to_excel(xw, sheet_name="RV_matrix_normal_miles")
    mat_high.to_excel(xw, sheet_name="RV_matrix_high_miles")
    two_yr.to_excel(xw, sheet_name="procurement_2yr_ranking", index=False)

matrix.to_csv(OUT / "rv_matrix_all.csv")
two_yr.to_csv(OUT / "procurement_2yr_ranking.csv", index=False)
pd.DataFrame(stability_rows).to_csv(OUT / "procurement_rank_stability.csv", index=False)
print(f"\nSaved RV matrix workbook -> {xlsx}")
print("Saved procurement_rank_stability.csv (how robust each top pick is).")
print("Low-confidence cells are flagged in the 'low_confidence' column.")
