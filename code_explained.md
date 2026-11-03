# How the code works

Two scripts, no simulation framework, only numpy and matplotlib:

| File | What it does | Output |
| --- | --- | --- |
| `lidar_eba.py` | the model: datasheet values, 4 small functions, a results table | printed table, `lidar_eba.png` |
| `figures.py` | the three slide visuals, built on the functions of `lidar_eba.py` | `fig_beams_250m.png`, `fig_k_distribution.png`, `fig_ranges.png` |

```
python lidar_eba.py     # table + plot
python figures.py       # slide figures
```

The question the code answers: **for an object of size W × H at distance R with reflectivity ρ, what is the probability that the lidar gets at least 5 returns from it in one frame?** Then: up to which distance is that probability ≥ 99 %?

---

## 1. `lidar_eba.py`, top to bottom

### Inputs (the constants at the top)

```python
LIDAR = "InnovizTwo (ROI)"
DTH = np.radians(0.1)               # horizontal angular resolution [rad]
DTV = np.radians(0.05)              # vertical angular resolution [rad]
R0, RHO0, P0 = 210.0, 0.10, 0.90    # range spec: R0 at RHO0 with detection probability P0
R_MAX = 300
FPS = 20
```

- **Lidar block**: the only lidar-specific part. To change the lidar, change these lines and rerun both scripts.
- `R0, RHO0, P0` is the datasheet sentence "210 m @ 10 % reflectivity, 90 % true positives per pixel" turned into three numbers.
- **Scenario block** (`R_REQ = 250`, `K_MIN = 5`, `CONF = 0.99`, `OBJECTS`): the requirement and the objects as flat W × H rectangles.
- `ALPHA = 0`: default weather, clear air (the datasheet conditions).
- `WEATHER`: three conditions, each as (visibility, share of driving time). `ALPHAS` turns the visibility into α (step 5).
- `C = -ln(1 - P0) · R0² / RHO0`: the one calibrated constant, explained in step 2.

### Step 1: `beam_counts(size, R, dth)` – how many beams hit one side of the object

At distance R, neighbouring beams are `R · dth` metres apart (small-angle approximation). A side of length `size` therefore spans

  L = size / (R · dth) beam spacings.

L is not a whole number, and whether you get ⌊L⌋ or ⌊L⌋+1 beams depends on where the beam grid happens to fall relative to the object's edge. If that position is uniformly random, the probabilities are:

- ⌊L⌋ + 1 beams with probability frac(L)
- ⌊L⌋ beams with probability 1 − frac(L)

The function returns both counts and both probabilities.

> Pedestrian, 250 m, width 0.5 m: spacing = 250 × 0.001745 = 0.436 m, L = 1.15 → 1 column (85 %) or 2 columns (15 %).
> Height 1.8 m with 0.218 m spacing: L = 8.25 → 8 rows (75 %) or 9 rows (25 %).

### Step 2: `p_beam(R, rho)` – probability that one beam that hits gives a return

```python
return 1 - np.exp(-C * rho / R**2 * np.exp(-2 * alpha * R))
```

- **Physics:** for an object larger than the laser spot, the echo power is proportional to ρ / R² (twice as far → a quarter of the signal).
- **Model:** p = 1 − exp(−C · ρ/R²). Weak echo → p ≈ 0; strong echo → p → 1.
- **Calibration:** C is chosen so that p(210 m, 10 %) = 0.90, the datasheet point. Solving 1 − exp(−C·ρ0/R0²) = P0 gives `C = -ln(1 - P0) · R0² / ρ0`.
- `exp(-2·alpha·R)`: light travels to the target and back through fog/rain. With `ALPHA = 0` this factor is 1.

> At 250 m, 10 %: C·ρ/R² = 2.303 × (210/250)² = 1.625 → p = 1 − e^(−1.625) = **0.803**

### Step 3: `p_at_least(k, n, p)` and `p_detect(w, h, R, rho)` – the statistics

`p_at_least` is the binomial tail written out:

  P(K ≥ k) = 1 − Σ_{i<k} C(n,i) · pⁱ · (1−p)ⁿ⁻ⁱ

That's the probability of at least k successes in n independent coin flips with success probability p.

`p_detect` combines steps 1–3. It loops over the 2 × 2 possible beam counts (horizontal ⌊L⌋ or ⌊L⌋+1, times vertical ⌊L⌋ or ⌊L⌋+1), computes `p_at_least(5, n, p)` for each, and weights them by their probability (the law of total probability).

> Pedestrian, 250 m, 10 %, p = 0.803:
>
> | beams n | weight | P(K ≥ 5 given n) |
> | --- | --- | --- |
> | 1 × 8 = 8 | 0.85 × 0.75 = 0.64 | 0.947 |
> | 1 × 9 = 9 | 0.85 × 0.25 = 0.21 | 0.982 |
> | 2 × 8 = 16 | 0.15 × 0.75 = 0.11 | 1.000 |
> | 2 × 9 = 18 | 0.15 × 0.25 = 0.04 | 1.000 |
> | **total** | | **0.962** |

`expected_returns` is simply n · p (the average). It's used for the right-hand plot only. The verdict uses the probability, because an average of 7.6 can still mean "fails 4 % of the time".

### Step 4: `max_range(w, h, rho)` – the verdict

The function walks R from 10 m to `R_MAX` in 1 m steps, keeps the distances where `p_detect ≥ CONF` (99 %), and returns the largest one. If that distance is at least 250 m, the object passes.

### Step 5: weather, `ALPHAS` and `p_weighted`

Rain and fog scatter the light on its way to the object and back, so the echo is multiplied by exp(−2αR). We don't know α directly, but weather reports give the **visibility** V, and the standard conversion is

  α = 3.912 / V  (Koschmieder; 3.912 = −ln 0.02, the 2 % contrast a human eye still sees)

| Condition | Visibility | α [1/m] | Share of time (our estimate) | p per beam at 250 m, 10 % |
| --- | --- | --- | --- | --- |
| clear | > 20 km (α = 0) | 0 | 88 % | 0.80 |
| rain / haze | 5 km | 0.00078 | 8 % | 0.67 |
| fog | 1 km | 0.0039 | 4 % | 0.21 |

All functions take `alpha` as an argument, so every result can be computed per condition. `p_weighted` averages P(K ≥ 5) over the three conditions with the shares as weights (the law of total probability again):

  P_weighted = 0.88 · P_clear + 0.08 · P_rain + 0.04 · P_fog

> Pedestrian at 250 m: 0.88 · 0.962 + 0.08 · 0.803 + 0.04 · 0.047 = **0.913**

Simplifications: 905 nm light is treated like visible light (the Koschmieder formula is for visible light; the difference is small next to our other uncertainties); wet roads, spray and a wet sensor window are ignored; the shares are rough estimates, not HungaroMet statistics.

### `__main__`

1. Prints p at 250 m, then for each object and two reflectivities (10 %, 50 %): E[K] at 250 m, P(K ≥ 5) at 250 m, the 99 % range, and PASS/FAIL.
2. Prints the stopping distance at 130 km/h (0.5 s latency, 6 m/s² braking): v·t + v²/2a ≈ 127 m. It also prints how many frames are left between 250 m and that point.
3. Prints P(K ≥ 5) at 250 m and the 99 % range for each weather condition, plus the weighted P.
4. Plots P(K ≥ 5) versus distance, one panel per weather condition, saved as `lidar_eba.png`.

---

## 2. `figures.py`

It imports the model functions, so the figures always match the numbers.

- `fig_beams()`: draws the beam grid at 250 m as dots, the objects as rectangles at real scale, and counts the dots inside each rectangle. It shows one grid position; another position changes the counts by one row or column.
- `k_distribution()` + `fig_k()`: the full distribution P(K = k) for the pedestrian at 250 m, i.e. the same mixture of binomials as `p_detect`, but every k instead of only the tail. Red bars are K < 5. The small bump at 12–17 returns comes from the 15 % of frames where the pedestrian gets 2 columns.
- `fig_ranges()`: one bar per object with its 99 % range (from `max_range`), the 250 m requirement line and the stopping-distance zone.

---

## 3. Assumptions

| # | Assumption | Where | Matters? |
| --- | --- | --- | --- |
| 1 | Objects are flat rectangles facing the lidar, with the chosen sizes | `OBJECTS` | medium: the pedestrian's width (0.5 m) sets 1 vs 2 columns |
| 2 | Regular beam grid; the offset relative to the object is uniformly random, independently in H and V | `beam_counts` | low |
| 3 | A beam is a point: a beam either hits or misses, with no partial hits at the edges (beam divergence ignored) | `beam_counts` | low–medium for small objects |
| 4 | Echo ∝ ρ/R² (Lambertian target larger than the spot, facing the lidar) | `p_beam` | standard physics |
| 5 | **Shape of the detection curve** p = 1 − exp(−Cρ/R²) | `p_beam` | **high for the pedestrian** (see below) |
| 6 | Extrapolation from the 210 m datasheet point to 250 m | `C` | follows from 4 + 5 |
| 7 | Beams succeed or fail independently → binomial | `p_at_least` | medium; rain or a dirty window make failures correlated |
| 8 | Weather only through visibility (exp(−2αR)); shares 88/8/4 % are our estimate | `WEATHER` | high in fog; the weighted number depends on the shares |
| 9 | False positives (1 % per pixel) ignored | – | low for this question |
| 10 | Verdict per single frame, with a 99 % threshold (our choice); 5 returns is from the task | `CONF`, `K_MIN` | **high for the pedestrian** |

From the datasheet, **not** assumptions: the resolution, the 210 m range, the 90 % per beam, the frame rate.

---

## 4. How clear-cut is the math?

- **Exact, given the assumptions:** the geometry (step 1) and the statistics (step 3). The binomial tail and the averaging over beam counts are textbook probability, with no approximation and no simulation noise.
- **A modelling choice:** the curve p(R) in step 2. The datasheet fixes one point on it (210 m → 90 %); the shape between that point and 250 m is our choice.

How much the pedestrian verdict (dark, 250 m) moves when we change things:

| Variant | p per beam at 250 m | P(K ≥ 5) | 99 % range |
| --- | --- | --- | --- |
| **our model** | 0.80 | **96.2 %** | **235 m** |
| other curve shape: p = P0^((R/R0)²·ρ0/ρ) (speckle model) | 0.86 | 98.9 % | 248 m |
| datasheet value 80 % instead of 90 % | 0.68 | 82 % | 214 m |
| datasheet value 95 % instead of 90 % | 0.88 | 99.3 % | 254 m |
| threshold 95 % instead of 99 % | – | – | 253 m |
| threshold 99.9 % | – | – | 219 m |
| naive: "p = 90 % up to 210 m, 0 beyond" | 0 | 0 % | 210 m |

**Our choice:** we keep p = 1 − exp(−Cρ/R²). It has one constant, the datasheet fixes it, and it is the more cautious of the two shapes. The datasheet can't settle the shape: it has only one usable point. Its other numbers (side regions: 140 m @ 10 %, 175 m @ 50 %) don't follow ρ/R², so the 50 % results are probably optimistic; the 10 % results are anchored at 10 % and not affected.

**Reading:** cars and trucks pass and the tyre fails under every variant, so those verdicts are robust. The pedestrian (and motorcycle) sits **right at the edge**, so its verdict depends on modelling choices. The honest statement is: "dark pedestrians are borderline at 250 m; in our model they reach 99 % up to about 235 m".

---

## 5. Other ways to do it

- **Monte Carlo instead of formulas:** draw a random grid offset, count the beams, draw a Bernoulli per beam, and repeat 100 000 times. You get the same numbers with sampling noise. It's more flexible, for example for random object positions, sizes, or a distribution of reflectivities.
- **Poisson approximation:** K ≈ Poisson(n·p). Simpler, but too pessimistic here (pedestrian: 87 % instead of 96 %), because with p = 0.8 the binomial is much narrower than a Poisson.
- **A physical detection model:** model the signal-to-noise ratio (SNR ∝ ρ/R²) with Gaussian noise and a threshold, so p = Φ((SNR − T)/σ). It's more realistic but has two parameters, and the datasheet gives only one point. The false-positive rate (1 %) could pin down the threshold.
- **Reflectivity as a random variable:** instead of "10 % worst case", use a distribution of pedestrian clothing reflectivities and average over it. This gives a less conservative, "typical" answer.
- **Several frames:** require detection in k of m consecutive frames (as tracking does). Frames are correlated, so this needs a model of that correlation, or a conservative bound.
- **Simulation environment** (e.g. CARLA with a lidar sensor): ray-traced geometry, real shapes. Much more work, and it still needs the same detection-probability model.

To switch the lidar: change the lidar block at the top of `lidar_eba.py` (resolution, `R0`, `RHO0`, `P0`, `R_MAX`, `FPS`), then rerun `lidar_eba.py` and `figures.py`.
