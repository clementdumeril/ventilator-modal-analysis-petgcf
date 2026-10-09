"""Tetrahedral NETGEN mesh of the prepared housing CAD in SALOME (run with: salome shell -- python mesh_carter_netgen.py).

Input BREP, output MED/HDF and size parameters (max/min size, fineness, threads) are set through the
CARTER_* environment variables below.
"""
import os

import salome

salome.salome_init()

import GEOM
import SMESH
import SALOMEDS
from salome.geom import geomBuilder
from salome.smesh import smeshBuilder


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
BREP_PATH = os.environ.get("CARTER_BREP_PATH", os.path.join(ROOT, "carter_modal_v1.brep"))
MED_PATH = os.environ.get("CARTER_MED_PATH", os.path.join(OUT_DIR, "carter_modal_v1_coarse.med"))
HDF_PATH = os.environ.get("CARTER_HDF_PATH", os.path.join(OUT_DIR, "carter_modal_v1_mesh.hdf"))

MAX_SIZE = float(os.environ.get("CARTER_MAX_SIZE", "14.0"))
MIN_SIZE = float(os.environ.get("CARTER_MIN_SIZE", "2.0"))
FINENESS = int(os.environ.get("CARTER_FINENESS", "2"))
NB_THREADS = int(os.environ.get("CARTER_MESH_THREADS", "4"))


def main():
    geompy = geomBuilder.New()
    smesh = smeshBuilder.New()

    shape = geompy.ImportBREP(BREP_PATH)
    if shape is None:
        raise RuntimeError("ImportBREP returned None")
    geompy.addToStudy(shape, "carter_modal_v1")

    mesh = smesh.Mesh(shape, "carter_modal_v1_tetra")
    algo = mesh.Tetrahedron(smeshBuilder.FULL_NETGEN)
    params = algo.Parameters()
    params.SetMaxSize(MAX_SIZE)
    params.SetMinSize(MIN_SIZE)
    params.SetFineness(FINENESS)
    params.SetSecondOrder(0)
    params.SetOptimize(1)
    params.SetUseSurfaceCurvature(1)
    params.SetFuseEdges(1)
    try:
        params.SetNbThreads(NB_THREADS)
    except Exception:
        pass

    print("BREP:", BREP_PATH)
    print("MED:", MED_PATH)
    print("mesh_max_size:", MAX_SIZE)
    print("mesh_min_size:", MIN_SIZE)
    print("mesh_fineness:", FINENESS)

    done = mesh.Compute()
    if not done:
        for item in mesh.GetLog(0):
            print(item)
        raise RuntimeError("SMESH/NETGEN failed to compute the mesh")

    print("nodes:", mesh.NbNodes())
    print("edges:", mesh.NbEdges())
    print("faces:", mesh.NbFaces())
    print("triangles:", mesh.NbTriangles())
    print("volumes:", mesh.NbVolumes())
    print("tetras:", mesh.NbTetras())

    mesh.ExportMED(MED_PATH, False, 41, True, None, False, [], "", -1.0, True)
    salome.myStudy.SaveAs(HDF_PATH, False, False)


if __name__ == "__main__":
    main()
