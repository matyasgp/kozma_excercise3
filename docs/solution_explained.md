# The solution, step by step

This explains the whole solution from start to finish, in the same order as the presented deck (slide numbers in brackets). Each step says what we do, why, and what comes out. There are no questions here, just the explanation.

---

## Step 1. The question (slide 1)

The task: take a high-end automotive lidar and decide whether it is good enough for **Emergency Brake Assist (EBA)** on a highway car. EBA needs two things:

- the object must be seen at **250 m**, and
- it must give **at least 5 returns**: 5 measured lidar points on the object.

Five points is roughly what a perception system needs to say "there is something here" rather than "that was noise".

The task asks for a **statistical** analysis. That's the key idea of the solution: **the number of returns is not a fixed number, it's random.** The same pedestrian at the same distance gives 9 returns in one frame and 3 in the next. So the question "does it get 5 returns?" has no yes/no answer. The right question is:

> **How likely is it that one frame gives at least 5 returns?**

We demand that this probability is **at least 99 %** at 250 m: at most one missed frame in a hundred. The 99 % is our choice.

The animation on slide 1 shows this in action. Our car drives at 130 km/h towards a dark pedestrian. Every square is one lidar frame (20 per second), and in each frame the returns are drawn at random.

---

## Step 2. The lidar and the one number that matters (slide 2)

We chose the **InnovizTwo** by Innoviz, an automotive-grade lidar built for series production. We use its official datasheet (v3.1, 2024, forward "Condor" configuration). The values we take from it:

- **Angular resolution 0.1° × 0.05°.** In the central region of interest (30° × 9.6°, the area straight ahead), neighbouring beams are 0.1° apart horizontally and 0.05° vertically.
- **210 m at 10 % reflectivity, with 90 % true positives per pixel.** This is the crucial line. It says: aim a beam at a dark target (10 % reflectivity, like dark clothing) 210 m away, and it comes back 90 % of the time. Footnote 4 adds the conditions: 100 klx sunlight (bright sun, the hardest case, because sunlight adds noise), clear weather, and a 1 % false-positive rate.
- **20 frames per second.**

Why this lidar: most datasheets give a range but don't say how reliably it is achieved. The InnovizTwo datasheet states the **per-beam detection probability** outright. That is exactly the input our model needs, so we don't have to invent it. (We first tried a Hesai AT512, but it has no official datasheet and no detection probability, so we switched.)

Why the forward region: at 250 m the 30° × 9.6° region is about 130 m wide and 40 m tall. Our lane and the neighbouring lanes are inside it, so anything EBA must brake for at 250 m is seen with this resolution.

---

## Step 3. Geometry: how many beams hit the object? (slides 2 and 3)

Lidar beams fan out from the sensor on a fixed angular grid. The further away, the further apart they are. At distance R, two neighbouring beams are

  **spacing = R · Δθ** (Δθ in radians)

At 250 m:
- horizontally: 250 m × 0.1° = **0.44 m** between beams
- vertically: 250 m × 0.05° = **0.22 m** between beams

We model each object as a flat rectangle facing the car, W wide and H high. The number of beams that fit on it is

  **n = (W / horizontal spacing) × (H / vertical spacing)**

Because both spacings grow with R, **n falls with 1/R²**. Twice as far means a quarter of the beams.

At 250 m, on average:

| Object | Size W × H | Columns | Rows | Beams on average |
|---|---|---|---|---|
| Pedestrian | 0.5 × 1.8 m | 1.15 | 8.25 | **9.5** |
| Motorcycle with rider | 0.8 × 1.4 m | 1.83 | 6.42 | 11.8 |
| Car (rear) | 1.8 × 1.5 m | 4.13 | 6.88 | 28.4 |
| Truck (rear) | 2.5 × 3.5 m | 5.73 | 16.04 | 91.9 |
| Tyre / lost cargo | 0.5 × 0.5 m | 1.15 | 2.29 | 2.6 |

**First source of randomness: where the grid falls.** You can't have 1.15 columns. A pedestrian 1.15 spacings wide gets **1 column or 2**, depending on where the beam grid happens to sit relative to their edges. If that position is random, the chance of the extra column is exactly the fractional part:
- 2 columns with probability 0.15,
- 1 column with probability 0.85.

(The reason: the extra beam fits only if the first beam lands within the leftover 0.15 of a spacing at the edge.)

The same holds vertically: 8 rows (75 %) or 9 rows (25 %). So the pedestrian at 250 m is hit by **8, 9, 16 or 18 beams**, each with its own probability.

This is what the slide 2 animation shows. As the grid shifts, the counts jump: the pedestrian shows 16 beams in the frame where it happens to get two columns.

**The key observation:** at 250 m a pedestrian is almost always **a single vertical line of 8–9 beams**. The horizontal resolution is what limits it.

---

## Step 4. Detection: does a beam that hits actually come back? (slide 3)

A beam can hit the object and still produce no return. The echo has to be stronger than the noise, and its strength fluctuates from shot to shot. So each beam that hits is like a coin flip: it returns with probability **p**, and gives nothing with probability 1 − p.

**Second source of randomness: each beam is a coin flip.**

How does p depend on distance R and reflectivity ρ? Two ingredients:

1. **Physics.** For a target larger than the laser spot, the echo power is proportional to **ρ / R²** (the lidar equation). Half as reflective means half the echo; twice as far means a quarter of the echo.
2. **Statistics.** Think of the detector as counting signal events (photons), which arrive randomly with an average proportional to the echo power. The beam "returns" if at least one event is detected. For random (Poisson) events with average λ, the chance of at least one is 1 − e^(−λ).

Together:

  **p(R, ρ) = 1 − exp( −C · ρ / R² )**

This has **one unknown, C**, and the datasheet gives us exactly one point to fix it: p = 0.9 at R = 210 m, ρ = 10 %. Solving:

  C = −ln(1 − 0.9) · 210² / 0.1 ≈ 1.0 × 10⁶

Now we can compute p anywhere. At 250 m on a 10 % target:

  C · ρ / R² = 2.303 × (210/250)² = 1.625  →  **p = 1 − e^(−1.625) = 0.80**

So at 250 m each beam that hits a dark object comes back **80 %** of the time (90 % at 210 m).

| Distance | 150 m | 200 m | 210 m | 235 m | 250 m | 300 m |
|---|---|---|---|---|---|---|
| p (10 % target) | 0.99 | 0.92 | 0.90 | 0.84 | **0.80** | 0.68 |

A note on honesty: 250 m is beyond the datasheet's 210 m, so this is a 19 % extrapolation. We picked the simplest curve that fits the one point. Another common curve shape (the "speckle model") would give a slightly higher p and a pedestrian range of 248 m instead of 235 m. So ours is the cautious choice.

---

## Step 5. Statistics: the number of returns (slide 3)

Now combine the two steps. Given n beams on the object, each returning independently with probability p, the number of returns K is a count of successes in n coin flips. That's the **binomial distribution**:

  **K ~ Binomial(n, p)**,  P(K = k) = C(n, k) · pᵏ · (1 − p)ⁿ⁻ᵏ

The requirement "at least 5 returns" becomes

  **P(K ≥ 5) = 1 − [P(K=0) + P(K=1) + P(K=2) + P(K=3) + P(K=4)]**

But n is itself random (step 3). So we compute P(K ≥ 5) for each possible beam count and **weight each case by its probability** (the law of total probability).

### The worked example: dark pedestrian at 250 m (p = 0.80)

| Beams | How | Chance of this case | Chance of ≥ 5 returns | Contribution |
|---|---|---|---|---|
| 8 | 1 column × 8 rows | 0.854 × 0.749 = 0.640 | 0.947 | 0.606 |
| 9 | 1 column × 9 rows | 0.854 × 0.251 = 0.214 | 0.982 | 0.210 |
| 16 | 2 columns × 8 rows | 0.146 × 0.749 = 0.109 | 1.000 | 0.109 |
| 18 | 2 columns × 9 rows | 0.146 × 0.251 = 0.037 | 1.000 | 0.037 |
| | | | **Total** | **0.962** |

So **P(K ≥ 5) = 96.2 %**.

Compare that with the simple, non-statistical way: average beams × p = 9.5 × 0.80 = **7.6 returns on average**. 7.6 is comfortably above 5, so the simple way says "pass". But 3.8 % of frames, about **one in 26**, have fewer than 5 returns. That misses our 99 %.

> **The average passes, the probability fails.**

This is the central message of the whole solution, and the reason the task asks for statistics.

The slide 3 animation shows it:
- **Left:** a single frame: 8 beams, one of them misses (red ×), so K = 7.
- **Right:** a histogram of many simulated frames building up. The red bars, frames with fewer than 5 returns, all come from the one-column case.

The histogram has two humps:
- the big one at 6–7 returns: 1 column, the common case;
- a small one at 12–15 returns: 2 columns.

The simulated share converges to the model's 96.2 %. (A long check with 200 000 simulated frames gives 96.19 %.)

---

## Step 6. From one distance to a range: the verdict rule (slide 4)

We repeat step 5 for every distance from 10 m to 300 m, in 1 m steps, and for every object. That gives the curves on slide 4: **P(K ≥ 5) against distance**.

For each object we read off **R99**: the largest distance where P(K ≥ 5) is still at least 99 %. The object passes if R99 ≥ 250 m.

Why the curves look the way they do:
- **Far away they drop,** because both the number of beams (1/R²) and p fall.
- **They have kinks** wherever the object gains or loses a whole row or column of beams. The tyre, for example, kinks at about 190 m and 143 m, where it loses one possible row each time.

---

## Step 7. Results in clear weather (slide 4)

All for dark (10 %) objects in the datasheet's conditions:

| Object | P(K ≥ 5) at 250 m | 99 % range R99 | Verdict |
|---|---|---|---|
| Car | > 99.99 % | ≥ 300 m | **pass** |
| Truck | > 99.99 % | ≥ 300 m | **pass** |
| Pedestrian | 96.2 % | 235 m | **fail**, 15 m short |
| Motorcycle | 95.7 % | 237 m | **fail**, 13 m short |
| Tyre / lost cargo | 3 % | 143 m | **fail** |

Why each one comes out this way:

- **Car and truck:** 28 and 92 beams. Even at p = 0.80, 5 returns out of 28 is practically certain.
- **Pedestrian:** usually 1 column of 8–9 beams. With p = 0.80, getting at least 5 of 8 fails about 5 % of the time.
- **Motorcycle:** wider (usually 2 columns) but shorter (6–7 rows). These effects roughly cancel, so it ends up like the pedestrian.
- **Tyre:** 1 column × 2–3 rows, so 2 to 6 beams. With 4 beams or fewer, 5 returns is impossible no matter how good the detector. **This is a resolution limit, not a darkness limit:** at 50 % reflectivity the tyre still only reaches 4 %.

Bright (50 %) pedestrians and motorcycles would pass (289 m and ≥ 300 m). We treat that as optimistic, because the datasheet's side-region values hint that brightness helps less than ρ/R² suggests.

---

## Step 8. Weather (slide 5)

The datasheet assumes clear weather. Rain and fog absorb and scatter light on its way out and back, so the echo is weaker. We add one factor to the echo:

  **echo × e^(−2αR)**,  and so  p = 1 − exp( −C · ρ/R² · e^(−2αR) )

- The **2** is because light crosses the air twice.
- **α** (attenuation per metre) comes from the **visibility V** via Koschmieder's law: **α = 3.912 / V**. The 3.912 is −ln(0.02), because visibility is defined as the distance where contrast drops to 2 %.

Three conditions:

| Condition | Visibility | Per-beam p at 250 m |
|---|---|---|
| Clear | no attenuation (the datasheet conditions) | 0.80 |
| Rain / haze | 5 km | 0.67 |
| Fog | 1 km (the WMO threshold for fog, so the *mildest* fog) | 0.21 |

Results:

| Object | P(K ≥ 5) at 250 m: clear / rain / fog | Weighted | R99: clear / rain / fog |
|---|---|---|---|
| Car | 100 % / 100 % / 71 % | 98.8 % | ≥ 300 / 296 / 221 m |
| Pedestrian | 96.2 % / 80 % / 5 % | 91.3 % | 235 / 215 / 167 m |
| Motorcycle | 95.7 % / 90 % / 9 % | 91.8 % | 237 / 232 / 184 m |

The truck passes in all three; the tyre fails in all three.

What this shows:
- **Rain** costs the pedestrian about 20 m (235 → 215 m) and barely affects the others.
- **Fog is the real problem.** Even a car is reliable only to 221 m, so in fog the car must slow down, just like a human driver.

**The weighted result** combines the three conditions by how often they occur:

  P = 0.88 · P_clear + 0.08 · P_rain + 0.04 · P_fog

The shares (88 % clear, 8 % rain, 4 % fog) are **our own estimate for Hungary**, not official statistics. For a dark pedestrian this gives 91.3 %: over a typical year, about 91 % of frames at 250 m see the pedestrian with at least 5 returns. This is context, not the verdict; the verdict is per weather condition.

The slide 5 animation sweeps the visibility continuously from very clear down to 1 km, so you can watch the curves slide left as the air gets worse.

---

## Step 9. The verdict and why 250 m matters (slide 6)

**Stopping distance**, to put 250 m in context. At 130 km/h (36.1 m/s, the Hungarian motorway limit):
- 0.5 s system reaction → 18 m
- braking at 6 m/s² → 36.1² / (2 × 6) = 109 m
- **total ≈ 127 m**

Between 250 m and 127 m the car travels for 3.4 s, which is **68 frames** at 20 FPS. That's the slide 1 animation: it runs from 250 m to the braking point.

Those 68 frames are why the system works better in practice than one frame suggests: tracking gets many chances. But we **don't count them as extra probability**. Consecutive frames see the same object, at almost the same distance, with almost the same grid position and the same weather, so they are not independent tries. Our verdict is per single frame; the extra frames are a safety margin.

**The verdict:**
- **Cars and trucks:** EBA requirement met at 250 m in clear weather, even when dark.
- **Dark pedestrians and motorcycles:** 99 % only up to about 235 m, **15 m short**.
- **Small debris:** reliable only to about 140 m; only 2–3 beams hit it.
- **Fog (1 km visibility):** even cars only to 221 m, so speed must be adapted.
- **The bottleneck is the 0.1° horizontal resolution, not the sensitivity:** narrow objects get only 1–2 beam columns. A finer horizontal resolution would fix the pedestrian. The datasheet allows 0.05° at a cost in range or frame rate; if the range held, the pedestrian would reach 290 m.

---

## Step 10. What the model assumes (slide 6)

The limitations on the slide, and what each one does to the result:

- **Flat, frontal targets.** Real objects are rounded and have gaps (legs, windows). Probably slightly fewer beams in reality, so the model is slightly optimistic.
- **Independent beams.** In reality, rain, dirt on the window or a dark jacket affect neighbouring beams together. That makes bad frames more likely, so the model is optimistic here.
- **False positives ignored.** The datasheet's 90 % comes with 1 % false positives. False positives matter for false braking, not for missing an object, which is our question.
- **Single frame.** Cautious, as explained in step 9.

Others worth knowing:
- **Beams are treated as points.** A real beam has a width and can catch an edge. This works in the object's favour, mainly for small ones.
- **The detection curve beyond 210 m** is an extrapolation. The alternative shape gives 248 m instead of 235 m.
- **The 99 % threshold** is our choice. With 95 % the pedestrian would pass (253 m); with 99.9 % it reaches 219 m.
- **The weather shares** are our estimate. Any reasonable shares keep the pedestrian below 99 %.

The important point: under every variation we tried, **the vehicle and tyre verdicts never change.** Only the dark pedestrian and motorcycle move, between "just short" and "just reaching" 250 m. The honest summary is:

> **Dark pedestrians and motorcycles are borderline at 250 m: about 235–248 m depending on the curve shape. Vehicles pass clearly, small debris fails clearly, and fog defeats everyone.**

---

## The whole solution in five lines

1. **Geometry:** beams on the object = (W / R·Δθ_h) × (H / R·Δθ_v), with ±1 row or column depending on where the grid falls.
2. **Detection:** each beam returns with p = 1 − exp(−Cρ/R² · e^(−2αR)); C is fixed by the datasheet's 90 % at 210 m and 10 %.
3. **Statistics:** returns K ~ Binomial(n, p), averaged over the possible beam counts.
4. **Verdict:** R99 = the largest distance where P(K ≥ 5) ≥ 99 %, compared with 250 m.
5. **Result:** vehicles pass, dark pedestrians and motorcycles fall about 15 m short (the average passes, the probability fails), debris fails, and fog fails everyone.
