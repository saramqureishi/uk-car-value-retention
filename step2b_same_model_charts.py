"""
Day 2 - SUPPORTING VISUAL: same-model fuel comparisons with sample sizes.

This backs up the regression in plain sight. For a few models sold as BOTH
petrol and hybrid (e.g. Toyota Yaris, Corolla, RAV4), we plot median % retained
vs age for each fuel, and we PRINT the sample size (n) behind every line so a
viewer can see how thin some comparisons are.

This is a SUPPORTING chart, not the main method. The main finding comes from the
regression + model-clustered CI in step2_hedonic.py.

HOW TO RUN
  Run step1_clean.py first, then:
      ../venv/bin/python step2b_same_model_charts.py
  Needs pandas, numpy, matplotlib. Writes PNGs into ./output.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # no display needed; save to file
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(__file__).parent / "output"
cars = pd.read_csv(OUT / "clean_cars.csv")

baseline = (cars[cars.age <= 1].groupby("model")["price"].median()
            .rename("base_price"))
cars = cars.merge(baseline, on="model", how="inner")
cars["retained"] = cars["price"] / cars["base_price"] * 100

# models that exist in both Petrol and Hybrid, with enough data
both = (cars[cars.fuel.isin(["Petrol", "Hybrid"])]
        .groupby(["model", "fuel"]).size().unstack(fill_value=0))
both = both[(both.get("Petrol", 0) >= 50) & (both.get("Hybrid", 0) >= 50)]
targets = list(both.index[:6])
print("Models compared (petrol vs hybrid, n>=50 each):", targets)

fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharey=True)
for ax, model in zip(axes.ravel(), targets):
    d = cars[cars.model == model]
    for fuel, colour in [("Petrol", "#c0392b"), ("Hybrid", "#27ae60")]:
        s = (d[d.fuel == fuel].groupby("age")["retained"]
             .agg(["median", "size"]).reset_index())
        s = s[s["size"] >= 5]  # don't draw points built on <5 cars
        ax.plot(s["age"], s["median"], marker="o", label=f"{fuel}", color=colour)
        total_n = int(d[d.fuel == fuel].shape[0])
        ax.plot([], [], " ", label=f"   n={total_n}")
    ax.set_title(model)
    ax.set_xlabel("age (years)")
    ax.set_ylabel("% of near-new price")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

fig.suptitle("Same-model value retention: Petrol vs Hybrid (proxy: asking prices, 2020 data)",
             fontsize=13)
fig.tight_layout()
fig.savefig(OUT / "same_model_petrol_vs_hybrid.png", dpi=120)
print(f"Saved chart -> {OUT/'same_model_petrol_vs_hybrid.png'}")

# overall depreciation curve by fuel (context chart)
fig2, ax2 = plt.subplots(figsize=(8, 5))
for fuel, colour in [("Petrol", "#c0392b"), ("Diesel", "#2c3e50"),
                     ("Hybrid", "#27ae60")]:
    s = (cars[cars.fuel == fuel].groupby("age")["retained"]
         .median().reset_index())
    s = s[s["age"] <= 10]
    ax2.plot(s["age"], s["retained"], marker="o", label=fuel, color=colour)
ax2.set_title("Median value retention by fuel (NOT model-adjusted - see regression)")
ax2.set_xlabel("age (years)"); ax2.set_ylabel("% of near-new price")
ax2.legend(); ax2.grid(alpha=0.3)
fig2.tight_layout()
fig2.savefig(OUT / "overall_retention_by_fuel.png", dpi=120)
print(f"Saved chart -> {OUT/'overall_retention_by_fuel.png'}")
