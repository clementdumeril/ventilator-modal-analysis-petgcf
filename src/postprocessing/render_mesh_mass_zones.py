"""Render the V5 NETGEN mesh with the two embedded-mass zones, and recount the zone elements.

Reads the MED mesh with h5py (no SALOME needed), selects the TETRA4 elements whose nodes are
at least half inside each sphere (same rule as CRIT_NOEUD='MAJORITE' in the .comm file), prints the
element counts and volumes, and writes assets/figures/mesh_mass_zones.png with VTK.

usage: python render_mesh_mass_zones.py <mesh.med>
The .med file (about 30 MB) is not versioned; it is regenerated from cad/ with SALOME-NETGEN.
"""
import sys
from pathlib import Path

import h5py
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray

REPO = Path(__file__).resolve().parents[2]
ZONES = {  # centre (mm), radius (mm): from carter_modal_petgcf_composants_v5_socle_xy_z.comm
    "motor": ((23.093853, -45.158407, 163.598992), 30.0, (0.90, 0.45, 0.10)),
    "electronics": ((24.323447, 9.996963, 52.043480), 45.0, (0.20, 0.60, 0.30)),
}

with h5py.File(sys.argv[1], "r") as f:
    mesh = f["ENS_MAA"][next(iter(f["ENS_MAA"]))]
    step = mesh[next(iter(mesh))]
    xyz = step["NOE/COO"][:].reshape(3, -1).T            # MED stores coordinates component-wise
    tet = step["MAI/TE4/NOD"][:].reshape(4, -1).T - 1     # 1-based, component-wise
    tri = step["MAI/TR3/NOD"][:].reshape(3, -1).T - 1


def tet_volume(t):
    a, b, c, d = (xyz[t[:, i]] for i in range(4))
    return np.abs(np.einsum("ij,ij->i", b - a, np.cross(c - a, d - a))) / 6


print(f"nodes {len(xyz)}, TETRA4 {len(tet)}, skin TRIA3 {len(tri)}, volume {tet_volume(tet).sum():.0f} mm3")


def polydata(cells, ncorner):
    pd = vtk.vtkUnstructuredGrid()
    pts = vtk.vtkPoints(); pts.SetData(numpy_to_vtk(xyz, deep=True)); pd.SetPoints(pts)
    conn = np.hstack([np.full((len(cells), 1), ncorner), cells]).ravel()
    arr = vtk.vtkCellArray(); arr.SetCells(len(cells), numpy_to_vtkIdTypeArray(conn.astype(np.int64), deep=True))
    pd.SetCells(vtk.VTK_TETRA if ncorner == 4 else vtk.VTK_TRIANGLE, arr)
    return pd


ren = vtk.vtkRenderer(); ren.SetBackground(1, 1, 1)
skin = vtk.vtkDataSetMapper(); skin.SetInputData(polydata(tri, 3))
a = vtk.vtkActor(); a.SetMapper(skin)
a.GetProperty().SetColor(0.75, 0.78, 0.82); a.GetProperty().SetOpacity(0.35)
a.GetProperty().EdgeVisibilityOn(); a.GetProperty().SetEdgeColor(0.35, 0.38, 0.42); a.GetProperty().SetLineWidth(0.4)
ren.AddActor(a)

for name, (c, r, col) in ZONES.items():
    inside = (np.linalg.norm(xyz - np.array(c), axis=1) <= r)[tet].sum(1) >= 2
    print(f"{name:12s} {inside.sum():6d} TETRA4, {tet_volume(tet[inside]).sum():.0f} mm3")
    surf = vtk.vtkDataSetSurfaceFilter(); surf.SetInputData(polydata(tet[inside], 4))
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(surf.GetOutputPort())
    z = vtk.vtkActor(); z.SetMapper(m); z.GetProperty().SetColor(*col)
    ren.AddActor(z)

for i, (txt, col) in enumerate([("TETRA4 mesh, 95,358 nodes (skin shown)", (0.3, 0.3, 0.3)),
                                ("motor zone: +0.090 kg", ZONES["motor"][2]),
                                ("electronics zone: +0.075 kg", ZONES["electronics"][2])]):
    t = vtk.vtkTextActor(); t.SetInput(txt); t.SetDisplayPosition(30, 960 - 34 * i)
    t.GetTextProperty().SetFontSize(24); t.GetTextProperty().SetColor(*col); ren.AddActor2D(t)

centre = xyz.mean(0); size = np.ptp(xyz, 0).max()
cam = ren.GetActiveCamera(); cam.SetFocalPoint(*centre)
cam.SetPosition(*(centre + 2.6 * size * np.array([0.75, -0.55, 0.38]))); cam.SetViewUp(0, 0, 1)
ren.ResetCameraClippingRange()
win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.AddRenderer(ren); win.SetSize(1400, 1000)
win.Render()
w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(win); w2i.Update()
out = vtk.vtkPNGWriter(); out.SetFileName(str(REPO / "assets" / "figures" / "mesh_mass_zones.png"))
out.SetInputConnection(w2i.GetOutputPort()); out.Write()
print("written assets/figures/mesh_mass_zones.png")
