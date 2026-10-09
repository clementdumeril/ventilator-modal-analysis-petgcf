"""Robust stress metrics per impact case: max, p99 and p95 of von Mises after excluding cells within
4, 8 or 12 mm of the blocked contact nodes. Writes results/resume_robuste_* and synthese_robuste_*.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy


ROOT = Path(__file__).resolve().parents[1]
VTM_DIR = ROOT / "03_VISUALISATION_PARAVIEW"
CSV_DIR = ROOT / "02_RESULTATS_CSV"
FIG_DIR = ROOT / "01_RAPPORT_LATEX" / "figures"
TABLE_DIR = ROOT / "01_RAPPORT_LATEX" / "tables"


CASES = {
    "cyl_ymin": {
        "label_fr": "Impact lateral Y-",
        "short_fr": "Y- lateral",
        "point": np.array([0.0, -136.692359, 0.0]),
        "normal": np.array([0.0, 1.0, 0.0]),
        "contact_nodes": 63,
        "precision_mm": 3.0,
    },
    "cyl_ymax": {
        "label_fr": "Impact lateral Y+",
        "short_fr": "Y+ lateral",
        "point": np.array([0.0, 102.879253, 0.0]),
        "normal": np.array([0.0, 1.0, 0.0]),
        "contact_nodes": 63,
        "precision_mm": 5.0,
    },
    "cyl_oblique_ymin_z": {
        "label_fr": "Impact oblique Y- + Z",
        "short_fr": "Oblique",
        "point": np.array([-6.31, -135.05, 164.18]),
        "normal": np.array([0.0, 0.70710678, 0.70710678]),
        "contact_nodes": 1091,
        "precision_mm": 1.0,
    },
}

EXCLUSION_WIDTHS_MM = (4.0, 8.0, 12.0)


def first_dataset(obj):
    if isinstance(obj, vtk.vtkDataSet):
        return obj
    if isinstance(obj, vtk.vtkCompositeDataSet):
        iterator = obj.NewIterator()
        iterator.UnRegister(None)
        iterator.InitTraversal()
        while not iterator.IsDoneWithTraversal():
            child = first_dataset(iterator.GetCurrentDataObject())
            if child is not None:
                return child
            iterator.GoToNextItem()
    return None


def load_dataset(path: Path) -> vtk.vtkDataSet:
    reader = vtk.vtkXMLMultiBlockDataReader()
    reader.SetFileName(str(path))
    reader.Update()
    dataset = first_dataset(reader.GetOutput())
    if dataset is None:
        raise RuntimeError(f"No dataset found in {path}")
    return dataset


def cell_centers(dataset: vtk.vtkDataSet) -> np.ndarray:
    centers = vtk.vtkCellCenters()
    centers.SetInputData(dataset)
    centers.Update()
    return vtk_to_numpy(centers.GetOutput().GetPoints().GetData())


def get_cell_array(dataset: vtk.vtkDataSet, name: str) -> np.ndarray:
    array = dataset.GetCellData().GetArray(name)
    if array is None:
        raise KeyError(name)
    return vtk_to_numpy(array)


def get_point_array(dataset: vtk.vtkDataSet, name: str) -> np.ndarray:
    array = dataset.GetPointData().GetArray(name)
    if array is None:
        raise KeyError(name)
    return vtk_to_numpy(array)


def time_from_name(path: Path) -> float:
    match = re.search(r"_t(\d+)us", path.name)
    if not match:
        raise ValueError(path.name)
    return int(match.group(1)) * 1.0e-6


def distance_to_contact(case_id: str, centers: np.ndarray) -> np.ndarray:
    case = CASES[case_id]
    normal = case["normal"] / np.linalg.norm(case["normal"])
    return np.abs((centers - case["point"]) @ normal)


def row_for_file(case_id: str, path: Path) -> dict[str, object]:
    dataset = load_dataset(path)
    centers = cell_centers(dataset)
    distance_mm = distance_to_contact(case_id, centers)
    vmis = get_cell_array(dataset, "VMIS_MPa")
    tresca = get_cell_array(dataset, "TRESCA_MPa")
    prin3 = get_cell_array(dataset, "PRIN_3_MPa")
    displacement = get_point_array(dataset, "DEPL_MAG_mm")

    row: dict[str, object] = {
        "case_id": case_id,
        "label": CASES[case_id]["label_fr"],
        "time_s": time_from_name(path),
        "contact_nodes": CASES[case_id]["contact_nodes"],
        "contact_precision_mm": CASES[case_id]["precision_mm"],
        "vmis_max_raw_mpa": float(np.nanmax(vmis)),
        "vmis_p99_raw_mpa": float(np.nanpercentile(vmis, 99.0)),
        "vmis_p95_raw_mpa": float(np.nanpercentile(vmis, 95.0)),
        "depl_max_mm": float(np.nanmax(displacement)),
    }

    for width in EXCLUSION_WIDTHS_MM:
        mask = distance_mm > width
        kept = vmis[mask]
        row[f"kept_cells_gt{int(width)}mm"] = int(mask.sum())
        row[f"vmis_max_gt{int(width)}mm_mpa"] = float(np.nanmax(kept))
        row[f"vmis_p99_gt{int(width)}mm_mpa"] = float(np.nanpercentile(kept, 99.0))
        row[f"vmis_p95_gt{int(width)}mm_mpa"] = float(np.nanpercentile(kept, 95.0))

    mask8 = distance_mm > 8.0
    row["tresca_max_gt8mm_mpa"] = float(np.nanmax(tresca[mask8]))
    row["prin3_max_gt8mm_mpa"] = float(np.nanmax(prin3[mask8]))
    return row


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: object, digits: int = 1) -> str:
    return f"{float(value):.{digits}f}"


def write_latex_tables(temporal_rows: list[dict[str, object]]) -> None:
    peak_rows: list[dict[str, object]] = []
    sensitivity_rows: list[dict[str, object]] = []

    for case_id in CASES:
        case_rows = [row for row in temporal_rows if row["case_id"] == case_id]
        peak_raw = max(case_rows, key=lambda row: float(row["vmis_max_raw_mpa"]))
        peak_f8 = max(case_rows, key=lambda row: float(row["vmis_max_gt8mm_mpa"]))
        peak_disp = max(case_rows, key=lambda row: float(row["depl_max_mm"]))
        peak_rows.append(
            {
                "case_id": case_id,
                "label": CASES[case_id]["short_fr"],
                "contact_nodes": CASES[case_id]["contact_nodes"],
                "raw": peak_raw["vmis_max_raw_mpa"],
                "time_raw_ms": float(peak_raw["time_s"]) * 1000.0,
                "max_gt8": peak_f8["vmis_max_gt8mm_mpa"],
                "p99_gt8": peak_f8["vmis_p99_gt8mm_mpa"],
                "p95_gt8": peak_f8["vmis_p95_gt8mm_mpa"],
                "prin3_gt8": peak_f8["prin3_max_gt8mm_mpa"],
                "disp_max": peak_disp["depl_max_mm"],
                "time_disp_ms": float(peak_disp["time_s"]) * 1000.0,
            }
        )
        sensitivity_rows.append(
            {
                "label": CASES[case_id]["short_fr"],
                "max_gt4": peak_f8["vmis_max_gt4mm_mpa"],
                "max_gt8": peak_f8["vmis_max_gt8mm_mpa"],
                "max_gt12": peak_f8["vmis_max_gt12mm_mpa"],
                "p99_gt8": peak_f8["vmis_p99_gt8mm_mpa"],
            }
        )

    lines = [
        r"\begin{tabular}{lrrrrrr}",
        r"\toprule",
        r"Cas & Noeuds contact & VMIS brut & VMIS $d>8$ & p99 $d>8$ & p95 $d>8$ & $u_{\max}$ \\",
        r" &  & (MPa) & (MPa) & (MPa) & (MPa) & (mm) \\",
        r"\midrule",
    ]
    for row in peak_rows:
        lines.append(
            f"{row['label']} & {row['contact_nodes']} & {fmt(row['raw'])} & "
            f"{fmt(row['max_gt8'])} & {fmt(row['p99_gt8'])} & {fmt(row['p95_gt8'])} & "
            f"{fmt(row['disp_max'], 2)} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    (TABLE_DIR / "robust_metrics_table.tex").write_text("\n".join(lines) + "\n", encoding="ascii")

    lines = [
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Cas & max $d>4$ mm & max $d>8$ mm & max $d>12$ mm & p99 $d>8$ mm \\",
        r" & (MPa) & (MPa) & (MPa) & (MPa) \\",
        r"\midrule",
    ]
    for row in sensitivity_rows:
        lines.append(
            f"{row['label']} & {fmt(row['max_gt4'])} & {fmt(row['max_gt8'])} & "
            f"{fmt(row['max_gt12'])} & {fmt(row['p99_gt8'])} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    (TABLE_DIR / "filter_sensitivity_table.tex").write_text("\n".join(lines) + "\n", encoding="ascii")

    with (CSV_DIR / "synthese_robuste_choc_cylindrique_v1.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(peak_rows[0].keys()))
        writer.writeheader()
        writer.writerows(peak_rows)


def plot_robust_metrics(temporal_rows: list[dict[str, object]]) -> None:
    labels = []
    max_gt8 = []
    p99_gt8 = []
    p95_gt8 = []
    for case_id in CASES:
        case_rows = [row for row in temporal_rows if row["case_id"] == case_id]
        peak = max(case_rows, key=lambda row: float(row["vmis_max_gt8mm_mpa"]))
        labels.append(CASES[case_id]["short_fr"])
        max_gt8.append(float(peak["vmis_max_gt8mm_mpa"]))
        p99_gt8.append(float(peak["vmis_p99_gt8mm_mpa"]))
        p95_gt8.append(float(peak["vmis_p95_gt8mm_mpa"]))

    x = np.arange(len(labels))
    width = 0.25
    plt.figure(figsize=(7.0, 4.2))
    plt.bar(x - width, max_gt8, width, label="Maximum hors contact")
    plt.bar(x, p99_gt8, width, label="p99 hors contact")
    plt.bar(x + width, p95_gt8, width, label="p95 hors contact")
    plt.xticks(x, labels)
    plt.ylabel("Von Mises (MPa)")
    plt.title("Indicateurs robustes hors bande de contact d > 8 mm")
    plt.grid(axis="y", alpha=0.3)
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "robust_vmis_metrics.png", dpi=220)
    plt.close()

    oblique_rows = [row for row in temporal_rows if row["case_id"] == "cyl_oblique_ymin_z"]
    peak = max(oblique_rows, key=lambda row: float(row["vmis_max_gt8mm_mpa"]))
    widths = np.array(EXCLUSION_WIDTHS_MM)
    maxima = [float(peak[f"vmis_max_gt{int(width)}mm_mpa"]) for width in widths]
    p99 = [float(peak[f"vmis_p99_gt{int(width)}mm_mpa"]) for width in widths]
    plt.figure(figsize=(6.5, 3.8))
    plt.plot(widths, maxima, marker="o", linewidth=1.8, label="Maximum")
    plt.plot(widths, p99, marker="s", linewidth=1.8, label="p99")
    plt.xlabel("Distance minimale au plan de contact (mm)")
    plt.ylabel("Von Mises (MPa)")
    plt.title("Sensibilite du filtrage - cas oblique")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "filter_sensitivity_oblique.png", dpi=220)
    plt.close()


def main() -> None:
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for case_id in CASES:
        for path in sorted((VTM_DIR / case_id).glob("*.vtm")):
            rows.append(row_for_file(case_id, path))

    write_csv(CSV_DIR / "resume_robuste_choc_cylindrique_v1.csv", rows)
    write_latex_tables(rows)
    plot_robust_metrics(rows)
    print("Wrote robust metrics CSV, tables and figures.")


if __name__ == "__main__":
    main()
