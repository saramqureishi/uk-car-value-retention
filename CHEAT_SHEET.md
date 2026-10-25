# Interview Cheat Sheet (plain English)
*For explaining the UK used-car value-retention project out loud. Read this a
few times. The goal is that you can say these things in your own words.*

---

## 30-second summary (say this if asked "tell me about the project")
"I analysed about 99,000 UK used-car adverts to look at how fast cars lose
value, and whether hybrids hold value better than petrol and diesel. The
interesting part was that the obvious answer turned out to be misleading, and
most of my work was about being honest about what the data could and couldn't
tell me."

---

## The data, and the big honesty caveat
- These are **asking prices** from car adverts around **2020**, not the prices a
  rental company actually gets at auction. So I call my value figure a **proxy**,
  never "residual value".
- My "100%" starting point is a roughly **1-year-old car**, not a brand-new one.
  So my numbers **miss the big first-year drop** (industry says about 20 to 30%).
  I'm upfront that this understates true depreciation from new.

*If they ask why it matters:* "A fleet buyer buys new, so the real loss is
bigger than my proxy shows. I'd want trade/auction data and new prices to do it
properly."

---

## The 5 findings, what each means, and likely questions

### Finding 1: Cars lose about 8 to 10% of value per year from age alone
**Means:** holding everything else equal, each extra year knocks about 8 to 10%
off. Including the miles a car does each year, it's more like 13% a year, and for
a hard-driven rental car (20,000 miles/yr) closer to 19%.
**Q: "How did you separate age from mileage?"**
A: "I used a regression that includes both, so the age figure is the effect of
age with mileage held fixed, and I could also add a realistic mileage on top."

### Finding 2: The "hybrids hold value better" story is mostly a brand effect
**Means:** raw numbers said hybrids kept about 14 points more value at 3 years.
But most hybrids in the data were Toyotas, which hold value anyway. When I
compared the same model petrol vs hybrid, about **60% of that gap disappeared**.
**Q: "So do hybrids hold value better?"**
A: "This data can't confirm it. The leftover difference was small and, once I
measured uncertainty properly, it wasn't statistically clear. The point estimate
slightly favours hybrids, but I wouldn't claim it as a finding."
**Q: "What do you mean by measuring uncertainty properly?"**
A: "Adverts for the same model are very similar, so I resampled whole models, not
individual rows. If you resample rows you fool yourself into thinking you're more
certain than you are. The honest interval crossed zero."

### Finding 3: A simple forecast is almost as good as a complex one, and a
### transparent regression beats a black box
**Means:** to predict a car's value a couple of years further on, I compared a
simple rule, my regression, and a machine-learning model. The machine-learning
"black box" did **not** beat the simple baseline. My regression did, by a modest
amount, and it's explainable.
**Q: "Why not just use the most accurate model?"**
A: "For this task the black box wasn't more accurate, and it's harder to explain
to a business. I'd rather use a transparent model people can trust and question."

### Finding 4: I tested it the hard, honest way
**Means:** instead of an easy random test, I trained on younger cars and
predicted older ones, which is the real forecasting job. I also tested on car
models the data had never seen (harder, and the error was bigger, as expected).
**Q: "Why is that harder test better?"**
A: "A random split lets near-identical adverts land in both training and testing,
which flatters the score. Forecasting forward in age is what the job actually
needs, so it's the honest test."

### Finding 5: I turned it into something a buyer can use
**Means:** I built a table of how much each model keeps after 1, 2, 3 years, with
the sample size shown and shaky cells flagged. And a ranking of the best models
to buy if you keep them 2 years. I checked how stable those rankings were.
**Q: "How confident are you in the top picks?"**
A: "The Yaris was a robust number one in its class, top in about 96% of my
resamples. The others were consistently strong but less certain, so I'd call them
strong rather than give a precise figure."

---

## The two numbers that look like they clash (be ready for this)
The model table says a strong car keeps about 88% at 2 years; my regression
average is about 81%. 
**Say:** "They answer different questions. 88% is for hand-picked strong models;
81% is the average across all models including the fast depreciators. Both are
right, I'd quote the model table for 'which car to buy' and the regression for
'typical fleet depreciation per year'."

---

## If they ask about the tools (don't bluff)
- "I cleaned and analysed the data in Python, built the outputs in Excel and a
  Tableau dashboard. I also designed an optional pipeline that lands the raw data
  in S3 and loads it into Snowflake with staging and mart SQL models, since I'm
  studying toward SnowPro Core."
- **Never say Avis uses any of these.** You don't know that.

## The one-liner that sums up your judgement
"My first answer looked impressive but was partly an illusion. The valuable part
was finding that out and being honest about it, which is what I'd want to do for
real pricing decisions."
