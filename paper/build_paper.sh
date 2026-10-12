#!/usr/bin/env bash
# Rebuild paper/main.pdf. Tables and figures are regenerated first from the data in the repository
# (data/convergence/ and shock/results_extended/).
set -e
cd "$(dirname "$0")/.."
python paper/scripts/fig_convergence.py
python paper/scripts/fig_campbell.py
python paper/scripts/fig_damping.py
python paper/scripts/table_rayleigh.py
python paper/scripts/fig_shock.py
python paper/scripts/fig_hotspots.py
cd paper
pdflatex -interaction=nonstopmode main.tex >/dev/null
bibtex main >/dev/null
pdflatex -interaction=nonstopmode main.tex >/dev/null
pdflatex -interaction=nonstopmode main.tex
