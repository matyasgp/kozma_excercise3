# Speaker notes: InnovizTwo for EBA (5-minute pitch)

One section per slide in `presentation.pdf`: **what to say** (paste into the Google Slides speaker notes) and **background** (so everyone in the team can answer questions). The timing adds up to about 5 minutes.

---

## Slide 1: Title (~15 s)

**Say:**
> We evaluated whether the InnovizTwo lidar is good enough for Emergency Brake Assist on a highway car. Our requirement: detect an object at 250 m with at least 5 lidar returns.

---

## Slide 2: The lidar, InnovizTwo (~45 s)

**Say:**
> InnovizTwo is Innoviz's automotive-grade lidar for mass production. We use its forward configuration: in the central region, 30 by 9.6 degrees, where the lane ahead is, the beams are 0.1 degrees apart horizontally and 0.05 degrees vertically.
> The datasheet says it sees a dark, 10 % target at 210 m with 90 % true positives per pixel. That last number is exactly what our model needs, so we don't have to assume it.
> The picture shows what that grid means at 250 m: one beam every 44 cm horizontally and 22 cm vertically. A car gets 28 beams, a pedestrian only 9, a tyre 3.

**Background:**
- *Source:* InnovizTwo GMSL Series Production Datasheet v3.1 (2024), "Condor" configuration, the one for front-facing consumer cars ([PDF](https://levelfivesupplies.com/wp-content/uploads/2023/08/InnovizTwo-GMSL-Series-Production-Datasheet_v3.1-1.pdf)).
- *Reflectivity ρ*: the fraction of light an object reflects. Dark clothing or a tyre is about 5–10 %, a white car about 80 %. 10 % is the standard worst case in lidar datasheets.
- *"90 % true positives per pixel"* (datasheet note 4): at 210 m, 10 % reflectivity, 100 klx sunlight, 90 % of the beams that hit the target give a detection; 1 % false positives per pixel.
- *Why the ROI?* At 250 m the 30° × 9.6° ROI is about 130 m wide and 40 m tall, so everything in our lane and the neighbouring lanes is inside it. The side regions are coarser (0.2° × 0.05°, 140 m @ 10 %).

---

## Slide 3: Model, returns per frame are a random variable (~1 min 45 s, the core slide)

**Say:**
> Our model has three steps.
> **One, geometry:** how many beams hit the object? At distance R the beams are R times the angular resolution apart. The number of beams drops with 1 over R squared.
> **Two, each beam is a coin flip.** A beam that hits does not always come back: the echo has to beat the noise, and it fluctuates. The echo gets weaker with reflectivity over R squared. We fitted the one constant in the model to the datasheet: 90 % at 210 m on a 10 % target. At 250 m that becomes 80 % per beam.
> **Three, statistics:** n beams, each succeeding with probability p, so the number of returns K is binomially distributed. "At least 5 returns" therefore becomes a probability, P(K ≥ 5), and we require 99 %.
> The histogram is the dark pedestrian at 250 m. On average it gets 7.6 returns, which looks like a pass. But in almost 4 % of the frames it gets fewer than 5, so P(K ≥ 5) is only 96 %. **The average passes, the probability fails.**

**Background:**
- *Why does the beam count change?* The grid does not line up with the object's edges. The pedestrian is 0.5 m wide and the columns are 0.44 m apart, so it gets 1 column (85 % of the time) or 2 (15 %). Height 1.8 m / 0.22 m gives 8 or 9 rows. So n is 8, 9, 16 or 18. We model the grid offset as uniformly random.
- *Why ρ / R²?* For an object larger than the laser spot, the received power falls with distance squared and scales with reflectivity (the lidar equation for an extended target).
- *Why p = 1 − exp(−C·ρ/R²)?* A simple curve that is ≈ 0 for a weak echo and → 1 for a strong one, with a single constant C, fixed by the datasheet point (210 m, 10 %, 90 %). It's a modelling choice; near the datasheet point any reasonable curve gives similar values.
- *Binomial:* n independent yes/no trials with the same success probability. P(K ≥ 5) = 1 − [P(0) + … + P(4)], where P(k) = C(n,k)·pᵏ·(1−p)ⁿ⁻ᵏ.
- *The histogram* is exact (binomial, averaged over the possible beam counts), not a simulation. The bump at 12–17 returns is the 15 % of frames where the pedestrian gets 2 columns.

---

## Slide 4: Results, 10 % reflectivity, three weather conditions (~1 min 15 s)

**Say:**
> The probability of at least 5 returns over distance, for five dark objects, in three weather conditions. The dashed line is 250 m, the dotted line our 99 %.
> In clear weather, the datasheet conditions, cars and trucks stay at 100 %. Pedestrians and motorcycles drop below 99 % at about 235 m; at 250 m they are at 96 %. The tyre is hopeless beyond 140 m.
> Rain costs about 20 m. Fog with 1 km visibility is the real problem: even a car reaches 99 % only up to 221 m, and a pedestrian only up to 167 m.
> Weighted with how often each weather occurs in Hungary, by our estimate, a dark pedestrian at 250 m is detected in 91 % of the frames.

**Background:**
- *How weather enters:* the light travels to the object and back through the air, so the echo is multiplied by exp(−2αR). We get α from the visibility V with the standard formula α = 3.912 / V (Koschmieder): rain/haze V = 5 km, fog V = 1 km. Clear: α = 0, as in the datasheet.
- *Per-beam p at 250 m, dark target:* clear 0.80, rain 0.67, fog 0.21.
- *Weights 88 / 8 / 4 %:* our rough estimate, not an official statistic. Budapest has about 80 days a year with at least 1 mm of rain, but rain lasts a few hours, not all day; dense fog is mostly a winter thing. For real numbers: HungaroMet (met.hu) climate data.
- *Weighted P* = 0.88 · P_clear + 0.08 · P_rain + 0.04 · P_fog (law of total probability over the weather).
- Expected returns at 250 m (clear): car 22.8, truck 73.8, motorcycle 9.4, pedestrian 7.6, tyre 2.1.
- At 50 % reflectivity (bright clothing), pedestrians pass up to 289 m in clear weather.
- *Kinks in the curves* come from the beam count jumping between whole numbers as R changes.

---

## Slide 5: Conclusion (~1 min)

**Say:**
> Our verdict: InnovizTwo fulfils the EBA requirement for vehicles, but not for dark pedestrians and motorcycles. Those reach 99 % only up to about 235 m, 15 m short of 250 m. Small debris is reliable only to about 140 m. In dense fog not even a car is seen reliably at 250 m, so there the system has to slow down, just like a human driver.
> The bottleneck is not sensitivity but the 0.1-degree horizontal resolution: a narrow object only gets one or two beam columns.
> Limitations: we model objects as flat rectangles, assume beams fail independently, ignore false positives, and judge a single frame. At 130 km/h the car needs about 127 m to stop, so between 250 m and that point there are still 68 frames at 20 FPS. In practice the system gets many chances, but frames are correlated, so we don't count that as extra probability.

**Background:**
- *Stopping distance at 130 km/h:* v = 36 m/s; 0.5 s latency gives 18 m, and braking at 6 m/s² gives v²/2a ≈ 109 m. That is ≈ 127 m in total. From 250 m: (250 − 127)/36 ≈ 3.4 s, i.e. 68 frames at 20 FPS.
- *Why not multiply over frames?* The same object at almost the same distance gives strongly correlated frames (same grid position, same weather), so treating them as independent would overstate the margin.

---

## Likely questions

- **"250 m is beyond the 210 m datasheet range, isn't that extrapolation?"** Yes: we calibrate at 210 m and extend with the ρ/R² law. We say so; the ranges we report are model estimates.
- **"Why 5 returns?"** It's the requirement from the task: a perception stack needs a few points to form a cluster and classify it.
- **"What about the side regions?"** Coarser (0.2° × 0.05°) and only 140 m @ 10 %. For EBA in our lane the ROI is what matters.
- **"Why this curve shape for p?"** It's the simplest one with a single constant, fitted to the datasheet point. Another common shape (speckle model) gives 248 m instead of 235 m for the pedestrian, so ours is on the cautious side. The datasheet alone can't decide between them.
- **"Where do the weather weights come from?"** Our estimate, shown as such. The method doesn't depend on them: put in official HungaroMet numbers and rerun.
- **"Could another configuration fix the pedestrian?"** The datasheet says up to 0.05° × 0.05° can be configured (at the cost of frame rate or FoV). That doubles the columns; worth a sentence if asked.
