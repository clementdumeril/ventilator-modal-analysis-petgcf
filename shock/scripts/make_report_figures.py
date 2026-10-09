"""Matplotlib figures for the (French) shock report. English README figures: make_shock_figures_en.py.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "02_RESULTATS_CSV"
FIG_DIR = ROOT / "01_RAPPORT_LATEX" / "figures"
TABLE_DIR = ROOT / "01_RAPPORT_LATEX" / "tables"

CASE_LABELS = {
    "cyl_ymin": "Lateral Y-",
    "cyl_ymax": "Lateral Y+",
    "cyl_oblique_ymin_z": "Oblique Y- + Z",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def as_float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def savefig(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=220)
    plt.close()


def plot_vmis_time(rows: list[dict[str, str]]) -> None:
    plt.figure(figsize=(7.0, 4.2))
    for case_id, label in CASE_LABELS.items():
        case_rows = [row for row in rows if row["case_id"] == case_id]
        times = [as_float(row, "time_s") * 1000.0 for row in case_rows]
        raw = [as_float(row, "vmis_max_mpa") for row in case_rows]
        filtered = [as_float(row, "vmis_filtered_mpa") for row in case_rows]
        plt.plot(times, raw, marker="o", linewidth=1.8, label=f"{label} brut")
        plt.plot(times, filtered, marker="s", linestyle="--", linewidth=1.4, label=f"{label} hors contact")

    plt.xlabel("Temps depuis le debut de l'impulsion (ms)")
    plt.ylabel("Contrainte maximale de Von Mises (MPa)")
    plt.title("Evolution des contraintes pendant l'impulsion simplifiee")
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=7.5, ncol=2)
    savefig(FIG_DIR / "vmis_time_history.png")


def plot_peak_bars(peaks: list[dict[str, str]]) -> None:
    labels = [CASE_LABELS[row["case_id"]] for row in peaks]
    raw = np.array([as_float(row, "vmis_max_mpa") for row in peaks])
    filtered = np.array([as_float(row, "vmis_filtered_mpa") for row in peaks])
    x = np.arange(len(labels))
    width = 0.36

    plt.figure(figsize=(7.0, 4.1))
    plt.bar(x - width / 2, raw, width, label="Pic brut")
    plt.bar(x + width / 2, filtered, width, label="Hors bande de contact")
    plt.xticks(x, labels)
    plt.ylabel("Pic de Von Mises (MPa)")
    plt.title("Pics bruts et pics hors bande de contact")
    plt.grid(axis="y", alpha=0.3)
    plt.legend()
    savefig(FIG_DIR / "vmis_peak_comparison.png")


def plot_displacement_time(rows: list[dict[str, str]]) -> None:
    plt.figure(figsize=(7.0, 4.0))
    for case_id, label in CASE_LABELS.items():
        case_rows = [row for row in rows if row["case_id"] == case_id]
        times = [as_float(row, "time_s") * 1000.0 for row in case_rows]
        disp = [as_float(row, "depl_max_mm") for row in case_rows]
        plt.plot(times, disp, marker="o", linewidth=1.8, label=label)

    plt.xlabel("Temps depuis le debut de l'impulsion (ms)")
    plt.ylabel("Deplacement maximal (mm)")
    plt.title("Deplacement maximal pendant le calcul transitoire")
    plt.grid(True, alpha=0.3)
    plt.legend()
    savefig(FIG_DIR / "displacement_time_history.png")


def plot_design_schematic() -> None:
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    ax.set_aspect("equal")
    ax.axis("off")

    theta = np.linspace(0, 2 * np.pi, 300)
    ax.plot(np.cos(theta), np.sin(theta), color="#263238", linewidth=3.0)
    ax.plot(0.62 * np.cos(theta), 0.62 * np.sin(theta), color="#546e7a", linewidth=2.0)
    for angle in [90, 210, 330]:
        a = np.deg2rad(angle)
        ax.plot([0, 0.62 * np.cos(a)], [0, 0.62 * np.sin(a)], color="#546e7a", linewidth=4)
    hub = plt.Circle((0, 0), 0.22, color="#607d8b")
    ax.add_patch(hub)

    ax.annotate("Impact lateral Y-", xy=(-0.05, -1.03), xytext=(-1.65, -1.35),
                arrowprops=dict(arrowstyle="->", linewidth=2.0), fontsize=10)
    ax.annotate("Impact lateral Y+", xy=(0.05, 1.03), xytext=(0.75, 1.32),
                arrowprops=dict(arrowstyle="->", linewidth=2.0), fontsize=10)
    ax.annotate("Impact oblique", xy=(0.78, -0.75), xytext=(1.15, -1.25),
                arrowprops=dict(arrowstyle="->", linewidth=2.0), fontsize=10)
    ax.text(-1.55, 0.25, "Zone de conception:\nbord arrondi,\nbumper TPU,\ngrands conges", fontsize=10,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#f5f5f5", edgecolor="#9e9e9e"))
    ax.set_xlim(-1.9, 1.8)
    ax.set_ylim(-1.55, 1.55)
    savefig(FIG_DIR / "impact_cases_schematic.png")


def write_peak_table(peaks: list[dict[str, str]]) -> None:
    lines = [
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Cas & Noeuds contact & VMIS brut (MPa) & VMIS hors contact (MPa) & $u_{\max}$ (mm) \\",
        r"\midrule",
    ]
    for row in peaks:
        lines.append(
            f"{CASE_LABELS[row['case_id']]} & {int(row['contact_nodes'])} & "
            f"{as_float(row, 'vmis_max_mpa'):.1f} & {as_float(row, 'vmis_filtered_mpa'):.1f} & "
            f"{as_float(row, 'depl_max_mm'):.2f} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    (TABLE_DIR / "peak_results_table.tex").write_text("\n".join(lines) + "\n", encoding="ascii")


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_csv(CSV_DIR / "resume_temporel_choc_cylindrique_v1.csv")
    peaks = read_csv(CSV_DIR / "resume_pics_choc_cylindrique_v1.csv")
    plot_vmis_time(rows)
    plot_peak_bars(peaks)
    plot_displacement_time(rows)
    plot_design_schematic()
    write_peak_table(peaks)
    print(f"Wrote figures to {FIG_DIR}")
    print(f"Wrote tables to {TABLE_DIR}")


if __name__ == "__main__":
    main()
