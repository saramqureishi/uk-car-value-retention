# UK Used-Car Value Retention: a one-page summary

**Question.** How fast do cars lose value, and do hybrids hold value better than
petrol and diesel? (The question the Graduate Residual Value Analyst role asks.)

**Data.** About 99,000 UK used-car listings across 9 brands, collected around
2020. **Important honesty note:** these are dealer *asking prices*, not the
auction or wholesale values a rental company actually realises when it sells a
fleet car. There is no original new-price field, so "value retained" here is a
**proxy**: each car's price as a percentage of the near-new (0 to 1 year old)
median price for the *same model*. I never call this "residual value".

**The baseline understates true depreciation (read this first).** My 100%
reference is the median price of 0 to 1 year old listings. In practice that
bucket is dominated by roughly 1-year-old cars with about 5,000 miles, not
brand-new ones: age-0 listings actually sit *above* the baseline (for example a
0-year Yaris shows about 120%). So the proxy **misses the large first-year drop
from the new showroom price**, which industry sources put at roughly 20 to 30%
in the first year
([Auto Trader, car depreciation explained](https://www.autotrader.co.uk/content/guides/car-depreciation-explained)).
Every retention figure here is therefore measured from a near-new, not a
brand-new, starting point, and **understates total depreciation for a buyer of
new cars**. For a fleet buyer this matters: the real loss from new is bigger
than these numbers show.

**The per-model table does not control for trim or spec.** Within one model, the
near-new and older listings can contain different spec mixes, which skews the
comparison. For example the Audi Q7 shows over 100% retention at 2 years, not
because it holds value, but because its 2-year-old listings skew towards
higher-spec versions than its near-new baseline. The regression partly handles
this through engine size, but the simple per-model table does not, so I treat
extreme or above-100% values as a data-quality flag, not a finding.

---

## What I found

**1. Cars lose roughly 8 to 10% of value per year from age alone** (holding the
model constant): petrol about -9.8%/yr, diesel about -10.0%/yr, hybrid about
-7.6%/yr.

**2. Including the miles a car actually does each year, total loss is higher.**
Using the data-derived typical mileage (about 7,000 miles/yr) the total is about
-13%/yr for petrol and diesel and about -11%/yr for hybrid. For a **rental-style
20,000 miles/yr**, total loss rises to roughly **-19%/yr** (petrol/diesel) and
**-17%/yr** (hybrid). Fleets that drive cars hard lose value faster, which
matters for how long you should hold a car.

**3. The "hybrids hold value better" headline is mostly a brand effect.** Raw
numbers suggested hybrids retained about 14 percentage points more than petrol
at 3 years. But hybrids in this data are mostly Toyotas, which hold value
whatever the fuel. Once I compared like-for-like (same model) and controlled for
it in a regression, **about 60% of that gap disappeared**. The remaining
hybrid edge (about +2.2%/yr) was **not statistically clear**: resampling by
model (not by row, which would overstate confidence) gave a 95% interval of
about **-0.3% to +3.6%**, which crosses zero.
**So this data cannot confirm a hybrid advantage, even though the point estimate
still slightly favours hybrids.**

**4. The transparent regression wins; the black box does not.** Forecasting
value at 4 to 5 years from younger cars (error measured on % retained, lower is
better), all methods reported, nothing hidden:

| Method | Error (percentage points) |
|---|---|
| Naive baseline, global average loss | 10.2 |
| Naive baseline, per-model average loss (stronger) | 10.5 |
| Hedonic regression, at typical mileage (fair comparison) | **9.0** |
| Hedonic regression, at each car's actual mileage | 8.1 |
| Gradient-boosted model (black box) | 10.4 |

On a fair footing (regression run at typical mileage, so it uses only the same
age-based information as the baseline) the regression beats the per-model
baseline by about 14%. The black-box gradient-boosted model does **not** beat
the baseline, so the transparent regression is the one to use. For a brand-new
model the data had never seen, error rose to about 13 points (the fair
unseen-model case); for a model seen only when young it was about 8.

**5. Decision-ready output.** I built an RV matrix (model x age 0 to 3, %
retained, with sample sizes and low-confidence cells flagged) and a procurement
ranking. I checked rank stability by bootstrapping, so picks are presented as
*consistently strong* rather than as precise percentages. For a 2-year hold the
**Yaris** was a robust top pick in its segment (ranked first in about 96% of
bootstrap resamples); the **A3** (about 70%) and **Kona** (about 61%) were
consistently strong but less certain, so I would not over-state them.

**Reconciling the two retention numbers (they look contradictory but aren't).**
The matrix shows these strong models keeping about 88% at 2 years, while the
regression implies a fleet average of about 81% at 2 years (age-only). The
7-point gap is consistent with the matrix figure being for deliberately *good*,
value-holding models, whereas the regression figure is the average across *all*
models including fast depreciators, so good models sit above it. The matrix also
reflects each car's actual mileage, while the regression holds mileage fixed.
Rule of thumb: quote the **matrix** for "which model should we buy", and the
**regression** for "typical fleet depreciation per year". (The forward-test
section uses the hedonic regression as the primary predictor; it beat a
per-model naive baseline by about 23%, while a black-box gradient-boosted model
did not, so the transparent model is the one to use.)

---

## What has changed since 2020 (why this is a baseline, not today's truth)

This dataset is a 2020 snapshot, and the market moved a lot afterwards:

- Used prices **spiked sharply in 2021 to 2022** on supply shortages. ONS
  identified second-hand cars among the largest contributors to transport
  inflation in that period
  [ONS, used-car / consumer price work](https://www.ons.gov.uk/economy/inflationandpriceindices/articles/usingautotradercarlistingsdatatotransformconsumerpricestatisticsuk/july2023),
  and Auto Trader's index reported used prices up roughly 30%+ year on year
  around the 2022 peak
  [Auto Trader analysis](https://www.autotraderinsight-blog.co.uk/auto-trader-insight-blog/used-car-prices-analysis-april).
- Prices then **cooled and softened** over 2023 to 2025, with Auto Trader
  reporting an extended run of year-on-year declines before stabilising.
  [Auto Trader market data, via Motor Finance](https://www.motorfinanceonline.com/news/uk-used-car-market-may/)
- **Used EV values fell notably.** As of a December 2024 Auto Trader figure, the
  average used EV was priced around 10% lower year on year.
  [Auto Trader, cost of motoring 2025 (Dec 2024 data)](https://www.autotrader.co.uk/content/news/cost-of-motoring-in-2025)
  By May 2025, Auto Trader reported that 3 to 5 year old used EVs had become
  cheaper than their petrol equivalents.
  [Auto Trader market data, via Motor Finance (May 2025)](https://www.motorfinanceonline.com/news/uk-used-car-market-may/)

Because this dataset has only 6 pure electric cars, I make **no EV claims from
the data itself** and rely only on the cited published figures above.

*Content from the cited sources was rephrased for compliance with licensing
restrictions.*

---

## How I'd extend it
Pull a current dataset to test the EV question properly; validate the proxy
against published trade/auction values; and ask the team which holding periods
and mileage bands they actually plan to, so the matrix matches real fleet policy.
