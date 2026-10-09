"""Extract von Mises and displacement maxima per archived time step from the Code_Aster .rmed results
(raw maximum and maximum outside the contact band). Writes results/resume_temporel_* and resume_pics_*.
The input folder of .rmed files is hard-coded below; the .rmed files (>1 GB) are not in the repository.
"""
from __future__ import annotations

import csv
import os
import re
from pathlib import Path

import h5py
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ORIGINAL_RMED_DIR = Path(
    r"D:\v2025\carter_modal_v1_analysis\ETUDE_CHOC_CARTER_CYLINDRIQUE_V1\04_RESULTATS"
)
RESULT_DIR = Path(os.environ.get("CARTER_RMED_DIR", DEFAULT_ORIGINAL_RMED_DIR))
LOG_DIR = ROOT / "07_LOGS_CALCUL"
CSV_DIR = ROOT / "02_RESULTATS_CSV"
DOC_DIR = ROOT / "08_ANNEXES"


CASES = {
    "cyl_ymin": {
        "label": "Impact lateral carter cote Y-",
        "filter": "ymin",
    },
    "cyl_ymax": {
        "label": "Impact lateral carter cote Y+",
        "filter": "ymax",
    },
    "cyl_oblique_ymin_z": {
        "label": "Impact oblique cote Y- avec composante verticale",
        "filter": "oblique",
    },
}


def med_names(raw: bytes, width: int = 16) -> list[str]:
    text = raw.decode("ascii", errors="ignore")
    return [text[i : i + width].strip() for i in range(0, len(text), width) if text[i : i + width].strip()]


def contact_nodes(case_id: str) -> int | None:
    path = LOG_DIR / f"message_{case_id}.txt"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"!\s*N_CONTACT\s*!\s*(\d+)\s*!", text)
    return int(match.group(1)) if match else None


def filtered_mask(case_id: str, centers: np.ndarray) -> np.ndarray:
    if case_id == "cyl_ymin":
        return np.abs(centers[:, 1] - (-136.692359)) > 8.0
    if case_id == "cyl_ymax":
        return np.abs(centers[:, 1] - 102.879253) > 8.0
    if case_id == "cyl_oblique_ymin_z":
        point = np.array([-6.31, -135.05, 164.18])
        normal = np.array([0.0, 0.70710678, 0.70710678])
        return np.abs((centers - point) @ normal) > 8.0
    raise KeyError(case_id)


def read_mesh(file: h5py.File) -> tuple[np.ndarray, np.ndarray]:
    base = "ENS_MAA/00000001/-0000000000000000001-0000000000000000001"
    coo = file[f"{base}/NOE/COO"]
    node_count = int(coo.attrs["NBR"])
    nodes = coo[()].reshape((3, node_count)).T
    nod = file[f"{base}/MAI/TE4/NOD"][()]
    elem_count = len(nod) // 4
    conn = nod.reshape((4, elem_count)).T - 1
    centers = nodes[conn].mean(axis=1)
    return nodes, centers


def extract_case(case_id: str) -> tuple[list[dict[str, object]], dict[str, object]]:
    rmed = RESULT_DIR / f"carter_choc_{case_id}.rmed"
    rows: list[dict[str, object]] = []

    with h5py.File(rmed, "r") as file:
        nodes, centers = read_mesh(file)
        elem_count = len(centers)
        keep_mask = filtered_mask(case_id, centers)

        sieq = file["CHA/RESU____SIEQ_ELGA"]
        sieq_components = med_names(bytes(sieq.attrs["NOM"]))
        vmis_idx = sieq_components.index("VMIS")
        sieq_nco = int(sieq.attrs["NCO"])

        depl = file["CHA/RESU____DEPL"]
        depl_nco = int(depl.attrs["NCO"])

        for step in sorted(sieq.keys()):
            time_s = float(sieq[step].attrs["PDT"])
            vmis = sieq[step]["MAI.TE4/MED_NO_PROFILE_INTERNAL/CO"][()].reshape((sieq_nco, elem_count))[vmis_idx]
            raw_idx = int(np.nanargmax(vmis))
            filtered_values = np.where(keep_mask, vmis, -np.inf)
            filtered_idx = int(np.nanargmax(filtered_values))

            disp_data = depl[step]["NOE/MED_NO_PROFILE_INTERNAL/CO"][()].reshape((depl_nco, len(nodes))).T
            disp_norm = np.linalg.norm(disp_data, axis=1)
            disp_idx = int(np.nanargmax(disp_norm))

            rows.append(
                {
                    "case_id": case_id,
                    "label": CASES[case_id]["label"],
                    "contact_nodes": contact_nodes(case_id),
                    "time_s": time_s,
                    "vmis_max_mpa": float(vmis[raw_idx]),
                    "elem_id": raw_idx + 1,
                    "x_mm": float(centers[raw_idx, 0]),
                    "y_mm": float(centers[raw_idx, 1]),
                    "z_mm": float(centers[raw_idx, 2]),
                    "vmis_filtered_mpa": float(vmis[filtered_idx]),
                    "elem_filtered_id": filtered_idx + 1,
                    "x_filtered_mm": float(centers[filtered_idx, 0]),
                    "y_filtered_mm": float(centers[filtered_idx, 1]),
                    "z_filtered_mm": float(centers[filtered_idx, 2]),
                    "depl_max_mm": float(disp_norm[disp_idx]),
                    "node_depl_max_id": disp_idx + 1,
                }
            )

    peak = max(rows, key=lambda row: row["vmis_max_mpa"])
    return rows, peak


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if not RESULT_DIR.exists():
        raise SystemExit(
            "Raw .rmed directory not found. Set CARTER_RMED_DIR before regenerating CSV summaries."
        )
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict[str, object]] = []
    peaks: list[dict[str, object]] = []
    for case_id in CASES:
        rows, peak = extract_case(case_id)
        all_rows.extend(rows)
        peaks.append(peak)

    write_csv(CSV_DIR / "resume_temporel_choc_cylindrique_v1.csv", all_rows)
    write_csv(CSV_DIR / "resume_pics_choc_cylindrique_v1.csv", peaks)

    lines = [
        "# Resultats - choc sur carter cylindrique V1",
        "",
        "Calculs lances sur `qltus2` via Code_Aster 17.4.0 dans Apptainer.",
        "Le modele utilise le maillage V5 oriente avec base dans le plan XY et hauteur selon +Z.",
        "",
        "Hypothese commune revisee: impulsion inertielle severe 0-2.5 ms avec zone de contact bloquee.",
        "Le pulse applique n'est pas strictement coherent avec une chute de 0.8 m; il sert a comparer les zones sensibles.",
        "Le contact est idealise par un groupe de noeuds bloque, donc les contraintes exactement au contact peuvent etre localement singulieres.",
        "",
        "## Pics par cas",
        "",
        "| Cas | Noeuds contact | VMIS brut max (MPa) | t (ms) | Position max (mm) | VMIS hors bande contact (MPa) |",
        "| --- | ---: | ---: | ---: | --- | ---: |",
    ]

    for peak in peaks:
        lines.append(
            "| {label} | {contact_nodes} | {vmis_max_mpa:.1f} | {time_ms:.1f} | "
            "x={x_mm:.1f}, y={y_mm:.1f}, z={z_mm:.1f} | {vmis_filtered_mpa:.1f} |".format(
                time_ms=float(peak["time_s"]) * 1000.0,
                **peak,
            )
        )

    lines.extend(
        [
            "",
            "## Lecture physique",
            "",
            "- Les deux chocs lateraux simples donnent des pics bruts de l'ordre de 88 a 117 MPa.",
            "- Le cas oblique donne 867 MPa au pic brut, mais ce maximum est sur la bande de contact imposee.",
            "- Le filtrage principal conserve les elements situes a plus de 8 mm du plan de contact.",
            "- Les percentiles p95/p99 hors contact doivent etre preferes pour juger une zone etendue.",
            "- Les zones a surveiller restent les levres et jonctions du carter cylindrique, autour de z=145 a 200 mm, surtout cote Y-.",
            "",
            "## Limites",
            "",
            "Ce niveau ne simule pas encore un vrai rebond/contact avec loi de contact, frottement, endommagement PETG-CF ou propagation de fissure. Il sert a localiser les zones sensibles et a preparer une comparaison de variantes.",
            "",
            "## Fichiers",
            "",
            "- `02_RESULTATS_CSV/resume_temporel_choc_cylindrique_v1.csv`: valeurs a chaque instant archive.",
            "- `02_RESULTATS_CSV/resume_pics_choc_cylindrique_v1.csv`: pic par cas.",
            "- `02_RESULTATS_CSV/resume_robuste_choc_cylindrique_v1.csv`: p95/p99 et sensibilite au filtrage.",
            "- `03_VISUALISATION_PARAVIEW/*.pvd`: resultats a ouvrir dans ParaView/ParaVis.",
        ]
    )

    (DOC_DIR / "resultats_choc_carter_cylindrique_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote CSV summaries and documentation.")


if __name__ == "__main__":
    main()
