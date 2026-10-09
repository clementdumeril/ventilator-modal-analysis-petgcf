"""Export the Code_Aster .rmed shock results to ParaView .vtm/.pvd series (paths are hard-coded below).
"""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape
import os

import h5py
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ORIGINAL_RMED_DIR = Path(
    r"D:\v2025\carter_modal_v1_analysis\ETUDE_CHOC_CARTER_CYLINDRIQUE_V1\04_RESULTATS"
)
RESULT_DIR = Path(os.environ.get("CARTER_RMED_DIR", DEFAULT_ORIGINAL_RMED_DIR))
OUT_DIR = ROOT / "04_RESULTATS_VTM"

CASES = [
    "cyl_ymin",
    "cyl_ymax",
    "cyl_oblique_ymin_z",
]

KEEP_SIEQ = {"VMIS", "TRESCA", "PRIN_1", "PRIN_2", "PRIN_3", "TRSIG", "TRIAX"}
KEEP_SIEF = {"SIXX", "SIYY", "SIZZ", "SIXY", "SIXZ", "SIYZ"}


def med_names(raw: bytes, width: int = 16) -> list[str]:
    text = raw.decode("ascii", errors="ignore")
    return [text[i : i + width].strip() for i in range(0, len(text), width) if text[i : i + width].strip()]


def read_mesh(file: h5py.File) -> tuple[np.ndarray, np.ndarray]:
    base = "ENS_MAA/00000001/-0000000000000000001-0000000000000000001"
    coo = file[f"{base}/NOE/COO"]
    node_count = int(coo.attrs["NBR"])
    nodes = coo[()].reshape((3, node_count)).T.astype(np.float64, copy=False)

    nod = file[f"{base}/MAI/TE4/NOD"][()]
    elem_count = len(nod) // 4
    conn = (nod.reshape((4, elem_count)).T - 1).astype(np.int64, copy=False)
    return nodes, conn


def add_point_array(grid: vtk.vtkUnstructuredGrid, name: str, data: np.ndarray) -> None:
    arr = numpy_to_vtk(np.ascontiguousarray(data), deep=True)
    arr.SetName(name)
    grid.GetPointData().AddArray(arr)


def add_cell_array(grid: vtk.vtkUnstructuredGrid, name: str, data: np.ndarray) -> None:
    arr = numpy_to_vtk(np.ascontiguousarray(data), deep=True)
    arr.SetName(name)
    grid.GetCellData().AddArray(arr)


def make_grid(nodes: np.ndarray, conn: np.ndarray) -> vtk.vtkUnstructuredGrid:
    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(np.ascontiguousarray(nodes), deep=True))

    elem_count = len(conn)
    offsets = np.arange(0, 4 * (elem_count + 1), 4, dtype=np.int64)
    connectivity = np.ascontiguousarray(conn.reshape(-1), dtype=np.int64)

    cells = vtk.vtkCellArray()
    cells.SetData(
        numpy_to_vtkIdTypeArray(offsets, deep=True),
        numpy_to_vtkIdTypeArray(connectivity, deep=True),
    )

    grid = vtk.vtkUnstructuredGrid()
    grid.SetPoints(points)
    grid.SetCells(vtk.VTK_TETRA, cells)
    return grid


def add_field_data(grid: vtk.vtkUnstructuredGrid, case_id: str, time_s: float) -> None:
    time_arr = vtk.vtkDoubleArray()
    time_arr.SetName("TIME_S")
    time_arr.InsertNextValue(time_s)
    grid.GetFieldData().AddArray(time_arr)

    case_arr = vtk.vtkStringArray()
    case_arr.SetName("CASE_ID")
    case_arr.InsertNextValue(case_id)
    grid.GetFieldData().AddArray(case_arr)


def averaged_to_nodes(values: np.ndarray, conn: np.ndarray, node_count: int) -> np.ndarray:
    sums = np.zeros(node_count, dtype=np.float64)
    counts = np.zeros(node_count, dtype=np.float64)
    flat_nodes = conn.reshape(-1)
    flat_values = np.repeat(values, 4)
    np.add.at(sums, flat_nodes, flat_values)
    np.add.at(counts, flat_nodes, 1.0)
    out = np.zeros(node_count, dtype=np.float64)
    np.divide(sums, counts, out=out, where=counts > 0)
    return out


def write_vtu(path: Path, grid: vtk.vtkUnstructuredGrid) -> None:
    writer = vtk.vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(path))
    writer.SetInputData(grid)
    writer.SetDataModeToBinary()
    if hasattr(writer, "SetCompressorTypeToZLib"):
        writer.SetCompressorTypeToZLib()
    if writer.Write() != 1:
        raise RuntimeError(f"Failed to write {path}")


def write_vtm(path: Path, vtu_name: str, block_name: str) -> None:
    text = f"""<?xml version="1.0"?>
<VTKFile type="vtkMultiBlockDataSet" version="1.0" byte_order="LittleEndian">
  <vtkMultiBlockDataSet>
    <Block index="0" name="{escape(block_name)}">
      <DataSet index="0" name="volume" file="{escape(vtu_name)}"/>
    </Block>
  </vtkMultiBlockDataSet>
</VTKFile>
"""
    path.write_text(text, encoding="utf-8", newline="\n")


def write_pvd(path: Path, datasets: list[tuple[float, str]]) -> None:
    lines = [
        '<?xml version="1.0"?>',
        '<VTKFile type="Collection" version="1.0" byte_order="LittleEndian">',
        "  <Collection>",
    ]
    for time_s, file_name in datasets:
        lines.append(f'    <DataSet timestep="{time_s:.12g}" group="" part="0" file="{escape(file_name)}"/>')
    lines.extend(["  </Collection>", "</VTKFile>"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def export_case(case_id: str) -> None:
    rmed = RESULT_DIR / f"carter_choc_{case_id}.rmed"
    case_dir = OUT_DIR / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    datasets: list[tuple[float, str]] = []
    with h5py.File(rmed, "r") as file:
        nodes, conn = read_mesh(file)
        node_count = len(nodes)
        elem_count = len(conn)

        sieq = file["CHA/RESU____SIEQ_ELGA"]
        sieq_names = med_names(bytes(sieq.attrs["NOM"]))
        sieq_nco = int(sieq.attrs["NCO"])

        sief = file["CHA/RESU____SIEF_ELGA"]
        sief_names = med_names(bytes(sief.attrs["NOM"]))
        sief_nco = int(sief.attrs["NCO"])

        depl = file["CHA/RESU____DEPL"]
        depl_nco = int(depl.attrs["NCO"])

        for step in sorted(sieq.keys()):
            time_s = float(sieq[step].attrs["PDT"])
            time_us = int(round(time_s * 1_000_000))
            stem = f"{case_id}_t{time_us:07d}us"

            grid = make_grid(nodes, conn)
            add_field_data(grid, case_id, time_s)

            disp = depl[step]["NOE/MED_NO_PROFILE_INTERNAL/CO"][()].reshape((depl_nco, node_count)).T
            add_point_array(grid, "DEPL_mm", disp)
            grid.GetPointData().SetVectors(grid.GetPointData().GetArray("DEPL_mm"))
            add_point_array(grid, "DEPL_MAG_mm", np.linalg.norm(disp, axis=1))

            sieq_values = sieq[step]["MAI.TE4/MED_NO_PROFILE_INTERNAL/CO"][()].reshape((sieq_nco, elem_count))
            for index, name in enumerate(sieq_names):
                if name in KEEP_SIEQ:
                    add_cell_array(grid, f"{name}_MPa", sieq_values[index])
            vmis = sieq_values[sieq_names.index("VMIS")]
            add_point_array(grid, "VMIS_MPa_node_avg", averaged_to_nodes(vmis, conn, node_count))

            sief_values = sief[step]["MAI.TE4/MED_NO_PROFILE_INTERNAL/CO"][()].reshape((sief_nco, elem_count))
            for index, name in enumerate(sief_names):
                if name in KEEP_SIEF:
                    add_cell_array(grid, f"{name}_MPa", sief_values[index])

            vtu_path = case_dir / f"{stem}.vtu"
            vtm_path = case_dir / f"{stem}.vtm"
            write_vtu(vtu_path, grid)
            write_vtm(vtm_path, vtu_path.name, case_id)
            datasets.append((time_s, f"{case_id}/{vtm_path.name}"))
            print(f"Wrote {vtm_path}")

    write_pvd(OUT_DIR / f"{case_id}.pvd", datasets)


def write_open_bat() -> None:
    bat = r"""@echo off
setlocal
set "PVLAUNCH=D:\v2025\run_paraview.bat"
if not exist "%PVLAUNCH%" (
    echo Lanceur ParaView SALOME introuvable:
    echo   %PVLAUNCH%
    pause
    exit /b 1
)
call "%PVLAUNCH%" ^
  "%~dp0cyl_ymin.pvd" ^
  "%~dp0cyl_ymax.pvd" ^
  "%~dp0cyl_oblique_ymin_z.pvd"
"""
    (OUT_DIR / "ouvrir_chocs_vtm_paraview.bat").write_text(bat, encoding="ascii", newline="\r\n")


def main() -> None:
    if not RESULT_DIR.exists():
        raise SystemExit(
            "Raw .rmed directory not found. Set CARTER_RMED_DIR or place the .rmed files "
            "next to this deliverable before regenerating VTM exports."
        )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for case_id in CASES:
        export_case(case_id)
    write_open_bat()
    print(f"VTM export complete: {OUT_DIR}")


if __name__ == "__main__":
    main()
