# Reproducibility notes

## What is in the repository

- `cad/`: the prepared and oriented CAD used for meshing.
- `src/mesh/`: SALOME-NETGEN meshing script (defaults are the settings of the reference mesh: min 1 mm, max 10 mm,
  fineness 2).
- `src/code_aster/`: reference modal input of June 2026 (code_aster 16.9) and its solver log.
- `data/convergence/`: inputs, mesh statistics and frequency/mass tables of the October 2026 convergence runs
  (code_aster 17.4, TETRA4 and TETRA10 on several meshes).
- `shock/code_aster/`: the June impact inputs (code_aster 17.4, `DYNA_NON_LINE`), with `shock/results/` and
  `shock/logs/`.
- `shock/extended_2026-10/`: the October impact generators (`make_cases_vibra.py`, `make_cases_modes_bc.py`),
  post-processing (`postprocess_extended.py`) and, per run series, the generated inputs, solver messages and wall times.
- `shock/results_extended/`: the time histories extracted from the October runs (CSV).
- `paper/`: the report source (`main.tex`, `references.bib`), the scripts that regenerate its tables and figures
  (`paper/scripts/`), and `paper/build_paper.sh`.
- `docs/archive/`: the June 2026 modal report (PDF and LaTeX source) and the June 2026 shock report (French), kept as
  they were published.

## Impact runs

`make_cases_vibra.py` reads the June `.comm` files (default `shock/code_aster/`, or `CHOC_SRC`), the mesh in MED format
(`CHOC_MESH`; not versioned, produced by the meshing script) and the Code_Aster launcher (`CHOC_RUN_ASTER`). Options:
`CHOC_QUAD=1` for quadratic elements, `CHOC_ZETA` (with `CHOC_FA`, `CHOC_FB`, default 15 and 300 Hz) for Rayleigh
damping, `CHOC_DT` for the time step (default 1e-4 s), `CHOC_STRESS_FROM` to compute stresses only from a given instant
(used for the 60 ms TETRA10 runs, whose stresses at every instant need more scratch space than was free) and
`CHOC_TMPDIR` for the scratch directory. Cases: `cyl_ymin`, `cyl_ymax`, `oblique_base_edge` (the June
`cyl_oblique_ymin_z` input fixes a slice through the housing and is kept only as a record).

```bash
CHOC_MESH=/path/to/carter_socle_xy_z_netgen.med CHOC_QUAD=1 CHOC_ZETA=0.05 \
  python shock/extended_2026-10/make_cases_vibra.py runs_q5 0.03 0.0002
run_aster runs_q5/cyl_ymin.export
python shock/extended_2026-10/postprocess_extended.py runs_q5 runs_q5/time_history.csv
```

This Windows build of Code_Aster prints `DIAGNOSTIC JOB : OK` even after a fatal error: check that the message file
contains no `FATAL ERROR` and that the `.rmed` file exists before post-processing.

## Report

```bash
bash paper/build_paper.sh
```

## Not versioned

Meshes (`.med`) and result files (`.rmed`, 4 to 6.5 GB per impact run) are not versioned. The numbers used in the report
come from the CSV and text files listed above.
