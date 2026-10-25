# Data (not committed) - how to download it

The raw dataset is **not included in this repo** (licensing and size). Download
it yourself before running the scripts.

## What you need
The "100,000 UK Used Car" dataset: one CSV per brand, each with columns
`model, year, price, transmission, mileage, fuelType, tax, mpg, engineSize`.

## Option 1 - Kaggle (original source)
Search Kaggle for **"100,000 UK Used Car Data Set"** (by aishwaryamuthukumar
/ adityadesai13). Download and unzip the per-brand CSVs into this `data/` folder:
`audi.csv, bmw.csv, ford.csv, hyundi.csv, merc.csv, skoda.csv, toyota.csv,
vauxhall.csv, vw.csv`.

## Option 2 - public GitHub mirror (what this project used)
```bash
cd data
base="https://raw.githubusercontent.com/Salama1429/UK-cars-price-prediction/master/Data"
for b in audi bmw ford hyundi merc skoda toyota vauxhall vw; do
  curl -sfL -o "$b.csv" "$base/$b.csv"
done
```

## After downloading
From the project root:
```bash
./venv/bin/python step1_clean.py   # and the rest, see top-level README
```

**Licensing note:** check the dataset's licence on Kaggle before redistributing.
This project only ships the *code* and *aggregated outputs*, not the raw data.
