"""Suite figures for the design slide (Exercise 4).

  figures/suite_layout.png      where the 19 perception sensors sit on the car (to scale) and where they look
  figures/requirements.png      the required detection range per direction (car, pedestrian, near field)
  figures/reach_by_modality.png per modality, every sensor's field of view out to its clear-day range on a car,
                                against the required car range (square-root radius, so the near field and
                                250 m fit on one plot; mount offsets are left out)
Run `python layout.py`.
"""
import logging
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon, Rectangle

from coverage import BEARINGS, MODS, load
from model import effective_range
from requirements import FRONT_CONE, NEAR, REAR_CONE, REQ, required_range

INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
STYLE = {"camera": ("#2a78d6", "o"), "lidar": ("#008300", "s"), "radar": ("#eda100", "^"), "thermal": ("#e87ba4", "D")}
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10,
                     "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE})

# display nudges [m, vehicle frame] so co-located sensors don't hide each other (the figure says so)
NUDGE = {"R_front": (0, -0.32), "F_front": (0, 0.32), "T_front": (0, 0.30), "L_front": (0, 0),
         "C_front_tele": (0, 0.12), "C_front_main": (0, -0.12), "C_rear": (0, 0.2), "F_rear": (0, -0.2),
         "C_side_lf": (0.18, 0), "C_side_rf": (0.18, 0), "C_side_lr": (-0.18, 0), "C_side_rr": (-0.18, 0),
         "F_left": (-0.5, 0), "F_right": (-0.5, 0)}
# one label per mounting location: (text, label anchor in plot coords, sensors it points at, alignment)
LABELS = [
    ("Front bumper\nInnovizTwo lidar · DRVEGRD 171 radar\nLWIR thermal 32° · 3 MP fisheye", (0, 3.6),
     ["L_front"], "center"),
    ("Windscreen\n8 MP 30° + 8 MP 60° cameras", (2.2, 2.3), ["C_front_main"], "left"),
    ("Roof\nHesai OT128 360° lidar\n(+ u-blox ZED-F9K GNSS/IMU)", (2.2, -0.9), ["L_roof"], "left"),
    ("Front corners\n2 × DRVEGRD 171, ±50°", (-2.2, 3.1), ["R_fl", "R_fr"], "right"),
    ("Each mirror\n8 MP 120° forward (±70°)\n8 MP 120° backward (±140°)\n3 MP fisheye, looking down",
     (-2.2, 0.85), ["C_side_lf", "C_side_rf"], "right"),
    ("Rear corners\n2 × DRVEGRD 171, ±130°", (-2.2, -3.1), ["R_rl", "R_rr"], "right"),
    ("Rear\n8 MP 60° camera · 3 MP fisheye", (0, -3.5), ["C_rear"], "center"),
]

SHORT_LABELS = ["front bumper", "windscreen", "roof", "front corners", "mirrors", "rear corners", "rear"]
SHORT_NOTES = ["car 253 m", "pedestrian\n82 m", "car\n81 m", "car 96 m", "pedestrian\n15 m", "near field\n0.1–5 m"]


def to_plot(x, y):
    """Vehicle frame (x forward, y left) -> plot (front up, left on the left)."""
    return -y, x


def suite_layout(sensors, veh, detail=True):
    fig, ax = plt.subplots(figsize=(7.4, 7.4) if detail else (4.6, 4.6))
    L, W = veh["length"], veh["width"]
    ax.add_patch(Rectangle((-W / 2, -L / 2), W, L, facecolor="#f0efec", edgecolor=INK2, lw=1.2, zorder=1))
    ax.add_patch(Polygon([(-0.75, 0.45), (0.75, 0.45), (0.65, 1.15), (-0.65, 1.15)], closed=True,
                         facecolor=GRID, edgecolor="none", zorder=1))         # windscreen, for orientation
    pos = {}
    for sen in sensors:
        nx, ny = NUDGE.get(sen["id"], (0, 0))
        px, py = to_plot(sen["x"] + nx, sen["y"] + ny)
        pos[sen["id"]] = (px, py)
        col, mk = STYLE[sen["mod"]]
        dx, dy = to_plot(np.cos(np.radians(sen["yaw"])), np.sin(np.radians(sen["yaw"])))
        ax.plot([px, px + 0.5 * dx], [py, py + 0.5 * dy], color=col, lw=2.0, solid_capstyle="round", zorder=3)
        ax.plot(px, py, marker=mk, ms=8, color=col, mec=SURFACE, mew=1.5, zorder=4)
    for (text, (lx, ly), targets, ha), short in zip(LABELS, SHORT_LABELS):
        text = text if detail else short
        for t in targets:
            px, py = pos[t]
            ax.plot([lx, px], [ly, py], color=GRID, lw=0.8, zorder=0)
        va = "center" if ha != "center" else ("bottom" if ly > 0 else "top")
        dx = 0.1 if ha == "left" else -0.1 if ha == "right" else 0
        dy = 0.05 if va == "bottom" else -0.05 if va == "top" else 0
        ax.text(lx + dx, ly + dy, text, ha=ha, va=va, fontsize=8.6 if detail else 10.5, color=INK2, linespacing=1.25)
    handles = [Line2D([0], [0], color=c, marker=m, ls="none", ms=8, mec=SURFACE, mew=1.5, label=k.capitalize())
               for k, (c, m) in STYLE.items()]
    ax.legend(handles=handles, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.04),
              labelcolor=INK2)
    if detail:
        ax.set_xlim(-5.6, 5.6)
        ax.set_ylim(-5.0, 5.4)
    else:
        ax.set_xlim(-4.5, 4.5)
        ax.set_ylim(-4.3, 4.1)
    ax.set_aspect("equal")
    ax.axis("off")
    if detail:
        ax.set_title("19 perception sensors on a 4.8 × 1.9 m car (to scale, front up)\n"
                     "stroke = viewing direction; co-located sensors drawn slightly apart", color=INK, fontsize=10.5)
    fig.tight_layout()
    fig.savefig("figures/suite_layout_detail.png" if detail else "figures/suite_layout.png", dpi=250)
    plt.close(fig)


def sq(r):
    return np.sqrt(np.maximum(r, 0))


def reach_by_modality(sensors, sub="clear_day", target="car"):
    fig, axs = plt.subplots(1, 4, figsize=(13.33, 4.7))
    ticks = [10, 50, 100, 250, 450]
    req = np.array([required_range(b, target) for b in BEARINGS])
    rx, ry = to_plot(sq(req) * np.cos(np.radians(BEARINGS)), sq(req) * np.sin(np.radians(BEARINGS)))
    for ax, mod in zip(axs, MODS):
        col, _ = STYLE[mod]
        ss = [x for x in sensors if x["mod"] == mod]
        for r in ticks:
            t = np.linspace(0, 2 * np.pi, 200)
            ax.plot(sq(r) * np.cos(t), sq(r) * np.sin(t), color=GRID, lw=0.8, zorder=0)
            ax.text(sq(r) * np.cos(np.radians(-50)), sq(r) * np.sin(np.radians(-50)), f"{r} m", color=MUTED,
                    fontsize=7.5, ha="left", va="top")
        for x in ss:
            half = x["m"]["hfov"] / 2
            phis = np.linspace(-half, half, int(2 * half) + 2)
            rr = np.array([effective_range(x["m"], target, sub, x["forward"], p) for p in phis])
            th = np.radians(x["yaw"] + phis)
            px, py = to_plot(sq(rr) * np.cos(th), sq(rr) * np.sin(th))
            if half < 180:
                px, py = np.r_[0, px, 0], np.r_[0, py, 0]
            ax.fill(px, py, color=col, alpha=0.10, lw=0, zorder=1)
            ax.plot(px, py, color=col, lw=1.2, zorder=2)
        ax.plot(rx, ry, color=INK, lw=1.6, zorder=3)
        ax.set_aspect("equal")
        lim = sq(480)
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.axis("off")
        n = len(ss)
        ax.set_title(f"{mod.capitalize()} · {n} sensor{'s' if n > 1 else ''}", color=INK, fontsize=12,
                     fontweight="semibold")
    fig.legend(handles=[Line2D([0], [0], color=INK, lw=1.6,
                               label="required car range (253 m ahead, 81 m sides, 96 m behind)"),
                        Line2D([0], [0], color=MUTED, lw=1.2,
                               label="each sensor's field of view out to its clear-day range on a car")],
               loc="lower center", ncol=2, frameon=False, labelcolor=INK2, fontsize=9.5)
    fig.text(0.5, 0.955, "What each modality reaches (front up, square-root distance scale)", ha="center",
             color=INK2, fontsize=10)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.87, bottom=0.10, wspace=0.05)
    fig.savefig("figures/reach_by_modality.png", dpi=200)
    plt.close(fig)


def requirements_figure(detail=True):
    fig, ax = plt.subplots(figsize=(6.4, 6.4) if detail else (4.6, 4.6))
    for r in (10, 50, 100, 250):
        t = np.linspace(0, 2 * np.pi, 200)
        ax.plot(sq(r) * np.cos(t), sq(r) * np.sin(t), color=GRID, lw=0.8, zorder=0)
        ax.text(sq(r) * np.cos(np.radians(-58)), sq(r) * np.sin(np.radians(-58)), f"{r} m", color=MUTED,
                fontsize=8, ha="left", va="top")
    t = np.linspace(0, 2 * np.pi, 200)
    ax.fill(np.r_[sq(NEAR[1] + 2.4) * np.cos(t)], np.r_[sq(NEAR[1] + 2.4) * np.sin(t)], color=MUTED, alpha=0.18,
            lw=0, zorder=1)
    for target, col, lw in (("car", INK, 2.0), ("pedestrian", INK2, 1.6)):
        req = np.array([required_range(b, target) for b in BEARINGS])
        x, y = to_plot(sq(req) * np.cos(np.radians(BEARINGS)), sq(req) * np.sin(np.radians(BEARINGS)))
        ax.plot(np.r_[x, x[0]], np.r_[y, y[0]], color=col, lw=lw, zorder=3)
    ax.add_patch(Rectangle((-0.35, -0.9), 0.7, 1.8, facecolor=INK2, edgecolor="none", zorder=4))
    notes = [  # (text, text position, ha, point the leader line goes to) in plot coords
        (f"car {REQ[('front', 'car')]:.0f} m\nstop from 130 km/h\n(±{FRONT_CONE['car']:.0f}°: 720 m curve)",
         (4.2, 14.6), "left", (2.9, 15.3)),
        (f"pedestrian {REQ[('front', 'pedestrian')]:.0f} m\nstop from 70 km/h\n(±{FRONT_CONE['pedestrian']:.0f}°)",
         (-4.2, 12.2), "right", (-2.3, 8.4)),
        (f"car {REQ[('side', 'car')]:.0f} m: pull out\nbefore cross traffic\nat 60 km/h", (10.0, 3.2), "left",
         (8.4, 3.2)),
        (f"car {REQ[('rear', 'car')]:.0f} m: lane change,\ncar closing at 60 km/h\n(±{REAR_CONE['car']:.0f}°)",
         (2.2, -12.0), "left", (0.6, -9.7)),
        (f"pedestrian {REQ[('side', 'pedestrian')]:.0f} m all round:\njogger during\na 4.9 s turn",
         (-10.0, -4.0), "right", (-3.2, -2.2)),
        (f"near field {NEAR[0]}–{NEAR[1]:.0f} m\n(gray disc),\n0.5 m objects", (-10.0, 3.6), "right",
         (-1.9, 1.9)),
    ]
    for (text, (x, y), ha, (ax_, ay_)), short in zip(notes, SHORT_NOTES):
        text = text if detail else short
        ax.plot([x + (0.2 if ha == "left" else -0.2), ax_], [y, ay_], color=MUTED, lw=0.7, zorder=2)
        ax.text(x + (0.35 if ha == "left" else -0.35), y, text, ha=ha, va="center", fontsize=8.6 if detail else 10.5, color=INK2,
                linespacing=1.2, zorder=5)
    if detail:
        ax.legend(handles=[Line2D([0], [0], color=INK, lw=2.0, label="car"),
                           Line2D([0], [0], color=INK2, lw=1.6, label="pedestrian")],
                  loc="lower right", frameon=False, labelcolor=INK2, fontsize=9)
    ax.set_xlim(-17.5, 17.5)
    ax.set_ylim(-16.5, 17.0)
    ax.set_aspect("equal")
    ax.axis("off")
    if detail:
        ax.set_title("Required detection range per direction (front up, square-root scale)", color=INK,
                     fontsize=10.5)
    fig.tight_layout()
    fig.savefig("figures/requirements_detail.png" if detail else "figures/requirements.png", dpi=250)
    plt.close(fig)


def main():
    sensors, veh = load()
    os.makedirs("figures", exist_ok=True)
    suite_layout(sensors, veh)
    suite_layout(sensors, veh, detail=False)
    reach_by_modality(sensors)
    requirements_figure()
    requirements_figure(detail=False)
    print("wrote figures/suite_layout.png, figures/reach_by_modality.png and figures/requirements.png")


if __name__ == "__main__":
    main()
