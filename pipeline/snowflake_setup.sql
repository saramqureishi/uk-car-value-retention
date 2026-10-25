-- ============================================================================
-- UK Used-Car Value Retention - Snowflake pipeline (OPTIONAL data-eng layer)
-- ----------------------------------------------------------------------------
-- This is the "engine" version of the project for the DATA ENGINEERING CV.
-- It loads the cleaned CSV into Snowflake and builds clean SQL models
-- (raw -> staging -> mart), mirroring a real ELT pipeline.
--
-- HONESTY: this is MY project design. It does NOT describe Avis's stack.
-- Run it on a free Snowflake 30-day trial. I am studying toward SnowPro Core,
-- so this is practice made real.
--
-- HOW TO RUN
--   1. Sign up for a free Snowflake trial (signup.snowflake.com).
--   2. Open a worksheet and run this file top to bottom.
--   3. For loading, either:
--        (a) upload output/clean_cars.csv via Snowsight "Load Data" into
--            RAW_CAR_LISTINGS, OR
--        (b) use the S3 external-stage block (see pipeline/s3_setup.md) if you
--            want to show the S3 -> Snowflake path.
-- ============================================================================

-- ---- 0. environment --------------------------------------------------------
CREATE WAREHOUSE IF NOT EXISTS RV_WH
  WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;
CREATE DATABASE IF NOT EXISTS RV_DB;
CREATE SCHEMA  IF NOT EXISTS RV_DB.RAW;
CREATE SCHEMA  IF NOT EXISTS RV_DB.STAGING;
CREATE SCHEMA  IF NOT EXISTS RV_DB.MART;

USE WAREHOUSE RV_WH;
USE SCHEMA RV_DB.RAW;

-- ---- 1. RAW landing table --------------------------------------------------
-- mirrors the cleaned CSV columns exactly.
CREATE OR REPLACE TABLE RV_DB.RAW.CAR_LISTINGS (
    model         STRING,
    year          INTEGER,
    price         NUMBER(10,2),
    transmission  STRING,
    mileage       NUMBER(10,0),
    fuelType      STRING,
    tax           NUMBER(10,2),
    mpg           NUMBER(10,2),
    engineSize    NUMBER(5,2),
    brand         STRING,
    age           INTEGER,
    fuel          STRING
);

-- Load option (a): Snowsight "Load Data" wizard into RV_DB.RAW.CAR_LISTINGS
--                  using output/clean_cars.csv, header = skip 1 row.

-- ---- 2. STAGING: typed, filtered, documented -------------------------------
CREATE OR REPLACE VIEW RV_DB.STAGING.STG_CAR_LISTINGS AS
SELECT
    model,
    brand,
    year,
    (2020 - year)                          AS age,          -- dataset year 2020
    price,
    mileage,
    NULLIF(engineSize, 0)                  AS engine_size,
    transmission,
    -- tidy fuel into the three analysed buckets
    CASE WHEN fuel IN ('Petrol','Diesel','Hybrid') THEN fuel ELSE 'Other' END
                                           AS fuel
FROM RV_DB.RAW.CAR_LISTINGS
WHERE price BETWEEN 500 AND 150000
  AND mileage BETWEEN 0 AND 200000
  AND year BETWEEN 1990 AND 2020;

-- ---- 3. MART: % retained vs each model's near-new baseline -----------------
-- baseline = median price of age<=1 cars for that model.
CREATE OR REPLACE VIEW RV_DB.MART.MODEL_BASELINE AS
SELECT model,
       MEDIAN(price) AS base_price
FROM RV_DB.STAGING.STG_CAR_LISTINGS
WHERE age <= 1
GROUP BY model;

CREATE OR REPLACE VIEW RV_DB.MART.FCT_RETENTION AS
SELECT s.model,
       s.brand,
       s.fuel,
       s.age,
       s.mileage,
       s.price,
       b.base_price,
       ROUND(s.price / b.base_price * 100, 1) AS pct_retained
FROM RV_DB.STAGING.STG_CAR_LISTINGS s
JOIN RV_DB.MART.MODEL_BASELINE    b USING (model)
WHERE b.base_price IS NOT NULL
  AND s.price / b.base_price * 100 BETWEEN 5 AND 120;

-- ---- 4. RV MATRIX in SQL: median % retained + n per (model, age 0-3) --------
-- low-confidence flag when n < 10, same rule as the Python version.
CREATE OR REPLACE VIEW RV_DB.MART.RV_MATRIX AS
SELECT model,
       age,
       ROUND(MEDIAN(pct_retained), 1) AS median_pct_retained,
       COUNT(*)                        AS n,
       (COUNT(*) < 10)                 AS low_confidence
FROM RV_DB.MART.FCT_RETENTION
WHERE age BETWEEN 0 AND 3
GROUP BY model, age
ORDER BY model, age;

-- quick sanity checks
SELECT 'rows in fact table' AS check, COUNT(*) FROM RV_DB.MART.FCT_RETENTION
UNION ALL
SELECT 'models in RV matrix', COUNT(DISTINCT model) FROM RV_DB.MART.RV_MATRIX;
