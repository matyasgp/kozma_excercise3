# Q&A guide for the final deck (InnovizTwo_EBA.pptx)

This guide follows the deck the team will present: 6 slides, dark theme, animated figures. Every number on those slides comes from the same model as ours. I checked them all against `lidar_eba.py`. What's new is the **animations**, and they invite their own questions. So this guide goes slide by slide: what the audience sees, what they're likely to ask, and what to answer. At the end are the traps, where the deck can be attacked.

Read this first. `docs/full_report.md` is the background.

---

## The deck in one minute

| # | Title | What's on it |
|---|---|---|
| 1 | InnovizTwo for Emergency Brake Assist | Animation: our car at 130 km/h approaches a dark pedestrian from 248 m to the braking point (127 m), one square per frame; "detected (K ≥ 5): 68/68" |
| 2 | The sensor | Key specs (0.1° × 0.05°, 210 m @ 10 %, 90 % per pixel, 20 FPS); animation of the beam grid over five objects at 250 m |
| 3 | Model | n formula, p formula, binomial; animation: one pedestrian frame on the left, a histogram building up over 1705 simulated frames on the right (P = 0.966 vs model 0.962) |
| 4 | Results | Animated P(K ≥ 5) vs distance, 50 → 300 m; at 250 m: car/truck > 99.99 %, pedestrian 96.2 %, motorcycle 95.7 %, tyre 3 % |
| 5 | Weather | The same curves, morphing through visibilities from clear to fog; per-beam p 0.80 / 0.67 / 0.21; the full weather table |
| 6 | Verdict + limitations | Five verdict bullets, four limitation bullets |

Key message, as the deck says it: **"The average passes, the probability fails."**

---

## Slide by slide

### Slide 1: the approach animation

**What it shows.** A dark pedestrian from 248 m down to the braking point at 127 m. 68 frames at 20 Hz, each frame one random draw. The counter ends at **68/68 detected**.

**Likely question: "Your animation detects the pedestrian in every frame. So doesn't it pass?"**
> "It's one random run. The per-frame chance is 96 % at 250 m and above 99 % from about 235 m inward, so on average only about 0.2 of the 68 frames miss. That's why the run looks perfect. But the requirement is per frame at 250 m, and there one frame in 26 misses. In practice, tracking over many frames helps a lot; we just don't count it as probability, because frames aren't independent."

Backup numbers: only 8 of the 68 frames are in the zone below 99 %. If the frames *were* independent, all 68 would be detected 79 % of the time.

**Likely question: "Why does the animation stop at 127 m?"**
> "That's where braking must start at the latest: 130 km/h, 0.5 s reaction, 6 m/s² braking: 18 m + 109 m."

**Likely question: "K = 32 at the end, but the pedestrian gets 9 beams?"**
> "Nine is at 250 m. Beams fall with 1/R², so at 127 m it's about 4× as many."

### Slide 2: the sensor and the beam grid

**What it shows.** Specs, plus the grid at 250 m over five objects with counts. In the animation the grid shifts, and the counts change (e.g. car 28 → 35).

**Likely question (easy to spot): "The figure shows 16 beams on the pedestrian, but the text says 9. And the wider motorcycle gets only 6?"**
> "That's the point of the animation: it depends on where the grid falls. A pedestrian is 1.15 beam columns wide at 250 m, so it gets 1 column 85 % of the time and 2 columns 15 % of the time. The figure shows the 2-column case: 2 × 8 = 16. The motorcycle is 1.8 columns, usually 2 but sometimes 1, which is the case shown. On average: pedestrian 9.5, motorcycle 11.8."

**Likely question: "Why the 0.1° × 0.05° region and not the full field of view?"**
> "At 250 m the 30° × 9.6° region is about 130 m wide, our lane plus the neighbours. Anything EBA must brake for at 250 m is in it. Outside it's 0.2° and only 140 m at 10 %."

**Likely question: "The datasheet says 0.05° × 0.05° is possible. Why not use it?"**
> "Footnote 1: the maximum resolution comes at the cost of frame rate, field of view, range or power. The production forward configuration uses 0.1°. If 0.05° kept the same range, the pedestrian would pass, at 290 m. The datasheet doesn't promise that."

**Likely question: "What does 90 % true positives per pixel mean exactly?"**
> "Footnote 4: at 210 m, on a 10 % Lambertian target, in 100 klx sunlight (bright sun, the worst case), 90 % of the beams that hit return, with 1 % false positives. One pixel is one beam, so that's our p at 210 m."

### Slide 3: the model

**What it shows.**
- **Left:** one frame. n = 8 beams, p = 0.80, one beam missed (red ×), K = 7.
- **Right:** a histogram that builds up frame by frame to 1705 frames: **P(K ≥ 5) = 0.966**, average 7.7, with "model: 0.962" in the corner.

**Likely question: "The simulation says 0.966 but the model says 0.962. Which is right?"**
> "The model. The simulation is a check with only 1705 frames, so its random error is about ±0.5 %. 0.966 is within that. With 200 000 frames we get 96.19 % against 96.18 %."

**Likely question: "Why does the histogram have two humps?"**
> "One or two beam columns. Most frames have 1 column, 8–9 beams, so the big hump is at 6–7 returns. About 15 % have 2 columns, 16–18 beams, so the small hump is at 12–15. The red bars, under 5 returns, all come from the one-column case."

**Likely question: "Why p = 1 − exp(−Cρ/R²)?"**
> "Three reasons:
> - **Physics:** the echo from a target larger than the beam spot is proportional to ρ/R².
> - **Statistics:** if detected signal events are Poisson, 'at least one event' gives 1 − e^(−λ).
> - **Practical:** it has one constant, and the datasheet gives exactly one point.
>
> C comes from 90 % at 210 m, 10 %. At 250 m that gives 0.80."

**Likely question: "250 m is beyond the datasheet's 210 m."**
> "Yes, a 19 % extrapolation. That's why we chose the cautious curve. The other common shape, the speckle model, gives 248 m instead of 235 m for the pedestrian. So our answer is 235–248 m depending on the curve: still short of 250 m, or just touching it."

**Likely question: "Why binomial, why 99 %?"**
> "Binomial: n beams, each independently returning with probability p, so the count of returns is Binomial(n, p). 99 % is our choice: at most one missed frame in 100. With 95 % the pedestrian would pass (253 m); with 99.9 % it reaches 219 m."

**Likely question: "Are the beams independent?"**
> "Not fully. Rain or a dark jacket affects neighbours together. Correlation makes things worse, so our results are on the optimistic side there. It's on the limitations list."

### Slide 4: results

**What it shows.** The curves are drawn while R runs from 50 to 300 m. At 250 m: car and truck > 99.99 %, pedestrian 96.2 %, motorcycle 95.7 %, tyre 3 %.

**Likely question: "Why do the curves have kinks?"**
> "Each time the object fits one more or one fewer row or column of beams, the possible beam counts change. The tyre's kinks at 143 m and 190 m are where it loses rows."

**Likely question: "Why does the tyre fail even though it's not dark?"**
> "It's 0.5 × 0.5 m, so 1 column × 2–3 rows: 2 to 6 beams at 250 m. With 4 beams or fewer you can never get 5 returns. At 50 % reflectivity it's still only 4 %. It's limited by resolution, not by darkness."

**Likely question: "Why do motorcycle and pedestrian look alike?"**
> "Both are narrow: 1–2 columns. The motorcycle is wider but shorter (6–7 rows instead of 8–9), and these effects roughly cancel. 237 m vs 235 m."

**Likely question: "What about bright objects?"**
> "At 50 % the pedestrian reaches 289 m. But the datasheet's side-region numbers suggest the gain from brightness is smaller than our ρ/R² assumes, so treat that as optimistic. The 10 % results aren't affected."

### Slide 5: weather

**What it shows.** The curves change as the visibility drops from very clear (tens of km) to 1 km. The numbers on the right are for the *current* frame of the animation. The table holds the three fixed conditions.

**Likely question: "How is weather modelled?"**
> "Light goes through the air twice, so the echo is multiplied by e^(−2αR). α comes from the visibility: α = 3.912 / V. That's Koschmieder's law; 3.912 is −ln(0.02), because visibility is defined as the distance where contrast drops to 2 %."

**Likely question: "Where do 88 / 8 / 4 % come from?"**
> "Our own estimate for Hungary, not official data. Budapest has about 80 rain days a year, but rain lasts hours, and fog is mainly in winter. Any reasonable shares keep the pedestrian below 99 %: 87–95 %."

**Likely question: "1 km fog, isn't that dense fog?"**
> "No, it's the mildest fog. The WMO defines fog as visibility below 1 km. At 500 m visibility a car is only reliable to 175 m."

**Likely question: "The slide says 'rain costs ~20 m', but the motorcycle loses only 5 m?"**
> "Right, ~20 m is the pedestrian (235 → 215 m). The motorcycle loses 5 m and the car 4 m. The pedestrian loses most because it's already at the edge with 1 column."

**Likely question: "Car weighted 98.8 %, that's below 99 %. Does the car fail?"**
> "It's all fog: 100 % in clear and rain, 71 % in fog. The weighted value is just how often in a typical year; the verdict is per condition. In fog, the car must slow down, like a human driver."

**Likely question: "Clear is labelled > 20 km visibility. Is that what you computed?"**
> "Clear means no attenuation at all, the datasheet's conditions. '> 20 km' just describes that air. At exactly 20 km the pedestrian would be at about 94 % instead of 96 %."

**Likely question: "Is Koschmieder valid for a 905 nm laser? What about snow, spray, a dirty window?"**
> "Koschmieder is defined for visible light. For fog the droplets are much larger than the wavelength, so 905 nm behaves similarly. Spray and a wet window are not modelled, which makes our rain case optimistic. Snow and dirt would enter the same way, as extra loss; we have no data for them."

### Slide 6: verdict and limitations

**Likely question: "So does it meet EBA or not?"**
> "In clear weather it does for vehicles. It doesn't for dark pedestrians and motorcycles: about 15 m short. It doesn't for small debris. In fog, not even for cars. The bottleneck is the 0.1° horizontal resolution, not the sensitivity."

**Likely question: "How would you fix it?"**
> "A finer horizontal resolution (0.05° would give the pedestrian 290 m if the range held), a second sensor, or fusion with radar or camera. Not more laser power: the pedestrian is limited by having 1 beam column."

**Likely question: "Why judge a single frame when there are 68?"**
> "Frames are strongly correlated: the same object, almost the same distance, the same grid position, the same weather. If they were independent, 2 frames would give 99.85 %. But we can't count that honestly, so the 68 frames are a margin, not a probability."

**Likely question: "Why ignore false positives?"**
> "They cause false braking, not missed objects, and our question is about missed objects. The datasheet's 90 % comes with 1 % false positives. A stricter false-positive setting would lower the 90 %."

**Likely question: "Why flat rectangles?"**
> "It's simple and transparent. Real shapes give fewer edge beams (optimistic). Real beams have a width and can catch an edge (pessimistic). They partly cancel."

---

## Traps in this deck (know these before you walk in)

1. **Title slide still says "Team: names TBD".** Not your problem in Q&A, but tell the team before the talk.
2. **The slide 6 title "EBA met for vehicles" is only true in clear weather.** Slide 6 itself says fog fails, so if challenged: "clear-weather verdict; fog is the next bullet."
3. **The car's weighted 98.8 % on slide 5 isn't marked as a fail.** Answer above.
4. **Slide 6 speaker notes say "in dense fog".** 1 km is the *mildest* fog. If you repeat the notes, say "fog with 1 km visibility", not "dense fog".
5. **Slide 2 figure: 16 pedestrian beams vs "9" in the text; motorcycle 6.** Answer above: it's one grid position.
6. **Slide 3: 0.966 vs 0.962.** Answer above: simulation noise.
7. **Slide 1: 68/68 detected.** Answer above: one random run, and 96 % applies only at 250 m.
8. **Slide 5: "rain costs ~20 m"** applies only to the pedestrian.
9. **The slide 3 formula has no weather factor;** slide 5 adds it. If asked: "the full formula has × e^(−2αR) inside, which is 1 in clear weather."
10. **Slide 2 says "on average a tyre 3".** The exact figure is 2.6. Fine to say "2 to 3".

---

## Numbers to know (match the deck's rounding)

| What | Say |
|---|---|
| Spacing at 250 m | 44 cm × 22 cm |
| Beams at 250 m (average) | car 28, pedestrian 9 (to 10), motorcycle 12, truck 92, tyre 2–3 |
| Per-beam p at 250 m | 0.80 clear, 0.67 rain, 0.21 fog |
| Pedestrian at 250 m | average 7.6 returns, P(K ≥ 5) = 96.2 %, about 1 frame in 26 misses |
| 99 % range (clear) | pedestrian 235 m, motorcycle 237 m, tyre ≈ 140 m (143), car and truck ≥ 300 m |
| Rain / fog 99 % range | pedestrian 215 / 167 m, car 296 / 221 m, truck – / 273 m |
| Weighted (88/8/4) | pedestrian 91.3 %, motorcycle 91.8 %, car 98.8 % |
| Braking at 130 km/h | 127 m (18 m reaction + 109 m braking), 68 frames from 250 m |
| Sensitivity, pedestrian | speckle curve 248 m; 95 % threshold 253 m; 99.9 % → 219 m; 4 returns 254 m; 6 returns 221 m; 5 % reflectivity 195 m |

## If you don't know

"Good point, our model doesn't include that. It would enter as fewer beams, a lower per-beam probability, or correlation between beams, and we'd expect it to make [the pedestrian] worse/better." Then stop. Don't guess numbers.
