"""Does the Hesai AT512 meet the EBA requirements (>= 5 returns per object at 250 m)?

Model, one function per step:
  1. Geometry   - a flat W x H object at distance R covers W/(R*dth) x H/(R*dtv) grid cells.
                  The beam grid has a random offset, so a side of length L (in cells)
                  is hit by floor(L) beams, or by floor(L)+1 with probability frac(L).
  2. Detection  - each beam that hits returns with p(R, rho) = 1 - exp(-c * rho/R^2 * exp(-2*alpha*R)),
                  i.e. signal ~ rho/R^2 (target larger than the beam), with atmospheric loss alpha.
                  c is calibrated so that p(R0, rho0) = P0, the datasheet range spec.
  3. Statistics - beams are independent, so returns K ~ Binomial(n, p); P(K >= 5) = 1 - P(K <= 4).
  4. Verdict    - the largest R where P(K >= 5) >= 99 %, compared with the 250 m requirement.

Datasheet (Hesai AT512): 0.05 x 0.05 deg, 120 x 25.6 deg FoV, 300 m @ 10 % reflectivity,
12.288 Mpts/s = 2400 x 512 x 10 Hz. P0 = 90 % is an assumption (not stated by Hesai).
"""
from math import comb

import numpy as np
import matplotlib.pyplot as plt

# --- lidar (datasheet) ---
DTH = np.radians(0.05)              # horizontal angular resolution [rad]
DTV = np.radians(0.05)              # vertical angular resolution [rad]
R0, RHO0, P0 = 300.0, 0.10, 0.90    # range spec: R0 at RHO0 with detection probability P0
R_MAX = 400                         # max range [m]; model not trusted beyond it
FPS = 10

# --- requirement / scenario ---
R_REQ, K_MIN, CONF = 250.0, 5, 0.99
OBJECTS = {                         # name: (width, height) [m], front view
    "pedestrian": (0.5, 1.8),
    "car":        (1.8, 1.5),
    "motorcycle": (0.8, 1.4),
    "truck":      (2.5, 3.5),
    "tyre/cargo": (0.5, 0.5),
}
ALPHA = 0.0                         # atmospheric extinction [1/m]; ~0.001-0.003 light rain, ~0.01+ fog

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


def p_detect(w, h, R, rho, k=K_MIN):
    """Step 3: P(K >= k), averaged over the 2 x 2 possible beam counts."""
    (nh, ph), (nv, pv) = beam_counts(w, R, DTH), beam_counts(h, R, DTV)
    p = p_beam(R, rho)
    return sum(ph[i] * pv[j] * p_at_least(k, nh[i] * nv[j], p) for i in range(2) for j in range(2))


def expected_returns(w, h, R, rho):
    return w / (R * DTH) * h / (R * DTV) * p_beam(R, rho)


def max_range(w, h, rho, R=np.arange(10, R_MAX + 1)):
    """Step 4: largest distance where the object is still detected with probability >= CONF."""
    ok = np.array([p_detect(w, h, r, rho) >= CONF for r in R])
    return R[ok].max() if ok.any() else 0


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

    R = np.arange(50, 351)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    for name, (w, h) in OBJECTS.items():
        line, = ax1.plot(R, [p_detect(w, h, r, 0.10) for r in R], label=name)
        ax2.semilogy(R, expected_returns(w, h, R, 0.10), color=line.get_color(), label=name)
    for ax in (ax1, ax2):
        ax.axvline(R_REQ, color="k", ls="--", lw=1)
        ax.set_xlabel("distance R [m]")
        ax.grid(alpha=0.3)
    ax1.axhline(CONF, color="gray", ls=":", lw=1)
    ax1.set_ylabel(f"P(K >= {K_MIN})")
    ax1.set_title("Hesai AT512, 10 % reflectivity: P(at least 5 returns)")
    ax2.axhline(K_MIN, color="gray", ls=":", lw=1)
    ax2.set_ylabel("expected returns E[K]")
    ax2.set_title("expected returns per frame")
    ax1.legend()
    plt.tight_layout()
    plt.savefig("lidar_eba.png", dpi=150)
    plt.show()
