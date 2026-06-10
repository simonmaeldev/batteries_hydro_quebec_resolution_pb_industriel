# /// script
# dependencies = [
#     "marimo",
#     "pandas",
#     "numpy",
#     "matplotlib",
# ]
# requires-python = ">=3.11"
# ///

import marimo

__generated_with = "0.23.9"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import warnings
    warnings.filterwarnings("ignore")
    return mo, np, pd, plt, warnings


@app.cell
def _(mo):
    mo.md(
        "# Plots par batterie - Analyse detaillee\n\n"
        "Navigation: grille SOH, recherche batterie, analyse multi-metrique avec delta cycle-a-cycle.\n\n"
        "**Filtres appliques**: cycle 0 supprime, SOH hors [1,130] supprime, dernier cycle supprime, cycles lents retires."
    )
    return


@app.cell
def _(pd):
    def flag_cycles(grp):
        grp_sorted = grp.sort_values("Cycle")
        med_cur = grp_sorted["Avg_Charge_Current (A)"].median()
        grp_sorted["is_slow"] = grp_sorted["Avg_Charge_Current (A)"] < med_cur / 6
        grp_sorted["is_anomaly"] = grp_sorted["Avg_Charge_Current (A)"] < med_cur / 3
        last_cycle = grp_sorted["Cycle"].max()
        grp_sorted["is_last"] = grp_sorted["Cycle"] == last_cycle
        return grp_sorted

    df_raw = pd.read_csv("all_batteries_combined.csv")
    df_f = df_raw.groupby("Cell_Name", group_keys=False).apply(flag_cycles)
    df_f = df_f[df_f["Cycle"] > 0]
    df_f = df_f[df_f["SOH_Energy (%)"].between(1, 130)]
    df_clean = df_f[~(df_f["is_slow"] | df_f["is_last"])].drop(
        columns=["is_slow", "is_anomaly", "is_last"]
    )

    cell_info = (
        df_clean.groupby("Cell_Name")
        .agg(
            Chemistry=("Chemistry", "first"),
            Temperature=("Temperature", "first"),
            CAM_Loading=("CAM_Loading (mg/cm\u00b2)", "first"),
            C_rate=("C-rate", "first"),
        )
        .reset_index()
    )
    cell_info.columns = ["Cell_Name", "Chemistry", "Temperature", "CAM_Loading", "C-rate"]

    chem_order = {"A": 0, "B": 1, "C": 2}
    temp_order = {"25C": 0, "45C": 1, "60C": 2}
    cell_info["sort_key"] = cell_info.apply(
        lambda r: (
            chem_order.get(r.Chemistry, 99),
            temp_order.get(r.Temperature, 99),
            r.CAM_Loading or 0,
            str(r["C-rate"]),
        ),
        axis=1,
    )
    cell_info = cell_info.sort_values("sort_key").reset_index(drop=True)
    battery_names = cell_info["Cell_Name"].tolist()

    print(
        f"Donnees chargees: {len(df_clean):,} lignes, "
        f"{len(battery_names)} batteries, "
        f"{cell_info['Chemistry'].nunique()} chimies, "
        f"{cell_info['Temperature'].nunique()} temperatures, "
        f"{cell_info['C-rate'].nunique()} C-rates"
    )
    return (
        battery_names,
        cell_info,
        chem_order,
        df_clean,
        df_f,
        df_raw,
        flag_cycles,
        temp_order,
    )


@app.cell
def _(cell_info, mo):
    chem_opts = sorted(cell_info["Chemistry"].unique().tolist())
    temp_opts = sorted(cell_info["Temperature"].unique().tolist())
    crate_opts = sorted(cell_info["C-rate"].unique().tolist())

    chem_filter = mo.ui.multiselect(
        options=chem_opts, label="Chemistry", value=chem_opts
    )
    temp_filter = mo.ui.multiselect(
        options=temp_opts, label="Temperature", value=temp_opts
    )
    crate_filter = mo.ui.multiselect(
        options=crate_opts, label="C-rate"
    )

    mo.hstack([chem_filter, temp_filter, crate_filter], gap=2)
    return chem_filter, chem_opts, crate_filter, crate_opts, temp_filter, temp_opts


@app.cell
def _(cell_info, chem_filter, crate_filter, temp_filter):
    filtered = cell_info.copy()
    if chem_filter.value:
        filtered = filtered[filtered["Chemistry"].isin(chem_filter.value)]
    if temp_filter.value:
        filtered = filtered[filtered["Temperature"].isin(temp_filter.value)]
    if crate_filter.value:
        filtered = filtered[filtered["C-rate"].isin(crate_filter.value)]

    n_filtered = len(filtered)
    filtered
    return filtered, n_filtered


@app.cell
def _(mo):
    n_cols_slider = mo.ui.number(start=2, stop=10, value=4, label="Colonnes")
    n_cols_slider
    return (n_cols_slider,)


@app.cell
def _(filtered, mo, n_cols_slider):
    n_cols = n_cols_slider.value
    n_per_page = n_cols * n_cols
    total_pages = max(1, -(-len(filtered) // n_per_page))
    return n_cols, n_per_page, total_pages


@app.cell
def _():
    page_state, set_page = mo.state(1)
    return page_state, set_page


@app.cell
def _(page_state, set_page, total_pages):
    if page_state() > total_pages:
        set_page(total_pages)


@app.cell
def _(filtered, mo, n_cols, n_per_page, page_state, set_page, total_pages):
    cur_page = page_state()
    start_idx = (cur_page - 1) * n_per_page
    end_idx = min(start_idx + n_per_page, len(filtered))

    prev_btn = mo.ui.button(
        label="◀ Prev",
        on_click=lambda v: set_page(max(1, cur_page - 1)),
        disabled=cur_page <= 1,
    )
    next_btn = mo.ui.button(
        label="Next ▶",
        on_click=lambda v: set_page(min(total_pages, cur_page + 1)),
        disabled=cur_page >= total_pages,
    )

    mo.hstack([prev_btn, mo.md(f"Page {cur_page}/{total_pages}"), next_btn], gap=1)
    return end_idx, start_idx


@app.cell
def _(mo):
    mo.md("## Grille SOH par batterie")


@app.cell
def _(df_clean, end_idx, filtered, mo, n_cols, n_per_page, plt, start_idx):
    if end_idx <= start_idx:
        mo.stop("Aucune batterie a afficher.")

    page_cells = filtered.iloc[start_idx:end_idx]["Cell_Name"].tolist()
    n_items = len(page_cells)
    n_rows = max(1, -(-n_items // n_cols))

    fig_grid, axs_grid = plt.subplots(
        n_rows, n_cols, figsize=(3.5 * n_cols, 2.5 * n_rows), squeeze=False
    )

    for idx, cell_name in enumerate(page_cells):
        row_idx = idx // n_cols
        col_idx = idx % n_cols
        _ax = axs_grid[row_idx][col_idx]

        sub = df_clean[df_clean["Cell_Name"] == cell_name].sort_values("Cycle")
        _ax.plot(sub["Cycle"], sub["SOH_Energy (%)"], linewidth=0.8, color="steelblue")
        _ax.axhline(y=80, color="red", linestyle="--", alpha=0.4, linewidth=0.5)
        _ax.set_title(cell_name, fontsize=7)
        _ax.set_xlabel("Cycle", fontsize=6)
        _ax.set_ylabel("SOH (%)", fontsize=6)
        _ax.tick_params(labelsize=5)
        _ax.set_xlim(0, sub["Cycle"].max() + 10)

    # Masquer les axes vides
    for idx in range(n_items, n_rows * n_cols):
        row_idx = idx // n_cols
        col_idx = idx % n_cols
        axs_grid[row_idx][col_idx].set_visible(False)

    plt.tight_layout()
    plt.gca()
    return axs_grid, cell_name, col_idx, fig_grid, n_items, n_rows, page_cells, row_idx, sub


@app.cell
def _(end_idx, filtered, mo, n_cols, n_per_page, start_idx, total_pages):
    _cur_page = start_idx // n_per_page + 1

    info = (
        mo.md(
            f"**Page {_cur_page}/{total_pages}** - batteries "
            f"{start_idx + 1}-{end_idx} sur {len(filtered)}"
        )
        if total_pages > 1
        else mo.md(f"**{len(filtered)} batteries** affichees sur {n_cols} colonnes")
    )
    info


@app.cell
def _(mo):
    mo.md("## Recherche et analyse detaillee")


@app.cell
def _(battery_names, mo):
    search = mo.ui.text(
        label="Rechercher une batterie",
        placeholder="Tapez le nom de la batterie...",
    )
    search
    return (search,)


@app.cell
def _(battery_names, search):
    _txt = search.value.strip()
    if _txt:
        suggestions = [
            n for n in battery_names if _txt.lower() in n.lower()
        ]
    else:
        suggestions = []
    return suggestions, _txt


@app.cell
def _():
    # State for the selected battery
    sel_state, set_sel = mo.state(None)
    return sel_state, set_sel


@app.cell
def _(mo, search, set_sel, suggestions):
    _txt = search.value.strip()

    if not _txt or not suggestions:
        result = mo.md("Tapez un nom de batterie pour voir les suggestions.")
    else:
        pills = [
            mo.ui.button(
                label=f"  {name}  ",
                value=name,
                on_click=lambda v, n=name: set_sel(n),
                kind="neutral",
            )
            for name in suggestions
        ]
        result = mo.hstack(pills, wrap=True, gap=0.5)
    result
    return


@app.cell
def _(mo, sel_state):
    sel = sel_state()
    _ = mo.md(f"## Analyse : {sel}") if sel else mo.md("Aucune batterie selectionnee.")
    return (sel,)


@app.cell
def _(df_clean, mo, plt, sel):
    if sel is None:
        mo.stop("Selectionnez une batterie ci-dessus.")

    df_batt = df_clean[df_clean["Cell_Name"] == sel].sort_values("Cycle").copy()
    if len(df_batt) == 0:
        mo.stop(f"Aucune donnee pour {sel}.")

    metrics = {
        "SOH_Energy (%)": ("SOH", "%"),
        "Polarization (Ohm cm\u00b2)": ("Polarization", "\u03a9\u00b7cm\u00b2"),
        "Avg_Charge_Current (A)": ("Courant charge", "A"),
        "Avg_Discharge_Voltage (V)": ("Tension decharge", "V"),
        "Avg_Charge_Voltage (V)": ("Tension charge", "V"),
    }

    fig, axs = plt.subplots(5, 1, figsize=(14, 12), sharex=True)

    for i, (col, (label, unit)) in enumerate(metrics.items()):
        _ax = axs[i]
        vals = df_batt[col].values
        cyc = df_batt["Cycle"].values

        color = plt.cm.tab10(i)
        _ax.plot(cyc, vals, color=color, linewidth=1.2, label=label)

        ax2 = _ax.twinx()
        delta_pct = np.full_like(vals, np.nan, dtype=float)
        delta_pct[1:] = (vals[1:] - vals[:-1]) / np.abs(vals[:-1]) * 100
        delta_display = np.clip(delta_pct, -100, 200)
        ax2.plot(
            cyc,
            delta_display,
            color=color,
            linestyle=":",
            linewidth=0.8,
            alpha=0.7,
            label="\u0394%",
        )
        ax2.axhline(y=0, color="gray", linestyle=":", alpha=0.3, linewidth=0.5)
        ax2.set_ylabel("\u0394%", fontsize=8, color="gray")
        ax2.tick_params(labelsize=7, colors="gray")

        _ax.set_ylabel(f"{label}\n({unit})", fontsize=8)
        _ax.tick_params(labelsize=7)
        _ax.legend(fontsize=7, loc="upper left")
        _ax.grid(True, alpha=0.15)

    axs[-1].set_xlabel("Cycle", fontsize=9)
    fig.suptitle(f"{sel}", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.gca()
    return (
        ax2,
        axs,
        color,
        col,
        cyc,
        delta_display,
        delta_pct,
        df_batt,
        fig,
        i,
        label,
        metrics,
        unit,
        vals,
    )


if __name__ == "__main__":
    app.run()
