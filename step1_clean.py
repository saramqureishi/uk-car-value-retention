"""
Day 1 - Clean the data and log every removal (data-quality table).

Input : per-brand UK used-car listing CSVs in ./data
Output: ./output/clean_cars.csv        (analysis-ready)
        ./output/data_quality_log.csv  (what was removed and why)

Honesty notes:
 - These are DEALER ASKING PRICES from ~2020 listings, not auction/wholesale
   values. Treated as a PROXY only, never as true residual value.
 - Age is measured relative to the dataset's collection year (2020).

HOW TO RUN
  From the project folder:
      ../venv/bin/python step1_clean.py
  (or: python step1_clean.py  if pandas is on your system Python)
  It prints the removal log + fuel mix and writes two files into ./output.
  Run this FIRST - every later step reads output/clean_cars.csv.
"""

import pandas as pd
from pathlib import Path

DATA = Path(__file__).parent / "data"
OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)

COLLECTION_YEAR = 2020

BRANDS = {
    "audi": "Audi", "bmw": "BMW", "ford": "Ford", "hyundi": "Hyundai",
    "merc": "Mercedes", "skoda": "Skoda", "toyota": "Toyota",
    "vauxhall": "Vauxhall", "vw": "Volkswagen",
}

log = []  # data-quality removal log


def record(step, removed, remaining, reason):
    log.append({"step": step, "rows_removed": removed,
                "rows_remaining": remaining, "reason": reason})


# ---------------------------------------------------------------- LOAD
frames = []
for stem, brand in BRANDS.items():
    f = DATA / f"{stem}.csv"
    if not f.exists():
        continue
    d = pd.read_csv(f)
    d.columns = [c.strip() for c in d.columns]
    d["brand"] = brand
    frames.append(d)

cars = pd.concat(frames, ignore_index=True)
n = len(cars)
record("load", 0, n, "raw listings combined across 9 brand files")

# normalise text columns
for c in ["model", "fuelType", "transmission"]:
    cars[c] = cars[c].astype(str).str.strip()

# ---------------------------------------------------------- CLEANING STEPS
# 1. drop exact duplicate adverts
before = len(cars)
cars = cars.drop_duplicates()
record("dedupe", before - len(cars), len(cars), "removed exact duplicate adverts")

# 2. impossible / future registration years
before = len(cars)
cars = cars[(cars["year"] >= 1990) & (cars["year"] <= COLLECTION_YEAR)]
record("year_range", before - len(cars), len(cars),
       f"kept registration years 1990-{COLLECTION_YEAR} (removed impossible/future years)")

# 3. implausible prices (data entry errors, placeholder values)
before = len(cars)
cars = cars[(cars["price"] >= 500) & (cars["price"] <= 150_000)]
record("price_range", before - len(cars), len(cars),
       "kept GBP 500-150,000 (removed placeholder/extreme prices)")

# 4. implausible mileage
before = len(cars)
cars = cars[(cars["mileage"] >= 0) & (cars["mileage"] <= 200_000)]
record("mileage_range", before - len(cars), len(cars),
       "kept 0-200,000 miles (removed impossible/extreme odometer values)")

# 5. derive age; drop anything outside a sensible 0-20 window
cars["age"] = COLLECTION_YEAR - cars["year"]
before = len(cars)
cars = cars[(cars["age"] >= 0) & (cars["age"] <= 20)]
record("age_window", before - len(cars), len(cars), "kept vehicle age 0-20 years")

# 6. tidy fuel buckets
fuel_map = {"Petrol": "Petrol", "Diesel": "Diesel",
            "Hybrid": "Hybrid", "Electric": "Electric", "Other": "Other"}
cars["fuel"] = cars["fuelType"].map(fuel_map).fillna("Other")

# 7. drop rows missing any field we need
before = len(cars)
need = ["price", "age", "mileage", "fuel", "brand", "model",
        "transmission", "engineSize"]
cars = cars.dropna(subset=need)
record("missing_fields", before - len(cars), len(cars),
       "removed rows missing any required field")

# ---------------------------------------------------------------- SAVE
cars.to_csv(OUT / "clean_cars.csv", index=False)
qa = pd.DataFrame(log)
qa.to_csv(OUT / "data_quality_log.csv", index=False)

print(f"Final clean rows: {len(cars):,} of {n:,} raw "
      f"({n - len(cars):,} removed, {(n-len(cars))/n*100:.1f}%)")
print("\nData-quality removal log:")
print(qa.to_string(index=False))
print("\nFuel mix (note how few pure Electric):")
print(cars["fuel"].value_counts().to_string())
print("\nModels available in >1 fuel type (needed for within-model fuel test):")
mf = cars.groupby("model")["fuel"].nunique().sort_values(ascending=False)
print(mf[mf > 1].head(15).to_string())
