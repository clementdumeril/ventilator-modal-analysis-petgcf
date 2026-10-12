"""Where the impact peaks are: contact patches and peak elements at 5 % damping, on the housing seen from the front and
from the side.

Inputs: shock/results_extended/mesh_nodes_subsample.npz (40,000 nodes drawn at random from the quadratic mesh, for the
outline only) and the 5 % time histories (TETRA4 and TETRA10) in shock/results_extended/.
Writes paper/figures/hotspots.pdf and assets/figures/hotspots.png.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from fig_damping import CASES, RES, REPO, T4, T10, peaks

# contact planes (point, unit normal, tolerance in mm) of the fixed node groups, from the .comm files
PLANES = {"cyl_ymin": ((0, -136.692359, 0), (0, 1, 0), 3.0),
          "cyl_ymax": ((0, 102.879253, 0), (0, 1, 0), 5.0),
          "oblique_base_edge": ((28.03, -99.17, 0), (0, 0.70710678, 0.70710678), 3.0)}
COLOR = {"cyl_ymin": "#7B6CC2", "cyl_ymax": "#2F7FB8", "oblique_base_edge": "#D9473B"}

xyz = np.load(RES / "mesh_nodes_subsample.npz")["xyz_mm"]
p4, p10 = peaks(T4[5]), peaks(T10[5])
fig, axs = plt.subplots(1, 2, figsize=(7.4, 4.0), gridspec_kw={"width_ratios": [1.6, 1]})
for ax, (i, j, title) in zip(axs, [(1, 2, "front (y-z)"), (0, 2, "side (x-z)")]):
    ax.scatter(xyz[:, i], xyz[:, j], s=0.15, c="0.75", lw=0, rasterized=True)
    for c, (p, n, tol) in PLANES.items():
        on = np.abs((xyz - np.array(p)) @ np.array(n, float)) <= tol
        ax.scatter(xyz[on, i], xyz[on, j], s=6, marker="s", color="k", lw=0)
        for src, mk in ((p4, dict(mfc="none", mew=1.4)), (p10, dict())):
            if c in src:
                q = src[c][3]
                ax.plot(q[i], q[j], "o", ms=8, color=COLOR[c], **mk)
    ax.set_aspect("equal"); ax.set_title(title, fontsize=9)
    ax.set_xlabel(("x", "y", "z")[i] + " (mm)"); ax.set_ylabel(("x", "y", "z")[j] + " (mm)")
    ax.tick_params(labelsize=7)
handles = [plt.Line2D([], [], ls="", marker="o", color=COLOR[c], label=lab.replace("$-$", "−")) for c, lab in CASES.items()]
handles += [plt.Line2D([], [], ls="", marker="o", color="0.3", mfc="none", label="TETRA4, 5 %"),
            plt.Line2D([], [], ls="", marker="o", color="0.3", label="TETRA10, 5 %"),
            plt.Line2D([], [], ls="", marker="s", color="k", ms=4, label="fixed nodes")]
fig.legend(handles=handles, fontsize=7, ncol=3, loc="lower center", frameon=False)
fig.tight_layout(rect=(0, 0.12, 1, 1))
fig.savefig(REPO / "paper" / "figures" / "hotspots.pdf", dpi=200)
fig.savefig(REPO / "assets" / "figures" / "hotspots.png", dpi=150)   # README copy
for name, src in (("TETRA4 5 %", p4), ("TETRA10 5 %", p10)):
    for c in src:
        print(name, c, "peak %.0f MPa at %.1f ms, element centre" % src[c][:2], np.round(src[c][3]).astype(int))
print("written hotspots.pdf/png")
