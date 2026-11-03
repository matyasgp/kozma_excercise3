"""Does the InnovizTwo meet the EBA requirements (>= 5 returns per object at 250 m)?

Model, one function per step:
  1. Geometry   - a flat W x H object at distance R covers W/(R*dth) x H/(R*dtv) grid cells.
                  The beam grid has a random offset, so a side of length L (in cells)
                  is hit by floor(L) beams, or by floor(L)+1 with probability frac(L).
  2. Detection  - each beam that hits returns with p(R, rho) = 1 - exp(-c * rho/R^2 * exp(-2*alpha*R)),
                  i.e. signal ~ rho/R^2 (target larger than the beam), with atmospheric loss alpha.
                  c is calibrated so that p(R0, rho0) = P0, the datasheet range spec.
  3. Statistics - beams are independent, so returns K ~ Binomial(n, p); P(K >= 5) = 1 - P(K <= 4).
  4. Verdict    - the largest R where P(K >= 5) >= 99 %, compared with the 250 m requirement.
  5. Weather    - alpha from visibility V (Koschmieder: alpha = 3.912/V) for clear, rain and fog;
                  the yearly figure is the time-weighted average P = sum_w share_w * P_w.

Datasheet (InnovizTwo GMSL Series Production Datasheet v3.1, 2024, Condor configuration):
ROI (central 30 x 9.6 deg, where the lane ahead is) 0.1 x 0.05 deg, 210 m @ 10 % reflectivity
with True Positives = 90 % per pixel (100 klx sunlight); 20 FPS; detection range 0.3-300 m.
"""
from math import comb

import numpy as np
import matplotlib.pyplot as plt

# --- lidar (datasheet) ---
LIDAR = "InnovizTwo (ROI)"
DTH = np.radians(0.1)               # horizontal angular resolution [rad]
DTV = np.radians(0.05)              # vertical angular resolution [rad]
R0, RHO0, P0 = 210.0, 0.10, 0.90    # range spec: R0 at RHO0 with detection probability P0
R_MAX = 300                         # max range [m]; model not trusted beyond it
FPS = 20

# --- requirement / scenario ---
R_REQ, K_MIN, CONF = 250.0, 5, 0.99
OBJECTS = {                         # name: (width, height) [m], front view
    "pedestrian": (0.5, 1.8),
    "car":        (1.8, 1.5),
    "motorcycle": (0.8, 1.4),
    "truck":      (2.5, 3.5),
    "tyre/cargo": (0.5, 0.5),
}
ALPHA = 0.0                         # atmospheric extinction [1/m]; 0 = clear air (datasheet conditions)

# --- weather: name: (visibility [m], share of driving time in Hungary) ---
# alpha = 3.912 / visibility (Koschmieder). Shares are our rough estimate, not official statistics
# (Budapest: ~80 days/year with >= 1 mm rain, but rain lasts only a few hours; fog mostly in winter).
WEATHER = {
    "clear": (np.inf, 0.88),
    "rain":  (5000.0, 0.08),
    "fog":   (1000.0, 0.04),
}
ALPHAS = {name: 3.912 / vis for name, (vis, _) in WEATHER.items()}

C = -np.log(1 - P0) * R0**2 / RHO0  # calibration of step 2


def beam_counts(size, R, dth):
    """Step 1, one side: possible beam counts and their probabilities (random grid offset)."""
    L = size / (R * dth)
    lo, frac = np.floor(L), L - np.floor(L)
    return (lo, lo + 1), (1 - frac, frac)


def p_beam(R, rho, alpha=ALPHA):
    """Step 2: probability that one beam hitting the object gives a return."""
    return 1 - np.exp(-C * rho / R**2 * np.exp(-2 * alpha * R))


def p_at_least(k, n, p):
    """Binomial tail P(K >= k) = 1 - sum_{i<k} C(n,i) p^i (1-p)^(n-i)."""
    n = int(n)
    return 1 - sum(comb(n, i) * p**i * (1 - p)**(n - i) for i in range(min(k, n + 1)))


def p_detect(w, h, R, rho, alpha=ALPHA, k=K_MIN):
    """Step 3: P(K >= k), averaged over the 2 x 2 possible beam counts."""
    (nh, ph), (nv, pv) = beam_counts(w, R, DTH), beam_counts(h, R, DTV)
    p = p_beam(R, rho, alpha)
    return sum(ph[i] * pv[j] * p_at_least(k, nh[i] * nv[j], p) for i in range(2) for j in range(2))


def expected_returns(w, h, R, rho, alpha=ALPHA):
    return w / (R * DTH) * h / (R * DTV) * p_beam(R, rho, alpha)


def max_range(w, h, rho, alpha=ALPHA, R=np.arange(10, R_MAX + 1)):
    """Step 4: largest distance where the object is still detected with probability >= CONF."""
    ok = np.array([p_detect(w, h, r, rho, alpha) >= CONF for r in R])
    return R[ok].max() if ok.any() else 0


def p_weighted(w, h, R, rho):
    """Step 5: P(K >= 5) averaged over the weather, weighted by its share of driving time."""
    return sum(share * p_detect(w, h, R, rho, ALPHAS[name]) for name, (_, share) in WEATHER.items())


if __name__ == "__main__":
    print(f"per-beam detection at {R_REQ:.0f} m: rho=10% -> {p_beam(R_REQ, 0.10):.3f}, "
          f"rho=50% -> {p_beam(R_REQ, 0.50):.3f}")
    print(f"\n{'object':12s} {'rho':>4s} {'E[K]@250':>9s} {'P(K>=5)@250':>12s} {'R(99%)':>7s}  verdict")
    for name, (w, h) in OBJECTS.items():
        for rho in (0.10, 0.50):
            r99 = max_range(w, h, rho)
            print(f"{name:12s} {rho:4.0%} {expected_returns(w, h, R_REQ, rho):9.1f} "
                  f"{p_detect(w, h, R_REQ, rho):12.4f} {r99:6d}m  {'PASS' if r99 >= R_REQ else 'FAIL'}")

    # context: how far ahead must EBA see? (130 km/h, 0.5 s system latency, 6 m/s^2 braking)
    v, t_lat, a = 130 / 3.6, 0.5, 6.0
    d_stop = v * t_lat + v**2 / (2 * a)
    print(f"\nstopping distance @130 km/h: {d_stop:.0f} m -> from {R_REQ:.0f} m there are "
          f"{(R_REQ - d_stop) / v * FPS:.0f} frames before braking must start")

    print(f"\nweather, {RHO0:.0%} reflectivity (per-beam p at {R_REQ:.0f} m: "
          + ", ".join(f"{n} {p_beam(R_REQ, RHO0, a):.2f}" for n, a in ALPHAS.items()) + ")")
    print(f"{'object':12s}" + "".join(f" {'P@250 ' + n:>11s}" for n in WEATHER) + f" {'weighted':>9s}"
          + "".join(f" {'R99 ' + n:>9s}" for n in WEATHER))
    for name, (w, h) in OBJECTS.items():
        print(f"{name:12s}" + "".join(f" {p_detect(w, h, R_REQ, RHO0, a):11.3f}" for a in ALPHAS.values())
              + f" {p_weighted(w, h, R_REQ, RHO0):9.3f}"
              + "".join(f" {max_range(w, h, RHO0, a):8d}m" for a in ALPHAS.values()))

    # plot: P(K >= 5) vs distance, one panel per weather condition
    R = np.arange(50, R_MAX + 1)
    fig, axes = plt.subplots(1, len(WEATHER), figsize=(13, 4.2), sharey=True)
    for ax, (wname, (vis, share)) in zip(axes, WEATHER.items()):
        for name, (w, h) in OBJECTS.items():
            ax.plot(R, [p_detect(w, h, r, RHO0, ALPHAS[wname]) for r in R], label=name)
        ax.axvline(R_REQ, color="k", ls="--", lw=1)
        ax.axhline(CONF, color="gray", ls=":", lw=1)
        ax.set_xlabel("distance R [m]")
        ax.grid(alpha=0.3)
        vis_txt = "visibility > 20 km" if np.isinf(vis) else f"visibility {vis / 1000:.0f} km"
        ax.set_title(f"{wname} ({vis_txt}, {share:.0%} of time)")
    axes[0].set_ylabel(f"P(K >= {K_MIN})")
    axes[0].legend(loc="lower left")
    fig.suptitle(f"{LIDAR}, {RHO0:.0%} reflectivity: probability of at least {K_MIN} returns")
    plt.tight_layout()
    plt.savefig("lidar_eba.png", dpi=150)
    plt.show()
