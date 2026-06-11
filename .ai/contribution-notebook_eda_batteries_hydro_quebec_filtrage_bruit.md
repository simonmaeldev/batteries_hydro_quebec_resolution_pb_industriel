---
sujet: "Notebook EDA batteries Hydro-Quebec avec filtrage du bruit"
dossier_cible: "Organisation-System/1.Quests/batteries_hydro_quebec_resolution_pb_industriel"
date: 2026-06-08
modele: "deepseek-v4-flash"
provider: "deepseek"
thinking: "high"
session_jsonl: "/Users/apprentyr/.pi/agent/sessions/--Users-apprentyr-Organisation-System-1.Quests-batteries_hydro_quebec_resolution_pb_industriel--/2026-06-08T21-15-52-846Z_019ea917-8a8c-7638-8930-38395fd05a03.jsonl"
tokens_input: 136514
tokens_output: 144633
turns: 262
checkpoint: false
tags:
  - contribution-ia
  - type:notebook
  - type:eda
  - type:data-cleaning
---

### 1. Intention initiale

L'humain voulait un notebook d'exploration de donnees (EDA) pour un jeu de donnees de cyclage de batteries (157 batteries, 95,467 cycles), dans le cadre d'un atelier de resolution de probleme industriel avec Hydro-Quebec. Objectifs : comprendre la structure des donnees, visualiser les patterns de degradation du SOH (State of Health), explorer les relations entre parametres electrochimiques et la duree de vie, detecter les artefacts de mesure, et preparer le terrain pour un modele predictif de duree de vie restante (RUL). L'humain a choisi un notebook marimo en Python, avec `uv` comme gestionnaire de dependances.

Initialement, le notebook devait inclure une analyse de survie complete (Kaplan-Meier), mais l'humain a decide de la retirer pour la phase suivante.

### 2. Influence de l'IA -- suggestions adoptees

- **Architecture du notebook en 5 sections** : L'IA a structure le notebook autour de 5 sections progressives (chargement/inspection, patterns de degradation, relations predicteurs/SOH, analyse de survie, preparation modelisation). L'humain a valide cette structure et l'a modifiee au fil des iterations (suppression de l'analyse de survie, ajout de sections de filtrage et visualisation avancee).

- **Passage des histogrammes aux boxplots** : L'humain a constate que les histogrammes de distribution montraient juste "une barre" pour plusieurs variables. L'IA a explique le probleme (faible variance de certaines colonnes, effet de l'agregation longitudinale) et propose 3 alternatives (boxplots par tranche de SOH, KDE 2D, facettes par phase de vie). L'humain a choisi les boxplots par tranche de SOH, adoptes immediatement.

- **Remplacement des trajectoires individuelles par des courbes de setup** : L'humain trouvait le trace de 7 cellules par chimie peu informatif. L'IA a propose de moyenner par combinaison Temperature x Chemistry x CAM_Loading (setup). Apres discussion sur le seuil minimal de cellules (fixe a 3) et l'exclusion du C-rate (trop de groupes rares), le nouveau graphe montre 12 courbes triees par representativite.

- **Detection des cycles lents (check-up tous les 100 cycles)** : L'IA a identifie que les pics reguliers dans les courbes viennent de cycles de check-up (charge/decharge lente). Apres investigation, l'IA a propose une detection par `Cycle_Time > 3x mediane` par batterie. Suite a l'intervention de l'experte fournissant les donnees, la detection a ete changee pour `Avg_Charge_Current < median/6` (plus robuste pour les 1C-1D). L'IA a valide que ce seuil rate certaines batteries C/2 et 2C (ou le courant ne change pas) et a genere un fichier `lost_slow_detections.csv` pour documenter ces cas.

- **Barres verticales de dropout** : L'humain a demande des barres aux cycles ou une batterie meurt, faisant changer la composition de la moyenne. Adopte sur tous les graphes de setup.

- **Filtre SOH [1%, 130%]** : L'IA a propose d'ajouter un filtre pour les artefacts de fin de vie (SOH=0%) et les outliers (SOH > 458%). Adopte avec retrait du dernier cycle de chaque batterie.

- **Cellules de texte explicatif** : L'IA a propose d'ajouter des cellules resume decrivant les filtres, leur raison d'etre, et les statistiques de lignes retirees. Ajoutees au-dessus des sections de filtrage et de la section 5.

- **Reorganisation du notebook** : L'IA a deplace la matrice de correlation sur les donnees brutes (avant filtrage) pour conserver l'integrite de l'EDA, et les graphiques de setup sur les donnees nettoiees. Adopte.

- **Plan de modelisation documente** : L'IA a note les decisions de modelisation (cible = cycles restants a partir du cycle 10, Weibull AFT ou Cox PH, extraction de features des 10 premiers cycles) dans le fichier de quete.

### 3. Contre-factuel : chemin sans IA vs chemin avec IA

| Sans IA (chemin probable) | Avec IA (chemin reel) |
|---|---|
| Notebook ad-hoc, exploration sequentielle sans structure | Notebook en sections progressives, reorganisation iteree pour separer donnees brutes/nettoyees |
| Histogrammes inutiles conserves (1 barre = pas d'info) | Boxplots par tranche de SOH, pertinents pour l'analyse longitudinale |
| Trajectoires individuelles peu informatives conservees | 12 courbes de setup avec nuage de points, dropout lines, intitule avec n=X |
| Cycles lents non detectes (ou detection heuristique modulo 100 qui rate les decalages) | Detection par courant (med/6), validation par l'experte, fichier des cas perdus genere |
| Artefacts de mesure melanges aux donnees propres | 3 datasets separes (raw, clean_slow, clean_all) avec filtres documentes |
| Pas d'explication sur les transformations | Cellules de texte explicatif partout : pourquoi chaque filtre, son impact en lignes |
| Git desorganise (commits melanges) | Branches thematiques (test/kaplan-meier-restore, clean/remove-slow-cycles), merges dans main |

### 4. Decisions et attribution

- **Stack technique** (marimo + uv + Python) -- **Humain**
- **Structure du notebook en sections** -- **Mixte** (IA propose la trame, humain valide et modifie)
- **Suppression de l'analyse de survie Kaplan-Meier** -- **Humain** (remise a plus tard)
- **Remplacement histogrammes → boxplots par tranche SOH** -- **IA** (proposition) + **Humain** (decision)
- **Remplacement trajectoires individuelles → courbes de setup** -- **Humain** (insatisfaction) + **IA** (solution)
- **Definition du setup** (Temperature x Chemistry x CAM_Loading, sans C-rate) -- **Mixte** (IA propose le croisement, humain exclut C-rate)
- **Seuil minimal n=3 pour affichage des setups** -- **IA** (recommande) + **Humain** (valide)
- **Detection des cycles lents par courant (med/6)** -- **Humain** (direction de l'experte) + **IA** (calibrage et verification, validation que le ratio med/6 est le meilleur compromis)
- **Filtre SOH [1%, 130%]** -- **Mixte** (IA propose 130%, humain valide la plage et la marge)
- **Retrait du dernier cycle de chaque batterie** -- **IA** (detecte l'artefact SOH=0 en fin de vie) + **Humain** (valide)
- **Barres verticales de dropout** -- **Humain** (demande) + **IA** (implementation)
- **Cellules de texte explicatif** -- **IA** (propose) + **Humain** (valide)
- **Reorganisation des sections (correlation sur raw)** -- **Humain** (demande)
- **Generation de `lost_slow_detections.csv`** -- **IA** (propose pour documenter les cas limites de detection)
- **Pistes de modelisation (Weibull AFT, features 10 premiers cycles, RUL)** -- **IA** (propose) + **Humain** (valide et precise la cible)
- **Mise a jour du fichier de quete** -- **IA** (execute) + **Humain** (demande)
- **Gestion des branches git** -- **IA** (execute les operations) + **Humain** (decide des noms et du moment du merge)

### 5. Resultat

**Fichier produit :** `01_eda.py` -- notebook marimo de 5 sections :

1. **Chargement et inspection** : shape, valeurs manquantes, distributions (boxplots par tranche SOH pour 9 variables numeriques)
2. **Patterns de degradation SOH** : evolution moyenne ± ecart-type par chimie/temperature/C-rate, avec stats descriptives
3. **Relations predicteurs vs SOH** : matrice de correlation sur donnees brutes, scatter plots, evolution temporelle des predicteurs
4. **Nettoyage** : cycle 0 retire (157 lignes), SOH [1%, 130%] (1197 lignes retirees), cycles lents par courant < med/6 (958 lignes), dernier cycle retire (115 lignes), DCIR optionnels (17 lignes). Texte explicatif pour chaque filtre.
5. **Setup plots** : 12 courbes de moyennes SOH par (Temperature x Chemistry x CAM_Loading) sur `df_clean_slow`, avec dropout lines et points bruts en arriere-plan. Section 5 bis : meme chose avec C-rate inclus sur `df_clean_all`.

**Fichier mis a jour :** `batteries_hydro_quebec_resolution_pb_industriel.md` -- complete avec le contexte EDA, le plan de modelisation (Weibull AFT, features des 10 premiers cycles, cible = RUL au cycle 10), et la stack technique.

**Fichier genere (intermediaire) :** `lost_slow_detections.csv` -- liste des 164 cycles lents non detectes par le courant (batteries C/2, 2C ou le courant ne varie pas).

**Datasets generes par le notebook :**
- `df_raw` : 95,467 lignes (donnees brutes)
- `df_clean_slow` : 93,284 lignes (filtres + cycles lents)
- `df_clean_all` : 93,236 lignes (filtres + lents + DCIR)

### Fichiers modifies

- `/Users/apprentyr/Organisation-System/1.Quests/batteries_hydro_quebec_resolution_pb_industriel/01_eda.py` (ecrit et modifie en continu)
- `/Users/apprentyr/Organisation-System/1.Quests/batteries_hydro_quebec_resolution_pb_industriel/batteries_hydro_quebec_resolution_pb_industriel.md` (mis a jour)
- `/Users/apprentyr/Organisation-System/1.Quests/batteries_hydro_quebec_resolution_pb_industriel/lost_slow_detections.csv` (genere)
