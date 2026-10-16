# Model assumptions

Main modeling assumptions behind the modal analysis.

## Geometry

I simplified the CAD before meshing: small faces and short edges removed, and the detailed arms replaced with plain prismatic ribs.

The V5 orientation puts the base on the `XY` plane and the height along `+Z`. This rigid transformation does not change the modes.

## Mesh

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

Real printed PETG-CF is anisotropic, with stiffness depending on print orientation, infill and layer bonding.

## Embedded masses

The motor and electronics are added as extra density in two mesh regions:

| Region | Elements | Volume (mm3) | Mass (kg) |
|---|---:|---:|---:|
| PETG-CF housing region | 278,034 | 499,125.546 | 0.648863 |
| Motor region | 23,127 | 117,900.693 | 0.243271 |
| Electronics base region | 11,616 | 87,162.950 | 0.188312 |
| Total | 312,777 | 704,189.190 | 1.080446 |

## Boundary conditions

The modal model is free-free. It gives the intrinsic modes but does not represent a fan resting on a table; mounting stiffness would need a supported model.

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
