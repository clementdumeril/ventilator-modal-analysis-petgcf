"""Impact histories at 5 % damping: quadratic elements (reference) against linear elements, 0-30 ms, and the two cases
continued to 60 ms with quadratic elements (Y- and oblique).

Inputs in shock/results_extended/: time_history_quad_zeta05.csv, time_history_quad_base_edge_zeta05.csv and
time_history_quad_zeta05_60ms.csv and time_history_quad_base_edge_zeta05_60ms.csv
(TETRA10, 5 %; the 60 ms runs have stresses from 26 ms on), time_history_zeta05.csv and
time_history_base_edge_zeta05.csv (TETRA4, 5 %), from postprocess_extended.py on the October 2026 DYNA_VIBRA runs.
Writes paper/figures/shock_history.pdf and assets/figures/shock_history.png.
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "shock" / "results_extended"
LABEL = {"cyl_ymin": "Lateral, Y$-$", "cyl_ymax": "Lateral, Y+", "oblique_base_edge": "Oblique, base edge"}
COLOR = {"cyl_ymin": "#7B6CC2", "cyl_ymax": "#2F7FB8", "oblique_base_edge": "#D9473B"}


def load(*fnames):
    rows = []
    for fname in fnames:
        if (RES / fname).exists():
            rows += list(csv.DictReader(open(RES / fname, encoding="utf-8")))
    out = {}
    for c in LABEL:
        r = {round(float(x["time_s"]) * 1e4): x for x in rows if x["case_id"] == c}   # later files win on overlaps
        r = [r[k] for k in sorted(r)]
        if r:
            out[c] = (np.array([float(x["time_s"]) for x in r]) * 1e3,
                      np.array([float(x["vmis_max_gt8mm_mpa"]) for x in r]),
                      np.array([float(x["depl_max_mm"]) for x in r]),
                      np.array([float(x["vmis_p95_gt8mm_mpa"]) for x in r]))
    return out


quad = load("time_history_quad_zeta05.csv", "time_history_quad_base_edge_zeta05.csv", "time_history_quad_zeta05_60ms.csv",
            "time_history_quad_base_edge_zeta05_60ms.csv")
lin = load("time_history_zeta05.csv", "time_history_base_edge_zeta05.csv")
fig, axs = plt.subplots(2, 1, figsize=(7.2, 5.6), sharex=True)
for c, lab in LABEL.items():
    if c in quad:
        t, s, u, _ = quad[c]
        axs[0].plot(t, s, color=COLOR[c], lw=1.4, label=f"{lab}, TETRA10")
        axs[1].plot(t, u, color=COLOR[c], lw=1.4)
    if c in lin:
        t, s, u, _ = lin[c]
        axs[0].plot(t, s, color=COLOR[c], lw=0.9, ls="--", label=f"{lab}, TETRA4")
        axs[1].plot(t, u, color=COLOR[c], lw=0.9, ls="--")
for ax in axs:
    ax.axvspan(0, 2.524, color="0.85", lw=0)
    ax.axvline(30, color="0.5", lw=0.6, ls=":")
    ax.grid(alpha=0.3)
axs[0].text(0.2, 0.92, "pulse", transform=axs[0].get_xaxis_transform(), fontsize=8)
axs[1].text(30.5, 0.04, "end of the 30 ms runs", transform=axs[1].get_xaxis_transform(), fontsize=7, color="0.4")
axs[0].set_ylabel("max von Mises,\n$>$8 mm from contact (MPa)")
axs[1].set_ylabel("max displacement (mm)"); axs[1].set_xlabel("time (ms)")
axs[0].legend(fontsize=7, ncol=2, loc="upper right")
fig.tight_layout()
fig.savefig(REPO / "paper" / "figures" / "shock_history.pdf")
fig.savefig(REPO / "assets" / "figures" / "shock_history.png", dpi=150)   # README copy
for name, src in (("TETRA10, 5 %", quad), ("TETRA4, 5 %", lin)):
    for c in src:
        t, s, u, p = src[c]
        k = int(np.argmax(s)); late = t > 30.05
        msg = f"{name} {c}: peak {s[k]:.1f} MPa at {t[k]:.1f} ms, max p95 {p.max():.1f}, u_max {u.max():.2f} mm"
        if late.any():
            j = int(np.argmax(np.where(late, s, -np.inf)))
            msg += f"; after 30 ms: max {s[j]:.1f} MPa at {t[j]:.1f} ms, u at {t[-1]:.0f} ms {u[-1]:.1f} mm"
        print(msg)
print("written shock_history.pdf/png")
