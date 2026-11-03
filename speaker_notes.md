# Speaker notes: Hesai AT512 for EBA (5-minute pitch)

One section per slide in `presentation.pdf`: **what to say** (paste into the Google Slides speaker notes) and **background** (so everyone in the team can answer questions). The timing adds up to about 5 minutes.

---

## Slide 1: Title (~15 s)

**Say:**
> We evaluated whether the Hesai AT512 lidar is good enough for Emergency Brake Assist on a highway car. Our requirement: detect an object at 250 m with at least 5 lidar returns.

---

## Slide 2: The lidar, Hesai AT512 (~45 s)

**Say:**
> The AT512 is Hesai's long-range automotive lidar, announced in 2024. It sees 300 m at 10 % reflectivity, i.e. a dark object, and has a very fine angular grid of 0.05 degrees, i.e. 2400 by 512 points per frame at 10 frames per second. The 120-degree field of view covers the adjacent lanes. The fine grid is the important property for us: the finer the grid, the more beams land on a small, distant object.
> One assumption: Hesai does not say how reliable the 300 m figure is. We assume it means 90 % detection probability, which is the usual industry convention.

**Background:**
- *Reflectivity ρ*: the fraction of light an object reflects back. Black clothing or a dark tyre is about 5–10 %, a white car about 80 %. 10 % is the standard "worst-case" number in lidar datasheets.
- *Angular resolution 0.05°*: neighbouring beams are 0.05° apart. 120° / 2400 columns = 0.05°, which checks out.
- *Frame rate 10 Hz*: not published, derived as 12.288 M points/s ÷ (2400 × 512) = 10 frames/s.
- Sources and open questions are listed in `README.md`.

---

## Slide 3: Model, returns per frame are a random variable (~1 min 45 s, the core slide)

**Say:**
> Our model has three steps.
> **One, geometry:** how many beams hit the object? At distance R the beams are R times 0.05 degrees apart, which is 22 cm at 250 m. A car, 1.8 by 1.5 m, is hit by about 57 beams. The number of beams drops with 1 over R squared.
> **Two, each beam is a coin flip.** A beam that hits does not always come back: the echo has to be stronger than the noise, and it fluctuates. The echo gets weaker with reflectivity over R squared. We fitted the one free constant to the datasheet: 90 % at 300 m on a 10 % target. That gives 96 % per beam at 250 m.
> **Three, statistics:** n beams, each succeeding with probability p, so the number of returns K is binomially distributed. The requirement "at least 5 returns" therefore becomes a probability, P(K ≥ 5), and we require 99 %.
> On the right, why this matters: a pedestrian at 350 m. Same person, same distance, but the returns change from frame to frame. On average 7.9 returns, which looks like a pass. But in 12 % of the frames there are fewer than 5. **The average passes, the probability fails.**

**Background:**
- *Why does the beam count change between frames?* The beam grid does not line up with the object's edges. An object 2.3 beam spacings wide gets 2 or 3 beams, depending on where the grid falls. We model that offset as uniformly random.
- *Why ρ / R²?* For an object larger than the laser spot, the received power falls with distance squared and scales with reflectivity (the lidar equation for an extended target).
- *Why p = 1 − exp(−C·ρ/R²)?* It's a simple curve that is ≈ 0 for a weak echo and → 1 for a strong one, with a single constant C. C is not a guess: it is fixed by the datasheet point (300 m, 10 %, 90 %). Near 250–300 m any reasonable curve through that point gives similar values.
- *Binomial:* n independent yes/no trials with the same success probability p. P(K ≥ 5) = 1 − [P(0) + … + P(4)], where P(k) = C(n,k)·pᵏ·(1−p)ⁿ⁻ᵏ.
- *The frame table* comes from a random draw (beam count and Bernoulli trials per beam); the 12 % and 7.9 are exact, computed from the full distribution.

---

## Slide 4: Results, 10 % reflectivity (~1 min 15 s)

**Say:**
> Left: the probability of at least 5 returns over distance, for five objects, all dark (10 %). The dashed line is 250 m. Pedestrian, motorcycle, car and truck stay at essentially 100 % at 250 m. Only the pedestrian starts dropping, beyond about 300 m.
> The exception is the tyre, or lost cargo of about half a metre: at 250 m it is only 49 %.
> Right: the expected number of returns, on a log scale, with the 5-return line. The tyre crosses it right at 250 m, and the average alone would call that borderline. The probability on the left shows it actually fails half the time.

**Background:**
- *Why does the tyre fail?* At 250 m it is only 2.3 × 2.3 beam spacings, so it gets 4, 6 or 9 beams. Half of the time it gets only 4, and 4 beams can never give 5 returns. It fails the same way at 50 % reflectivity: **resolution is the limit, not reflectivity.**
- *Why the drop of the tyre curve looks like straight segments:* the beam count jumps between integers as R changes; the probability of the higher count changes linearly with distance.

---

## Slide 5: Conclusion (~1 min)

**Say:**
> The AT512 fulfils the EBA requirement for all vehicles and for pedestrians at 250 m, even when they are dark. With 99 % confidence it detects pedestrians up to about 300 m, motorcycles up to 350 m, and cars and trucks out to its maximum range.
> Small debris is detected reliably only up to about 200 m, because too few beams hit it. That is a property of the resolution.
> Limitations: we model objects as flat rectangles, we assume beams fail independently (rain or a dirty sensor would make failures correlated), the 90 % behind the range spec is our assumption, and we judge a single frame. In practice, at 130 km/h, there are about 34 more frames before braking must start, so the real system has extra margin.

**Background:**
- *Stopping distance at 130 km/h:* v = 36 m/s; 0.5 s latency gives 18 m, and braking at 6 m/s² gives v²/2a ≈ 109 m. That is ≈ 127 m in total. From 250 m there are (250 − 127)/36 ≈ 3.4 s, i.e. about 34 frames at 10 Hz.
- *Why not count those frames as independent chances?* The same object at almost the same distance gives strongly correlated frames, so multiplying probabilities would overstate the margin. We mention it as qualitative margin only.

---

## Likely questions

- **"Where does the 90 % come from?"** Assumption: Hesai does not publish it. If it were lower (say 50 %), C gets smaller and p at 250 m drops from 0.96 to about 0.63. Vehicles still pass easily; the pedestrian's 99 % range shrinks. Change `P0` in `lidar_eba.py` to show this live.
- **"Why 5 returns?"** It's the requirement from the task: a perception stack needs a few points to form a cluster and classify it.
- **"What about rain or fog?"** `ALPHA` in the script adds atmospheric attenuation exp(−2αR). We left it at 0 (clear weather).
- **"Is 0.05° really the resolution?"** One Hesai listing says 0.1°. With 0.1° there are 4× fewer beams; check before the presentation (see `README.md`).
