"""Mesh and element-order convergence of the first elastic modes (October 2026 runs).

Input: data/convergence/<case>/tables.txt (IMPR_TABLE output of Code_Aster: total mass, then NUME_MODE/FREQ)
and data/convergence/<case>/mesh_info.txt, copied from the run folders. Cases:
  pub_lin / pub_quad   published V5 mesh (95,358 nodes), TETRA4 / TETRA10
  c14f1_quad           V5 BREP remeshed, max 14 mm, fineness 1 (92,381 nodes), TETRA10
  h10_lin / h10_quad   V5 BREP remeshed, max 10 mm, fineness 2, TETRA4 / TETRA10
  f3_lin, f4_lin       V5 BREP remeshed, fineness 3 (max 10 mm) and 4 (max 6 mm), TETRA4
Writes paper/tables/convergence.tex and paper/figures/convergence.pdf.
"""
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data" / "convergence"
CASES = [("pub_lin", "published, TETRA4"), ("h10_lin", "h10, TETRA4"), ("f3_lin", "fineness 3, TETRA4"),
         ("f4_lin", "fineness 4, TETRA4"), ("c14f1_quad", "coarse (fineness 1), TETRA10"), ("pub_quad", "published, TETRA10"), ("h10_quad", "h10, TETRA10")]


def read(case):
    txt = (DATA / case / "tables.txt").read_text(encoding="utf-8", errors="ignore").splitlines()
    freqs, mass, in_freq = [], None, False
    for i, line in enumerate(txt):
        tok = line.split()
        if "MASSE" in tok and mass is None and i + 1 < len(txt):
            vals = txt[i + 1].split()
            try:
                mass = float(vals[tok.index("MASSE")])
            except (ValueError, IndexError):
                pass
        if tok and tok[-1] == "FREQ":           # header of the mode table: NUME_ORDRE NUME_MODE FREQ
            in_freq = True
            continue
        if in_freq and len(tok) >= 2 and re.fullmatch(r"\d+", tok[0]):
            freqs.append(float(tok[-1]))
        elif in_freq and freqs:
            in_freq = False
    info = (DATA / case / "mesh_info.txt").read_text(encoding="utf-8")
    nodes = int(re.search(r"(\d+) nodes", info).group(1))
    return nodes, mass, [f for f in freqs if f > 1.0][:5]


res = {c: read(c) for c, _ in CASES if (DATA / c / "tables.txt").exists()}
lines = [r"\begin{tabular}{lrrrrr}", r"\toprule",
         r"Mesh, element & nodes (corner) & mass (kg) & $f_1$ (Hz) & $f_2$ (Hz) & $f_3$ (Hz) \\", r"\midrule"]
for c, label in CASES:
    if c not in res:
        continue
    n, m, f = res[c]
    kg = m * 1e3          # Code_Aster units: mm, tonne, s
    n_tex = f"{n:,}".replace(",", r"\,")
    lines.append(rf"{label} & {n_tex} & {kg:.4f} & {f[0]:.2f} & {f[1]:.2f} & {f[2]:.2f} \\")
    print(f"{label:22s} nodes {n:7d} mass {kg:.5f} kg f1-5 {['%.2f' % x for x in f]}")
lines += [r"\bottomrule", r"\end{tabular}"]
(REPO / "paper" / "tables").mkdir(parents=True, exist_ok=True)
(REPO / "paper" / "tables" / "convergence.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

fig, axs = plt.subplots(1, 3, figsize=(9, 3.0))
for k, ax in enumerate(axs):
    lin = [(res[c][0], res[c][2][k]) for c in ("h10_lin", "f3_lin", "f4_lin") if c in res]
    if lin:
        ax.plot([a for a, _ in lin], [b for _, b in lin], "o-", label="V5 BREP, TETRA4")
    if "pub_lin" in res:
        ax.plot(res["pub_lin"][0], res["pub_lin"][2][k], "s", label="published, TETRA4")
    quad = sorted((res[c][0], res[c][2][k]) for c in ("c14f1_quad", "pub_quad", "h10_quad") if c in res)
    if quad:
        ax.plot([a for a, _ in quad], [b for _, b in quad], "D-", label="TETRA10")
    ax.set_title(f"mode {k+1}"); ax.set_xlabel("corner nodes"); ax.grid(alpha=0.3)
axs[0].set_ylabel("frequency (Hz)"); axs[0].legend(fontsize=7)
fig.tight_layout()
fig.savefig(REPO / "paper" / "figures" / "convergence.pdf")
fig.savefig(REPO / "assets" / "figures" / "convergence.png", dpi=150)   # README copy
print("written convergence.tex, convergence.pdf")
