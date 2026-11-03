# Q&A guide: everything you might be asked

For whoever answers questions after the pitch. Backup slides for showing on screen: `slides/backup_slides.pdf` (B1–B10, referenced below as **→ B#**).

---

## 0. The whole story in 30 seconds

> We took the InnovizTwo, an automotive lidar in series production, and asked: does it get at least 5 returns from an object at 250 m? A lidar return is random. Each beam that hits the object comes back only with some probability, and the number of beams that hit depends on where the grid falls. So "5 returns" is a probability, and we required 99 %. We fitted the one free constant to the datasheet: 90 % per beam at 210 m on a 10 % target. In clear weather, cars and trucks pass. Dark pedestrians and motorcycles reach 99 % only up to about 235 m, and small debris only to about 140 m. In fog even cars fail at 250 m.

## 1. Numbers to know by heart (→ B1)

| What | Value |
| --- | --- |
| Resolution (forward region of interest, ROI) | 0.1° × 0.05° → beam spacing at 250 m: **44 cm × 22 cm** |
| Datasheet point | **210 m @ 10 %, 90 % true positives per pixel**, 100 klx sunlight |
| Per-beam p at 250 m, 10 % | **0.80** (clear), 0.67 (rain), 0.21 (fog) |
| Beams on target at 250 m (geometric) | pedestrian 9.5, motorcycle 11.8, car 28.4, truck 91.9, tyre 2.6 |
| Pedestrian at 250 m | n = 8, 9, 16 or 18; E[K] = **7.6**; P(K ≥ 5) = **96.2 %** |
| 99 % range, 10 %, clear | pedestrian **235 m**, motorcycle **237 m**, tyre **143 m**, car and truck ≥ 300 m |
| Weather, pedestrian P at 250 m | 96 % clear / 80 % rain / 5 % fog → weighted **91 %** |
| Fog, 99 % range | car **221 m**, truck 273 m, pedestrian 167 m |
| Stopping at 130 km/h | 0.5 s + 6 m/s² → **127 m**; from 250 m: 6.9 s, **68 frames** at 20 FPS |

---

## 2. The lidar and the datasheet

**Why InnovizTwo?**
It's automotive-grade, built for series production (announced as selected by the Volkswagen Group), and has a long-range forward ROI. Above all, its datasheet states the **per-pixel detection probability** (90 %) explicitly, which is the one number our model needs. We first had the Hesai AT512 but dropped it: there is no official datasheet with a detection probability.

**Where exactly does 90 % at 210 m come from?** (→ B2)
InnovizTwo GMSL Series Production Datasheet v3.1 (2024), Condor configuration, the line "0.1°x0.05°: 210m @ 10% Reflectivity" and its footnote 4: 10 % Lambertian target, 100 klx ambient light, clear weather, "True Positives = 90% per pixel and False Positives = 1% per pixel". The PDF is hosted by the distributor Level Five Supplies; the content is Innoviz's.

**Is that the same convention as in the lecture?**
Yes. Lecture 3, slide 20 shows a Seyond Falcon datasheet with "250 m @ 10 %, 100 klx sunlight, POD > 90 %". Same structure: a range at 10 %, under sunlight, with ≥ 90 % probability of detection.

**Why the ROI and not the whole FoV?**
At 250 m the ROI (30° × 9.6°) is about 130 m wide and 40 m tall: our lane and the neighbouring ones. Anything EBA must brake for at 250 m is inside it. Outside the ROI the resolution is 0.2° × 0.05° and the range only 140 m @ 10 %.

**The datasheet says 0.05° × 0.05° is possible. Why not use that?** (→ B9)
Footnote 1: the maximum resolution "can be configured ... based on trade-offs between frame rate, FOV, range, and power". The production forward configuration (Condor) uses 0.1° horizontally. *If* 0.05° × 0.05° kept the same range, the pedestrian would pass (290 m) and the tyre would reach 194 m. But the datasheet says range and frame rate pay for it, so we don't claim that.

**Last year a team also had InnovizTwo and said it passes.**
They assumed 0.05° × 0.05° everywhere and judged at 200 m, using expected returns only. We use the real forward configuration, the task's 250 m and a probability. Both differences push toward our stricter verdict.

**What does 100 klx mean?**
Bright direct sunlight, the worst case for a lidar, because sunlight adds noise. At night or on overcast days the range is longer, so our clear-weather results are on the safe side.

**What about the 1 % false positives?**
Ignored. They matter for false braking, not for missing an object. The datasheet says the false-positive rate is configurable from 0.01 % to above 10 %. Stricter settings would lower the 90 %, looser ones raise it. The 90 % holds together with 1 %.

---

## 3. The model, step by step

### Geometry (→ B3)

**How do you count beams?**
At distance R neighbouring beams are R·Δθ apart. A side of length W spans L = W / (R·Δθ) spacings. Horizontal × vertical gives n. It falls with 1/R².

**Why do beam counts vary?**
The grid doesn't line up with the object's edges. With a uniformly random offset, a side gets ⌊L⌋+1 beams with probability frac(L), otherwise ⌊L⌋. Derivation: the beams sit at u + j·s, with u uniform on [0, s); one extra beam fits if u < W − ⌊L⌋s, which happens with probability frac(L). Check: the average count is exactly L.

**Why is the pedestrian the hard case?**
It's 0.5 m wide and the columns are 0.44 m apart, so it gets **1 column (85 %)** or 2 (15 %). It is basically a single vertical line of 8–9 beams. The bottleneck is the horizontal resolution, not the sensitivity.

**Small-angle approximation OK?**
tan(0.1°) vs 0.1° in radians differ by about 1 part in a million. Yes.

**Why flat rectangles?**
A simple, conservative front view. Real shapes (legs, a rounded car) give fewer beams on the edges, and a wider beam can catch an edge it nominally misses. These effects partly cancel. It's a stated limitation.

**Where do the object sizes come from?**
Pedestrian 0.5 × 1.8 m (adult shoulder width, height). Car 1.8 × 1.5 m (rear of a typical passenger car). Motorcycle with rider 0.8 × 1.4 m. Truck 2.5 × 3.5 m (EU limit 2.55 m wide, 4 m high). Tyre / lost cargo 0.5 × 0.5 m. Last year's teams used similar values.

### Detection probability per beam (→ B4)

**Why p = 1 − exp(−Cρ/R²)?**
1. *Physics:* for a target larger than the laser spot, the received power is ∝ ρ/R² (lidar equation, Lambertian target).
2. *Statistics:* model the detected signal events in one beam as Poisson with mean λ ∝ power. A beam returns if at least one event is detected: p = 1 − e^(−λ). This fits photon-counting detectors (SPAD/SiPM, lecture 3, slide 14).
3. *Practical:* it has one free constant, and the datasheet gives exactly one point.

**How is C found?**
Solve p(210 m, 10 %) = 0.9: C = −ln(0.1) · 210² / 0.1. Then at R with ρ = 10 %: Cρ/R² = ln 10 · (210/R)². At 250 m: 2.303 × 0.706 = 1.625 → p = 1 − e^(−1.625) = **0.803**.

**Isn't 250 m an extrapolation beyond 210 m?**
Yes, by 19 %. That's why the curve shape matters, and why we report it as a model estimate. The alternative shape, the speckle model p = P0^((R/R0)²ρ0/ρ), gives 248 m instead of 235 m for the pedestrian. Ours is the cautious one.

**Can the datasheet tell which curve is right?**
No. It has one usable point. Its other numbers are no help: the 300 m at 50 % is just the maximum range, and the side region (140 m @ 10 %, 175 m @ 50 %) doesn't follow ρ/R² at all (ρ/R² predicts 313 m). You'd need measurements at several distances.

**Isn't a 5 % target more realistic for dark clothing?** (→ B7)
10 % is the industry-standard worst case. At 5 %: pedestrian 195 m, motorcycle 227 m, car 282 m, truck ≥ 300 m.

**Does p depend on the angle of incidence?**
Not in our model: we assume targets face the lidar. Tilted surfaces reflect less (Lambert's cosine law), another reason our numbers are a best case for the shape.

### Statistics (→ B5)

**Why binomial?**
n independent yes/no trials (beams), each succeeding with probability p, so K ~ Binomial(n, p). P(K ≥ 5) = 1 − Σ_{i=0}^{4} C(n,i) pⁱ (1−p)^(n−i).

**And with the varying beam count?**
Law of total probability: four cases (n = 8, 9, 16, 18 for the pedestrian), each weighted by its probability: 0.64 · 0.947 + 0.21 · 0.982 + 0.11 · 1 + 0.04 · 1 = **0.962**.

**Are beams really independent?**
Not fully. Rain, dirt on the window or a dark jacket affect neighbouring beams together. Correlation widens the distribution, so the real P(K ≥ 5) would be lower. Independence makes ours optimistic. It's a stated limitation.

**How do you know the code is right?** (→ B6)
Three checks:
1. Calibration: p(210 m, 10 %) = 0.900 exactly.
2. The hand calculation above matches the code.
3. A Monte Carlo simulation with 200 000 random grid offsets and binomial draws gives P = 96.19 % and E[K] = 7.60, against 96.18 % and 7.6 from the formula.

**Why not just the expected value?**
That's the point of the talk. The pedestrian has E[K] = 7.6 ≥ 5, but 3.8 % of frames have fewer than 5 returns. **The average passes, the probability fails.** Last year's teams mostly compared averages with 5.

**Why 99 %?**
Our choice: EBA should miss an object in at most 1 frame in 100. Sensitivity for the pedestrian: 95 % → 253 m (pass), 99 % → 235 m, 99.9 % → 219 m. A stricter safety argument would go even higher (ISO 26262 targets are per hour, not per frame).

**Why 5 returns?**
It's the task's requirement: a perception stack needs a few points to form a cluster and classify it. Sensitivity for the pedestrian (→ B7): 3 returns → 274 m, 4 → 254 m, 5 → 235 m, 6 → 221 m, 8 → 196 m.

**What does "return" mean here?**
A measured point on the object. Not the multiple echoes per pulse (first/last/strongest) from lecture 3, slide 16.

---

## 4. Results

**Why does the motorcycle behave like the pedestrian?**
It's 0.8 m wide → 1.83 columns, so 1 or 2 columns, and 6–7 rows. 99 % range 237 m.

**Why does the tyre fail so badly?**
0.5 × 0.5 m → 1 column × 2–3 rows → only 2–3 beams at 250 m. Even with p = 1 it can't reach 5. It is limited by geometry, not signal: 99 % only up to 143 m.

**Why are there kinks in the curves?**
Every time R crosses a value where L passes a whole number, the possible beam counts change.

**Bright objects?**
At 50 % reflectivity the pedestrian passes up to 289 m and the motorcycle ≥ 300 m. Caveat: the datasheet's side-region numbers suggest the gain from brighter targets is smaller than ρ/R² predicts, so treat the 50 % results as optimistic.

**What would fix the pedestrian?**
A finer horizontal resolution (e.g. 0.05°, see above), a second sensor, or fusion with radar/camera. The sensitivity isn't the bottleneck.

---

## 5. Weather (→ B8)

**How is weather modelled?**
The light passes through the air twice, so the signal is multiplied by e^(−2αR) (Beer–Lambert). α comes from the visibility V: α = 3.912 / V (Koschmieder). 3.912 = −ln 0.02, because visibility is defined as the distance at which contrast drops to 2 %.

**Why these three conditions?**
- **Clear:** α = 0, the datasheet's conditions.
- **Rain / haze:** V = 5 km, typical moderate rain.
- **Fog:** V = 1 km. The WMO definition of fog is visibility below 1 km, so this is the *mildest* fog.

**Denser fog?**
At V = 500 m the car reaches 99 % only to 175 m, the pedestrian to 144 m. At V = 200 m: car 114 m, pedestrian 98 m.

**Where do the 88 / 8 / 4 % shares come from?**
Our own estimate. Budapest has about 80 days per year with ≥ 1 mm of rain, but rain lasts hours, not days; fog is mostly a winter thing. They are not official HungaroMet data. Sensitivity: 80/12/8 % → pedestrian weighted 87 %; 95/4/1 % → 95 %. Below 99 % either way.

**Is a weighted average meaningful for safety?**
It's an average over time; it answers "how often in a typical year". Safety is judged per condition: in fog the system must slow down, just as a human driver would. The weighted number is context, not the verdict.

**Is Koschmieder valid at 905 nm?**
It's defined for visible light. For fog droplets (much larger than the wavelength) the extinction is similar at 905 nm. For rain, the bigger problems are a wet sensor window and spray, which we don't model. So rain is optimistic.

**What about snow, spray, sun glare, a dirty window?**
Not modelled. They'd go in the same way (extra loss, or extra noise lowering C), but we have no datasheet numbers for them.

---

## 6. EBA context (→ B10)

**Why 250 m if the car stops in 127 m?**
250 m is the task's requirement. It leaves margin for tracking and classification, for a sensor that's partly blinded and for higher speeds. At 140 km/h the stopping distance is 146 m; at 100 km/h 78 m.

**Where does 127 m come from?**
130 km/h (the Hungarian motorway limit) = 36.1 m/s; 0.5 s system latency → 18 m; braking at 6 m/s² (firm, not full; a dry road allows 8–9) → 109 m. Total 127 m.

**The system sees 68 frames before it must brake, so 96 % per frame is fine?**
If the frames were independent: 2 frames → 99.85 %, 3 frames → 99.994 %. But they are not: same object, almost the same distance, same grid offset, same weather. So we don't count that as extra probability, and we judge single frames. The honest statement: "in practice tracking gets several chances, but our verdict doesn't rely on it."

---

## 7. Comparison and method

**Why not a simulation (CARLA etc.)?**
It would still need the same detection-probability model, and that's the hard part. A closed form is transparent: every number can be checked by hand.

**Why not a Poisson approximation for K?**
With p = 0.8 the binomial is much narrower than a Poisson. Poisson would give 87 % instead of 96 %, i.e. it's too pessimistic.

**What would you do with more time?**
1. Measure p(R) at several distances to fix the curve shape.
2. A reflectivity *distribution* for clothing instead of the 10 % worst case.
3. Frame-to-frame correlation (k-of-m frames).
4. Official HungaroMet weather shares.
5. Real object shapes and beam divergence.

**How does this compare to last year?**
Most teams counted beams and compared the average with 5; several scaled the beam count by reflectivity, which isn't physical (reflectivity changes whether a beam is detected, not how many hit). One team computed a probability, but without a datasheet-calibrated p. None modelled weather.

---

## 8. If you don't know

- **"Good point, our model doesn't cover that.** It would enter as [extra loss / a different p / a different n]." Almost everything maps onto one of the three steps: geometry, p per beam, statistics.
- **Point to the sensitivity table (→ B7):** the vehicle and tyre verdicts don't change under any variant. Only the pedestrian and motorcycle are borderline, and we say so.
- **Never claim more precision than we have:** "about 235 m in our model; between 235 and 248 m depending on the curve shape".
