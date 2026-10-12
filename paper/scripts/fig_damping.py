"""Impact peaks over 0-30 ms against Rayleigh damping, for linear (TETRA4) and quadratic (TETRA10) elements.

Inputs in shock/results_extended/ (postprocess_extended.py on the October 2026 DYNA_VIBRA runs):
  time_history_30ms.csv, time_history_zeta02/05/10.csv     TETRA4, lateral cases, 0 / 2 / 5 / 10 % damping
  time_history_base_edge_zeta00/02/05/10.csv              TETRA4, oblique impact on the base edge
  time_history_quad_30ms.csv, time_history_quad_zeta05.csv TETRA10, lateral cases, 0 / 5 %
  time_history_quad_base_edge_zeta05.csv                  TETRA10, oblique impact on the base edge, 5 %
The June oblique case (cyl_oblique_ymin_z), whose fixed nodes form a slice through the housing, is left out.
Peak = maximum over time of the von Mises stress more than 8 mm from the contact plane.
Writes paper/tables/shock_damping.tex.
"""
import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "shock" / "results_extended"
CASES = {"cyl_ymin": "Lateral, Y$-$", "cyl_ymax": "Lateral, Y+", "oblique_base_edge": "Oblique, base edge"}
T4 = {0: ["time_history_30ms.csv", "time_history_base_edge_zeta00.csv"],
      2: ["time_history_zeta02.csv", "time_history_base_edge_zeta02.csv"],
      5: ["time_history_zeta05.csv", "time_history_base_edge_zeta05.csv"],
      10: ["time_history_zeta10.csv", "time_history_base_edge_zeta10.csv"]}
T10 = {0: ["time_history_quad_30ms.csv"],
       5: ["time_history_quad_zeta05.csv", "time_history_quad_base_edge_zeta05.csv"]}


def peaks(fnames, t_max=0.030 + 1e-9):
    """case -> (peak stress MPa, time of peak ms, max displacement mm, (x, y, z) of the peak element), over 0-30 ms"""
    rows = []
    for fname in fnames:
        if (RES / fname).exists():
            rows += [r for r in csv.DictReader(open(RES / fname, encoding="utf-8")) if float(r["time_s"]) <= t_max]
    out = {}
    for c in CASES:
        rc = [r for r in rows if r["case_id"] == c]
        if not rc:
            continue
        top = max(rc, key=lambda r: float(r["vmis_max_gt8mm_mpa"]))
        out[c] = (float(top["vmis_max_gt8mm_mpa"]), float(top["time_s"]) * 1e3,
                  max(float(r["depl_max_mm"]) for r in rc),
                  tuple(float(top[k]) for k in ("x_max_gt8mm", "y_max_gt8mm", "z_max_gt8mm")))
    return out


if __name__ == "__main__":
    p4 = {z: peaks(f) for z, f in T4.items()}
    p10 = {z: peaks(f) for z, f in T10.items()}
    # summary table: one row per (element, damping), one column group per impact case:
    # peak (MPa), time of the peak (ms) and height z of the peak element (mm)
    head = r"Element & $\zeta$ & " + " & ".join([r"$\sigma$ & $t$ & $z$"] * len(CASES)) + r" \\"
    groups = r"& & " + " & ".join(r"\multicolumn{3}{c}{" + lab + "}" for lab in CASES.values()) + r" \\"
    lines = [r"\begin{tabular}{ll" + "rrr" * len(CASES) + "}", r"\toprule", groups, head, r"\midrule"]
    for elem, src, zs in (("TETRA4", p4, T4), ("TETRA10", p10, T10)):
        for z in zs:
            cells = []
            for c in CASES:
                v = src[z].get(c)
                cells += [f"{v[0]:.0f}", f"{v[1]:.1f}", f"{v[3][2]:.0f}"] if v else ["--", "--", "--"]
            lines.append(elem + " & " + str(z) + r"\,\% & " + " & ".join(cells) + r" \\")
            print(elem, z, cells)
    lines += [r"\bottomrule", r"\end{tabular}"]
    (REPO / "paper" / "tables").mkdir(parents=True, exist_ok=True)
    (REPO / "paper" / "tables" / "shock_damping.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("written shock_damping.tex")
