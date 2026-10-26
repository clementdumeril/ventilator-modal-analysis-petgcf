# Natural frequencies and impact response of a 3D-printed PETG-CF fan housing

I used Code_Aster to study a desk-fan housing printed in carbon-fiber PETG: free-free modes compared against the rotor harmonics at 2000 rpm, and three damped impact cases followed to 30 ms.

<p align="center">
  <img src="assets/animations/mode_001_vibration.gif" width="640"><br>
  <em>First elastic mode (shape from the June linear-element run; deformation amplified).</em>
</p>

This was an internal study at Polytechnia, the engineering consultancy I co-founded in 2026, not a client deliverable. The airflow and noise of the same fan are in [ducted-fan-aeroacoustics](https://github.com/clementdumeril/ducted-fan-aeroacoustics). The full report is [`paper/main.pdf`](paper/main.pdf).

## Results

With quadratic elements, the first mode is at 35 to 44 Hz over E = 3.8 to 6 GPa, where 3.8 GPa is the published value for printed PETG with 30 % carbon fiber. At 2000 rpm the rotor lines are at 33.3, 66.7, 100 and 133.3 Hz, with the BPF at 166.7 Hz. Within that modulus range modes 3, 4 and 5 cross the 3X, 4X and BPF lines (at E ≈ 5.0, 4.6 and 4.5 GPa), so I can't rule out a resonance without measuring the printed part.

<p align="center">
  <img src="assets/figures/campbell.png" width="75%"><br>
  <em>Each band spans a mode for E = 3.8 GPa (bottom) to 6.0 GPa (top).</em>
</p>

Impact, 0 to 30 ms, quadratic elements, nominal 5 % Rayleigh damping:

| Impact case | Peak von Mises > 8 mm from contact | Time | Location |
|---|---:|---:|---|
| Lateral, Y- (shroud touches the floor) | 174 MPa | 27.4 ms | upper arm to shroud |
| Lateral, Y+ (stand touches the floor) | 114 MPa | 3.0 ms | upper arm to motor hub |
| Oblique 45°, base edge touches the floor | 139 MPa | 8.2 ms | stand to shroud |

The peaks are local (95th percentile below 23 MPa) and sit at junctions where I simplified the arms to plain ribs. A linear model does not predict cracking, but these junctions have no margin for a fall this severe.

<p align="center">
  <img src="assets/figures/hotspots.png" width="80%"><br>
  <em>Fixed nodes per case and the three peak locations.</em>
</p>

## Corrections

When I reran the June 2026 study in October 2026, the June frequencies of modes 1 to 3 were 12 to 20 % too high (linear elements; June modes 4 and 5 do not match the quadratic ones at all, so those two crossings rest on the quadratic runs only), the impact runs stopped too early, and one impact case fixed a slice of the housing instead of a contact patch. The numbers above are from the October runs.

## Limitations

- No material property was measured. The model is isotropic and linear elastic, while a printed part is anisotropic.
- The modes are free-free, and the impact model has no contact law or rebound (the patch stays clamped).
- There is no tap test, accelerometer measurement or drop test yet.

## Running it

Requires Code_Aster 17.4 (16.9 for the June reference modal run), SALOME 9.13, Python >= 3.10 (`pip install -r requirements.txt`), and LaTeX.

```bash
CARTER_BREP_PATH=cad/fan_housing_meshprep_v5_xy_z.brep salome -t src/mesh/mesh_carter_netgen.py   # mesh
run_aster src/code_aster/carter_modal_petgcf_composants_v5_socle_xy_z.export                      # June linear-element reference (Code_Aster 16.9, superseded; edit the paths first)
bash paper/build_paper.sh                                                                          # figures and report
```

The quadratic modes reported above come from [`data/convergence/pub_quad/case.comm`](data/convergence/pub_quad/case.comm) (Code_Aster 17.4, mesh on UNITE 20). Impact runs: [`docs/reproducibility.md`](docs/reproducibility.md). Model assumptions: [`docs/model_assumptions.md`](docs/model_assumptions.md). Meshes and `.rmed` results are not versioned.

## Credits

- Fan CAD: Polytechnia FreeCAD model. CAD preparation, meshing, Code_Aster models, post-processing and report: Clément Dumeril.
- Tools: Code_Aster (EDF), SALOME-NETGEN, ParaView, FreeCAD.

[clement.dumeril.net](https://clement.dumeril.net) · [github.com/clementdumeril](https://github.com/clementdumeril) · MIT license
