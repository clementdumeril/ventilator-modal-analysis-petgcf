"""Damping ratio of the Rayleigh model at the frequencies that matter, for the three nominal levels.

C = alpha M + beta K with alpha, beta set so that zeta = zeta_n at FA = 15 Hz and FB = 300 Hz (as in
shock/extended_2026-10/make_cases_vibra.py). In between, zeta(f) = alpha / (4 pi f) + pi beta f is lower, with a minimum
of 2 sqrt(FA FB) / (FA + FB) zeta_n = 0.43 zeta_n at sqrt(FA FB) = 67 Hz.
Frequencies: first modes with the contact patch fixed (shock/results_extended/patch_blocked_modes.csv, linear elements)
and free-free modes 1 and 5 with quadratic elements (data/convergence/pub_quad).
Writes paper/tables/rayleigh.tex.
"""
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FA, FB = 15.0, 300.0
ROWS = [(15.0, "lower tuning frequency"),
        (16.6, r"mode 1 with the $-y$ patch fixed"),
        (42.6, r"mode 1 with the $+y$ patch fixed"),
        (44.0, "free-free mode 1"),
        (math.sqrt(FA * FB), "minimum of the ratio"),
        (192.1, "free-free mode 5"),
        (300.0, "upper tuning frequency")]


def zeta(f, zn):
    wa, wb = 2 * math.pi * FA, 2 * math.pi * FB
    alpha, beta = 2 * zn * wa * wb / (wa + wb), 2 * zn / (wa + wb)
    return alpha / (4 * math.pi * f) + math.pi * beta * f


lines = [r"\begin{tabular}{rlrrr}", r"\toprule",
         r"$f$ (Hz) & & \multicolumn{3}{c}{$\zeta$ (\%) for $\zeta_n=$ 2, 5, 10\,\%} \\", r"\midrule"]
for f, what in ROWS:
    lines.append(f"{f:.1f} & {what} & " + " & ".join(f"{100 * zeta(f, zn):.1f}" for zn in (0.02, 0.05, 0.10)) + r" \\")
lines += [r"\bottomrule", r"\end{tabular}"]
(REPO / "paper" / "tables" / "rayleigh.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
for f in (29.0, 151.8):
    print(f"zeta at {f} Hz for zeta_n = 5 %: {100 * zeta(f, 0.05):.2f} %")
