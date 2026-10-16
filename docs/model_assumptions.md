# Model assumptions

These are the main modeling assumptions behind the PETG-CF fan housing modal analysis.

## Geometry

I simplified the original CAD geometry before meshing: small non-structural faces removed, fewer short edges, and the highly detailed arms replaced with plain prismatic ribs. This made the tetrahedral meshing much more reliable while keeping the main load-bearing structure of the housing.

The final V5 orientation places the real base on the `XY` plane and the housing height along `+Z`. This is a rigid transformation, so it does not change the computed modes.

## Mesh

The model uses a tetrahedral finite-element mesh:

| Quantity | Value |
|---|---:|
| Element type | TETRA4 |
| Nodes | 95,358 |
| Volume elements | 312,777 |
| Mechanical degrees of freedom | 286,074 |
| Mesh volume | 704,189.190 mm3 |

## Material

The housing is modeled as equivalent isotropic PETG-CF:

| Property | Value |
|---|---:|
| Young's modulus | 6000 MPa (no documented source; carried over 3.8 to 6.0 GPa in `paper/main.pdf`) |
| Poisson ratio | 0.35 |
| Density | 1.30e-9 tonne/mm3 |

This is an engineering approximation. Real printed PETG-CF is expected to be anisotropic, with stiffness depending on print orientation, wall count, infill, temperature, and layer bonding quality.

## Embedded masses

The motor and electronic base are not modeled as detailed CAD components. Their masses are represented by increasing the equivalent density in two local mesh regions:

| Region | Elements | Volume (mm3) | Mass (kg) |
|---|---:|---:|---:|
| PETG-CF housing region | 278,034 | 499,125.546 | 0.648863 |
| Motor region | 23,127 | 117,900.693 | 0.243271 |
| Electronics base region | 11,616 | 87,162.950 | 0.188312 |
| Total | 312,777 | 704,189.190 | 1.080446 |

## Boundary conditions

The published modal model is free-free. That is fine for finding the intrinsic structural modes, but it does not represent a fan resting on a table or gasket. Evaluating the effect of mounting stiffness would need a supported modal model.

## Excitation lines

For a nominal operating speed of 2000 rpm:

| Excitation | Frequency |
|---|---:|
| 1X rotation | 33.333 Hz |
| 4X harmonic | 133.333 Hz |
| Five-blade passing frequency | 166.667 Hz |

In the June 2026 model (linear tetrahedra) the third elastic mode, at 131.946 Hz, was the closest computed mode to a
rotational harmonic. That result is superseded: linear tetrahedra overestimate the first modes by 12 to 20 %; with quadratic
elements (element-order checked), modes 3, 4 and 5 cross the 3X, 4X and blade-passing lines inside the modulus range 3.8 to 6.0 GPa
(see `paper/main.pdf`).
