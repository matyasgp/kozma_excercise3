# Q&A cheat sheet (for the answerer)

One page to have in hand during the Q&A. It does not assume any particular slide deck: the team's final slides may look different, but the numbers below come from the same model (`lidar_eba.py`). Longer answers: `docs/qa_guide.md`.

## Before the session
- **Get the final deck** from the team and check that its numbers match the table below. If it rounds differently (e.g. "96 %" instead of "96.2 %"), quote the deck's version so you don't contradict it.
- **Check whether the final deck shows weather.** If it doesn't, only bring up the rain/fog numbers when someone asks.
- **Check which verdict the deck states.** Ours: vehicles pass, dark pedestrians/motorcycles fall about 15 m short, small debris fails, fog fails everyone.

## How to answer (about 30 seconds each)
1. **Answer in one sentence.**
2. **Give one number.**
3. **Name the limitation**, if there is one.

For example: "The beam count varies because the grid doesn't line up with the object. For the pedestrian that means 8 to 18 beams. We assume the offset is uniformly random."

## The numbers (10 % reflectivity, 250 m)

| | Clear | Rain (5 km vis.) | Fog (1 km vis.) | 99 % range, clear |
|---|---|---|---|---|
| Per-beam p | 0.80 | 0.67 | 0.21 | – |
| Pedestrian 0.5 × 1.8 m | 96.2 % | 80 % | 5 % | **235 m** |
| Motorcycle 0.8 × 1.4 m | 95.7 % | 90 % | 9 % | 237 m |
| Car 1.8 × 1.5 m | 100 % | 100 % | 71 % | ≥ 300 m (fog: 221 m) |
| Truck 2.5 × 3.5 m | 100 % | 100 % | 100 % | ≥ 300 m (fog: 273 m) |
| Tyre 0.5 × 0.5 m | fails | fails | fails | 143 m |

- **Datasheet:** InnovizTwo, 0.1° × 0.05° (forward ROI), 210 m @ 10 %, 90 % true positives per pixel, 100 klx sunlight, 20 FPS.
- **Beam spacing at 250 m:** 44 cm × 22 cm, so the pedestrian gets 1 column (85 % of the time) or 2.
- **Pedestrian:** 7.6 returns on average, but only 96.2 % of frames have ≥ 5. "The average passes, the probability fails."
- **Stopping:** 127 m at 130 km/h (0.5 s latency, 6 m/s²).

## The ten most likely questions from other groups

Other groups solved the same task with a different lidar, so expect "why did you do it differently from us?" questions.

1. **"Where does your detection probability come from?"**
   The datasheet itself. Footnote 4 says 90 % true positives per pixel at 210 m on a 10 % target. We fit the one constant in p = 1 − exp(−Cρ/R²) to that point.

2. **"Why use a probability, not just the expected number of points?"**
   The average hides the bad frames. The pedestrian averages 7.6 returns, but 3.8 % of frames have fewer than 5. That gap is the whole point of the statistical model.

3. **"250 m is beyond the 210 m in the datasheet. Isn't that extrapolation?"**
   Yes, by 19 %, using the lidar equation (ρ/R²). Another common curve shape (the speckle model) gives 248 m instead of 235 m, so ours is the cautious one.

4. **"Why 99 %?"**
   It's our choice: at most 1 missed frame in 100. For the pedestrian, 95 % → 253 m (pass) and 99.9 % → 219 m. The verdict for vehicles and debris doesn't change.

5. **"Why does the number of beams vary?"**
   The beam grid falls randomly relative to the object's edges. A side gets one extra beam with probability equal to the fractional part of W/(R·Δθ). A Monte Carlo simulation confirms the formula: 96.19 % vs 96.18 %.

6. **"Are the beams really independent?"**
   No, that's a limitation. Rain or a dark jacket affects neighbouring beams together. Correlation would make the real result *worse*, so our numbers are optimistic.

7. **"The car sees about 68 frames before it must brake. Isn't 96 % per frame enough?"**
   It would be if the frames were independent: 99.85 % with two frames. They aren't: it's the same object, distance and weather. So we judge single frames and treat tracking as extra margin.

8. **"How did you model weather, and where do the 88/8/4 % shares come from?"**
   The beam's signal is weakened by e^(−2αR), with α = 3.912 / visibility (Koschmieder). The shares are our own estimate for Hungary, not official data. Any reasonable shares give a pedestrian result well below 99 % (87–95 %).

9. **"Why the InnovizTwo? / Would 0.05° × 0.05° pass?"**
   It's a series-production automotive lidar, and its datasheet states the detection probability explicitly. 0.05° × 0.05° is possible, but footnote 1 says it costs frame rate, field of view or range. *If* the range stayed the same, the pedestrian would pass (290 m).

10. **"So does it meet EBA or not?"**
    For vehicles, yes. For dark pedestrians and motorcycles it falls about 15 m short. For small debris and in fog, no. The bottleneck is the horizontal resolution, not the sensitivity. A fix would be a finer resolution or fusion with radar/camera.

## Traps to avoid
- **Car weighted 98.8 %.** It is *below* 99 %, all of it from fog. If asked, say: "In clear and rain the car passes; the weighted number is just context. The verdict is per weather condition."
- **"Return" means a point on the object,** not the multiple echoes per pulse from the lecture.
- **The weather shares** are not HungaroMet data. Say "our estimate".
- **The Volkswagen claim** ("selected by VW") is not verified. Don't use it.
- **Don't overstate precision.** Say "about 235 m in our model".

## If you don't know
"Good point, our model doesn't cover that. It would enter as [less signal → lower p / fewer beams → lower n / correlation → wider distribution]." Every effect maps onto one of the three steps: geometry, per-beam probability, statistics.
