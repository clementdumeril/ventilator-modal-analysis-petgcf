"""Campbell-type diagram: housing modes (stationary part, no gyroscopic terms) against rotor excitation lines.

Frequencies: quadratic tetrahedra (TETRA10) on the published mesh, data/convergence/pub_quad/tables.txt, which the
convergence study shows to be converged; the published linear-tetrahedron values (data/modal_frequencies.csv) are
drawn as open markers at the nominal speed for reference.
Each mode is drawn as a band covering E = 3.8-6.0 GPa. The model uses E = 6.0 GPa; for an isotropic material with
fixed density and Poisson ratio, K is proportional to E and the mode shapes do not change, so
f(E) = f_6GPa * sqrt(E / 6.0 GPa). 3.8 GPa is the tensile modulus reported for 30 % CF-PETG printed by FFF
(Prabhakaran et al., 2025). Writes paper/figures/campbell.pdf and prints the band edges and crossings.
"""
import csv
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[2]
E_MODEL, E_LOW, RPM = 6.0, 3.8, 2000.0


def freqs_from_table(path):
    out, on = [], False
    for line in Path(path).read_text(encoding="utf-8", errors="ignore").splitlines():
        tok = line.split()
        if tok and tok[-1] == "FREQ":
            on = True; continue
        if on and len(tok) >= 2 and re.fullmatch(r"\d+", tok[0]):
            out.append(float(tok[-1]))
        elif on and out:
            break
    return [f for f in out if f > 1.0][:5]


modes = freqs_from_table(REPO / "data" / "convergence" / "pub_quad" / "tables.txt")
with open(REPO / "data" / "modal_frequencies.csv", newline="") as f:
    lin = [float(r["frequency_hz"]) for r in csv.DictReader(f)][:5]

lines = {f"{k}X": k * RPM / 60 for k in (1, 2, 3, 4, 6)} | {"BPF": 5 * RPM / 60}
rpm = np.linspace(0, 2600, 200)
fig, ax = plt.subplots(figsize=(6.4, 4.3))
for k, f0 in enumerate(modes, 1):
    lo = f0 * math.sqrt(E_LOW / E_MODEL)
    ax.axhspan(lo, f0, color="#9BB8D8", alpha=0.45, lw=0)
    ax.axhline(f0, color="#185FA5", lw=1.0)
    ax.text(2620, (lo + f0) / 2, f"mode {k}", va="center", fontsize=7.5, color="#185FA5")
    cross = [f"{n} at E = {E_MODEL * (v / f0) ** 2:.2f} GPa" for n, v in lines.items() if lo <= v <= f0]
    print(f"mode {k}: {lo:6.1f} - {f0:6.1f} Hz (TETRA4 published: {lin[k-1]:.1f} Hz); crosses: {cross or 'none'}")
ax.plot([RPM] * 3, lin[:3], "o", mfc="none", mec="0.4", ms=5, label="June TETRA4, modes 1-3, E = 6 GPa")
# June TETRA4 modes 4-5 (251, 290 Hz): no linear-element mode lies between 132 and 228 Hz even on the finest mesh,
# and these two still fall fast with refinement; probably TETRA10 modes 4-5 overestimated (shapes not compared)
ax.plot([RPM] * 2, lin[3:5], "x", color="0.55", ms=5, label="June TETRA4, modes 4-5 (see text)")
for n in range(1, 7):
    if n == 5:
        continue
    ax.plot(rpm, n * rpm / 60, color="0.35", lw=0.8, ls="--")
    if n * RPM / 60 < 300:
        ax.text(RPM - 30, n * RPM / 60 + 3, f"{n}X", fontsize=7.5, color="0.3", ha="right")
ax.plot(rpm, 5 * rpm / 60, color="#D85A30", lw=1.2)
ax.text(1500, 5 * 1500 / 60 + 6, "BPF (5X)", fontsize=7.5, color="#D85A30")
ax.axvline(RPM, color="k", lw=0.7)
ax.set_xlim(0, 2600); ax.set_ylim(0, 300)
ax.set_xlabel("Rotor speed (rpm)"); ax.set_ylabel("Frequency (Hz)")
ax.legend(fontsize=7, loc="upper left"); ax.grid(alpha=0.25)
fig.tight_layout()
out = REPO / "paper" / "figures"; out.mkdir(parents=True, exist_ok=True)
fig.savefig(out / "campbell.pdf")
fig.savefig(REPO / "assets" / "figures" / "campbell.png", dpi=150)   # README copy
print("written", out / "campbell.pdf")
