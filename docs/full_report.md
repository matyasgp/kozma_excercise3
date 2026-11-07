# Exercise 3: the full report

**InnovizTwo for Emergency Brake Assist: a statistical lidar performance model**

This is the complete record of the project: what the task was, how the work went, every decision and why it was made, the full model with derivations and worked examples, all results, every check, every assumption and its effect, and what is still open. Read it once from start to end and you know everything the team knows.

Shorter documents for other uses:
- `docs/qa_cheatsheet.md`: one page for the Q&A.
- `docs/qa_guide.md`: answers sorted by question.
- `docs/derivation.pdf`: the maths as a typeset document.
- `docs/code_explained.md`: the code, line by line.

All numbers here were recomputed from `lidar_eba.py` on 2026-11-07.

---

## Contents

1. [The task](#1-the-task)
2. [How the work went](#2-how-the-work-went)
3. [Choosing the lidar](#3-choosing-the-lidar)
4. [The datasheet values we use](#4-the-datasheet-values-we-use)
5. [The model, step by step](#5-the-model-step-by-step)
6. [Weather](#6-weather)
7. [The verdict and the EBA context](#7-the-verdict-and-the-eba-context)
8. [All results](#8-all-results)
9. [How we know the numbers are right](#9-how-we-know-the-numbers-are-right)
10. [How robust the results are](#10-how-robust-the-results-are)
11. [Assumptions and limitations](#11-assumptions-and-limitations)
12. [Alternatives we considered](#12-alternatives-we-considered)
13. [Check against the lecture](#13-check-against-the-lecture)
14. [Comparison with last year's teams](#14-comparison-with-last-years-teams)
15. [Open issues](#15-open-issues)
16. [Files and how to rerun](#16-files-and-how-to-rerun)
17. [Glossary](#17-glossary)
18. [Sources](#18-sources)

---

## 1. The task

From slide 2 of the course deck *Lidar Performance – Statistical modelling* ("Select and Model"):

- Form a team of 3–5 people.
- Choose an **automotive-grade lidar provider** and, from them, a **high-end lidar** for a car driving on highways.
- Decide whether its performance meets the **Emergency Brake Assist (EBA)** requirements:
  - **250 m detection range**
  - **at least 5 returns per object**
- Do it as a **statistical analysis**, in any programming language.
- **Pitch the results in 5 minutes.**

The rest of that deck (slides 3–118) holds earlier years' solutions. We worked from slide 2 only and read the old solutions afterwards, just for comparison (section 14).

**How we read the requirement.** "Detection range 250 m with ≥ 5 returns" means: an object at 250 m must produce at least 5 measured points in a frame. A single return is random, so we turned the requirement into a probability: **P(K ≥ 5) ≥ 99 % at 250 m**, where K is the number of returns from the object in one frame. The 99 % is our choice (sections 5.4 and 10).

---

## 2. How the work went

The work in order, with the reason for each change.

1. **Setup.** We read the task slide and agreed on the approach: no simulator, a small closed-form model that every team member can follow by hand. Python with numpy and matplotlib only (scipy wasn't installed, and writing the binomial tail out is clearer anyway).

2. **First model: Hesai AT512.** We first chose the AT512 (300 m at 10 %, 0.05° × 0.05°). Result: everything passed except small debris. Two problems:
   - **No official datasheet.** Hesai publishes no AT512 datasheet; the numbers came from a press release and news articles. A Hesai listing even showed conflicting values (0.1° × 0.1°, 250 m).
   - **The detection probability was our assumption.** We assumed 90 %; nothing in the sources said it.

3. **First slides.** An 8-slide beamer draft, cut to **5 slides** (the task/requirements slide was dropped) to fit 5 minutes. The repo `matyasgp/kozma_excercise3` was created, and from then on every change was pushed.

4. **Making the statistics visible.** The first draft hid the statistics. We added the key message, **"the average passes, the probability fails"**, and a histogram of the number of returns K.

5. **Looking for an official datasheet.** We compared five lidars with public documents (section 3) and **switched to InnovizTwo**. Its datasheet states the detection probability explicitly: "True Positives = 90 % per pixel" at 210 m, 10 % reflectivity. That turned our one key assumption into a published number. The verdict changed from "everything passes" to **"vehicles pass, dark pedestrians and motorcycles don't"**.

6. **Assumptions and robustness.** We wrote `code_explained.md` and tested the sensitivity: a different curve shape, a different datasheet value, a different threshold. The vehicle and debris verdicts never change; pedestrian and motorcycle are borderline.

7. **The curve-shape question.** Can we decide which detection curve is right? No: the datasheet has one usable point. The other values don't help (section 5.2). Decision: **keep the simplest curve** (one constant), which is also the more cautious of the two we tried.

8. **Weather.** Three conditions (clear, rain, fog) plus a weighted result for Hungary, added without changing the core maths: one extra factor e^(−2αR).

9. **Derivation.** `derivation.tex/pdf` gives the maths and a reason for every parameter.

10. **Lecture check.** Kozma's Lecture 3 (Lidar Sensors) supports the approach: its example datasheet uses the same "range at 10 %, 100 klx, POD > 90 %" convention (section 13). No changes needed.

11. **Last year's work.** 13 teams. Ours is the most complete; last year's InnovizTwo team reached a different verdict for reasons we can explain (section 14). No changes needed.

12. **Final check.** It found five wording issues on the slides, all listed in `note.md` and section 15. They are not fixed yet: the code is frozen while teammates work on it.

13. **Q&A preparation.** The Q&A guide, 10 backup slides, a Monte Carlo check and extra sensitivity numbers. All computed by importing the model, without changing it.

14. **Repo cleanup.** Files moved into `slides/`, `docs/` and the local-only `sources/`; the code is unchanged.

15. **Team split.** The teammates built their own final presentation in a different form, with the same underlying calculations. One person (the answerer) takes the questions, at least one from each other group. Hence the cheat sheet and this report.

---

## 3. Choosing the lidar

### Candidates

| Lidar | Document | Range at 10 % | Detection probability stated? | Resolution | Frame rate |
|---|---|---|---|---|---|
| **InnovizTwo** (Innoviz) | Production datasheet v3.1, © Innoviz 2024 (hosted by distributor Level Five Supplies) | **210 m** (forward ROI), 140 m (sides) | **Yes: 90 % true positives per pixel**, 1 % false positives, 100 klx | ROI 0.1° × 0.05°, sides 0.2° × 0.05° | 20 FPS |
| MicroVision IRIS | Datasheet on MicroVision's CDN | 200 m (280 m max) | Yes: > 90 % PoD, 0.1 % false alarms | 0.12° × 0.05° | 1–30 Hz |
| Seyond Falcon K2 Pro | Seyond datasheet (distributor) | 250 m (500 m max) | Yes: PoD > 90 % at 100 klx | 0.2° × 0.24°, ROI 0.1° × 0.1–0.15° | 10 FPS |
| Hesai AT128P | User manual from Hesai's own site | 210 m | No | 0.1° × 0.2° | 10 Hz |
| Valeo SCALA 3 | Product web page only | 200 m | No | 0.05° × 0.05° | 10 fps |
| Hesai AT512 (first choice) | Press release only | 300 m | No | 0.05° × 0.05° (disputed) | 10 Hz (derived) |

Ruled out besides: Ouster OS2 (industrial rotating lidar, not automotive-grade) and Aeva Atlas (marketing figures only).

### Why InnovizTwo

1. **The datasheet states our key parameter.** "True Positives = 90 % per pixel" is exactly the per-beam probability p in our model.
2. **It's an automotive series-production lidar** with a detailed datasheet and separate numbers per region of the field of view.
3. **The result is interesting.** Its 210 m is below the 250 m requirement, so the statistics decide the verdict instead of just confirming it.

**Downsides, stated openly:** 250 m means extrapolating 19 % beyond the datasheet point. And the verdict is no longer a clean pass.

**Runner-up:** the Seyond Falcon K2 Pro (90 % at exactly 250 m), but it's the roadside/V2X version of an automotive lidar.

---

## 4. The datasheet values we use

Source: *InnovizTwo GMSL Series Production Datasheet v3.1* (2024), Condor (forward) configuration.
Link: https://levelfivesupplies.com/wp-content/uploads/2023/08/InnovizTwo-GMSL-Series-Production-Datasheet_v3.1-1.pdf
A local copy is in `sources/`, which is not in the repo because of copyright.

| Value | Datasheet | In the code |
|---|---|---|
| Angular resolution in the region of interest (ROI) | 0.1° (H) × 0.05° (V) | `DTH`, `DTV` |
| ROI size | 30° × 9.6° (centre of the field of view) | – |
| Range | "0.1°x0.05°: 210m @ 10% Reflectivity" | `R0 = 210`, `RHO0 = 0.10` |
| Detection probability | footnote 4: "True Positives = 90% per pixel" | `P0 = 0.90` |
| Frame rate | 20 FPS | `FPS = 20` |
| Detection range | 0.3–300 m | `R_MAX = 300` |
| Full field of view | 120° × 28.8° | – |
| Side regions | 0.2° × 0.05°, 140 m @ 10 %, 175 m @ 50 % | not used (section 5.2) |
| Wavelength | 905 nm | – |

**Footnote 4 in full (the conditions behind 210 m / 90 %):** 25 °C; 10 % Lambertian target; 100 klx ambient light; a defined scanning configuration; native vertical field-of-view setting; 0° roll/pitch; clear weather; no blockage on the window; normal power mode. True positives 90 % per pixel and false positives 1 % per pixel for long-range detection. False positives are configurable in firmware from 0.01 % to more than 10 %.

What each part means for us:
- **One pixel = one beam**, so 90 % per pixel = p(210 m, 10 %) = 0.9.
- **100 klx** is bright direct sunlight, the worst case (sunlight is noise). At night or under clouds the range is longer, so our clear-weather results are on the safe side.
- **"Clear weather"** is why our baseline uses α = 0. Rain and fog are our additions.
- **False positives (1 %)** are tied to the 90 %. A stricter setting lowers the 90 %, a looser one raises it. We ignore false positives (a stated limitation): they cause false braking, not missed objects.

**Footnote 1:** "Maximum resolution of 0.05°x0.05° can be configured across the entire FOV based on trade-offs between frame rate, FOV, range, and power consumption." This is behind the "why not 0.05°?" question (section 10).

**Why the ROI and not the whole field of view.** At 250 m the ROI is about 130 m wide (2·250·tan 15°) and 40 m tall: our lane and the neighbouring ones. Anything EBA must brake for at 250 m is inside it.

---

## 5. The model, step by step

There are two sources of randomness:
1. **Where the beam grid falls on the object.** This sets how many beams hit it.
2. **Whether each beam that hits actually returns.** Detection is a random event.

The model has four steps, plus weather (section 6).

### 5.1 Geometry: how many beams hit the object

The object is a flat rectangle, W wide and H high, facing the lidar at distance R. Neighbouring beams are Δθ apart in angle, so **R·Δθ apart in metres** (small-angle approximation; tan 0.1° and 0.1° in radians differ by about 1 part in a million).

At 250 m:
- horizontal spacing: 250 × 0.1° × π/180 = **0.436 m**
- vertical spacing: 250 × 0.05° × π/180 = **0.218 m**

A side of length W spans **L = W / (R·Δθ)** spacings. The geometric beam count is n = L_h · L_v, which **falls as 1/R²**.

**The random grid offset.** The grid doesn't line up with the object's edges. Say the beams sit at positions u + j·s (j = 0, 1, 2, …) with spacing s, and the offset u is uniform on [0, s). The beams inside [0, W] are those with u + j·s ≤ W.
- There are always ⌊L⌋ of them.
- There is one more if u < W − ⌊L⌋·s, which happens with probability (W − ⌊L⌋·s)/s = **frac(L)**, the fractional part of L.

So a side gets **⌊L⌋ + 1 beams with probability frac(L)**, otherwise ⌊L⌋. Check: the expected count is ⌊L⌋ + frac(L) = L exactly. Horizontal and vertical are independent, so there are **2 × 2 = 4 possible beam counts**, each with probability (horizontal prob.) × (vertical prob.).

**Beam counts at 250 m:**

| Object | W × H [m] | L_h | L_v | Geometric n | Possible columns (prob.) | Possible rows (prob.) |
|---|---|---|---|---|---|---|
| Pedestrian | 0.5 × 1.8 | 1.15 | 8.25 | 9.5 | 1 (85 %), 2 (15 %) | 8 (75 %), 9 (25 %) |
| Car | 1.8 × 1.5 | 4.13 | 6.88 | 28.4 | 4 (87.5 %), 5 (12.5 %) | 6 (12.5 %), 7 (87.5 %) |
| Motorcycle + rider | 0.8 × 1.4 | 1.83 | 6.42 | 11.8 | 1 (17 %), 2 (83 %) | 6 (58 %), 7 (42 %) |
| Truck (rear) | 2.5 × 3.5 | 5.73 | 16.04 | 91.9 | 5 (27 %), 6 (73 %) | 16 (96 %), 17 (4 %) |
| Tyre / lost cargo | 0.5 × 0.5 | 1.15 | 2.29 | 2.6 | 1 (85 %), 2 (15 %) | 2 (71 %), 3 (29 %) |

**The key insight:** at 250 m the pedestrian is almost always **one single column** of beams. The horizontal resolution is the bottleneck.

**Object sizes, and why:**
- Pedestrian 0.5 × 1.8 m: adult shoulder width and height.
- Car 1.8 × 1.5 m: the rear of a typical passenger car.
- Motorcycle with rider 0.8 × 1.4 m.
- Truck 2.5 × 3.5 m: the EU width limit is 2.55 m and the height limit 4 m.
- Tyre / lost cargo 0.5 × 0.5 m.

Last year's teams used similar sizes.

### 5.2 Detection: does a beam that hits actually return?

A beam can hit the object and still give no return, because the echo is too weak compared with noise. We model this as a probability p(R, ρ), where ρ is the target's reflectivity.

**The formula:**

  p(R, ρ) = 1 − exp( −C · ρ / R² )

**Why this shape.** There are three reasons.
1. **Physics.** For a target larger than the laser spot, the received power is proportional to ρ / R² (the lidar equation for a Lambertian target). Twice as far means a quarter of the signal; half the reflectivity means half the signal.
2. **Statistics.** Model the detected signal events in one beam as Poisson-distributed with a mean λ proportional to the received power: λ = C·ρ/R². A beam "returns" if at least one event is detected: p = 1 − P(0 events) = 1 − e^(−λ). This fits photon-counting detectors (SPAD/SiPM, Lecture 3 slide 14).
3. **Simplicity.** It has exactly one free constant, and the datasheet gives exactly one point.

Behaviour: for a strong signal p → 1. For a weak signal p ≈ C·ρ/R², proportional to the signal.

**Calibration.** The datasheet says p(210 m, 10 %) = 0.90:

  1 − exp(−C · 0.1 / 210²) = 0.9  →  **C = −ln(1 − 0.9) · 210² / 0.1 = ln(10) · 441 000 ≈ 1.015 × 10⁶ m²**

A convenient form for 10 % targets: C·ρ/R² = ln(10) · (210/R)².

**At 250 m, 10 %:** ln 10 × (210/250)² = 2.303 × 0.7056 = 1.625 → p = 1 − e^(−1.625) = **0.803**.

**Per-beam p at other distances:**

| R [m] | 100 | 150 | 200 | 210 | 235 | 250 | 275 | 300 |
|---|---|---|---|---|---|---|---|---|
| p at 10 % | 1.000 | 0.989 | 0.921 | **0.900** | 0.841 | **0.803** | 0.739 | 0.676 |
| p at 5 % | 0.994 | 0.895 | 0.719 | 0.684 | 0.601 | 0.556 | 0.489 | 0.431 |

**Can the datasheet tell us which curve shape is right?** No. It has one usable point (210 m, 10 %, 90 %). We checked its other numbers:
- **ROI, 300 m at 50 %:** that's the sensor's maximum range, a cap rather than a measurement.
- **Side regions, 140 m at 10 % and 175 m at 50 %:** under ρ/R², 140 m at 10 % should become 140·√5 ≈ **313 m** at 50 %. The datasheet says 175 m, so no ρ/R² curve fits. Some other limit is involved there. Consequence: our 50 % results are probably **optimistic**. The 10 % results are unaffected, because they're anchored at 10 %.

**Another common shape (the speckle model):** p = P0^((R/R0)²·ρ0/ρ). It gives p(250 m) = 0.86 and a pedestrian 99 % range of 248 m instead of 235 m. **Ours is the more cautious one.** We kept the simpler and more cautious curve and report 235–248 m as the honest band when asked.

### 5.3 Statistics: the number of returns

Given n beams on the object, each returning independently with probability p, the number of returns is

  **K ~ Binomial(n, p)**,  P(K = k) = C(n, k) · pᵏ · (1 − p)ⁿ⁻ᵏ

  **P(K ≥ 5) = 1 − Σ_{i=0}^{4} C(n, i) · pⁱ · (1 − p)ⁿ⁻ⁱ**

The beam count n is itself random (four cases, section 5.1). The **law of total probability** combines them:

  P(K ≥ 5) = Σ over the 4 cases of  P(case) · P(K ≥ 5 | n_case)

**Worked example: dark pedestrian (10 %) at 250 m, clear weather, p = 0.803**

| Columns × rows | n | P(case) | P(K ≥ 5 given n) | Product |
|---|---|---|---|---|
| 1 × 8 | 8 | 0.854 × 0.749 = 0.640 | 0.947 | 0.606 |
| 1 × 9 | 9 | 0.854 × 0.251 = 0.214 | 0.982 | 0.210 |
| 2 × 8 | 16 | 0.146 × 0.749 = 0.109 | 1.000 | 0.109 |
| 2 × 9 | 18 | 0.146 × 0.251 = 0.037 | 1.000 | 0.037 |
| **Total** | | 1.000 | | **0.962** |

- Expected returns: E[K] = 9.5 × 0.803 = **7.6**, well above 5.
- Yet P(K ≥ 5) = **96.2 %**, so **3.8 % of frames (about 1 in 26) have fewer than 5 returns.**
- **The average passes, the probability fails.** This is the central message of the work.

**Worked example: tyre at 250 m.** 1 × 2 beams (60 % of the time), 1 × 3 or 2 × 2 (35 %), 2 × 3 (4 %). With 2–4 beams you can never get 5 returns, whatever p is. Only the 2 × 3 case has a chance, so P(K ≥ 5) = **2.8 %**. At 50 % reflectivity it is still only 4.3 %: **the tyre is limited by geometry, not by signal.**

**What "return" means.** A measured point on the object. It does *not* mean the multiple echoes per laser pulse (first/last/strongest) from Lecture 3, slide 16.

### 5.4 The verdict

For each object, step R from 10 m to 300 m in 1 m steps, compute P(K ≥ 5), and find the **largest R where P(K ≥ 5) ≥ 99 %**. Call it **R99**. The object passes if R99 ≥ 250 m.

300 m is the sensor's maximum range, so "≥ 300 m" means "passes up to the maximum range".

**Why 99 %:** EBA should miss an object in at most 1 frame in 100. It's our choice, and section 10 shows what other thresholds give.

**Why the curves have kinks:** whenever R crosses a value where L becomes a whole number, the possible beam counts change by one row or column.

---

## 6. Weather

**Model.** Light crosses the air twice (out and back), so the signal is multiplied by e^(−2αR) (Beer–Lambert law):

  p(R, ρ, α) = 1 − exp( −C · ρ/R² · e^(−2αR) )

**α from visibility (Koschmieder):** α = 3.912 / V. The 3.912 = −ln(0.02), because meteorological visibility is defined as the distance at which contrast drops to 2 %.

**Three conditions:**

| Condition | Visibility V | α [1/m] | Per-beam p at 250 m, 10 % | Why this value |
|---|---|---|---|---|
| Clear | > 20 km (α = 0) | 0 | 0.803 | the datasheet's conditions |
| Rain / haze | 5 km | 0.00078 | 0.667 | typical moderate rain |
| Fog | 1 km | 0.0039 | 0.205 | the WMO definition of fog is V < 1 km, so this is the *mildest* fog |

**Weighted result for Hungary:**

  P_weighted = 0.88 · P_clear + 0.08 · P_rain + 0.04 · P_fog

The shares are **our own estimate, not official HungaroMet data**. Budapest has about 76–84 days a year with ≥ 1 mm of rain, but rain lasts hours, not days. Fog is mostly a winter thing and its day counts vary a lot between sources. The method doesn't depend on the shares: change `WEATHER` in `lidar_eba.py` and rerun.

**How to read the weighted number.** It's an average over time ("how often in a typical year"), not a safety verdict. Safety is judged per condition: in fog the car must slow down, as a human driver would.

**Not modelled:** snow, spray from other vehicles, a wet or dirty sensor window, sun glare. They would enter the same way (an extra loss, or extra noise lowering C), but we have no datasheet numbers for them. Koschmieder is defined for visible light. For fog droplets (much larger than the 905 nm wavelength) the extinction is similar, but our rain case is optimistic because spray and a wet window are ignored.

---

## 7. The verdict and the EBA context

**Stopping distance** at 130 km/h (the Hungarian motorway limit):
- 130 km/h = 36.1 m/s
- System latency 0.5 s → 18 m
- Braking at 6 m/s² (firm, not full; a dry road allows 8–9 m/s²) → 36.1² / (2·6) = 109 m
- **Total ≈ 127 m**

At 100 km/h the total is about 78 m; at 140 km/h about 146 m.

**Time and frames.** Covering 250 m takes 6.9 s. From 250 m to the point where braking must start (127 m) takes 3.4 s, which is **68 frames** at 20 FPS.

**Why 250 m if the car stops in 127 m?** 250 m is the task's requirement. It leaves margin for tracking and classification, a partly blinded sensor, and higher speeds. We keep 250 m. Many teams last year quietly lowered it to 200 m or 150 m.

**The multi-frame argument.** If frames were independent, the pedestrian's chance of being seen in at least one frame would be 99.85 % with 2 frames and 99.994 % with 3. But frames are *not* independent: same object, almost the same distance, the same grid offset, the same weather. So we judge single frames and treat tracking as extra margin, not as probability we count.

**The verdict:**
- **Cars and trucks:** pass at 250 m in clear weather, even at 10 % reflectivity. Cars also pass in rain.
- **Dark pedestrians and motorcycles:** 99 % only up to about 235 m, about 15 m short. Bright ones (50 %) pass.
- **Small debris:** about 143 m. Only 2–3 beams hit it, so this is a geometry limit.
- **Fog (1 km visibility):** even cars only reach 221 m. The vehicle must adapt its speed.
- **The bottleneck** is the 0.1° horizontal resolution: narrow objects get 1–2 columns.

---

## 8. All results

### 8.1 Clear weather, 250 m

| Object | ρ | E[K] at 250 m | P(K ≥ 5) at 250 m | R99 | Verdict |
|---|---|---|---|---|---|
| Pedestrian | 10 % | 7.6 | **96.2 %** | **235 m** | fail |
| Car | 10 % | 22.8 | > 99.99 % | ≥ 300 m | pass |
| Motorcycle | 10 % | 9.4 | **95.7 %** | **237 m** | fail |
| Truck | 10 % | 73.8 | > 99.99 % | ≥ 300 m | pass |
| Tyre / cargo | 10 % | 2.1 | 2.8 % | 143 m | fail |
| Pedestrian | 50 % | – | > 99.99 % | 289 m | pass* |
| Motorcycle | 50 % | – | > 99.99 % | ≥ 300 m | pass* |
| Tyre / cargo | 50 % | – | 4.3 % | 143 m | fail |

\* probably optimistic, see section 5.2.

**Pedestrian, P(K ≥ 5) vs distance (10 %, clear):** 210 m 99.98 %, 235 m 99.1 %, 250 m 96.2 %, 275 m 81.0 %, 300 m 54.0 %.

### 8.2 Weather, 10 % reflectivity

| Object | P(K ≥ 5) at 250 m: clear / rain / fog | Weighted (88/8/4) | R99: clear / rain / fog |
|---|---|---|---|
| Car | 100 % / 100 % / **71 %** | **98.8 %** (below 99 %, all from fog) | ≥ 300 / 296 / **221 m** |
| Pedestrian | 96.2 % / 80 % / 5 % | 91.3 % | 235 / 215 / 167 m |
| Motorcycle | 95.7 % / 90 % / 9 % | 91.8 % | 237 / 232 / 184 m |
| Truck | 100 % / 100 % / 100 % | 100 % | ≥ 300 / ≥ 300 / 273 m |
| Tyre / cargo | 2.8 % / 1.5 % / 0 % | 2.6 % | 143 / 143 / 133 m |

**Denser fog, R99:** at 500 m visibility, car 175 m and pedestrian 144 m. At 200 m visibility, car 114 m and pedestrian 98 m.

### 8.3 Figures (written by the scripts into the repo root)

- `fig_beams_250m.png`: the beam grid at 250 m (44 cm × 22 cm) drawn over the objects at true scale.
- `fig_k_distribution.png`: the distribution of K for the dark pedestrian at 250 m. Red bars are frames with < 5 returns (3.8 %); the average is 7.6.
- `lidar_eba.png`: P(K ≥ 5) vs distance, one panel per weather condition, with lines at 250 m and 99 %.
- `fig_ranges.png`: R99 per object as bars, against the 250 m requirement and the 127 m stopping zone.

---

## 9. How we know the numbers are right

1. **Calibration check:** the code gives p(210 m, 10 %) = 0.900 exactly.
2. **Hand calculation:** the pedestrian table in section 5.3 (0.962) matches the code (0.9618). An earlier tyre hand calculation also matched.
3. **Monte Carlo simulation:** 200 000 frames, each with a random grid offset and random Bernoulli returns. Result: **P = 96.19 %, E[K] = 7.60**, against 96.18 % and 7.6 from the formula.
4. **Consistency:** slides, speaker notes, derivation, README, Q&A material and code all show the same numbers (96.2 %, 235 m, 0.803, 127 m, 68 frames, the weather table). Checked in the final review.

---

## 10. How robust the results are

**Everything for the dark pedestrian (10 %, clear):**

| Variant | Per-beam p at 250 m | P(K ≥ 5) at 250 m | R99 |
|---|---|---|---|
| **Our model** | 0.80 | **96.2 %** | **235 m** |
| Speckle curve shape | 0.86 | 98.9 % | 248 m |
| Datasheet 80 % instead of 90 % | 0.68 | 82 % | 214 m |
| Datasheet 95 % instead of 90 % | – | 99.3 % | 254 m |
| Threshold 95 % instead of 99 % | – | – | 253 m (pass) |
| Threshold 99.9 % | – | – | 219 m |
| Naive: "p = 90 % up to 210 m, 0 beyond" | 0 | 0 % | 210 m |
| Poisson approximation instead of binomial | – | 87 % | – |
| 5 % reflectivity | 0.56 | 59.5 % | 195 m |

**Minimum returns k (the task fixes 5; this shows the effect):** k = 3 → 274 m, 4 → 254 m, **5 → 235 m**, 6 → 221 m, 8 → 196 m.

**5 % reflectivity, all objects (R99):** pedestrian 195 m, motorcycle 227 m, car 282 m, truck ≥ 300 m, tyre 143 m.

**Weather shares (pedestrian, weighted P):** 80/12/8 % → 87 %; 88/8/4 % → 91 %; 95/4/1 % → 95 %. All below 99 %.

**0.05° × 0.05° configuration (footnote 1)**, assuming the range stayed the same: pedestrian 290 m (pass), tyre 194 m. The datasheet says the finer resolution costs frame rate, field of view, range or power, so we don't claim this.

**Conclusion:** the **vehicle and debris verdicts never change** under any variant. Only the dark pedestrian and motorcycle are borderline: just under or just over 99 %, depending on the choices. The honest statement is "dark pedestrians are borderline at 250 m: about 235 m in our model, 235–248 m depending on the curve shape".

---

## 11. Assumptions and limitations

Each with the direction it biases our result.

| # | Assumption | Effect on the result |
|---|---|---|
| 1 | Objects are flat rectangles facing the lidar | Real shapes (legs, rounded cars, windows) give fewer edge beams: **optimistic** |
| 2 | Beams are points (no beam divergence) | A wider beam can catch an edge it nominally misses: **pessimistic** for small objects |
| 3 | Beams are independent | Rain, dirt or a dark jacket affect neighbours together, which widens the distribution: **optimistic** |
| 4 | Detection curve 1 − exp(−Cρ/R²) | The other common shape gives 248 m: **cautious** |
| 5 | Extrapolation from 210 m to 250 m | Unavoidable with one datasheet point: **uncertain** |
| 6 | The random grid offset is uniform | Standard; the Monte Carlo confirms the maths |
| 7 | 10 % reflectivity as the worst case | Industry convention; 5 % is worse (section 10) |
| 8 | False positives ignored | They cause false braking, not misses: **neutral** for this question |
| 9 | Single-frame verdict | Tracking helps in practice: **cautious** |
| 10 | 100 klx sunlight (datasheet) | Night or overcast is better: **cautious** |
| 11 | Koschmieder weather; no spray or wet window | **Optimistic** for rain |
| 12 | Weather shares are our estimate | Any reasonable shares keep the pedestrian below 99 % |
| 13 | Surfaces face the lidar (no angle of incidence) | Tilted surfaces reflect less (Lambert's cosine law): **optimistic** |
| 14 | ρ/R² scaling also holds at 50 % | The datasheet side regions suggest not: 50 % results are **optimistic** |

---

## 12. Alternatives we considered

| Alternative | Why not |
|---|---|
| A simulator (CARLA etc.) | Far more work, and it still needs the same detection-probability model, which is the hard part. A closed form can be checked by hand. |
| Monte Carlo as the main method | Gives the same numbers (we used it as a check). The closed form is more transparent. |
| Poisson approximation for K | Too pessimistic: with p = 0.8 the binomial is much narrower than a Poisson (87 % vs 96 %). |
| A signal-to-noise model with a threshold | More physical, but it needs a second datasheet point we don't have. |
| Speckle curve shape | Equally reasonable; ours is simpler and more cautious. Reported as the band. |
| Expected returns only (what most teams did) | Hides the bad frames: the whole point of the work. |
| Counting multiple frames as independent | They aren't independent (section 7). |
| Reflectivity as a distribution | A good next step; the 10 % worst case is the convention. |
| The 0.05° × 0.05° configuration | Not the production forward configuration; it costs range or frame rate. |

**With more time we would:**
1. Measure p(R) at several distances, to fix the curve shape.
2. Use a reflectivity distribution for clothing instead of the 10 % worst case.
3. Model frame-to-frame correlation (k-of-m frames).
4. Use official HungaroMet weather shares.
5. Model real object shapes and beam divergence.

---

## 13. Check against the lecture

Kozma, Lecture 3 (Lidar Sensors), all 31 slides; Lectures 1–5 searched for EBA, reflectivity, probability and weather.

| Lecture slide | What it says | What it means for us |
|---|---|---|
| 13, target reflectivity models | Lambertian, specular, Gaussian, retroreflective | Our ρ/R² law assumes Lambertian targets, as datasheets do |
| 14, detectors | PIN, APD, SPAD, SiPM | Our "at least one detected event" model fits SPAD/SiPM detectors |
| 16, multiple returns | first/last/strongest echo per pulse | Different meaning of "return": ours means points on the object |
| 20, performance metrics | Example datasheet (Seyond Falcon): "250 m @ 10 % Lambertian, 100 klx, POD > 90 %", separate ROI resolution | **The same convention we calibrate on** |
| 21, performance testing | DIN SAE SPEC 91471 | Our model is a "paper version" of such a test |
| 22, performance limitations | resolution, beam divergence, environment, reflectance | We show resolution, reflectance and weather effects; beam divergence is ignored |

**Not in the lectures:** no detection-probability model, no binomial statistics, no weather formula, no EBA numbers. The 250 m and 5 returns come only from the exercise slide. Those parts rest on the derivation and the datasheet.

---

## 14. Comparison with last year's teams

13 teams in the course deck (slides 3–118, dated 2025).

- **Model:** almost all counted beams (size ÷ (R·Δθ)) and compared the count, or count × reflectivity, with 5. One deterministic number, no probability.
- **Probability:** only Team 05 (Luminar Iris vs AT512) used a per-beam p and P(≥ 5), without saying where p came from or modelling the beam-count variation. Team 3 wrote "≥ 99 % confidence" but never computed it.
- **Reflectivity:** several teams multiplied the hit count by ρ, which is not physical. Reflectivity changes *whether* a beam is detected, not *how many* hit.
- **Weather:** only mentioned as a next step, plus one team that applied a 20 % range loss for heat. Nobody modelled rain or fog or weighted by climate.
- **Requirement:** many lowered it to 200 m or 150 m. We keep 250 m.
- **Object sizes:** similar to ours. Their lost cargo was usually 0.2 × 0.2 m; ours is 0.5 × 0.5 m.

**Last year's InnovizTwo team (Team 1)** called it a pass: pedestrian "detectable under almost 200 m". The differences:
1. They used 0.05° × 0.05° everywhere (the configurable maximum, footnote 1); we use the forward configuration's 0.1° × 0.05°.
2. They judged at 200 m; we use the task's 250 m.
3. They compared averages; we use a probability.

All three differences push toward our stricter verdict.

**What sets our work apart:**
- A detection probability calibrated on the datasheet.
- Random beam counts.
- "The average passes, the probability fails".
- Weather with a climate weighting.
- A Monte Carlo check.

---

## 15. Open issues

Wording only; not applied because the team owns the final deck. Check whether the teammates' final presentation has them:

1. **Car weighted 98.8 %** is below 99 % but wasn't marked as a fail in our draft table. Answer if asked: "the verdict is per weather condition; the weighted value is context."
2. **"EBA met for vehicles"** is true only in clear weather (and rain for cars). In fog, cars reach 221 m.
3. **The detection formula on the model slide had no weather factor** (× e^(−2αR)).
4. **Team names** were "TBD" on our draft's title slide.
5. **`docs/code_explained.md` line 88** mentions a "right-hand plot" that no longer exists.

Also unverified: the claim that InnovizTwo was "selected by the Volkswagen Group" is from memory. Don't use it.

---

## 16. Files and how to rerun

```
Excercise3/
├── README.md, note.md
├── lidar_eba.py      the model (prints the tables, writes lidar_eba.png)
├── figures.py        slide figures (fig_beams_250m, fig_k_distribution, fig_ranges)
├── *.png             figures, written next to the scripts
├── slides/           presentation (5 slides), backup_slides (B1–B10), .tex + .pdf
├── docs/             full_report (this file), qa_cheatsheet, qa_guide, speaker_notes,
│                     code_explained, derivation (.tex + .pdf)
└── sources/          course deck + datasheet PDF (local only, not in the repo)
```

**To regenerate the numbers and figures:**

    python lidar_eba.py
    python figures.py

Requires numpy and matplotlib only.

**To change the lidar:** edit the lidar block at the top of `lidar_eba.py` (`DTH`, `DTV`, `R0`, `RHO0`, `P0`, `R_MAX`, `FPS`) and rerun.

**To change the weather shares:** edit `WEATHER` and rerun.

**PDFs:** `latexmk -pdf <file>.tex` inside `slides/` or `docs/`. Build files go to `build/`.

**Code functions:**
- `beam_counts`: step 1, the possible counts per side and their probabilities.
- `p_beam`: step 2, the per-beam probability, with weather.
- `p_at_least`: the binomial tail.
- `p_detect`: step 3, mixed over the 4 cases.
- `expected_returns`: n·p.
- `max_range`: step 4, R99.
- `p_weighted`: step 5, the weather average.

---

## 17. Glossary

- **EBA:** Emergency Brake Assist; the car brakes automatically for an obstacle ahead.
- **Return:** a measured point on the object (one beam that hit the object and was detected).
- **Beam / pixel:** one measurement direction of the lidar. The datasheet's "per pixel" = per beam.
- **Angular resolution Δθ:** the angle between neighbouring beams.
- **ROI (region of interest):** the central 30° × 9.6° of the InnovizTwo field of view, with the finer resolution.
- **Reflectivity ρ:** the fraction of light a surface reflects (10 % = dark clothing or paint).
- **Lambertian target:** a matte surface that scatters light evenly in all directions.
- **True positive / PoD:** probability of detection, here per beam.
- **False positive:** a return with no object behind it.
- **Binomial distribution:** the number of successes in n independent yes/no trials with probability p each.
- **Law of total probability:** P(A) = Σ P(case) · P(A | case).
- **R99:** the largest distance where P(K ≥ 5) ≥ 99 %.
- **α (extinction coefficient):** how fast air (rain, fog) weakens light, per metre.
- **Visibility V:** the distance at which contrast drops to 2 %; α = 3.912 / V.
- **Speckle model:** an alternative curve shape, p = P0^((R/R0)²ρ0/ρ).
- **Monte Carlo:** checking a result by simulating many random cases.
- **SPAD / SiPM:** photon-counting detectors used in lidars.

---

## 18. Sources

- **InnovizTwo GMSL Series Production Datasheet v3.1** (2024), © Innoviz Technologies: https://levelfivesupplies.com/wp-content/uploads/2023/08/InnovizTwo-GMSL-Series-Production-Datasheet_v3.1-1.pdf
- **Innoviz product page:** https://innoviz.tech/innoviztwo
- **Course deck** *Lidar Performance – Statistical modelling*, slide 2 (task); slides 3–118 (last year's teams).
- **Kozma, Lecture 3: Lidar Sensors**, slides 13, 14, 16, 20, 21, 22.
- **Climate of Budapest** (rain days): https://en.wikipedia.org/wiki/Climate_of_Budapest
- **HungaroMet climate data** (for official weather shares): https://www.met.hu/en/eghajlat/magyarorszag_eghajlata/eghajlati_adatsorok/Budapest/grafikonok
- **Lidar in adverse weather survey:** https://arxiv.org/pdf/2112.08936
- **Other candidate datasheets:**
  - MicroVision IRIS: https://cdn.microvision.com/resources/persistent/c2e60a8d9ae946038d7ea051298919b7b5bce81e/IRIS_Datasheet.pdf
  - Seyond Falcon K2 Pro: https://irp.cdn-website.com/237e2515/files/uploaded/Falcon+K2+Pro+LiDAR_Datasheet_EN_Public_ITS.pdf
  - Hesai AT128P manual: https://www.hesaitech.com/wp-content/uploads/2026/01/AT128P_User_Manual_A02-en-260110.pdf
