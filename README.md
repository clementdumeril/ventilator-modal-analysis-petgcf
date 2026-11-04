# PETG-CF fan housing: Code_Aster modal and impact analysis of a 3D-printed desk-fan housing

With quadratic tetrahedra, the first free-free mode of the printed PETG-CF housing lies at 35 to 44 Hz over the plausible modulus range (E = 3.8 to 6 GPa), modes 3 to 5 cross rotor lines at 2000 rpm inside that range, and three damped impact cases (251 g, 2.5 ms pulse) followed to 30 ms give local von Mises peaks of 114 to 174 MPa at the arm and stand junctions.

[Report (PDF)](paper/main.pdf) · [Model assumptions](docs/model_assumptions.md) · [Reproducibility](docs/reproducibility.md) · [Airflow and noise: ducted-fan-aeroacoustics](https://github.com/clementdumeril/ducted-fan-aeroacoustics) · [Cite](CITATION.cff)

<p align="center">
  <img src="assets/animations/mode_001_vibration.gif" width="640" alt="First elastic mode of the fan housing"><br>
  <em>First elastic mode (shape from the June linear-element run; deformation amplified).</em>
</p>

## Overview

This was an internal study at Polytechnia, the engineering consultancy I co-founded in 2026, not a client deliverable. The question was whether the printed housing of a desk fan has a natural frequency near the rotor lines and whether it survives a fall. The airflow and noise of the same fan are in [ducted-fan-aeroacoustics](https://github.com/clementdumeril/ducted-fan-aeroacoustics), which runs the rotor at 1509 rpm; this study checks the lines at a nominal 2000 rpm, so the two operating points should not be mixed.

Mine: CAD preparation for meshing, the NETGEN meshes, the Code_Aster modal and impact models, the convergence and verification runs, the post-processing and the report. Reused: the fan CAD (Polytechnia FreeCAD model), Code_Aster (EDF), SALOME-NETGEN and ParaView.

```mermaid
flowchart LR
    cad["Prepared CAD<br/>cad/*.step, *.brep"] -->|"defeatured solid"| mesh["SALOME-NETGEN<br/>mesh_carter_netgen.py<br/>TETRA4 / TETRA10"]
    mesh -->|".med mesh, mass zones"| modal["Code_Aster CALC_MODES<br/>free-free, 1-1500 Hz"]
    modal -->|"f_i (Hz), mass (kg)"| mt[("data/convergence/*/tables.txt")]
    mesh -->|".med mesh, fixed patch"| shock["Code_Aster DYNA_VIBRA<br/>make_cases_vibra.py<br/>251 g pulse, 0-30 ms"]
    shock -->|"von Mises > 8 mm from contact (MPa)"| sc[("shock/results_extended/*.csv")]
    mt --> fig["paper/scripts/<br/>Campbell, convergence,<br/>impact figures and tables"]
    sc --> fig
```

*Modal and impact chains and the committed files at each step. Meshes and `.rmed` results are not versioned.*

## Formulation

**Geometry and mesh.** The FreeCAD model was defeatured for meshing (small faces and short edges removed, support arms replaced by plain ribs; volume −1.4 %). Reference mesh: NETGEN, 1 to 10 mm, fineness 2, 95,358 nodes and 312,777 tetrahedra, run with linear (TETRA4) and quadratic (TETRA10) elements.

**Material and masses.** Isotropic linear-elastic PETG-CF, E = 6.0 GPa (no documented source; results carried over 3.8 to 6.0 GPa, 3.8 GPa being the published value for printed PETG with 30 % carbon fiber), ν = 0.35, ρ = 1300 kg/m³. Motor (0.090 kg) and electronics (0.075 kg) are estimated masses added as extra density in two spherical element groups, without stiffness. Total mass 1.080 kg.

**Modal problem.** Free-free, K φ = ω² M φ, solved with `CALC_MODES` (shift-invert Lanczos, Sturm count) in 1 to 1500 Hz. Since K is proportional to E, f(E) = f(6 GPa) √(E / 6 GPa) exactly. Rotor lines at 2000 rpm: 33.3, 66.7, 100 and 133.3 Hz (1X to 4X) and BPF 166.7 Hz.

**Impact model.** The nodes of a small patch where the housing touches the floor are fixed, and the rest receives a uniform triangular acceleration pulse (2.524 ms, 251 g peak, Δv = 3.11 m/s, about a 0.5 m free fall with no rebound): M ü + K u = −M e a(t). No contact law, friction or rebound. Three directions: lateral −y (shroud touches), lateral +y (stand touches), oblique 45° (base edge touches). `DYNA_VIBRA`, Newmark average acceleration (β = 1/4, γ = 1/2), Δt = 0.1 ms to 30 ms, Rayleigh damping with nominal ζ = 5 % at 15 and 300 Hz (2.1 to 2.9 % between 29 and 152 Hz). Stress is reported over elements more than 8 mm from the contact plane, to stay clear of the patch singularity.

## Results

| Quantity (TETRA10) | Value | Source |
|---|---|---|
| Mode 1, free-free, E = 3.8 to 6.0 GPa | 35.0 to 44.0 Hz | `data/convergence/pub_quad/tables.txt`, `paper/scripts/fig_campbell.py` |
| Crossings of rotor lines inside that range | mode 3 with 3X at E = 4.97 GPa, mode 4 with 4X at 4.63 GPa, mode 5 with BPF at 4.52 GPa | same script |
| Impact, lateral −y (5 % damping) | 174 MPa at 27.4 ms, upper arm to shroud | `shock/results_extended/time_history_quad_zeta05.csv`, `paper/scripts/fig_shock.py` |
| Impact, lateral +y | 114 MPa at 3.0 ms, upper arm to motor hub | same |
| Impact, oblique on the base edge | 139 MPa at 8.2 ms, stand to shroud | `time_history_quad_base_edge_zeta05.csv`, same script |
| 95th percentile of von Mises, all three cases | below 23 MPa | same |

<p align="center">
  <img src="assets/figures/campbell.png" width="75%" alt="Campbell-style diagram of modes against rotor lines"><br>
  <em>Each band spans a mode for E = 3.8 GPa (bottom) to 6.0 GPa (top), against the rotor lines at 2000 rpm.</em>
</p>

So a resonance at 2000 rpm cannot be ruled out without measuring the printed part. The impact peaks are local and sit at junctions where the arms were simplified to plain ribs. A linear model does not predict cracking, but these junctions have no margin for a fall this severe.

<p align="center">
  <img src="assets/figures/hotspots.png" width="80%" alt="Fixed nodes per impact case and the three peak locations"><br>
  <em>Fixed nodes per case and the three peak locations.</em>
</p>

## Verification

| Check | Result | Source |
|---|---|---|
| Element order and mesh, modes 1 to 3 | TETRA10 on four meshes (92,381 to 123,454 nodes) within 1 %: mode 1 43.88 to 44.08 Hz; TETRA4 keeps falling with refinement (49.2 → 46.5 Hz) | `data/convergence/*/tables.txt`, `paper/scripts/fig_convergence.py` |
| Independent estimate | Richardson extrapolation of the two finest TETRA4 meshes: 43.6 / 64.2 / 111.9 Hz, within 1 to 2 % of TETRA10 | same script |
| Mode count | Sturm count 21 eigenvalues in 1 to 1500 Hz, 21 modes computed (June reference run) | `src/code_aster/solver_log_code_aster.txt` |
| Transient solver | `DYNA_VIBRA` reproduces the June `DYNA_NON_LINE` run at every instant to 2.5 ms (79.82 MPa, p95 7.07 MPa, 4.24 mm for −y) | `shock/results_extended/validation_2p5ms_history.csv`, `june_2p5ms_history.csv` |
| Time step | halving Δt to 0.05 ms over 15 ms changes the stress history by at most 0.4 %; peak unchanged at 152.2 MPa (TETRA4, undamped) | `time_history_dt5e-5.csv` vs `time_history_30ms.csv` |
| Contact patches | the June oblique plane fixed a 1091-node slice through the housing; replaced by a plane through the base-edge node; lateral planes have no node beyond them | `shock/extended_2026-10/contact_planes_check.txt` |
| Window length | the −y and oblique TETRA10 runs continued to 60 ms reach at most 163 and 118 MPa after 30 ms | `time_history_quad_zeta05_60ms.csv`, `time_history_quad_base_edge_zeta05_60ms.csv` |

The TETRA10 meshes are close in size, so they show that the quadratic results are insensitive to the mesh rather than prove convergence. The impact peaks are not mesh-converged (+3 to +26 % from TETRA4 to TETRA10).

## How to run

The paper scripts need only NumPy and Matplotlib and read the committed tables and CSV files. Tested on Windows 10 with Python 3.11.9, NumPy 2.2.6 and Matplotlib 3.10.6 (November 2026: all six scripts in `paper/scripts/` reprinted the numbers above). Code_Aster 17.4 was used for the convergence and October impact runs, 16.9 for the June reference modal run, and SALOME 9.13 for meshing.

```bash
pip install -r requirements.txt
python paper/scripts/fig_campbell.py      # mode bands and crossing moduli
python paper/scripts/fig_convergence.py   # convergence table and Richardson estimate
python paper/scripts/fig_shock.py         # impact peaks, times, p95
bash paper/build_paper.sh                 # all figures and tables, then the report (needs LaTeX)

CARTER_BREP_PATH=cad/fan_housing_meshprep_v5_xy_z.brep salome -t src/mesh/mesh_carter_netgen.py   # mesh
run_aster src/code_aster/carter_modal_petgcf_composants_v5_socle_xy_z.export                      # June TETRA4 reference (16.9; edit the paths first)
```

The quadratic modes come from [`data/convergence/pub_quad/case.comm`](data/convergence/pub_quad/case.comm) (Code_Aster 17.4, mesh on UNITE 20). Impact runs: [`docs/reproducibility.md`](docs/reproducibility.md). The paper scripts overwrite the committed figures in `paper/figures/` and `assets/figures/`.

## Reproducing figures

| Figure | Script |
|---|---|
| `assets/figures/campbell.png`, `paper/figures/campbell.pdf` | `paper/scripts/fig_campbell.py` |
| `assets/figures/convergence.png`, `paper/figures/convergence.pdf`, `paper/tables/convergence.tex` | `paper/scripts/fig_convergence.py` |
| `assets/figures/shock_history.png`, `paper/figures/shock_history.pdf` | `paper/scripts/fig_shock.py` |
| `assets/figures/hotspots.png`, `paper/figures/hotspots.pdf` | `paper/scripts/fig_hotspots.py` |
| `paper/tables/shock_damping.tex`, `paper/tables/rayleigh.tex` | `paper/scripts/fig_damping.py`, `paper/scripts/table_rayleigh.py` |
| `assets/animations/mode_001_vibration.gif` | June 2026 ParaView render of the TETRA4 mode (script not in the repo) |

## Code structure

| Path | Content |
|---|---|
| `cad/` | defeatured housing (STEP, BREP) used for meshing |
| `src/mesh/`, `src/code_aster/` | NETGEN meshing script; June reference modal input and solver log |
| `src/postprocessing/` | June figure and mass-zone render scripts |
| `data/convergence/` | October modal runs: input, mesh statistics and frequency/mass table per mesh and element order |
| `shock/code_aster/`, `shock/results/` | June impact inputs and results (kept as a record) |
| `shock/extended_2026-10/`, `shock/results_extended/` | October impact generators, inputs, solver messages, contact-plane check, time histories |
| `paper/` | report source, figure and table scripts, PDF |
| `docs/` | model assumptions, reproducibility notes, June reports in `docs/archive/` |
| `web/` | June web summary (superseded numbers) |

## Corrections

When I reran the June 2026 study in October 2026, the June frequencies of modes 1 to 3 were 12 to 20 % too high (linear elements; June modes 4 and 5 do not match the quadratic ones at all, so those two crossings rest on the quadratic runs only), the impact runs stopped too early, and one impact case fixed a slice of the housing instead of a contact patch. The numbers above are from the October runs.

## Limitations

- No material property was measured. The model is isotropic and linear elastic, while a printed part is anisotropic; component masses are estimates.
- The modes are free-free, with no mounting stiffness. The impact patch stays clamped after the pulse, the pulse is uniform over the housing, and there is no contact law or rebound, so the late −y peak may be an artifact of the clamped patch.
- The impact peaks are local and not mesh-converged.
- There is no tap test, accelerometer measurement or drop test yet.

## Citation, license, credits

Cite with [`CITATION.cff`](CITATION.cff) or the report. MIT license, see [LICENSE](LICENSE).

- Fan CAD: Polytechnia FreeCAD model. CAD preparation, meshing, Code_Aster models, post-processing and report: Clément Dumeril.
- Tools: Code_Aster (EDF), SALOME-NETGEN, ParaView, FreeCAD. The 3.8 GPa modulus is from Prabhakaran et al. 2025, cited in [`paper/references.bib`](paper/references.bib).

Clément Dumeril · [clement.dumeril.net](https://clement.dumeril.net) · [github.com/clementdumeril](https://github.com/clementdumeril)
