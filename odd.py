"""Operating limits (ODD) for the L4/L5 answer (Exercise 4, step 6).

The coverage map asks "does the suite reach the 130 km/h requirement?". This script turns it around:
how fast may the car drive so that its stopping distance (requirements.stop_distance: 1 s + 3 m/s^2)
still fits inside the range of at least two independent modalities straight ahead?
  v2 = safe_speed(second-best modality range ahead)     (redundant: one modality may fail)
  v1 = safe_speed(best modality range ahead)            (no redundancy)
for a car and a pedestrian, per condition (worst sub-case), and as a sweep over fog visibility.

Run `python odd.py`: prints the table, writes safe_speed.csv and figures/safe_speed_fog.{png,pdf}.
"""
import logging
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import model
from coverage import MODS, load
from model import GROUPS, SUBCASES, effective_range
from requirements import safe_speed

INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10,
                     "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE})


def ahead_ranges(sensors, target, sub):
    """Best range straight ahead per modality [m] (sensors whose FOV contains the forward direction)."""
    best = {m: 0.0 for m in MODS}
    for x in sensors:
        phi = -x["yaw"]
        if abs((phi + 180) % 360 - 180) <= x["m"]["hfov"] / 2:
            best[x["mod"]] = max(best[x["mod"]], effective_range(x["m"], target, sub, x["forward"], phi))
    return best


def speeds(sensors, target, sub):
    r = sorted(ahead_ranges(sensors, target, sub).values(), reverse=True)
    return safe_speed(r[0]), safe_speed(r[1]), r[0], r[1]


def table(sensors):
    rows = []
    for g, subs in GROUPS.items():
        for target in ("car", "pedestrian"):
            per = {s: speeds(sensors, target, s) for s in subs}
            worst = min(per, key=lambda s: per[s][1])
            v1, v2, r1, r2 = per[worst]
            best = ahead_ranges(sensors, target, worst)
            rows.append(dict(condition=g, target=target, worst_case=worst, range_best=r1, range_second=r2,
                             v1=v1, v2=v2, ranges=best))
    return rows


def fog_sweep(sensors, V, lwir_ratio=None):
    """Safe speeds over fog visibility; lwir_ratio overrides model.LWIR_FOG_RATIO (sensitivity)."""
    keep = model.LWIR_FOG_RATIO
    if lwir_ratio is not None:
        model.LWIR_FOG_RATIO = lwir_ratio
    out = {"car": ([], []), "pedestrian": ([], [])}
    for v in V:
        sc = dict(SUBCASES["fog"], V=float(v))
        for target in out:
            v1, v2, _, _ = speeds(sensors, target, sc)
            out[target][0].append(v1)
            out[target][1].append(v2)
    model.LWIR_FOG_RATIO = keep
    return {k: (np.array(a), np.array(b)) for k, (a, b) in out.items()}


def figure(V, sw, sw_bad):
    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    ax.axhline(130, color=GRID, lw=1.0, zorder=0)
    ax.text(21, 132, "130 km/h highway design speed", ha="left", va="bottom", color=MUTED, fontsize=8.5)
    law_v = np.where(V < 50, 50, np.nan)
    ax.plot(V, law_v, color=MUTED, lw=2.0, solid_capstyle="round")
    ax.text(21, 31, "German law (StVO §3): max 50 km/h\nbelow 50 m visibility", color=MUTED, fontsize=8.5, va="top")
    lines = [("car", 1, INK, "car, 2 modalities"), ("pedestrian", 1, INK2, "pedestrian, 2 modalities"),
             ("car", 0, "#2a78d6", "car, best single modality (radar)")]
    for target, k, col, lab in lines:
        y = sw[target][k]
        ax.plot(V, y, color=col, lw=2.0, solid_capstyle="round", label=lab)
        if k == 1:                                        # sensitivity: LWIR no better than visible in fog
            ax.fill_between(V, sw_bad[target][k], y, color=col, alpha=0.10, lw=0)
    ax.fill_between([], [], color=INK2, alpha=0.15, lw=0,
                    label="band: if thermal sees no further than visible light in fog")
    ax.axvline(200, color=GRID, lw=1.0, zorder=0)
    ax.text(205, 8, "our fog case\n(V = 200 m)", color=MUTED, fontsize=8.5, va="bottom")
    ax.set_xscale("log")
    ax.set_xlim(V[0], V[-1])
    ax.set_ylim(0, 160)
    ax.set_xticks([20, 50, 100, 200, 500, 1000, 2000, 5000, 20000], ["20", "50", "100", "200", "500", "1k", "2k",
                                                                     "5k", "20k"])
    ax.set_xlabel("Visibility in fog [m]", color=INK2)
    ax.set_ylabel("Highest safe speed [km/h]", color=INK2)
    ax.grid(axis="y", color=GRID, lw=0.8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(GRID)
    ax.tick_params(colors=MUTED)
    ax.legend(loc="lower right", frameon=False, fontsize=9, labelcolor=INK2)
    ax.set_title("How fast the suite may drive in fog: stopping distance (1 s + 3 m/s²) inside the range ahead",
                 loc="left", color=INK, fontsize=10.5)
    fig.tight_layout()
    os.makedirs("figures", exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"figures/safe_speed_fog.{ext}", dpi=200)
    plt.close(fig)


def main():
    sensors, _ = load()
    rows = table(sensors)
    with open("safe_speed.csv", "w", encoding="utf-8") as f:
        f.write("condition,target,worst_case,range_best_m,range_second_m,v_best_kmh,v_two_kmh,"
                + ",".join(f"{m}_m" for m in MODS) + "\n")
        for r in rows:
            f.write(f"{r['condition']},{r['target']},{r['worst_case']},{r['range_best']:.0f},{r['range_second']:.0f},"
                    f"{r['v1']:.0f},{r['v2']:.0f}," + ",".join(f"{r['ranges'][m]:.0f}" for m in MODS) + "\n")
    print(f"{'condition':24s}{'target':12s}{'worst case':15s}{'2nd range':>10s}{'v (2 mod.)':>12s}{'v (best)':>10s}")
    for r in rows:
        print(f"{r['condition']:24s}{r['target']:12s}{r['worst_case']:15s}{r['range_second']:8.0f} m"
              f"{r['v2']:9.0f} km/h{r['v1']:7.0f} km/h")
    V = np.geomspace(20, 23000, 120)
    sw = fog_sweep(sensors, V)
    sw_bad = fog_sweep(sensors, V, lwir_ratio=1.0)
    for v in (50, 100, 200, 500, 1000):
        i = int(np.argmin(abs(V - v)))
        print(f"fog V = {V[i]:6.0f} m: car {sw['car'][1][i]:4.0f} km/h, pedestrian {sw['pedestrian'][1][i]:4.0f} km/h"
              f" (2 modalities; {sw_bad['car'][1][i]:3.0f} / {sw_bad['pedestrian'][1][i]:3.0f} if LWIR = visible);"
              f" radar alone {sw['car'][0][i]:4.0f} km/h")
    figure(V, sw, sw_bad)
    print("wrote safe_speed.csv and figures/safe_speed_fog.png/.pdf")


if __name__ == "__main__":
    main()
