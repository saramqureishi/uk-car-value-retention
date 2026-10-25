# Optional: land the raw data in AWS S3, then load into Snowflake

This is the optional cloud layer for the **data-engineering version** of the
project. It shows the realistic path: raw data lands in object storage (S3),
then an ELT pipeline loads it into the warehouse (Snowflake).

**Honesty note:** this is *my* project design. It does **not** describe Avis's
internal stack, and I should never claim it does.

Do this only if you will actually build it and reference it on the
data-engineering CV. The analyst version of the project does not need it.

---

## 1. Put the file in S3 (AWS free tier is fine for one small CSV)

1. Sign in to the AWS console, go to **S3**, create a bucket, e.g.
   `rv-project-<yourname>` (bucket names are globally unique).
2. Upload `output/clean_cars.csv` into the bucket.
3. Note the path: `s3://rv-project-<yourname>/clean_cars.csv`.

That is the whole "raw data landed in the cloud" step. One sentence in your
write-up: *"Raw listings land in an S3 bucket; an ELT job loads them into
Snowflake, where staging and mart models are built in SQL."*

## 2. Load S3 -> Snowflake via an external stage

Run this in a Snowflake worksheet (after `snowflake_setup.sql` has created the
database and RAW table). Replace the placeholders.

```sql
USE SCHEMA RV_DB.RAW;

-- a CSV file format that skips the header row
CREATE OR REPLACE FILE FORMAT RV_DB.RAW.CSV_FMT
  TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1;

-- an external stage pointing at your S3 bucket
-- (use a storage integration in production; keys shown only for a throwaway trial)
CREATE OR REPLACE STAGE RV_DB.RAW.S3_STAGE
  URL = 's3://rv-project-<yourname>/'
  CREDENTIALS = (AWS_KEY_ID = '<key>' AWS_SECRET_KEY = '<secret>')
  FILE_FORMAT = RV_DB.RAW.CSV_FMT;

-- load the file into the RAW table
COPY INTO RV_DB.RAW.CAR_LISTINGS
FROM @RV_DB.RAW.S3_STAGE/clean_cars.csv
ON_ERROR = 'ABORT_STATEMENT';

-- confirm
SELECT COUNT(*) AS rows_loaded FROM RV_DB.RAW.CAR_LISTINGS;
```

## 3. What to say about it (honest, one or two lines)

- "I designed a small ELT pipeline: raw CSV in S3, loaded into Snowflake, then
  staging and mart SQL models (raw -> staging -> mart)."
- "If this were wired to live mileage or market feeds, the mart views would
  refresh automatically. I did not build the live feed; that is a design note."

Do **not** say Avis uses S3 or Snowflake. You do not know that.
