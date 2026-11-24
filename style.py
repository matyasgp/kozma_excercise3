"""Shared figure style: colors, one color and marker per modality, matplotlib defaults.

Colors: the categorical light palette checked with the dataviz validator for all pairs (CVD dE 13.0, normal
vision 19.6). Radar yellow and thermal pink are below 3:1 contrast, so every series also gets its own marker
shape and the values are in the CSV files.
"""
import logging

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
MOD_COLOR = {"camera": "#2a78d6", "lidar": "#008300", "radar": "#eda100", "thermal": "#e87ba4"}
MOD_MARKER = {"camera": "o", "lidar": "s", "radar": "^", "thermal": "D"}

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10,
                     "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE})
