"""Spider charts per condition (Exercise 4, step 3), drawn from model.py's scores.

One chart per condition group with the four modalities as lines and the whole suite (best modality per
axis) as the gray area. Axes are the professor's template. Run `python spider.py`; it writes
figures/spider_conditions.{png,pdf} (all four in a row, for the pitch) and figures/spider_<group>.png.
Colors: categorical light palette checked with the dataviz validator for all pairs (CVD dE 13.0, normal
vision 19.6); radar yellow and thermal pink are below 3:1 contrast, so every series also has its own
marker shape and the legend and spider_scores.csv carry the values.
"""
import logging
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from model import AXES, load_suite, spider_scores

INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
SUITE = "#52514e"
STYLE = {  # modality: (color, marker, label)
    "camera": ("#2a78d6", "o", "Camera"),
    "lidar": ("#008300", "s", "Lidar"),
    "radar": ("#eda100", "^", "Radar"),
    "thermal": ("#e87ba4", "D", "Thermal (LWIR)"),
}
LABELS = ["Contrast,\nresolution", "Range", "Color", "Speed\ndetection", "3D recon-\nstruction", "Living\nobjects"]
CASES = {
    "Clear day": "23 km visibility",
    "Night": "unlit road, low beam only",
    "Fog / heavy rain": "worst of fog (200 m) and 25 mm/h rain",
    "Snow / glare / tunnel": "worst of snow, low sun and tunnel exit",
}
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10,
                     "axes.edgecolor": GRID, "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE})


def takeaway(g, s):
    """One line per chart, with the numbers taken from the scores."""
    c, l, r, t = (s[m] for m in ("camera", "lidar", "radar", "thermal"))
    return {
        "Clear day": "camera: detail and color; radar: speed; lidar: 3D",
        "Night": f"camera contrast {c[AXES[0]]:.2f}; thermal {t[AXES[5]]:.2f} on living objects",
        "Fog / heavy rain": f"optical range {l[AXES[1]]:.2f} (lidar); radar keeps {r[AXES[1]]:.2f}",
        "Snow / glare / tunnel": f"glare: camera contrast {c[AXES[0]]:.2f}; snow: lidar range {l[AXES[1]]:.2f}",
    }[g]


def draw(ax, g, s, small=False):
    n = len(AXES)
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    closed = np.append(ang, ang[0])
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 1.0)
    ax.axis("off")
    for r in (0.25, 0.5, 0.75, 1.0):                     # polygonal grid, solid hairlines
        ax.plot(closed, [r] * (n + 1), color=GRID, lw=0.8, zorder=0)
    for a in ang:
        ax.plot([a, a], [0, 1], color=GRID, lw=0.8, zorder=0)
    suite = [s["whole suite"][a] for a in AXES]
    ax.fill(closed, suite + suite[:1], color=SUITE, alpha=0.12, lw=0, zorder=1)
    ax.plot(closed, suite + suite[:1], color=SUITE, lw=1.0, zorder=1)
    for mod, (col, mk, _) in STYLE.items():
        v = [s[mod][a] for a in AXES]
        ax.plot(closed, v + v[:1], color=col, lw=2.0, solid_joinstyle="round", zorder=3)
        ax.plot(ang, v, ls="none", marker=mk, ms=6.5 if not small else 5.5, color=col,
                mec=SURFACE, mew=1.2, zorder=4)
    for a, lab in zip(ang, LABELS):
        ha = "center" if np.isclose(np.sin(a), 0, atol=0.05) else ("left" if np.sin(a) > 0 else "right")
        va = "bottom" if np.cos(a) > 0.5 else ("top" if np.cos(a) < -0.5 else "center")
        ax.text(a, 1.12, lab, ha=ha, va=va, color=INK2, fontsize=9 if small else 10, linespacing=1.05)


def legend_handles():
    h = [Line2D([0], [0], color=c, lw=2.0, marker=mk, ms=6.5, mec=SURFACE, mew=1.2, label=lab)
         for c, mk, lab in STYLE.values()]
    h.append(Patch(facecolor=SUITE, alpha=0.25, edgecolor=SUITE, lw=1.0, label="Whole suite (best per axis)"))
    return h


def panel(fig, x_c, y0, size, g, s, small):
    """One chart centred at x_c [in] with its plot bottom at y0 [in], plot `size` inches square."""
    W, H = fig.get_size_inches()
    ax = fig.add_axes([(x_c - size / 2) / W, y0 / H, size / W, size / H], projection="polar")
    draw(ax, g, s, small)
    top, gap = (y0 + size) / H, 0.2 * size          # gap: room for the axis labels around the plot
    fig.text(x_c / W, top + (gap + 0.36) / H, g, ha="center", color=INK, fontsize=13 if small else 14,
             fontweight="semibold")
    fig.text(x_c / W, top + (gap + 0.13) / H, CASES[g], ha="center", color=INK2, fontsize=9.5 if small else 10)
    fig.text(x_c / W, (y0 - gap - 0.25) / H, takeaway(g, s), ha="center", color=INK, fontsize=9.5 if small else 10)


def main():
    models, mounts = load_suite()
    sp = spider_scores(models, mounts)
    os.makedirs("figures", exist_ok=True)
    note = "Scores 0-1 from model.py (outer ring = 1). Gray area: whole suite, the best modality on each axis."

    fig = plt.figure(figsize=(13.33, 4.85))
    for i, (g, s) in enumerate(sp.items()):
        panel(fig, 0.3 + (i + 0.5) * (13.33 - 0.6) / 4, 1.45, 2.1, g, s, small=True)
    fig.legend(handles=legend_handles(), loc="lower center", ncol=5, frameon=False, fontsize=10,
               labelcolor=INK2, bbox_to_anchor=(0.5, 0.05))
    fig.text(0.5, 0.015, note, ha="center", color=MUTED, fontsize=8.5)
    for ext in ("png", "pdf"):
        fig.savefig(f"figures/spider_conditions.{ext}", dpi=200)
    plt.close(fig)

    for g, s in sp.items():
        fig = plt.figure(figsize=(5.6, 6.4))
        panel(fig, 2.8, 1.85, 3.0, g, s, small=False)
        fig.legend(handles=legend_handles(), loc="lower center", ncol=3, frameon=False, fontsize=9,
                   labelcolor=INK2, bbox_to_anchor=(0.5, 0.04))
        slug = g.lower().replace(" / ", "_").replace(" ", "_")
        fig.savefig(f"figures/spider_{slug}.png", dpi=200)
        plt.close(fig)
    print("wrote figures/spider_conditions.png/.pdf and one figure per condition")


if __name__ == "__main__":
    main()
