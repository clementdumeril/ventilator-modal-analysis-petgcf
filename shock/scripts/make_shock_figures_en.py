"""English figures for the README shock section, from the CSV files in shock/results/.

- shock_vmis_time.png       filtered von Mises maximum versus time, three impact cases
- shock_robust_metrics.png  max / p99 / p95 von Mises outside an 8 mm band around the contact
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SHOCK = Path(__file__).resolve().parents[1]
OUT = SHOCK.parent / "assets" / "figures"
LABELS = {"cyl_ymin": "Lateral impact, Y- side", "cyl_ymax": "Lateral impact, Y+ side",
          "cyl_oblique_ymin_z": "Oblique impact, Y- side with vertical component"}
COLORS = {"cyl_ymin": "#7B6CC2", "cyl_ymax": "#2F7FB8", "cyl_oblique_ymin_z": "#D9473B"}


def rows(name):
    with open(SHOCK / "results" / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# --- filtered von Mises versus time ---
fig, ax = plt.subplots(figsize=(9, 4.8))
temporal = rows("resume_temporel_choc_cylindrique_v1.csv")
for case, label in LABELS.items():
    r = [x for x in temporal if x["case_id"] == case]
    t = [float(x["time_s"]) * 1000 for x in r]
    s = [float(x["vmis_filtered_mpa"]) for x in r]
    ax.plot(t, s, "o-", color=COLORS[case], label=label)
ax.set_xlabel("Time (ms)"); ax.set_ylabel("Max von Mises outside contact band (MPa)")
ax.set_title("Stress build-up during the 2.5 ms acceleration pulse")
ax.grid(alpha=.3); ax.legend(fontsize=9)
plt.tight_layout(); plt.savefig(OUT / "shock_vmis_time.png", dpi=130); plt.close()

# --- robust metrics outside an 8 mm band ---
syn = {x["case_id"]: x for x in rows("synthese_robuste_choc_cylindrique_v1.csv")}
cases = list(LABELS)
short = ["Y- lateral", "Y+ lateral", "Oblique"]
xk = np.arange(len(cases)); w = 0.26
fig, ax = plt.subplots(figsize=(8.5, 4.8))
for j, (key, lab, col) in enumerate([("max_gt8", "max", "#2F7FB8"), ("p99_gt8", "p99", "#E08A2E"),
                                     ("p95_gt8", "p95", "#3E9B5B")]):
    vals = [float(syn[c][key]) for c in cases]
    bars = ax.bar(xk + (j - 1) * w, vals, w, color=col, label=lab)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.0f}", ha="center", fontsize=8)
for i, c in enumerate(cases):
    ax.text(xk[i], 128, f"raw max incl. contact: {float(syn[c]['raw']):.0f}", ha="center", fontsize=8, color="0.35")
ax.set_xticks(xk, short); ax.set_ylim(0, 135)
ax.set_ylabel("von Mises (MPa)")
ax.set_title("Stress outside an 8 mm band around the blocked contact nodes")
ax.legend(fontsize=9, loc="center right"); ax.grid(axis="y", alpha=.3)
plt.tight_layout(); plt.savefig(OUT / "shock_robust_metrics.png", dpi=130); plt.close()

print(f"Figures written to {OUT}")
