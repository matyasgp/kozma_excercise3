"""Slide figures, built from the model in lidar_eba.py.

fig_beams_250m.png   - the InnovizTwo beam grid at 250 m over the objects (lidar slide)
fig_k_distribution.png - distribution of returns K, pedestrian at 250 m (model slide)
fig_ranges.png       - 99 % detection range per object vs. the 250 m requirement (conclusion slide)
"""
from math import comb

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from lidar_eba import OBJECTS, DTH, DTV, R_REQ, R_MAX, K_MIN, beam_counts, p_beam, max_range

COLORS = {name: f"C{i}" for i, name in enumerate(OBJECTS)}   # same colours as lidar_eba.png
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False})


def k_distribution(w, h, R, rho):
    """P(K = k) for k = 0..n_max, mixing the binomial over the possible beam counts."""
    (nh, ph), (nv, pv) = beam_counts(w, R, DTH), beam_counts(h, R, DTV)
    p = p_beam(R, rho)
    dist = np.zeros(int(nh[1] * nv[1]) + 1)
    for i in range(2):
        for j in range(2):
            n = int(nh[i] * nv[j])
            for k in range(n + 1):
                dist[k] += ph[i] * pv[j] * comb(n, k) * p**k * (1 - p)**(n - k)
    return dist


def fig_beams(R=250.0):
    s_h, s_v = R * DTH, R * DTV
    layout = {"pedestrian": 0.0, "motorcycle": 1.0, "car": 2.3, "tyre/cargo": 4.6}
    gx, gy = np.meshgrid(np.arange(-0.3, 5.4, s_h) + 0.07, np.arange(0, 2.1, s_v) + 0.05)
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.plot(gx, gy, ".", color="0.8", ms=4)
    for name, x0 in layout.items():
        w, h = OBJECTS[name]
        ax.add_patch(Rectangle((x0, 0), w, h, fc=COLORS[name], alpha=0.25, ec=COLORS[name], lw=2))
        inside = (gx >= x0) & (gx <= x0 + w) & (gy <= h)
        ax.plot(gx[inside], gy[inside], "o", color=COLORS[name], ms=5)
        ax.text(x0 + w / 2, -0.12, f"{name}\n{inside.sum()} beams", ha="center", va="top", fontsize=11)
    ax.axhline(0, color="0.3", lw=1)
    ax.set_aspect("equal")
    ax.set_xlim(-0.35, 5.35)
    ax.set_ylim(-0.6, 2.15)
    ax.axis("off")
    ax.set_title(f"Beam grid at {R:.0f} m: {s_h * 100:.0f} cm x {s_v * 100:.0f} cm\n"
                 "(counts change by ±1 row/column with the grid position)", fontsize=12)
    fig.tight_layout()
    fig.savefig("fig_beams_250m.png", dpi=200)


def fig_k(name="pedestrian", R=250.0, rho=0.10):
    dist = k_distribution(*OBJECTS[name], R, rho)
    k = np.arange(len(dist))
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.bar(k, dist * 100, color=np.where(k < K_MIN, "#c0392b", "#27ae60"))
    ax.axvline(K_MIN - 0.5, color="k", ls="--", lw=1)
    ax.axvline((k * dist).sum(), color="0.4", ls=":", lw=1.5)
    ax.text(K_MIN - 0.7, max(dist) * 100 * 0.5, f"< {K_MIN} returns\n{dist[:K_MIN].sum():.1%}\nof frames",
            ha="right", va="top", color="#c0392b")
    ax.text((k * dist).sum() + 0.4, max(dist) * 100, f"average {(k * dist).sum():.1f}",
            ha="left", va="top", color="0.3")
    ax.set_xlabel("returns K in one frame")
    ax.set_ylabel("probability [%]")
    ax.set_xticks(k[::2])
    ax.set_title(f"{name}, {rho:.0%} reflectivity, {R:.0f} m", fontsize=13)
    fig.tight_layout()
    fig.savefig("fig_k_distribution.png", dpi=200)


def fig_ranges(rho=0.10):
    v, t_lat, a = 130 / 3.6, 0.5, 6.0
    d_stop = v * t_lat + v**2 / (2 * a)
    names = list(OBJECTS)[::-1]
    r99 = [max_range(*OBJECTS[n], rho) for n in names]
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.axvspan(0, d_stop, color="0.9")
    ax.text(d_stop / 2, -0.65, f"stopping @130 km/h ≈ {d_stop:.0f} m", ha="center", fontsize=10, color="0.35")
    ax.barh(names, r99, color=[COLORS[n] for n in names], alpha=0.85)
    for i, r in enumerate(r99):
        label = f"≥ {R_MAX} m" if r >= R_MAX else f"{r} m"
        ok = r >= R_REQ
        ax.text((R_REQ if ok else r) - 5, i, f"{label}  {'✔' if ok else '✘'}", ha="right", va="center",
                color="white", fontweight="bold")
    ax.axvline(R_REQ, color="k", ls="--", lw=1.5)
    ax.text(R_REQ - 4, -0.65, f"requirement {R_REQ:.0f} m", ha="right", fontsize=10)
    ax.set_xlim(0, R_MAX + 10)
    ax.set_ylim(-0.8, len(names) - 0.2)
    ax.set_xlabel(f"distance with P(K ≥ {K_MIN}) ≥ 99%  [m]")
    ax.set_title(f"99% detection range, {rho:.0%} reflectivity, clear weather", fontsize=13)
    fig.tight_layout()
    fig.savefig("fig_ranges.png", dpi=200)


if __name__ == "__main__":
    fig_beams()
    fig_k()
    fig_ranges()
