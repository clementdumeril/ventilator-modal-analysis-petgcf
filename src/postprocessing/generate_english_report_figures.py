from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(r"D:\v2025\carter_modal_v1_analysis\ETUDE_MODALE_PETGCF_COMPOSANTS_V5_SOCLE_XY_Z")
FIG_DIR = ROOT / "07_RAPPORT_LATEX_EN" / "figures"
TABLE_DIR = ROOT / "07_RAPPORT_LATEX_EN" / "tables"

FREQUENCIES = np.array(
    [
        49.214,
        73.181,
        131.946,
        250.576,
        289.925,
        339.059,
        377.305,
        450.782,
        492.777,
        522.370,
        584.026,
        622.931,
        643.105,
        748.567,
        925.806,
        1042.368,
        1137.910,
        1217.084,
        1277.192,
        1393.306,
        1459.501,
    ]
)

F0 = 49.214
M0 = 1.080446
RPM = 2000.0
ROT_FREQ = RPM / 60.0
BLADE_COUNT = 5
BPF = BLADE_COUNT * ROT_FREQ


def save_frequency_map():
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    shown = FREQUENCIES[FREQUENCIES <= 420.0]
    y = np.arange(1, len(shown) + 1)
    ax.scatter(shown, y, s=95, color="#2f6f9f", label="Computed modes")
    excitations = [
        (ROT_FREQ, "1X rotation = 33.3 Hz", "#b33a3a"),
        (2 * ROT_FREQ, "2X = 66.7 Hz", "#d67a22"),
        (3 * ROT_FREQ, "3X = 100.0 Hz", "#d67a22"),
        (4 * ROT_FREQ, "4X = 133.3 Hz", "#d67a22"),
        (BPF, "5-blade passing = 166.7 Hz", "#2c8a45"),
    ]
    for freq, label, color in excitations:
        ax.axvline(freq, color=color, lw=1.8, alpha=0.9, linestyle="--")
        ax.text(freq + 2.5, len(shown) + 0.15, label, rotation=90, va="top", fontsize=8)
    for idx, freq in enumerate(shown, start=1):
        ax.text(freq + 3.0, idx, f"M{idx}: {freq:.1f}", va="center", fontsize=8)
    ax.set_xlim(0, 420)
    ax.set_ylim(0.4, len(shown) + 0.7)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Elastic mode")
    ax.set_title("Computed modes versus 2000 rpm excitation lines")
    ax.grid(True, axis="x", alpha=0.25)
    ax.set_yticks(y)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "frequency_excitation_map_en.png", dpi=220)
    plt.close(fig)


def save_blade_sensitivity():
    blade_masses_g = np.array([0, 5, 10, 15, 20, 25, 30], dtype=float)
    total_added_kg = BLADE_COUNT * blade_masses_g / 1000.0
    f_est = F0 * np.sqrt(M0 / (M0 + total_added_kg))
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    ax.plot(blade_masses_g, f_est, marker="o", lw=2.2, color="#2f6f9f")
    for x, y in zip(blade_masses_g, f_est):
        ax.text(x, y - 0.18, f"{y:.1f}", ha="center", va="top", fontsize=8)
    ax.axhline(ROT_FREQ, color="#b33a3a", linestyle="--", lw=1.8, label="1X at 2000 rpm = 33.3 Hz")
    ax.axhline(BPF, color="#2c8a45", linestyle="--", lw=1.8, label="5-blade passing = 166.7 Hz")
    ax.set_xlabel("Estimated mass of one blade (g)")
    ax.set_ylabel("Estimated first-mode frequency (Hz)")
    ax.set_title("Mass-only estimate for adding five blades")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "blade_mass_sensitivity_en.png", dpi=220)
    plt.close(fig)


def save_mass_distribution():
    labels = ["PETG-CF body", "Motor zone", "Electronics zone"]
    values = np.array([0.648863, 0.243271, 0.188312])
    colors = ["#4c78a8", "#f58518", "#54a24b"]
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    bars = ax.bar(labels, values, color=colors)
    ax.set_ylabel("Equivalent mass (kg)")
    ax.set_title("V5 equivalent mass distribution")
    ax.grid(True, axis="y", alpha=0.25)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.012, f"{value:.3f} kg", ha="center")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "mass_distribution_en.png", dpi=220)
    plt.close(fig)


def save_blade_table():
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    with (TABLE_DIR / "blade_mass_scaling_en.csv").open("w", encoding="utf-8") as handle:
        handle.write("blade_mass_g,total_5_blades_kg,mode1_hz,mode2_hz,mode3_hz\n")
        for blade_mass_g in [5, 10, 15, 20, 25, 30]:
            added = BLADE_COUNT * blade_mass_g / 1000.0
            factor = np.sqrt(M0 / (M0 + added))
            handle.write(
                f"{blade_mass_g},{added:.3f},{F0 * factor:.3f},"
                f"{73.181 * factor:.3f},{131.946 * factor:.3f}\n"
            )


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    save_frequency_map()
    save_blade_sensitivity()
    save_mass_distribution()
    save_blade_table()


if __name__ == "__main__":
    main()
