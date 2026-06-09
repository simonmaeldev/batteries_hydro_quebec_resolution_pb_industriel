# Batteries Hydro-Quebec -- Prediction de duree de vie

16e Atelier de resolution de problemes industriels de Montreal.

**Objectif** : Predire la duree de vie residuelle (RUL) de batteries a partir des 10 premiers cycles de charge/decharge + parametres de fabrication.

**Equipe** : contribution ouverte -- voir ci-dessous.

---

## Installation

### 1. Cloner le repo

```bash
git clone git@github.com:simonmaeldev/batteries_hydro_quebec_resolution_pb_industriel.git
cd batteries_hydro_quebec_resolution_pb_industriel
```

### 2. Installer uv (gestionnaire de paquets Python)

**macOS / Linux :**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell) :**

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verifier l'installation :

```bash
uv --version
```

### 3. Creer l'environnement virtuel et installer les dependances

```bash
uv sync
```

Active l'environnement :

```bash
source .venv/bin/activate   # macOS / Linux
# ou
.venv\Scripts\activate      # Windows
```

### 4. Ajouter les donnees locales

Les donnees source (CSVs par batterie et fichier XLSX de metadonnees) NE sont PAS dans le repo pour des raisons de confidentialite.

Pour travailler, placez les fichiers suivants dans le dossier du projet :

| Fichier | Emplacement | Description |
|---|---|---|
| `Summary_cells_MC_YB_03-06-2026.xlsx` | racine du projet | Metadonnees des batteries (cell name, chimie, temperature, etc.) |
| Fichiers `*_GCPL.csv` | `Summary/` | Donnees de cyclage par batterie (157 fichiers) |

- `Summary/` doit contenir les ~157 fichiers CSV (ex: `SAV250718G_00_03_GCPL.csv`, `SAL241202J_01_02_GCPL.csv`, etc.)
- Les CSV doivent etre en encoding `latin-1` (standard des fichiers GCPL)

### 5. Fusionner les donnees (optionnel -- deja fait)

```bash
uv run python merge_batteries.py
```

Produit `all_batteries_combined.csv` (~27 MB, 95k lignes, 157 batteries).

### 6. Lancer le notebook d exploration

```bash
uv run marimo edit 01_eda.py
```

Dans le navigateur, les cellules se chargent automatiquement. Cliquer "Run all" pour executer l'EDA complete.

---

## Structure du projet

```
.
├── 01_eda.py                  # Notebook marimo d exploration
├── merge_batteries.py         # Script de fusion CSV + XLSX
├── pyproject.toml             # Dependances Python (uv)
├── uv.lock                    # Lockfile des dependances
├── .gitignore                 # Fichiers exclus du versioning (donnees !)
├── README.md                  # Ce fichier
├── Summary/                   # DONNEES BRUTES -- pas dans le repo
│   └── *_GCPL.csv             #   ~157 fichiers source
├── Summary_cells_MC_YB_03-06-2026.xlsx  # DONNEES -- pas dans le repo
└── all_batteries_combined.csv # FUSION -- pas dans le repo
```

---

## Donnees : confidentialite

**NE JAMAIS commit les fichiers de donnees.** Le `.gitignore` les bloque automatiquement (`.csv`, `.xlsx`, `Summary/`, `all_batteries_combined.csv`).

Si vous avez un doute :

```bash
git status
```

Verifiez qu aucun fichier de donnees n apparait en vert (stagé). Si oui, contactez l equipe.

---

## Contribution

1. **Clonez le repo** et installez l environnement (voir Installation)
2. **Placez vos donnees** localement (voir section donnees)
3. **Creez une branche** pour vos modifications :
   ```bash
   git checkout -b feature/mon-analyse
   ```
4. **Commitez** uniquement le code, pas les donnees
5. **Push** et ouvrez une Pull Request sur GitHub

Tout le monde ayant le lien peut contribuer. Le code est public, les donnees restent locales.

---

## Fichiers de code

### `01_eda.py`

Notebook marimo d analyse exploratoire. Contient :
- Chargement et nettoyage des donnees
- Visualisations univariees et multivariees
- Analyse de survie (Kaplan-Meier)
- Extraction de features des 10 premiers cycles

### `merge_batteries.py`

Script de fusion qui :
1. Lit le XLSX de metadonnees (`Summary_cells_MC_YB_03-06-2026.xlsx`, sheet "Cycled Cells")
2. Parcourt les CSV dans `Summary/` et apparie chaque fichier a sa ligne de metadonnees via le `Cell Name` (prefixe du nom de fichier)
3. Ecrit `all_batteries_combined.csv` avec colonnes cycliques + metadonnees fixes

---

## Licence

Interne au cours -- pas de redistribution des donnees.
