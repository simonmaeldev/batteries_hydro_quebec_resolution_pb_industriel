import marimo

__generated_with = "0.23.9"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    import warnings
    warnings.filterwarnings('ignore')
    return mo, np, pd, plt, sns


@app.cell
def _(mo):
    mo.md("""
    # Analyse exploratoire - Batteries Hydro-Quebec

    Prediction de duree de vie residuelle (RUL) a partir des cycles de charge/decharge.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## 1. Chargement et inspection des donnees brutes
    """)
    return


@app.cell
def _(pd):
    df_raw = pd.read_csv('all_batteries_combined.csv')
    return (df_raw,)


@app.cell
def _(df_raw):
    df_raw.info(show_counts=True)
    return


@app.cell
def _(df_raw, mo):
    n_cells_1 = df_raw['Cell_Name'].nunique()
    n_proj_1 = df_raw['Project'].nunique()
    n_chem_1 = df_raw['Chemistry'].nunique()
    n_rows_1 = len(df_raw)
    mo.md(f"**Apercu** : {n_rows_1:,} lignes, {n_cells_1} cellules, {n_proj_1} projets, {n_chem_1} chimies")
    return


@app.cell
def _(df_raw, mo, pd):
    nulls_1 = df_raw.isnull().sum()
    zeros_1 = (df_raw == 0).sum()
    tbl_nulls = pd.DataFrame({'nulls': nulls_1, 'zeros': zeros_1, 'dtype': df_raw.dtypes}).sort_values('nulls', ascending=False)
    tbl_nulls = tbl_nulls[tbl_nulls['nulls'] > 0]
    if len(tbl_nulls) > 0:
        mo.ui.table(tbl_nulls)
    else:
        mo.md(f"Aucune valeur manquante. (Total: {df_raw.isnull().sum().sum()})")
    return


@app.cell
def _(df_raw, mo, pd):
    cat_cols_1 = ['Project', 'Cell_Name', 'Chemistry', 'Cut-off', 'Temperature', 'C-rate']
    tabs_1 = {
        c: mo.ui.table(pd.DataFrame({'valeur': df_raw[c].value_counts().index, 'compte': df_raw[c].value_counts().values}))
        for c in cat_cols_1
    }
    mo.ui.tabs(tabs_1)
    return


@app.cell
def _(df_raw, np, pd, plt):
    num_cols_1 = [
        'Cycle_Time (h)', 'Avg_Discharge_Voltage (V)', 'Avg_Charge_Voltage (V)',
        'Avg_Charge_Current (A)', 'Discharge_Capacity (mAh)', 'Charge_Capacity (mAh)',
        'Coulomb_Efficiency (%)', 'SOH_Energy (%)', 'Polarization (Ohm cm\u00b2)',
    ]

    df_box = df_raw.replace(0, np.nan).copy()
    bins_soh = [0, 50, 80, 90, 95, 100, 130]
    labels_soh = ['<50%', '50-80%', '80-90%', '90-95%', '95-100%', '>100%']
    df_box['soh_bin'] = pd.cut(df_box['SOH_Energy (%)'], bins=bins_soh, labels=labels_soh, right=False)

    fig_box, axs_box = plt.subplots(3, 3, figsize=(18, 14))
    axs_box = axs_box.flatten()
    for i_box, col_box in enumerate(num_cols_1):
        if col_box == 'SOH_Energy (%)':
            axs_box[i_box].text(0.5, 0.5, 'SOH (reference)', ha='center', va='center',
                               transform=axs_box[i_box].transAxes, fontsize=12)
            axs_box[i_box].set_title('SOH_Energy (%)')
            continue
        df_box.boxplot(column=col_box, by='soh_bin', ax=axs_box[i_box], grid=False, showfliers=False)
        axs_box[i_box].set_title(col_box, fontsize=10)
        axs_box[i_box].set_xlabel('SOH')
        axs_box[i_box].set_ylabel('')
    plt.suptitle('Distribution des predicteurs par tranche de SOH', fontsize=14)
    plt.tight_layout()
    plt.gca()
    return (num_cols_1,)


@app.cell
def _(df_raw, mo, num_cols_1):
    stats_1 = df_raw[num_cols_1].describe(percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).T
    mo.ui.table(stats_1)
    return


@app.cell
def _(mo):
    mo.md("""
    ## 2. Patterns de degradation (SOH)
    """)
    return


@app.cell
def _(df_raw, mo):
    soh_by_cycle = df_raw.groupby('Cycle')['SOH_Energy (%)'].agg(['mean', 'std', 'min', 'max', 'count']).reset_index()
    soh_by_cycle = soh_by_cycle[soh_by_cycle['count'] > 5]
    mo.ui.table(soh_by_cycle.head(20))
    return (soh_by_cycle,)


@app.cell
def _(plt, soh_by_cycle):
    fig_soh, ax_soh = plt.subplots(figsize=(14, 5))
    ax_soh.plot(soh_by_cycle['Cycle'], soh_by_cycle['mean'], 'b-', linewidth=1)
    ax_soh.fill_between(soh_by_cycle['Cycle'],
                         soh_by_cycle['mean'] - soh_by_cycle['std'],
                         soh_by_cycle['mean'] + soh_by_cycle['std'],
                         alpha=0.2, color='blue')
    ax_soh.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='Seuil 80%')
    ax_soh.axhline(y=50, color='orange', linestyle='--', alpha=0.7, label='Seuil 50%')
    ax_soh.set_xlabel('Cycle')
    ax_soh.set_ylabel('SOH_Energy (%)')
    ax_soh.set_title('Evolution moyenne du SOH par cycle (mean +/- std)')
    ax_soh.legend()
    ax_soh.set_xlim(0, soh_by_cycle['Cycle'].max())
    plt.gca()
    return


@app.cell
def _(df_raw, plt):
    chem_list = sorted(df_raw['Chemistry'].unique())
    fig_chem, axs_chem = plt.subplots(1, 3, figsize=(18, 5))
    for ax_c, chem_c in zip(axs_chem, chem_list):
        sub_c = df_raw[df_raw['Chemistry'] == chem_c]
        agg_c = sub_c.groupby('Cycle')['SOH_Energy (%)'].agg(['mean', 'std', 'count'])
        agg_c = agg_c[agg_c['count'] > 3]
        ax_c.plot(agg_c.index, agg_c['mean'], linewidth=1.5)
        ax_c.fill_between(agg_c.index, agg_c['mean'] - agg_c['std'], agg_c['mean'] + agg_c['std'], alpha=0.2)
        ax_c.axhline(y=80, color='red', linestyle='--', alpha=0.5)
        ax_c.set_title(f'Chemistry {chem_c}')
        ax_c.set_xlabel('Cycle')
        ax_c.set_ylabel('SOH (%)')
        ax_c.set_xlim(0, agg_c.index.max())
    plt.tight_layout()
    plt.gca()
    return


@app.cell
def _(df_raw, plt):
    temp_list = sorted(df_raw['Temperature'].unique())
    fig_temp, axs_temp = plt.subplots(1, 3, figsize=(18, 5))
    for ax_t, temp_t in zip(axs_temp, temp_list):
        sub_t = df_raw[df_raw['Temperature'] == temp_t]
        agg_t = sub_t.groupby('Cycle')['SOH_Energy (%)'].agg(['mean', 'std', 'count'])
        agg_t = agg_t[agg_t['count'] > 3]
        ax_t.plot(agg_t.index, agg_t['mean'], linewidth=1.5)
        ax_t.fill_between(agg_t.index, agg_t['mean'] - agg_t['std'], agg_t['mean'] + agg_t['std'], alpha=0.2)
        ax_t.axhline(y=80, color='red', linestyle='--', alpha=0.5)
        ax_t.set_title(f'Temperature {temp_t}')
        ax_t.set_xlabel('Cycle')
        ax_t.set_ylabel('SOH (%)')
        ax_t.set_xlim(0, agg_t.index.max())
    plt.tight_layout()
    plt.gca()
    return


@app.cell
def _(df_raw, plt):
    crate_list = sorted(df_raw['C-rate'].unique())
    fig_cr, axs_cr = plt.subplots(2, 4, figsize=(20, 10))
    axs_cr = axs_cr.flatten()
    for ax_r, crate_r in zip(axs_cr, crate_list):
        sub_r = df_raw[df_raw['C-rate'] == crate_r]
        agg_r = sub_r.groupby('Cycle')['SOH_Energy (%)'].agg(['mean', 'std', 'count'])
        agg_r = agg_r[agg_r['count'] > 3]
        if len(agg_r) > 0:
            ax_r.plot(agg_r.index, agg_r['mean'], linewidth=1.5)
            ax_r.fill_between(agg_r.index, agg_r['mean'] - agg_r['std'], agg_r['mean'] + agg_r['std'], alpha=0.2)
            ax_r.set_xlim(0, agg_r.index.max())
        ax_r.axhline(y=80, color='red', linestyle='--', alpha=0.5)
        ax_r.set_title(f'C-rate {crate_r}')
        ax_r.set_xlabel('Cycle')
        ax_r.set_ylabel('SOH (%)')
    plt.tight_layout()
    plt.gca()
    return


@app.cell
def _(mo):
    mo.md("""
    ## 3. Relations entre predicteurs et SOH (donnees brutes)
    """)
    return


@app.cell
def _(df_raw, np, num_cols_1, plt, sns):
    corr_cols_3 = num_cols_1 + ['Cycle']
    corr_3 = df_raw[corr_cols_3].replace(0, np.nan).corr()

    fig_corr, ax_corr = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr_3, annot=True, fmt='.2f', cmap='RdBu_r', center=0, square=True, ax=ax_corr, cbar_kws={'shrink': 0.8})
    ax_corr.set_title('Matrice de correlation (donnees brutes)')
    plt.tight_layout()
    plt.gca()
    return (corr_3,)


@app.cell
def _(corr_3, mo, pd):
    soh_corr_3 = corr_3['SOH_Energy (%)'].drop('SOH_Energy (%)').sort_values(ascending=False)
    mo.ui.table(pd.DataFrame({'correlation avec SOH': soh_corr_3}))
    return


@app.cell
def _(df_raw, plt):
    key_preds_3 = ['Cycle', 'Avg_Discharge_Voltage (V)', 'Avg_Charge_Voltage (V)',
                   'Discharge_Capacity (mAh)', 'Charge_Capacity (mAh)',
                   'Polarization (Ohm cm\u00b2)', 'Coulomb_Efficiency (%)']

    fig_scat, axs_scat = plt.subplots(2, 4, figsize=(20, 10))
    axs_scat = axs_scat.flatten()
    for ax_sp, pred_sp in zip(axs_scat, key_preds_3):
        for chem_sp in ['A', 'B', 'C']:
            sub_sp = df_raw[df_raw['Chemistry'] == chem_sp].sample(min(2000, len(df_raw[df_raw['Chemistry'] == chem_sp])))
            ax_sp.scatter(sub_sp[pred_sp], sub_sp['SOH_Energy (%)'], s=1, alpha=0.3, label=f'Chem {chem_sp}')
        ax_sp.set_xlabel(pred_sp)
        ax_sp.set_ylabel('SOH (%)')
        ax_sp.legend(markerscale=5)
    plt.tight_layout()
    plt.gca()
    return


@app.cell
def _(df_raw, plt):
    cycle_preds_3 = ['Discharge_Capacity (mAh)', 'Avg_Discharge_Voltage (V)',
                     'Polarization (Ohm cm\u00b2)', 'Coulomb_Efficiency (%)']

    fig_evol, axs_evol = plt.subplots(2, 2, figsize=(16, 10))
    axs_evol = axs_evol.flatten()
    for ax_ev, pred_ev in zip(axs_evol, cycle_preds_3):
        for chem_ev in ['A', 'B', 'C']:
            sub_ev = df_raw[df_raw['Chemistry'] == chem_ev]
            agg_ev = sub_ev.groupby('Cycle')[pred_ev].mean()
            ax_ev.plot(agg_ev.index, agg_ev.values, label=f'Chem {chem_ev}', linewidth=1)
        ax_ev.set_xlabel('Cycle')
        ax_ev.set_ylabel(pred_ev)
        ax_ev.legend()
    plt.tight_layout()
    plt.gca()
    return


@app.cell
def _(mo):
    mo.md("""
    ## Annexe : Nettoyage des cycles lents (check-up tous les 100 cycles)
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    **Pourquoi ?** Tous les ~100 cycles, le protocole de test impose un cycle de charge/decharge tres lent (~18h au lieu de ~2.4h).
    Ce cycle lent fait artificiellement remonter le SOH de ~4-5% et fait x2.5 la Polarization. Des le cycle suivant, tout revient a la normale.

    **Impact** : 1122 cycles lents identifies sur les 157 batteries (7.1 en moyenne, max 27 pour SAL241202I). Ces cycles creent un bruit
    parasite dans les donnees et surestiment la sante reelle de la batterie a ces moments-la.

    **Traitement** : detection par `Avg_Charge_Current < median(Avg_Charge_Current) / 6` pour chaque batterie
    (le courant de charge est divise par ~8-10 pendant les check-ups), puis suppression des cycles lents.
    ZERO cycle de recuperation a ignorer -- la batterie revient a son etat normal des le cycle suivant.

    **Autres filtres** : cycle 0 retire (SOH=0), dernier cycle retire (artefact fin de test), SOH hors [1%, 130%] retire.
    """)
    return


@app.cell
def _(df_raw, plt):
    pol_col = 'Polarization (Ohm cm\u00b2)'

    cell_sl = 'SAL241202I'
    sub_sl = df_raw[df_raw['Cell_Name'] == cell_sl].sort_values('Cycle').copy()

    median_cur_sl = sub_sl['Avg_Charge_Current (A)'].median()
    sub_sl['is_slow'] = sub_sl['Avg_Charge_Current (A)'] < median_cur_sl / 6
    slow_cycles = sub_sl[sub_sl['is_slow']]['Cycle'].astype(int).values

    fig_slow, axs_slow = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

    ax_s0 = axs_slow[0]
    ax_s0.plot(sub_sl['Cycle'], sub_sl['SOH_Energy (%)'], 'b-', linewidth=0.8, alpha=0.5)
    ax_s0.scatter(sub_sl.loc[sub_sl['is_slow'], 'Cycle'], sub_sl.loc[sub_sl['is_slow'], 'SOH_Energy (%)'],
              color='red', s=20, zorder=5, label=f'Cycles lents (n={len(slow_cycles)})')
    ax_s0.axhline(y=80, color='gray', linestyle='--', alpha=0.4)
    ax_s0.set_ylabel('SOH_Energy (%)')
    ax_s0.set_title(f'{cell_sl} - Effet des cycles lents sur SOH (max slow cycles: 27)')
    ax_s0.legend()

    ax_s1 = axs_slow[1]
    ax_s1.plot(sub_sl['Cycle'], sub_sl['Discharge_Capacity (mAh)'], 'b-', linewidth=0.8, alpha=0.5)
    ax_s1.scatter(sub_sl.loc[sub_sl['is_slow'], 'Cycle'], sub_sl.loc[sub_sl['is_slow'], 'Discharge_Capacity (mAh)'],
              color='red', s=20, zorder=5)
    ax_s1.set_ylabel('Discharge_Capacity (mAh)')
    ax_s1.set_title('Discharge Capacity')

    ax_s2 = axs_slow[2]
    ax_s2.plot(sub_sl['Cycle'], sub_sl[pol_col], 'b-', linewidth=0.8, alpha=0.5)
    ax_s2.scatter(sub_sl.loc[sub_sl['is_slow'], 'Cycle'], sub_sl.loc[sub_sl['is_slow'], pol_col],
              color='red', s=20, zorder=5)
    ax_s2.set_xlabel('Cycle')
    ax_s2.set_ylabel('Polarization')
    ax_s2.set_title('Polarization')

    plt.tight_layout()
    plt.gca()
    return


@app.cell
def _(mo):
    mo.md("""
    **Recapitulatif des filtres appliques**

    1. **Cycle 0** : retire car SOH=0 par definition (cycle de reference avant le vrai test).
    2. **SOH > 130%** : artefacts de mesure aberrants (ex: SOH=458%). On garde une marge au-dessus de 100%
       car le SOH peut remonter legerement (>100%) lors des cycles lents de check-up.
    3. **SOH < 1%** : artefacts de fin de test (decharge totale). Les batteries reellement mortes (<80%)
       restent dans le dataset jusqu'a leur dernier cycle utile.
    4. **Dernier cycle** : retire pour chaque batterie (artefact de fin de test, souvent SOH=0 ou aberrant).
    5. **Cycles lents (check-up ts les 100 cycles)** : detection par `Avg_Charge_Current < median/6`.
       Le courant de charge est divise par ~8-10 pendant les check-ups, ce qui fait remonter le SOH de +4-5%.
       ZERO cycle de recuperation apres : le retour a la normale est immediat.
    6. **DCIR (optionnel)** : detection par `Avg_Charge_Current < median/3` pour les batteries
       avec protocole "w/ DCIR". Ces cycles intermediaires creent du bruit supplementaire.

    **Deux versions du dataset nettoye** :
    - `df_clean_slow` : filtres 1-4 uniquement (cycles normaux + check-up retires)
    - `df_clean_all` : filtres 1-5 (check-up + DCIR retires)
    """)
    return


@app.cell
def _(df_raw):
    """Filtrer : courant lent + dernier cycle + outliers SOH"""
    def flag_cycles(grp):
        grp_sorted = grp.sort_values('Cycle')
        # Detection par courant: courant < median/6 (expert: facteur ~10 sur 1C-1D)
        med_cur = grp_sorted['Avg_Charge_Current (A)'].median()
        grp_sorted['is_slow'] = grp_sorted['Avg_Charge_Current (A)'] < med_cur / 6
        # Anomalies: courant < median/3 (inclut slow + DCIR)
        grp_sorted['is_anomaly'] = grp_sorted['Avg_Charge_Current (A)'] < med_cur / 3
        # Dernier cycle de chaque batterie
        last_cycle = grp_sorted['Cycle'].max()
        grp_sorted['is_last'] = grp_sorted['Cycle'] == last_cycle
        return grp_sorted

    df_f = df_raw.groupby('Cell_Name', group_keys=False).apply(flag_cycles)

    # Filtrer cycle 0, SOH hors plage, dernier cycle, cycles anormaux
    df_f = df_f[df_f['Cycle'] > 0]
    df_f = df_f[df_f['SOH_Energy (%)'].between(1, 130)]

    n_tot = len(df_raw)
    n_slow = df_f['is_slow'].sum()
    n_anom = df_f['is_anomaly'].sum()
    n_last = df_f['is_last'].sum()
    n_cycle0 = (df_raw['Cycle'] == 0).sum()
    n_outliers = ((df_raw['Cycle'] > 0) & (~df_raw['SOH_Energy (%)'].between(1, 130))).sum()

    # clean_slow: retire cycle 0, SOH outliers, dernier cycle, slow cycles
    df_clean_slow = df_f[~(df_f['is_slow'] | df_f['is_last'])].drop(columns=['is_slow', 'is_anomaly', 'is_last'])
    # clean_all: idem + DCIR
    df_clean_all = df_f[~(df_f['is_anomaly'] | df_f['is_last'])].drop(columns=['is_slow', 'is_anomaly', 'is_last'])

    print(f"Dataset original           : {n_tot} lignes")
    print(f"  Cycle 0 retire           : {n_cycle0}")
    print(f"  SOH hors [1,130] retire  : {n_outliers}")
    print(f"  Dernier cycle retire     : {n_last}")
    print(f"  Courant lent (med/6)     : {n_slow} -> df_clean_slow ({len(df_clean_slow)})")
    print(f"  Anomalies (med/3)        : {n_anom} -> df_clean_all  ({len(df_clean_all)})")
    print(f"    dont DCIR seuls        : {n_anom - n_slow}")
    return df_clean_all, df_clean_slow


@app.cell
def _(mo):
    mo.md("""
    ## 4. Trajectoires moyennes par setup (donnees nettoyees)
    """)
    return


@app.cell
def _(df_clean_slow, plt):
    col_load_c = 'CAM_Loading (mg/cm\u00b2)'

    cs_c = df_clean_slow.groupby('Cell_Name').agg({
        'Temperature': 'first', 'Chemistry': 'first', col_load_c: 'first',
    }).reset_index()
    cs_c['setup_c'] = (cs_c['Temperature'] + ' | ' + cs_c['Chemistry'] + ' | load=' + cs_c[col_load_c].astype(str))
    sc_c = cs_c['setup_c'].value_counts()
    so_c = sc_c.index.tolist()
    sm_c = cs_c.set_index('Cell_Name')['setup_c'].to_dict()

    dp_c = df_clean_slow.copy()
    dp_c['setup_c'] = dp_c['Cell_Name'].map(sm_c)

    dp_c_sample = dp_c[dp_c['Cycle'] % 20 == 0].copy()

    fig_all_c, ax_all_c = plt.subplots(figsize=(14, 8))
    ax_all_c.scatter(dp_c_sample['Cycle'], dp_c_sample['SOH_Energy (%)'],
                  s=0.5, alpha=0.15, color='cornflowerblue', rasterized=True)

    # Calculer les dropouts: cycles ou des cellules meurent
    alive_c = dp_c.groupby(['setup_c', 'Cycle'])['Cell_Name'].nunique().reset_index()
    alive_c['drop'] = alive_c.groupby('setup_c')['Cell_Name'].diff()
    drop_cycles_c = alive_c[alive_c['drop'] < 0]['Cycle'].unique()

    for sn_c in so_c:
        nc_c = sc_c[sn_c]
        sub_c_d = dp_c[dp_c['setup_c'] == sn_c]
        ms_c = sub_c_d.groupby('Cycle')['SOH_Energy (%)'].mean()
        ax_all_c.plot(ms_c.index, ms_c.values, label=f'{sn_c} (n={nc_c})', linewidth=1.5)

    # Lignes verticales aux dropouts
    y_min_c, y_max_c = ax_all_c.get_ylim()
    for dc_c in drop_cycles_c:
        ax_all_c.axvline(x=dc_c, color='gray', linestyle=':', alpha=0.3, linewidth=0.5)

    ax_all_c.axhline(y=80, color='red', linestyle='--', alpha=0.5)
    ax_all_c.set_xlabel('Cycle')
    ax_all_c.set_ylabel('SOH_Energy (%)')
    ax_all_c.set_title('Trajectoire moyenne SOH par setup (donnees nettoyees des cycles lents)')
    ax_all_c.set_xlim(0, 3000)
    ax_all_c.legend(fontsize=8, loc='upper right')
    plt.tight_layout()
    plt.gca()
    return


@app.cell
def _(df_clean_slow, plt):
    col_load_g = 'CAM_Loading (mg/cm\u00b2)'

    cs_g = df_clean_slow.groupby('Cell_Name').agg({
        'Temperature': 'first', 'Chemistry': 'first', col_load_g: 'first',
    }).reset_index()
    cs_g['setup_g'] = (cs_g['Temperature'] + ' | ' + cs_g['Chemistry'] + ' | load=' + cs_g[col_load_g].astype(str))
    sc_g = cs_g['setup_g'].value_counts()
    so_g = sc_g.index.tolist()
    sm_g = cs_g.set_index('Cell_Name')['setup_g'].to_dict()

    dp_g = df_clean_slow.copy()
    dp_g['setup_g'] = dp_g['Cell_Name'].map(sm_g)
    dp_g_sample = dp_g[dp_g['Cycle'] % 20 == 0].copy()

    n_set_g = len(so_g)
    n_cols_g = 4
    n_rows_g = (n_set_g + n_cols_g - 1) // n_cols_g

    fig_grid_g, axs_grid_g = plt.subplots(n_rows_g, n_cols_g, figsize=(20, 4 * n_rows_g))
    axs_grid_g = axs_grid_g.flatten()

    for i_g, sn_g in enumerate(so_g):
        ax_g = axs_grid_g[i_g]
        nc_g = sc_g[sn_g]

        sub_samp_g = dp_g_sample[dp_g_sample['setup_g'] == sn_g]
        ax_g.scatter(sub_samp_g['Cycle'], sub_samp_g['SOH_Energy (%)'],
                   s=0.5, alpha=0.3, color='cornflowerblue', rasterized=True)

        sub_g = dp_g[dp_g['setup_g'] == sn_g]
        ms_g = sub_g.groupby('Cycle')['SOH_Energy (%)'].mean()
        ax_g.plot(ms_g.index, ms_g.values, linewidth=1.5)

        # Lignes de dropout pour ce setup
        alive_g = sub_g.groupby('Cycle')['Cell_Name'].nunique()
        drops_g = alive_g[alive_g.diff() < 0]
        for dc_g in drops_g.index:
            ax_g.axvline(x=dc_g, color='gray', linestyle=':', alpha=0.3, linewidth=0.5)

        ax_g.axhline(y=80, color='red', linestyle='--', alpha=0.4)
        ax_g.set_title(f'{sn_g}\n(n={nc_g})', fontsize=9)
        ax_g.set_xlabel('Cycle', fontsize=7)
        ax_g.set_ylabel('SOH (%)', fontsize=7)
        ax_g.set_xlim(0, 3000)
        ax_g.tick_params(labelsize=7)

    for j_g in range(i_g + 1, len(axs_grid_g)):
        axs_grid_g[j_g].set_visible(False)

    plt.tight_layout()
    plt.gca()
    return


@app.cell
def _(mo):
    mo.md("""
    ## 5. Trajectoires par setup + C-rate (donnees `df_clean_all`)

    Filtres appliques a `df_clean_all` :
    - Cycle 0 supprime (SOH=0 par definition)
    - Dernier cycle de chaque batterie supprime (artefact fin de test)
    - SOH < 1% supprime (artefact de decharge totale en fin de test)
    - SOH > 130% supprime (artefact de mesure, ex SOH=458%)
    - Cycles lents (Avg_Charge_Current < median/6) supprimes
    - DCIR (Avg_Charge_Current < median/3) supprimes

    Soit 93,138 lignes conservees sur 95,467 (-2.4%).
    """)
    return


@app.cell
def _(df_clean_all, plt):
    col_l_5 = 'CAM_Loading (mg/cm\u00b2)'

    cs_5 = df_clean_all.groupby('Cell_Name').agg({
        'Temperature': 'first', 'Chemistry': 'first', col_l_5: 'first', 'C-rate': 'first',
    }).reset_index()
    cs_5['setup_5'] = (cs_5['Temperature'] + ' | ' + cs_5['Chemistry'] + ' | load=' +
                       cs_5[col_l_5].astype(str) + ' | ' + cs_5['C-rate'])
    sc_5 = cs_5['setup_5'].value_counts()
    so_5 = sc_5.index.tolist()
    sm_5 = cs_5.set_index('Cell_Name')['setup_5'].to_dict()

    dp_5 = df_clean_all.copy()
    dp_5['setup_5'] = dp_5['Cell_Name'].map(sm_5)
    dp_5_samp = dp_5[dp_5['Cycle'] % 20 == 0].copy()

    alive_5 = dp_5.groupby(['setup_5', 'Cycle'])['Cell_Name'].nunique().reset_index()
    alive_5['drop_5'] = alive_5.groupby('setup_5')['Cell_Name'].diff()
    drop_cycles_5 = alive_5[alive_5['drop_5'] < 0]['Cycle'].unique()

    fig_5, ax_5 = plt.subplots(figsize=(14, 8))
    ax_5.scatter(dp_5_samp['Cycle'], dp_5_samp['SOH_Energy (%)'],
                  s=0.5, alpha=0.15, color='cornflowerblue', rasterized=True)

    for sn_5 in so_5:
        nc_5 = sc_5[sn_5]
        sub_5 = dp_5[dp_5['setup_5'] == sn_5]
        ms_5 = sub_5.groupby('Cycle')['SOH_Energy (%)'].mean()
        ax_5.plot(ms_5.index, ms_5.values, label=f'{sn_5} (n={nc_5})', linewidth=1.5)

    for dc_5 in drop_cycles_5:
        ax_5.axvline(x=dc_5, color='gray', linestyle=':', alpha=0.3, linewidth=0.5)

    ax_5.axhline(y=80, color='red', linestyle='--', alpha=0.5)
    ax_5.set_xlabel('Cycle')
    ax_5.set_ylabel('SOH_Energy (%)')
    ax_5.set_title('Trajectoire moyenne SOH par setup + C-rate (donnees sans anomalies)')
    ax_5.set_xlim(0, 3000)
    ax_5.legend(fontsize=7, loc='upper right')
    plt.tight_layout()
    plt.gca()
    return


@app.cell
def _(df_clean_all, plt):
    col_l_g = 'CAM_Loading (mg/cm\u00b2)'

    cs_g2 = df_clean_all.groupby('Cell_Name').agg({
        'Temperature': 'first', 'Chemistry': 'first', col_l_g: 'first', 'C-rate': 'first',
    }).reset_index()
    cs_g2['setup_g2'] = (cs_g2['Temperature'] + ' | ' + cs_g2['Chemistry'] + ' | load=' +
                         cs_g2[col_l_g].astype(str) + ' | ' + cs_g2['C-rate'])
    sc_g2 = cs_g2['setup_g2'].value_counts()
    so_g2 = sc_g2.index.tolist()
    sm_g2 = cs_g2.set_index('Cell_Name')['setup_g2'].to_dict()

    dp_g2 = df_clean_all.copy()
    dp_g2['setup_g2'] = dp_g2['Cell_Name'].map(sm_g2)
    dp_g2_samp = dp_g2[dp_g2['Cycle'] % 20 == 0].copy()

    n_set_g2 = len(so_g2)
    n_cols_g2 = 4
    n_rows_g2 = (n_set_g2 + n_cols_g2 - 1) // n_cols_g2

    fig_g2, axs_g2 = plt.subplots(n_rows_g2, n_cols_g2, figsize=(20, 4 * n_rows_g2))
    axs_g2 = axs_g2.flatten()

    for i_g2, sn_g2 in enumerate(so_g2):
        ax_g2 = axs_g2[i_g2]
        nc_g2 = sc_g2[sn_g2]

        sub_samp_g2 = dp_g2_samp[dp_g2_samp['setup_g2'] == sn_g2]
        ax_g2.scatter(sub_samp_g2['Cycle'], sub_samp_g2['SOH_Energy (%)'],
                     s=0.5, alpha=0.3, color='cornflowerblue', rasterized=True)

        sub_g2 = dp_g2[dp_g2['setup_g2'] == sn_g2]
        ms_g2 = sub_g2.groupby('Cycle')['SOH_Energy (%)'].mean()
        ax_g2.plot(ms_g2.index, ms_g2.values, linewidth=1.5)

        alive_g2 = sub_g2.groupby('Cycle')['Cell_Name'].nunique()
        drops_g2 = alive_g2[alive_g2.diff() < 0]
        for dc_g2 in drops_g2.index:
            ax_g2.axvline(x=dc_g2, color='gray', linestyle=':', alpha=0.3, linewidth=0.5)

        ax_g2.axhline(y=80, color='red', linestyle='--', alpha=0.4)
        ax_g2.set_title(f'{sn_g2}\n(n={nc_g2})', fontsize=8)
        ax_g2.set_xlabel('Cycle', fontsize=7)
        ax_g2.set_ylabel('SOH (%)', fontsize=7)
        ax_g2.set_xlim(0, 3000)
        ax_g2.tick_params(labelsize=7)

    for j_g2 in range(i_g2 + 1, len(axs_g2)):
        axs_g2[j_g2].set_visible(False)

    plt.tight_layout()
    plt.gca()
    return


if __name__ == "__main__":
    app.run()
