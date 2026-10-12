"""Check the fixed-node groups of the impact cases against the mesh.

Each case fixes the nodes within a tolerance of a plane (CREA_GROUP_NO OPTION='PLAN' in the .comm files). For a contact
patch the plane must be tangent to the housing: no node may lie beyond it, on the floor side. For each case this script
prints the number of fixed nodes, their bounding box, and the number of nodes beyond the plane by more than the
tolerance. The floor side is the side the housing moves towards, i.e. the pulse direction of the case.

usage: python check_contact_planes.py <mesh.med> > contact_planes_check.txt
(the mesh is the linear NETGEN mesh used by all impact runs; not versioned)
"""
import sys

import h5py
import numpy as np

# case: (point, unit normal, tolerance mm, pulse direction), from the .comm files
CASES = {
    "cyl_ymin": ((0.0, -136.692359, 0.0), (0.0, 1.0, 0.0), 3.0, (0.0, -1.0, 0.0)),
    "cyl_ymax": ((0.0, 102.879253, 0.0), (0.0, 1.0, 0.0), 5.0, (0.0, 1.0, 0.0)),
    "cyl_oblique_ymin_z (June)": ((-6.31, -135.05, 164.18), (0.0, 0.70710678, 0.70710678), 1.0,
                                  (0.0, -0.70710678, -0.70710678)),
    "oblique_base_edge": ((28.03, -99.17, 0.0), (0.0, 0.70710678, 0.70710678), 3.0, (0.0, -0.70710678, -0.70710678)),
}

with h5py.File(sys.argv[1], "r") as f:
    maa = f["ENS_MAA"][next(iter(f["ENS_MAA"]))]
    st = maa[next(iter(maa))]
    xyz = st["NOE/COO"][:].reshape(3, -1).T
print(f"mesh {sys.argv[1]}: {len(xyz)} nodes")
for case, (p, n, tol, a) in CASES.items():
    n = np.array(n); s = np.sign(n @ np.array(a))          # +1 if the floor is on the +n side
    d = (xyz - np.array(p)) @ n
    fixed = np.abs(d) <= tol
    beyond = s * d > tol
    lo, hi = xyz[fixed].min(0), xyz[fixed].max(0)
    print(f"{case}: {fixed.sum()} fixed nodes, bbox x {lo[0]:.1f}..{hi[0]:.1f} y {lo[1]:.1f}..{hi[1]:.1f} "
          f"z {lo[2]:.1f}..{hi[2]:.1f} mm; {beyond.sum()} nodes beyond the plane on the floor side")
i = np.argmin(xyz @ np.array([0.0, 0.70710678, 0.70710678]))
print(f"node minimising y+z (first contact of a 45 degree fall towards -y, -z): {np.round(xyz[i], 2)}")
