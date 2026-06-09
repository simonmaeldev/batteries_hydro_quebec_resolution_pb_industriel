---
title: "Resolution de probleme industriel - Prediction duree de vie batteries Hydro-Quebec"
created: 2026/06/08
status: in progress
due: 2026/06/12
---

# Resolution de probleme industriel - Prediction duree de vie batteries Hydro-Quebec

16e Atelier de resolution de problemes industriels de Montreal.

## Objectifs

1. **Predire la duree de vie (RUL)** des batteries a partir des predicteurs disponibles, et expliquer ce qui se passe (interpretabilite).
2. **Prediction precoce** : mesurer les 10 premiers cycles, puis predire le nombre de cycles total.

## Livrable

Rapport d'analyse.

## Donnees

Fichier : `all_batteries_combined.csv`
Nombre de lignes : 95,467 (donnees par cycle)
Nombre de batteries : 157
Projets : P1 a P6 (6 projets)

### Variables

- **Cycle** : numero de cycle
- **Cycle_Time (h)** : duree du cycle
- **Avg_Discharge_Voltage (V)** : tension moyenne de decharge
- **Avg_Charge_Voltage (V)** : tension moyenne de charge
- **Avg_Charge_Current (A)** : courant moyen de charge
- **Discharge_Capacity (mAh)** : capacite de decharge
- **Charge_Capacity (mAh)** : capacite de charge
- **Coulomb_Efficiency (%)** : efficacite coulombique (artefact au cycle 1)
- **SOH_Energy (%)** : State of Health energetique -- variable cible
- **Polarization (Ohm cm2)** : polarisation
- **Project** : projet (P1-P6)
- **Cell_Name** : identifiant unique de la batterie
- **Chemistry** : chimie cathode (A, B, C)
- **Cut-off** : tension de coupure (4.2V)
- **Temperature** : temperature du test (25C, 45C, 60C)
- **C-rate** : regime de charge/decharge (1C-1D, C/2-D/2, 2C-2D, etc.)
- **Cathode_Area (cm2)** : surface de cathode
- **CAM_Loading (mg/cm2)** : chargement de matiere active
- **CAM_Mass (g)** : masse de matiere active
- **CAM_Theoretical_Capacity (mAh/g)** : capacite theorique
- **CAM_Capacity_1st_cycle (mAh)** : capacite au 1er cycle
- **Normalized_CAM_Capacity_2nd_cycle (mAh/g)** : capacite normalisee au 2e cycle
- **Completed_cycles** : nombre total de cycles effectues
- **Cycles_>_80%_capacity** : cycles avant seuil 80% (ou "Not reached")
- **Cycles_>_50%_capacity** : cycles avant seuil 50% (ou "Not reached")

## Observations preliminaires

- **157 batteries**, 3 chimies (A: 40, B: 61, C: 56)
- 3 temperatures (25C: 106, 45C: 36, 60C: 15)
- SOH commence a ~100% et decline jusqu'a 0-80% selon les batteries
- 91 batteries ont franchi le seuil de 80% (evenements), 66 sont censurees a droite
- Grandes differences de degradation entre chimies : A semble plus stable
- Temperature 60C accelere fortement la degradation
- Polarization augmente avec l'age (bon indicateur)
- SOH peut depasser 100% (bruit de mesure : winsoriser)
- Coulomb_Efficiency a un artefact au cycle 1 (19612%) : a corriger

## Stack technique

Python (marimo notebook) + librairies :
- pandas, numpy, matplotlib, seaborn
- scipy, scikit-learn
- lifelines (analyse de survie)
- statsmodels

## Objectif 2 : Prediction precoce (RUL)

**Probleme** : a partir des 10 premiers cycles de charge/decharge d'une batterie, predire le nombre de cycles restants avant qu'elle n'atteigne 80% de SOH.

**Cible** : `failure_cycle_80 - 10` = cycles restants apres la fenetre d'observation de 10 cycles. Les batteries qui n'ont pas atteint 80% sont traitees comme des observations censurees a droite (analyse de survie).

**Features candidates** (a extraire des 10 premiers cycles) :
- Pente de SOH sur les cycles 1-10 (taux de degradation precoce)
- Polarisation initiale et son taux de changement
- Coulomb efficiency moyenne (apres filtrage du cycle 1)
- Valeurs moyennes : voltages, courants, capacites
- Parametres de fabrication invariants : Chemistry, Temperature, C-rate, CAM_Loading, Cathode_Area, CAM_Mass

**Modele cible** : modele parametrique interpretable.
- Cox Proportional Hazards (coefficients interpretables, semi-parametrique)
- Weibull Accelerated Failure Time (modele parametrique complet)
- Alternative : Random Survival Forest si la performance prime sur l'interpretabilite

**Contrainte** : le modele doit pouvoir etre utilise sur une nouvelle batterie dont on a mesure les 10 premiers cycles et les parametres de fabrication.

## Fichiers du projet

- `01_eda.py` : notebook marimo d'exploration et analyse exploratoire
- `all_batteries_combined.csv` : donnees combinees
- `Summary/` : donnees sources par batterie
- `merge_batteries.py` : script de fusion
- `pyproject.toml` : dependances Python (gestion uv)

