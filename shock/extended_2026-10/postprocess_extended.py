"""Time histories from the extended shroud-impact runs (.rmed written by Code_Aster 17.4).

Same definitions as the June post-processing (shock/scripts/postprocess_cylindrical_drop_results.py and
compute_robust_metrics.py in the repository): von Mises from SIEQ_ELGA (one Gauss point per TETRA4),
raw maximum over all elements (for TETRA10, the element value is the maximum over its Gauss points, 5 per element in code_aster), and
maximum / p99 / p95 over the elements whose centroid is more than
8 mm from the contact plane. Displacement magnitude maximum over all nodes.

usage: python postprocess_extended.py <run_dir> <out.csv> [case ...]
"""
import csv
import sys
from pathlib import Path

import h5py
import numpy as np

CONTACT = {  # point on the contact plane, unit normal (from the .comm files)
    "cyl_ymin": ((0.0, -136.692359, 0.0), (0.0, 1.0, 0.0)),
    "cyl_ymax": ((0.0, 102.879253, 0.0), (0.0, 1.0, 0.0)),
    "cyl_oblique_ymin_z": ((-6.31, -135.05, 164.18), (0.0, 0.70710678, 0.70710678)),   # June input: plane not tangent
    "oblique_base_edge": ((28.03, -99.17, 0.0), (0.0, 0.70710678, 0.70710678)),        # corrected oblique case
}
BAND_MM = 8.0


def names(raw, width=16):
    t = bytes(raw).decode("ascii", errors="ignore")
    return [t[i:i + width].strip() for i in range(0, len(t), width) if t[i:i + width].strip()]


def history(rmed, case):
    rows = []
    with h5py.File(rmed, "r") as f:
        maa = f["ENS_MAA"][next(iter(f["ENS_MAA"]))]
        step0 = maa[next(iter(maa))]
        coo = step0["NOE/COO"]
        nodes = coo[()].reshape((3, int(coo.attrs["NBR"]))).T
        etype = "TE4" if "TE4" in step0["MAI"] else "T10"      # linear or quadratic tetrahedra
        nn = 4 if etype == "TE4" else 10
        nod = step0[f"MAI/{etype}/NOD"][()]
        conn = nod.reshape((nn, len(nod) // nn)).T - 1
        centers = nodes[conn[:, :4]].mean(axis=1)                # corner nodes
        p, n = (np.array(v) for v in CONTACT[case])
        keep = np.abs((centers - p) @ n) > BAND_MM

        field = {k[8:]: f["CHA"][k] for k in f["CHA"]}   # MED name = result name padded to 8 + field, e.g. 'RESU____DEPL'
        sieq, depl = field["SIEQ_ELGA"], field["DEPL"]
        vm_i = names(sieq.attrs["NOM"]).index("VMIS"); nco = int(sieq.attrs["NCO"])
        dco = int(depl.attrs["NCO"])
        for key in sorted(sieq.keys(), key=lambda k: float(sieq[k].attrs["PDT"])):
            t = float(sieq[key].attrs["PDT"])
            co = sieq[key][f"MAI.{etype}/MED_NO_PROFILE_INTERNAL/CO"][()]
            npg = co.size // (nco * len(centers))                # Gauss points per element (1 for TETRA4)
            vm = co.reshape((nco, len(centers), npg))[vm_i].max(axis=1)   # element value = max over its Gauss points
            u = depl[key]["NOE/MED_NO_PROFILE_INTERNAL/CO"][()].reshape((dco, len(nodes))).T[:, :3]
            vk = vm[keep]; ik = int(np.argmax(np.where(keep, vm, -np.inf)))
            rows.append({
                "case_id": case, "time_s": t,
                "vmis_raw_max_mpa": float(vm.max()),
                "vmis_max_gt8mm_mpa": float(vk.max()),
                "vmis_p99_gt8mm_mpa": float(np.percentile(vk, 99)),
                "vmis_p95_gt8mm_mpa": float(np.percentile(vk, 95)),
                "x_max_gt8mm": float(centers[ik, 0]), "y_max_gt8mm": float(centers[ik, 1]), "z_max_gt8mm": float(centers[ik, 2]),
                "depl_max_mm": float(np.linalg.norm(u, axis=1).max()),
            })
    return rows


if __name__ == "__main__":
    run_dir, out_csv = Path(sys.argv[1]), Path(sys.argv[2])
    out = []
    for c in sys.argv[3:] or list(CONTACT):
        for name in (f"{c}.rmed", f"carter_choc_{c}.rmed"):   # new runs / June runs
            if (run_dir / name).exists():
                out += history(run_dir / name, c)
                print(f"{c}: {len(out)} rows so far")
                break
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    print("written", out_csv)
