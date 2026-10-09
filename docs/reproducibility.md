# Reproducibility Notes

This repository contains the main scientific artifacts needed to understand and reproduce the modal-analysis workflow.

## Included Artifacts

- CAD exchange files in `cad/`.
- Code_Aster command and export files in `src/code_aster/`.
- Code_Aster solver log in `src/code_aster/solver_log_code_aster.txt`.
- Post-processing scripts in `src/postprocessing/`.
- English LaTeX report source in `paper/`.
- Compiled PDF report in `reports/`.
- Result tables in `data/`.
- README figures and first-mode animation in `assets/`.
- SALOME-NETGEN meshing script in `src/mesh/` (defaults = settings of the published mesh: min 1 mm, max 10 mm, fineness 2).
- Drop-shock study in `shock/`: Code_Aster 17.4 `.comm`/`.export` files for the three shroud impact cases and the two
  base-drop levels, solver logs, result CSVs, post-processing scripts. Report (French): `docs/shock_report_fr.pdf`.

## External Tools

The original workflow used:

- FreeCAD for CAD preparation and exchange;
- SALOME/SMESH with NETGEN tetrahedral meshing;
- Code_Aster for finite-element modal solving;
- ParaViS/ParaView for result visualization;
- Python for post-processing figures and sensitivity plots;
- LaTeX for scientific report generation.

## Report Dates

The modal report (`paper/`, `reports/`) is dated 15 June 2026. Its "Drop or Shock Analysis Feasibility" section was
written before the shock runs of 24 June; the shock results are in `shock/` and `docs/shock_report_fr.pdf`.

## Report Compilation

From the `paper/` directory:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error -jobname=modal_report_petgcf_v5_en main.tex
bibtex modal_report_petgcf_v5_en
pdflatex -interaction=nonstopmode -halt-on-error -jobname=modal_report_petgcf_v5_en main.tex
pdflatex -interaction=nonstopmode -halt-on-error -jobname=modal_report_petgcf_v5_en main.tex
```

## Large Numerical Results

Some large binary solver outputs are not versioned in this portfolio repository to keep it readable for review. The numerical results are documented in:

- `reports/modal_report_petgcf_v5_en.pdf`
- `data/modal_frequencies.csv`
- `src/code_aster/solver_log_code_aster.txt`
- `shock/results/` (shock maxima, time histories and robust metrics) and `shock/logs/`

For a production-grade scientific archive, the mesh and result binaries should be deposited separately as release assets or in a data repository with checksums.
