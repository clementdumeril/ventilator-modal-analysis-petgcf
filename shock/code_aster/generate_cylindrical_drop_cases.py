"""Generate the three Code_Aster impact cases (.comm/.export) on the cylindrical shroud and the shell
scripts that run them in the Code_Aster Apptainer image on the qltus cluster. Comments in the files are in French.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REMOTE_ROOT = "/home/qltus1/aster_jobs/carter_choc_cylindrique_v1"


CASES = [
    {
        "case_id": "cyl_ymin",
        "title": "Impact lateral sur le cote Y- du carter cylindrique",
        "contact": """_F(
            NOM='N_CONTACT',
            OPTION='PLAN',
            POINT=(0.0, -136.692359, 0.0),
            VECT_NORMALE=(0.0, 1.0, 0.0),
            PRECISION=3.0,
        )""",
        "direction": "(0.0, -1.0, 0.0)",
    },
    {
        "case_id": "cyl_ymax",
        "title": "Impact lateral sur le cote Y+ du carter cylindrique",
        "contact": """_F(
            NOM='N_CONTACT',
            OPTION='PLAN',
            POINT=(0.0, 102.879253, 0.0),
            VECT_NORMALE=(0.0, 1.0, 0.0),
            PRECISION=5.0,
        )""",
        "direction": "(0.0, 1.0, 0.0)",
    },
    {
        "case_id": "cyl_oblique_ymin_z",
        "title": "Impact oblique sur le carter cylindrique cote Y- avec composante vers le bas",
        "contact": """_F(
            NOM='N_CONTACT',
            OPTION='PLAN',
            POINT=(-6.31, -135.05, 164.18),
            VECT_NORMALE=(0.0, 0.70710678, 0.70710678),
            PRECISION=1.0,
        )""",
        "direction": "(0.0, -0.70710678, -0.70710678)",
    },
]


COMM_TEMPLATE = """DEBUT(LANG='FR')

# Etude de chute sur carter cylindrique - Niveau 2
# {title}
# Dynamique transitoire elastique avec impact idealise par une impulsion.
# Unites: mm, tonne, N, s, MPa.

MAIL = LIRE_MAILLAGE(FORMAT='MED', UNITE=20)

MAIL = DEFI_GROUP(
    reuse=MAIL,
    MAILLAGE=MAIL,
    INFO=1,
    CREA_GROUP_MA=(
        _F(NOM='G_TETRA', TOUT='OUI', TYPE_MAILLE='TETRA4'),
        _F(
            NOM='G_MOTEUR',
            OPTION='SPHERE',
            TYPE_MAILLE='TETRA4',
            POINT=(23.093853, -45.158407, 163.598992),
            RAYON=30.0,
            CRIT_NOEUD='MAJORITE',
        ),
        _F(
            NOM='G_BASE_ELEC',
            OPTION='SPHERE',
            TYPE_MAILLE='TETRA4',
            POINT=(24.323447, 9.996963, 52.043480),
            RAYON=45.0,
            CRIT_NOEUD='MAJORITE',
        ),
        _F(
            NOM='G_MASSES_AJOUTEES',
            UNION=('G_MOTEUR', 'G_BASE_ELEC'),
            TYPE_MAILLE='TETRA4',
        ),
        _F(
            NOM='G_PETGCF',
            DIFFE=('G_TETRA', 'G_MASSES_AJOUTEES'),
            TYPE_MAILLE='TETRA4',
        ),
    ),
    CREA_GROUP_NO=(
        {contact}
    ),
)

MODELE = AFFE_MODELE(
    MAILLAGE=MAIL,
    AFFE=_F(
        GROUP_MA='G_TETRA',
        PHENOMENE='MECANIQUE',
        MODELISATION='3D',
    ),
)

PETGCF = DEFI_MATERIAU(
    ELAS=_F(
        E=6000.0,
        NU=0.35,
        RHO=1.30e-9,
    )
)

PETGCF_MOTEUR = DEFI_MATERIAU(
    ELAS=_F(
        E=6000.0,
        NU=0.35,
        RHO=2.063354290143e-9,
    )
)

PETGCF_BASE_ELEC = DEFI_MATERIAU(
    ELAS=_F(
        E=6000.0,
        NU=0.35,
        RHO=2.160457338233e-9,
    )
)

CHMAT = AFFE_MATERIAU(
    MAILLAGE=MAIL,
    AFFE=(
        _F(GROUP_MA='G_PETGCF', MATER=PETGCF),
        _F(GROUP_MA='G_MOTEUR', MATER=PETGCF_MOTEUR),
        _F(GROUP_MA='G_BASE_ELEC', MATER=PETGCF_BASE_ELEC),
    ),
)

# Approximation conservative du contact:
# la petite zone de contact cylindrique est bloque en translation.
BC_CONTACT = AFFE_CHAR_MECA(
    MODELE=MODELE,
    DDL_IMPO=_F(
        GROUP_NO='N_CONTACT',
        DX=0.0,
        DY=0.0,
        DZ=0.0,
    ),
)

# Impulsion inertielle simplifiee:
# le pulse actuel sert a comparer des zones sensibles, mais ne reproduit pas
# strictement une chute de 0.8 m. Son integrale vaut environ 3.11 m/s.
# Amplitude maximale: 2.465e6 mm/s2, soit environ 251 g.
# La direction change selon le plan de chute.
CHOC_DYN = AFFE_CHAR_MECA(
    MODELE=MODELE,
    PESANTEUR=_F(
        GROUP_MA='G_TETRA',
        GRAVITE=2465521.9,
        DIRECTION={direction},
    ),
)

PULSE = DEFI_FONCTION(
    NOM_PARA='INST',
    PROL_GAUCHE='CONSTANT',
    PROL_DROITE='CONSTANT',
    VALE=(
        0.0, 0.0,
        0.000631, 0.5,
        0.001262, 1.0,
        0.001893, 0.5,
        0.002524, 0.0,
        0.006000, 0.0,
    ),
)

L_INST = DEFI_LIST_REEL(
    DEBUT=0.0,
    INTERVALLE=_F(
        JUSQU_A=0.0025,
        PAS=1.0e-4,
    ),
)

L_ARCH = DEFI_LIST_REEL(
    DEBUT=0.0,
    INTERVALLE=_F(
        JUSQU_A=0.0025,
        PAS=5.0e-4,
    ),
)

RESU = DYNA_NON_LINE(
    MODELE=MODELE,
    CHAM_MATER=CHMAT,
    EXCIT=(
        _F(CHARGE=BC_CONTACT),
        _F(CHARGE=CHOC_DYN, FONC_MULT=PULSE),
    ),
    COMPORTEMENT=_F(
        GROUP_MA='G_TETRA',
        RELATION='ELAS',
        DEFORMATION='PETIT',
    ),
    SCHEMA_TEMPS=_F(
        SCHEMA='NEWMARK',
        FORMULATION='DEPLACEMENT',
    ),
    INCREMENT=_F(LIST_INST=L_INST),
    NEWTON=_F(
        PREDICTION='TANGENTE',
        MATRICE='TANGENTE',
        REAC_ITER=1,
    ),
    ARCHIVAGE=_F(LIST_INST=L_ARCH),
    SOLVEUR=_F(METHODE='MUMPS'),
)

RESU = CALC_CHAMP(
    reuse=RESU,
    RESULTAT=RESU,
    CRITERES=('SIEQ_ELGA',),
)

IMPR_RESU(
    FORMAT='MED',
    UNITE=80,
    RESU=_F(
        RESULTAT=RESU,
        NOM_CHAM=('DEPL', 'SIEF_ELGA', 'SIEQ_ELGA'),
    ),
)

FIN()
"""


EXPORT_TEMPLATE = """P actions make_etude
P debug nodebug
P memjob 12582912
P memory_limit 12288.0
P mode interactif
P mpi_nbcpu 1
P mpi_nbnoeud 1
P ncpus 1
P nomjob carter_choc_{case_id}
P server localhost
P time_limit 21600.0
P tpsjob 360
P version 17.4
A memjeveux 4096.0
A tpmax 21600.0
F comm {remote_root}/03_CODE_ASTER/carter_choc_{case_id}.comm D 1
F libr {remote_root}/02_MAILLAGE/carter_socle_xy_z_netgen.med D 20
F libr {remote_root}/04_RESULTATS/carter_choc_{case_id}.rmed R 80
F mess {remote_root}/03_CODE_ASTER/message_{case_id}.txt R 6
"""


RUN_ONE = """#!/usr/bin/env bash
set -euo pipefail

CASE_ID="${1:?case id required}"
JOB_DIR="/home/qltus1/aster_jobs/carter_choc_cylindrique_v1"
SIF="/home/qltus1/OpenFOAM/apps/code_aster/code_aster_stable.sif"

cd "$JOB_DIR"
mkdir -p logs 04_RESULTATS

apptainer exec --bind /home:/home "$SIF" bash -lc "source /opt/activate.sh && cd '$JOB_DIR' && run_aster '$JOB_DIR/03_CODE_ASTER/carter_choc_${CASE_ID}.export'"
"""


RUN_ALL = """#!/usr/bin/env bash
set -euo pipefail

JOB_DIR="/home/qltus1/aster_jobs/carter_choc_cylindrique_v1"
cd "$JOB_DIR"
mkdir -p logs

for case_id in cyl_ymin cyl_ymax cyl_oblique_ymin_z; do
  echo "===== START ${case_id} $(date -Is) ====="
  ./03_CODE_ASTER/run_one_case_qltus.sh "$case_id" > "logs/run_${case_id}.out" 2>&1
  echo "===== END ${case_id} $(date -Is) ====="
done
"""


README = """# Etude de choc sur le carter cylindrique V1

Cette version reprend le maillage V5 oriente correctement:

- base du ventilateur dans le plan XY;
- hauteur suivant +Z;
- materiau equivalent PETG-CF;
- masses embarquees moteur et electronique reprises de l'etude modale.

Les trois cas lances sont:

1. `cyl_ymin`: choc lateral sur le cote Y- du carter cylindrique;
2. `cyl_ymax`: choc lateral sur le cote Y+ du carter cylindrique;
3. `cyl_oblique_ymin_z`: choc oblique sur le carter avec composante vers le bas.

Le contact est idealise par une petite zone de noeuds bloquee et une impulsion
d'acceleration severe. Le pulse actuel ne reproduit pas strictement une chute
de 0.8 m: son integrale vaut environ 3.11 m/s, soit une hauteur equivalente
proche de 0.49 m. Ce n'est pas encore un vrai contact/rebond explicite, mais
c'est un premier niveau utile pour localiser les zones sensibles.
"""


OPEN_BAT = r"""@echo off
set PV=D:\v2025\W64\paraview\bin\paraview.exe
start "" "%PV%" "%~dp0carter_choc_cyl_ymin.rmed" "%~dp0carter_choc_cyl_ymax.rmed" "%~dp0carter_choc_cyl_oblique_ymin_z.rmed"
"""


def main() -> None:
    code_dir = ROOT / "03_CODE_ASTER"
    result_dir = ROOT / "04_RESULTATS"
    doc_dir = ROOT / "05_DOCUMENTATION"
    for directory in (code_dir, result_dir, doc_dir):
        directory.mkdir(parents=True, exist_ok=True)

    for case in CASES:
        case_id = case["case_id"]
        (code_dir / f"carter_choc_{case_id}.comm").write_text(
            COMM_TEMPLATE.format(**case), encoding="ascii", newline="\n"
        )
        (code_dir / f"carter_choc_{case_id}.export").write_text(
            EXPORT_TEMPLATE.format(case_id=case_id, remote_root=REMOTE_ROOT),
            encoding="ascii",
            newline="\n",
        )

    (code_dir / "run_one_case_qltus.sh").write_text(RUN_ONE, encoding="ascii", newline="\n")
    (code_dir / "run_all_cyl_qltus.sh").write_text(RUN_ALL, encoding="ascii", newline="\n")
    (ROOT / "README_ETUDE_CHOC_CARTER_CYLINDRIQUE_V1.md").write_text(
        README, encoding="ascii", newline="\n"
    )
    (result_dir / "ouvrir_resultats_choc_cylindrique_paraview.bat").write_text(
        OPEN_BAT, encoding="ascii", newline="\r\n"
    )

    print(f"Generated {len(CASES)} Code_Aster cases in {code_dir}")


if __name__ == "__main__":
    main()
