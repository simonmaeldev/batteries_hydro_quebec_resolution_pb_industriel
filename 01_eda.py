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
    from lifelines import KaplanMeierFitter
    warnings.filterwarnings('ignore')
    return KaplanMeierFitter, mo, np, pd, plt, sns


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
    tabs_1 = {c: mo.ui.table(pd.DataFrame({'valeur': df_raw[c].value_counts().index, 'compte': df_raw[c].value_counts().values})) for c in cat_cols_1}
    mo.ui.tabs(tabs_1)
    return


@app.cell
def _(df_raw, np, pd, plt):
    num_cols_1 = [
        'Cycle_Time (h)', 'Avg_Discharge_Voltage (V)', 'Avg_Charge_Voltage (V)',
        'Avg_Charge_Current (A)', 'Discharge_Capacity (mAh)', 'Charge_Capacity (mAh)',
        'Coulomb_Efficiency (%)', 'SOH_Energy (%)', 'Polarization (Ohm cm\u00b2)',
    ]

    # Boxplots par tranche de SOH pour chaque predicteur
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
    ax_soh.fill_between(soh_by_cycle['Cycle'], soh_by_cycle['mean'] - soh_by_cycle['std'], soh_by_cycle['mean'] + soh_by_cycle['std'], alpha=0.2, color='blue')
    ax_soh.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='Seuil 80%')
    ax_soh.axhline(y=50, color='orange', linestyle='--', alpha=0.7, label='Seuil 50%')
    ax_soh.set_xlabel('Cycle')
    ax_soh.set_ylabel('SOH_Energy (%)')
    ax_soh.set_title('Evolution moyenne du SOH par cycle')
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
    **Trajectoires individuelles** : echantillon de 7 cellules par chimie pour voir la variabilite intra-groupe.
    """)
    return


@app.cell
def _(df_raw, plt):
    sample_7 = df_raw.groupby('Chemistry').apply(lambda g: g['Cell_Name'].unique()[:7]).explode().values

    chem_list2 = sorted(df_raw['Chemistry'].unique())
    fig_indiv, axs_indiv = plt.subplots(1, 3, figsize=(18, 5))
    for ax_iv, chem_iv in zip(axs_indiv, chem_list2):
        selected = [c for c in sample_7 if df_raw[df_raw['Cell_Name'] == c]['Chemistry'].iloc[0] == chem_iv]
        for cell_iv in selected:
            d_iv = df_raw[df_raw['Cell_Name'] == cell_iv].sort_values('Cycle')
            ax_iv.plot(d_iv['Cycle'], d_iv['SOH_Energy (%)'], linewidth=0.8, alpha=0.7)
        ax_iv.axhline(y=80, color='red', linestyle='--', alpha=0.5)
        ax_iv.set_title(f'Chemistry {chem_iv}')
        ax_iv.set_xlabel('Cycle')
        ax_iv.set_ylabel('SOH (%)')
        ax_iv.set_xlim(0, 3000)
        ax_iv.set_ylim(0, 120)
    plt.tight_layout()
    plt.gca()
    return


@app.cell
def _(mo):
    mo.md("""
    ## 3. Relations entre predicteurs et SOH
    """)
    return


@app.cell
def _(df_raw, np, num_cols_1, plt, sns):
    corr_cols_3 = num_cols_1 + ['Cycle']
    corr_3 = df_raw[corr_cols_3].replace(0, np.nan).corr()

    fig_corr, ax_corr = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr_3, annot=True, fmt='.2f', cmap='RdBu_r', center=0, square=True, ax=ax_corr, cbar_kws={'shrink': 0.8})
    ax_corr.set_title('Matrice de correlation')
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
    ## 4. Analyse de survie exploratoire (seuil 80%)
    """)
    return


@app.cell
def _(df_raw):
    last_rows_4 = df_raw.loc[df_raw.groupby('Cell_Name')['Cycle'].idxmax()].copy()

    def find_failure_80(grp):
        crossed = grp[grp['SOH_Energy (%)'] < 80]
        if len(crossed) > 0:
            return crossed.iloc[0]['Cycle']
        return None

    fail_80 = df_raw.groupby('Cell_Name').apply(find_failure_80).reset_index()
    fail_80.columns = ['Cell_Name', 'failure_cycle_80']

    surv_4 = last_rows_4[['Cell_Name', 'Completed_cycles', 'Cycles_>_80%_capacity',
                          'Cycles_>_50%_capacity', 'Chemistry', 'Temperature', 'C-rate', 'Project']].copy()
    surv_4 = surv_4.merge(fail_80, on='Cell_Name', how='left')
    surv_4['event_80'] = surv_4['failure_cycle_80'].notna().astype(int)
    surv_4['duration_80'] = surv_4['failure_cycle_80'].fillna(surv_4['Completed_cycles'])

    n_events_4 = surv_4['event_80'].sum()
    n_censored_4 = len(surv_4) - n_events_4
    return n_censored_4, n_events_4, surv_4


@app.cell
def _(mo, n_censored_4, n_events_4):
    mo.md(f"""
    **Survie (80%)** : {n_events_4} evenements, {n_censored_4} censurees, taux d'evenement {n_events_4 / (n_events_4 + n_censored_4) * 100:.0f}%
    """)
    return


@app.cell
def _(mo, surv_4):
    mo.ui.table(surv_4[['Cell_Name', 'Chemistry', 'Temperature', 'C-rate', 'duration_80', 'event_80']].head(20))
    return


@app.cell
def _(mo):
    mo.md("""
    ### Courbes de Kaplan-Meier
    """)
    return


@app.cell
def _(KaplanMeierFitter, plt, surv_4):
    chem_list_km = sorted(surv_4['Chemistry'].unique())
    fig_km1, ax_km1 = plt.subplots(figsize=(10, 6))
    for chem_km in chem_list_km:
        sub_km = surv_4[surv_4['Chemistry'] == chem_km]
        kmf_1 = KaplanMeierFitter()
        kmf_1.fit(sub_km['duration_80'], event_observed=sub_km['event_80'], label=f'Chemistry {chem_km}')
        kmf_1.plot_survival_function(ax=ax_km1, linewidth=2)
    ax_km1.axhline(y=0.5, color='gray', linestyle=':', alpha=0.5)
    ax_km1.set_xlabel('Cycles')
    ax_km1.set_ylabel('Probabilite de survie')
    ax_km1.set_title('Survie par chimie (KM)')
    ax_km1.legend()
    plt.gca()
    return


@app.cell
def _(KaplanMeierFitter, plt, surv_4):
    fig_km2, axs_km2 = plt.subplots(1, 2, figsize=(16, 6))
    for i_km2, (col_km2, title_km2) in enumerate([('Temperature', 'Temperature'), ('C-rate', 'C-rate')]):
        ax_km2 = axs_km2[i_km2]
        for val_km2 in sorted(surv_4[col_km2].unique()):
            sub_km2 = surv_4[surv_4[col_km2] == val_km2]
            if len(sub_km2) > 2:
                kmf_2 = KaplanMeierFitter()
                kmf_2.fit(sub_km2['duration_80'], event_observed=sub_km2['event_80'], label=str(val_km2))
                kmf_2.plot_survival_function(ax=ax_km2, linewidth=2)
        ax_km2.set_xlabel('Cycles')
        ax_km2.set_ylabel('Probabilite de survie')
        ax_km2.set_title(f'Survie par {title_km2}')
        ax_km2.legend()
    plt.tight_layout()
    plt.gca()
    return


@app.cell
def _(mo):
    mo.md("""
    ## 5. Preparation pour la modelisation
    """)
    return


@app.cell
def _(df_raw, np):
    df_clean_5 = df_raw.copy()
    df_clean_5 = df_clean_5[df_clean_5['Cycle'] > 0]
    df_clean_5 = df_clean_5[df_clean_5['SOH_Energy (%)'].between(1, 130)]
    df_clean_5.loc[df_clean_5['Cycle'] == 1, 'Coulomb_Efficiency (%)'] = np.nan
    df_clean_5['log_Polarization'] = np.log(df_clean_5['Polarization (Ohm cm\u00b2)'].replace(0, np.nan))

    print(f"Avant : {len(df_raw)} lignes")
    print(f"Apres : {len(df_clean_5)} lignes")
    print(f"Retirees : {len(df_raw) - len(df_clean_5)}")
    return


@app.cell
def _(mo):
    mo.md("""
    ### Pistes pour la modelisation

    "
          "1. **Prediction precoce (RUL)** : features extraites des N premiers cycles -> modele parametrique (Weibull, Cox).
    "
          "2. **Features candidates** : pente SOH initiale, polarisation, coulomb efficiency, parametres CAM.
    "
          "3. **Explicabilite** : Cox PH (coefficients interpretables) ou Weibull AFT.
    "
          "4. **Alternative** : modeles mixtes sur trajectoire complete de SOH -> temps de passage a 80%.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ### Observations cles

    "
          "| Observation | Impact |
    "
          "|---|---|
    "
          "| Grande variabilite inter-cellules | Effets aleatoires ou features supplementaires |
    "
          "| Chimie A plus stable | Variable cle |
    "
          "| 60C accelere fortement la degradation | Effet non-lineaire |
    "
          "| Polarization augmente avec l'age | Bon indicateur |
    "
          "| Coulomb_Efficiency artefact cycle 1 | A corriger |
    "
          "| SOH > 100% (bruit) | Winsoriser |
    "
          "| 66/157 censurees | Analyse de survie necessaire |
    """)
    return


if __name__ == "__main__":
    app.run()
