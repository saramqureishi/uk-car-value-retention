"""
Day 3 - Honest forward test: can we predict OLDER cars from YOUNGER ones?

Real RV job = forecast a KNOWN model further down its life. So we TRAIN on young
cars (age 0-3) and TEST on older cars (age 4-5). A random split would be too easy
(near-identical listings leak across train/test), so we deliberately split by age.

Target = % RETAINED (price as a % of the model's near-new median), not pounds,
because the RV matrix needs a ratio and it stops expensive models dominating error.

WHAT WE COMPARE
  Baseline (naive):  extrapolate an average annual % loss out to age 4-5.
                     Two flavours, both reported:
                       - GLOBAL  : one average %/yr loss for the whole fleet
                       - PER-MODEL: each model's own average %/yr loss
                     Per-model is the stronger, fairer baseline.
  Primary model:     the HEDONIC regression (same spec as step2: model fixed
                     effects + age + mileage + fuel + fuel:age + transmission +
                     engine size), trained on age 0-3, used to predict age 4-5.
  Optional extra:    a gradient-boosted model (GBM), reported only as a "does a
                     black-box beat the transparent model?" check.

TWO UNSEEN-MODEL TESTS (both documented; the SECOND is the fair one)
  Test A: train on all young cars incl. the held-out models' young cars;
          predict the held-out models at 4-5. (Model has seen the model young.)
  Test B: train on young cars EXCLUDING the held-out models entirely;
          predict those models at 4-5. This is the true "brand-new model
          entering the fleet" case - the model has never seen it at all.
          Test B is the fair, honest measure of unseen-model performance.

HOW TO RUN
  Run step1_clean.py first, then:
      ../venv/bin/python step3_forward_test.py
  Needs pandas, numpy, scikit-learn. Writes output/forward_test_metrics.csv.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import mean_absolute_error

OUT = Path(__file__).parent / "output"
cars = pd.read_csv(OUT / "clean_cars.csv")
cars = cars[cars["fuel"].isin(["Petrol", "Diesel", "Hybrid"])].copy()

# ---- % retained target vs each model's near-new (age<=1) median ------------
baseline = (cars[cars.age <= 1].groupby("model")["price"].median()
            .rename("base_price"))
cars = cars.merge(baseline, on="model", how="inner")
cars["retained"] = cars["price"] / cars["base_price"] * 100
cars = cars[(cars.retained > 5) & (cars.retained <= 120)]

train = cars[cars.age <= 3].copy()
test = cars[(cars.age >= 4) & (cars.age <= 5)].copy()
print(f"Train (age 0-3): {len(train):,}   Test (age 4-5): {len(test):,}\n")


# ===========================================================================
# BASELINES (naive) - defined exactly
# ===========================================================================
# GLOBAL: fit retained ~ age on ALL training cars; one slope for everything.
g_slope, g_int = np.polyfit(train["age"], train["retained"], 1)
pred_global = g_int + g_slope * test["age"]
mae_global = mean_absolute_error(test["retained"], pred_global)

# PER-MODEL: each model's own line retained ~ age (needs >=2 ages in train).
per_model = {}
for m, d in train.groupby("model"):
    if d["age"].nunique() >= 2:
        s, i = np.polyfit(d["age"], d["retained"], 1)
        per_model[m] = (s, i)
def pm_pred(row):
    if row["model"] in per_model:
        s, i = per_model[row["model"]]
        return i + s * row["age"]
    return g_int + g_slope * row["age"]      # fall back to global
pred_pm = test.apply(pm_pred, axis=1)
mae_pm = mean_absolute_error(test["retained"], pred_pm)

print("Naive baselines (MAE on % retained, age 4-5):")
print(f"  GLOBAL  average loss ({g_slope:.1f} %/yr): {mae_global:.1f} pp")
print(f"  PER-MODEL average loss             : {mae_pm:.1f} pp   <- stronger/fairer baseline")


# ===========================================================================
# PRIMARY MODEL: hedonic regression (model fixed effects), % retained version
# ===========================================================================
XCOLS = ["age", "mileage", "engineSize", "auto", "semi",
         "is_diesel", "is_hybrid", "age_diesel", "age_hybrid"]

def add_design(df):
    df = df.copy()
    df["is_diesel"] = (df.fuel == "Diesel").astype(float)
    df["is_hybrid"] = (df.fuel == "Hybrid").astype(float)
    df["age_diesel"] = df.age * df.is_diesel
    df["age_hybrid"] = df.age * df.is_hybrid
    df["auto"] = (df.transmission == "Automatic").astype(float)
    df["semi"] = (df.transmission == "Semi-Auto").astype(float)
    return df

def fit_hedonic(tr):
    """Fixed-effects OLS of retained on the design, with per-model intercepts.
    Returns (beta dict, per-model intercept dict, global intercept)."""
    tr = add_design(tr)
    g = tr.groupby("model")
    means = {c: g[c].transform("mean") for c in XCOLS + ["retained"]}
    Xd = np.column_stack([tr[c] - means[c] for c in XCOLS])
    yd = tr["retained"] - means["retained"]
    beta, *_ = np.linalg.lstsq(Xd, yd, rcond=None)
    beta = dict(zip(XCOLS, beta))
    # recover each model's intercept so we can predict its level
    tr_pred_centered = sum(beta[c] * tr[c] for c in XCOLS)
    tr = tr.assign(_fit=tr_pred_centered)
    model_int = (tr.assign(resid=tr["retained"] - tr["_fit"])
                 .groupby("model")["resid"].mean().to_dict())
    global_int = np.mean(list(model_int.values()))
    return beta, model_int, global_int

def predict_hedonic(te, beta, model_int, global_int):
    te = add_design(te)
    core = sum(beta[c] * te[c] for c in XCOLS)
    inter = te["model"].map(model_int).fillna(global_int)
    return core + inter

beta, model_int, global_int = fit_hedonic(train)

# (1a) regression using each test car's ACTUAL mileage (uses more info than the
#      age-only baseline, so NOT a like-for-like comparison with it).
pred_hed_actual = predict_hedonic(test, beta, model_int, global_int)
mae_hed_actual = mean_absolute_error(test["retained"], pred_hed_actual)

# (1b) regression at TYPICAL mileage for the car's age, so it uses only
#      age-based info, exactly like the naive baseline -> FAIR comparison.
#      typical mileage = linear miles-per-year trend from TRAINING data,
#      extrapolated to the test ages (4-5), since those ages aren't in training.
m_slope, m_int = np.polyfit(train["age"], train["mileage"], 1)
test_typ = test.copy()
test_typ["mileage"] = (m_int + m_slope * test_typ["age"]).clip(lower=0)
pred_hed_typ = predict_hedonic(test_typ, beta, model_int, global_int)
mae_hed_typ = mean_absolute_error(test["retained"], pred_hed_typ)

print(f"\nPRIMARY - hedonic regression:")
print(f"  at ACTUAL mileage (uses extra info) : {mae_hed_actual:.1f} pp")
print(f"  at TYPICAL mileage (fair vs baseline): {mae_hed_typ:.1f} pp")
vs_pm = (mae_pm - mae_hed_typ) / mae_pm * 100
print(f"  fair version vs per-model baseline  : {vs_pm:+.0f}% "
      f"({'better' if vs_pm > 0 else 'no better - prefer the simpler baseline'})")
mae_hed = mae_hed_typ  # use the fair version as the headline


# ===========================================================================
# OPTIONAL EXTRA: gradient-boosted model (black-box check)
# ===========================================================================
mae_gbm = None
try:
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    feats = ["age", "mileage", "engineSize", "fuel", "brand", "model", "transmission"]
    pre = ColumnTransformer([("c", OneHotEncoder(handle_unknown="ignore"),
                              ["fuel", "brand", "model", "transmission"])],
                            remainder="passthrough")
    gbm = Pipeline([("pre", pre), ("m", GradientBoostingRegressor(random_state=42))])
    gbm.fit(train[feats], train["retained"])
    mae_gbm = mean_absolute_error(test["retained"], gbm.predict(test[feats]))
    print(f"\nOPTIONAL - gradient-boosted model: {mae_gbm:.1f} pp "
          f"(black-box; only worth it if clearly better than the transparent model)")
except Exception as e:
    print(f"\n(GBM optional extra skipped: {e})")


# ===========================================================================
# UNSEEN-MODEL TESTS (both defined; B is the fair one)
# ===========================================================================
rng = np.random.default_rng(0)
all_models = cars["model"].unique()
holdout = set(rng.choice(all_models, size=max(3, len(all_models)//5), replace=False))

# Test A: held-out models' YOUNG cars ARE in training (model seen when young)
trA = cars[cars.age <= 3]
teA = cars[(cars.age.between(4, 5)) & (cars.model.isin(holdout))]
bA, miA, giA = fit_hedonic(trA)
maeA = mean_absolute_error(teA["retained"], predict_hedonic(teA, bA, miA, giA))

# Test B: held-out models COMPLETELY excluded from training (truly new model)
trB = cars[(cars.age <= 3) & (~cars.model.isin(holdout))]
teB = cars[(cars.age.between(4, 5)) & (cars.model.isin(holdout))]
bB, miB, giB = fit_hedonic(trB)
maeB = mean_absolute_error(teB["retained"], predict_hedonic(teB, bB, miB, giB))

print(f"\nUnseen-model tests ({len(holdout)} held-out models):")
print(f"  Test A (model seen young)        : {maeA:.1f} pp  (easier, slightly unfair)")
print(f"  Test B (model never seen at all) : {maeB:.1f} pp  <- the FAIR unseen-model number")

# ---- save ------------------------------------------------------------------
# ---- REPORT EVERYTHING (point 2): all methods side by side ----------------
all_results = pd.DataFrame({
    "method": ["baseline_global_age_only",
               "baseline_per_model_age_only",
               "hedonic_at_typical_mileage_FAIR",
               "hedonic_at_actual_mileage",
               "gbm_optional_blackbox",
               "unseen_A_seen_young",
               "unseen_B_never_seen_FAIR"],
    "mae_pct_points": [round(mae_global, 1), round(mae_pm, 1),
                       round(mae_hed_typ, 1), round(mae_hed_actual, 1),
                       (round(mae_gbm, 1) if mae_gbm is not None else None),
                       round(maeA, 1), round(maeB, 1)],
    "note": ["naive, age only",
             "naive, each model's own age slope (stronger baseline)",
             "regression, mileage set to typical-for-age (comparable to baseline)",
             "regression, each car's real mileage (uses extra info)",
             "black-box; report even though it does not win",
             "unseen model but seen young (easier)",
             "unseen model, never seen at all (the fair unseen number)"],
})
print("\n=== ALL FORWARD-TEST RESULTS (nothing hidden) ===")
print(all_results.to_string(index=False))
all_results.to_csv(OUT / "forward_test_metrics.csv", index=False)
print("\nSaved forward_test_metrics.csv")
