"""Where the impact peaks are: contact patches and peak elements at nominal 5 % damping, on the housing seen from the
front and from the side.

Inputs: shock/results_extended/mesh_nodes_subsample.npz (40,000 nodes drawn at random from the quadratic mesh, for the
outline only) and the 5 % time histories (TETRA4 and TETRA10) in shock/results_extended/.
Peaks closer than 6 mm to each other are drawn as one location, labelled with the runs that peak there.
Writes paper/figures/hotspots.pdf and assets/figures/hotspots.png.
"""
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
SHORT = {"cyl_ymin": "Y−", "cyl_ymax": "Y+", "oblique_base_edge": "oblique"}
# part names, placed by hand in the front view (y, z) in mm
PARTS = {"shroud": (-60, 262), "hub": (-40, 140), "arm": (-88, 215), "stand": (95, 60), "base": (-60, 40)}

xyz = np.load(RES / "mesh_nodes_subsample.npz")["xyz_mm"]
runs = []                                                     # (case, element, peak MPa, (x, y, z))
for elem, src in (("T4", peaks(T4[5])), ("T10", peaks(T10[5]))):
    for c, v in src.items():
        runs.append((c, elem, v[0], np.array(v[3])))
spots = []                                                    # group peaks closer than 6 mm
for r in runs:
    for s in spots:
        if np.linalg.norm(s[0][3] - r[3]) < 6:
            s.append(r); break
    else:
        spots.append([r])

fig, axs = plt.subplots(1, 2, figsize=(7.6, 4.4), gridspec_kw={"width_ratios": [1.6, 1]})
for ax, (i, j, title) in zip(axs, [(1, 2, "front (y-z)"), (0, 2, "side (x-z)")]):
    ax.scatter(xyz[:, i], xyz[:, j], s=0.15, c="0.78", lw=0, rasterized=True)
    for c, (p, n, tol) in PLANES.items():
        on = np.abs((xyz - np.array(p)) @ np.array(n, float)) <= tol
        ax.scatter(xyz[on, i], xyz[on, j], s=7, marker="s", color=COLOR[c], lw=0)
    for k, s in enumerate(spots):
        q = np.mean([r[3] for r in s], axis=0)
        ax.plot(q[i], q[j], "o", ms=9, mfc="white", mec="k", mew=1.2)
        ax.text(q[i], q[j], "ABC"[k], ha="center", va="center", fontsize=7, fontweight="bold")
    ax.set_aspect("equal"); ax.set_title(title, fontsize=9)
    ax.set_xlabel(("x", "y", "z")[i] + " (mm)"); ax.set_ylabel(("x", "y", "z")[j] + " (mm)")
    ax.tick_params(labelsize=7)
for name, (y, z) in PARTS.items():
    axs[0].text(y, z, name, fontsize=7, color="0.25", style="italic", ha="center")
patches = [plt.Line2D([], [], ls="", marker="s", color=COLOR[c], ms=5, label=f"fixed nodes, {SHORT[c]}") for c in CASES]
fig.legend(handles=patches, fontsize=7, ncol=3, loc="lower center", frameon=False, bbox_to_anchor=(0.5, 0.075))
text = "   ".join(f"{'ABC'[k]}: " + ", ".join(f"{SHORT[r[0]]} {r[1]} {r[2]:.0f} MPa" for r in s) for k, s in enumerate(spots))
fig.text(0.5, 0.025, text, ha="center", fontsize=7)
fig.tight_layout(rect=(0, 0.13, 1, 1))
fig.savefig(REPO / "paper" / "figures" / "hotspots.pdf", dpi=200)
fig.savefig(REPO / "assets" / "figures" / "hotspots.png", dpi=150)   # README copy
for k, s in enumerate(spots):
    print("ABC"[k], np.round(np.mean([r[3] for r in s], axis=0)).astype(int), [(r[0], r[1], round(r[2])) for r in s])
print("written hotspots.pdf/png")
