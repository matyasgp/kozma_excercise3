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
    """Two short lines per chart, with the numbers taken from the scores."""
    c, l, r, t = (s[m] for m in ("camera", "lidar", "radar", "thermal"))
    return {
        "Clear day": "camera: detail, color\nradar: speed · lidar: 3D",
        "Night": f"camera contrast {c[AXES[0]]:.2f}\nthermal {t[AXES[5]]:.2f} on living objects",
        "Fog / heavy rain": f"optical range {l[AXES[1]]:.2f} (lidar)\nradar keeps {r[AXES[1]]:.2f}",
        "Snow / glare / tunnel": f"glare: camera contrast {c[AXES[0]]:.2f}\nsnow: lidar range {l[AXES[1]]:.2f}",
    }[g]


# font sizes [pt] and marker size for the two figure scales
STRIP = dict(label=9.5, title=12.5, sub=8.8, take=9.0, ms=5.0, lw=1.8)
SINGLE = dict(label=10.5, title=14, sub=10, take=10, ms=6.5, lw=2.0)


def draw(ax, s, f):
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
        ax.plot(closed, v + v[:1], color=col, lw=f["lw"], solid_joinstyle="round", zorder=3)
        ax.plot(ang, v, ls="none", marker=mk, ms=f["ms"], color=col, mec=SURFACE, mew=1.1, zorder=4)
    for a, lab in zip(ang, LABELS):
        ha = "center" if np.isclose(np.sin(a), 0, atol=0.05) else ("left" if np.sin(a) > 0 else "right")
        va = "bottom" if np.cos(a) > 0.5 else ("top" if np.cos(a) < -0.5 else "center")
        ax.text(a, 1.12, lab, ha=ha, va=va, color=INK2, fontsize=f["label"], linespacing=1.0)


def legend_handles(ms=6.5):
    h = [Line2D([0], [0], color=c, lw=2.0, marker=mk, ms=ms, mec=SURFACE, mew=1.1, label=lab)
         for c, mk, lab in STYLE.values()]
    h.append(Patch(facecolor=SUITE, alpha=0.25, edgecolor=SUITE, lw=1.0, label="Whole suite (best per axis)"))
    return h


def panel(fig, x_c, y0, size, g, s, f):
    """One chart centred at x_c [in] with its plot bottom at y0 [in], plot `size` inches square."""
    W, H = fig.get_size_inches()
    ax = fig.add_axes([(x_c - size / 2) / W, y0 / H, size / W, size / H], projection="polar")
    draw(ax, s, f)
    lab_h = 0.06 * size + 2.1 * f["label"] / 72          # room for a two-line axis label
    top = y0 + size + lab_h
    fig.text(x_c / W, (top + 0.08 + 1.5 * f["sub"] / 72) / H, g, ha="center", va="bottom", color=INK,
             fontsize=f["title"], fontweight="semibold")
    fig.text(x_c / W, (top + 0.06) / H, CASES[g], ha="center", va="bottom", color=INK2, fontsize=f["sub"])
    fig.text(x_c / W, (y0 - lab_h - 0.06) / H, takeaway(g, s), ha="center", va="top", color=INK,
             fontsize=f["take"], linespacing=1.15)


def main():
    models, mounts = load_suite()
    sp = spider_scores(models, mounts)
    os.makedirs("figures", exist_ok=True)
    note = "Scores 0-1 from model.py (outer ring = 1). Gray area: whole suite, the best modality on each axis."

    W, H = 10.0, 3.75                                      # sized for a 10 in wide slide (Google Slides default)
    fig = plt.figure(figsize=(W, H))
    for i, (g, s) in enumerate(sp.items()):
        panel(fig, 0.12 + (i + 0.5) * (W - 0.24) / 4, 1.2, 1.42, g, s, STRIP)
    fig.legend(handles=legend_handles(5.0), loc="lower center", ncol=5, frameon=False, fontsize=9,
               labelcolor=INK2, bbox_to_anchor=(0.5, 0.045), handlelength=1.6, columnspacing=1.2)
    fig.text(0.5, 0.012, note, ha="center", color=MUTED, fontsize=7.5)
    for ext in ("png", "pdf"):
        fig.savefig(f"figures/spider_conditions.{ext}", dpi=250)
    plt.close(fig)

    for g, s in sp.items():
        fig = plt.figure(figsize=(5.6, 6.4))
        panel(fig, 2.8, 1.9, 3.0, g, s, SINGLE)
        fig.legend(handles=legend_handles(), loc="lower center", ncol=3, frameon=False, fontsize=9,
                   labelcolor=INK2, bbox_to_anchor=(0.5, 0.03))
        slug = g.lower().replace(" / ", "_").replace(" ", "_")
        fig.savefig(f"figures/spider_{slug}.png", dpi=200)
        plt.close(fig)
    print("wrote figures/spider_conditions.png/.pdf and one figure per condition")


if __name__ == "__main__":
    main()
