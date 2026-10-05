"""Panoramica — Quanto dipende l'Italia dall'estero per le risorse strategiche."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from lab_connectors.formatters import fmt_num, fmt_pct
from sources import (
    DATA_YEARS,
    DATA_SOURCE_LABELS,
    cell,
    conc_label,
    fmt_usd,
    load_energy_balance,
    load_resource_dependency,
    product_label,
    resource_label,
    year_slice,
)

st.title("🌐 Italia Dipendenze")
st.caption(
    "Quanto dipende l'Italia dall'estero per gas, metalli critici e altre risorse strategiche: "
    "dipendenza fisica (bilanci energetico) + concentrazione dei fornitori (commercio)."
)

with st.expander("📖 Come leggere questa dashboard", expanded=False):
    st.markdown(
        """
**Due metriche, due domande diverse**

| Metrica | Domanda | Come si legge |
|---|---|---|
| **Dipendenza fisica %** | Quanto importiamo rispetto a quanto consumiamo? | >90% = quasi tutto dall'estero. >100% = si attinge anche alle scorte. |
| **HHI (Herfindahl)** | Da quanti paesi compriamo? | ~10.000 = un solo fornitore. >2.500 = concentrazione alta (zona rischio). 1.500–2.500 = media. <1.500 = diversificato. |
| **Top-1 %** | Quota del primo fornitore | Es. Algeria 48% sul gas = metà dell'import da un paese. |
| **Trade balance** | Export − import | Negativo = siamo net importer (compriamo più di quanto vendiamo). |

**Cosa NON è** un confronto diretto: rame/litio hanno HHI dal commercio ma non un "ID% fisico" Eurostat; carbone/petrolio hanno la dipendenza fisica ma a volte manca l'HHI bilaterale. Nella tabella `copertura dati` vedi quali lati sono presenti.

**Fonti**: Eurostat NRG_BAL_C (fisico, KTOE) · UN Comtrade (valori USD) · FAO (fertilizzanti, contesto).
        """
    )

year = st.selectbox("Anno dati", DATA_YEARS, index=len(DATA_YEARS) - 1)

rd = year_slice(load_resource_dependency(), year)
eb = year_slice(load_energy_balance(), year)

if rd.empty:
    st.warning(f"Nessun dato disponibile per l'anno {year}.")
    st.stop()

# ── KPI ───────────────────────────────────────────────────────────────────────
n_resources = rd["resource"].nunique()
has_trade = rd[rd["total_import_value_usd"].notna()]
import_total = float(has_trade["total_import_value_usd"].sum()) if not has_trade.empty else 0.0
n_high_hhi = int((rd["concentration_level"] == "high").sum()) if "concentration_level" in rd else 0
n_phys_high = int((rd["physical_id_pct"] > 90).sum()) if "physical_id_pct" in rd else 0

gas_row = rd[rd["resource"] == "gas"]
gas_dep = float(gas_row["physical_id_pct"].iloc[0]) if not gas_row.empty and pd.notna(gas_row["physical_id_pct"].iloc[0]) else None
gas_hhi = float(gas_row["hhi"].iloc[0]) if not gas_row.empty and pd.notna(gas_row["hhi"].iloc[0]) else None
gas_top = str(gas_row["top1_supplier"].iloc[0]) if not gas_row.empty and pd.notna(gas_row["top1_supplier"].iloc[0]) else "—"

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Risorse monitorate", fmt_num(n_resources))
with k2:
    st.metric(
        "Import commerciali",
        fmt_usd(import_total),
        help="Somma import delle risorse con dato Comtrade (USD). Non è il totale import Italia.",
    )
with k3:
    st.metric(
        "HHI alto",
        fmt_num(n_high_hhi),
        help="Risorse con concentration_level = high (HHI > 2500): pochi fornitori dominano.",
    )
with k4:
    if gas_dep is not None:
        st.metric(
            "Dipendenza gas",
            fmt_pct(gas_dep, decimals=1),
            help=f"Top fornitore: {gas_top}"
            + (f" · HHI {gas_hhi:,.0f}" if gas_hhi else "")
            + " · % del consumo apparente coperto da import",
        )
    else:
        st.metric("Dipendenza gas", "—")

st.caption(
    f"Oltre {n_phys_high} prodotti energetici con dipendenza import >90% nel {year} · "
    "HHI alto = concentrazione fornitura, non necessariamente volumi grandi."
)

# ── Tabella risorse critiche ──────────────────────────────────────────────────
st.subheader(f"Risorse strategiche — {year}")
st.caption(
    "Ordinamento: prima per HHI (concentrazione), poi per dipendenza fisica. "
    "`—` = metrica non calcolabile per quel tipo di risorsa (non zero)."
)

tbl = rd.copy()
tbl["risorsa"] = tbl["resource"].map(resource_label)
tbl["copertura"] = tbl["data_source"].map(DATA_SOURCE_LABELS) if "data_source" in tbl.columns else "—"
tbl["conc"] = tbl["concentration_level"].map(conc_label) if "concentration_level" in tbl.columns else "—"
tbl = tbl.sort_values(
    by=[c for c in ["hhi", "physical_id_pct", "total_import_value_usd"] if c in tbl.columns],
    ascending=False,
)

view = pd.DataFrame(
    {
        "Risorsa": tbl["risorsa"],
        "Dip. fisica %": [cell(v, kind="pct") for v in tbl.get("physical_id_pct", pd.Series(dtype=float))],
        "Import USD": [cell(v, kind="usd") for v in tbl.get("total_import_value_usd", pd.Series(dtype=float))],
        "HHI": [cell(v, kind="int") for v in tbl.get("hhi", pd.Series(dtype=float))],
        "Concentrazione": tbl["conc"],
        "Top fornitore": [cell(v) for v in tbl.get("top1_supplier", pd.Series(dtype=object))],
        "Top-1 %": [cell(v, kind="pct") for v in tbl.get("top1_share_pct", pd.Series(dtype=float))],
        "Copertura dati": tbl["copertura"],
    }
)
st.dataframe(view, width="stretch", hide_index=True)

# ── Grafico HHI ───────────────────────────────────────────────────────────────
hhi_df = tbl[tbl["hhi"].notna()].sort_values("hhi", ascending=True) if "hhi" in tbl.columns else pd.DataFrame()
if not hhi_df.empty:
    st.subheader("Concentrazione fornitori (HHI)")
    st.caption(
        "Barra più lunga = compri da meno paesi. "
        "Soglia 2500 = concentrazione tipicamente considerata alta. "
        "Il litio è vicino a un solo fornitore (Germania)."
    )
    colors = ["#dc2626" if v >= 5000 else "#d97706" if v > 2500 else "#2563eb" for v in hhi_df["hhi"]]
    fig = go.Figure(
        go.Bar(
            x=hhi_df["hhi"],
            y=hhi_df["risorsa"],
            orientation="h",
            marker_color=colors,
            hovertemplate="%{y}<br>HHI %{x:,.0f}<extra></extra>",
        ),
    )
    fig.add_vline(x=2500, line_dash="dash", line_color="#9ca3af", annotation_text="HHI 2500")
    fig.update_layout(
        height=420,
        margin={"t": 20, "b": 40, "l": 140},
        xaxis_title="HHI",
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch")

# ── Dipendenza fisica (energia) ───────────────────────────────────────────────
dep = eb[eb["gross_import_dependency_pct"].notna()].copy() if not eb.empty else pd.DataFrame()
if not dep.empty:
    st.subheader("Dipendenza import energetica")
    st.caption(
        "Quota del consumo apparente coperta da import. "
        ">100% = import + attingimento scorte. Rinnovabili/resto domestico in basso."
    )
    dep = dep.sort_values("gross_import_dependency_pct", ascending=False)
    top_dep = dep.head(12).copy()
    top_dep["label_it"] = top_dep["product_label"].map(product_label)
    fig2 = go.Figure(
        go.Bar(
            x=top_dep["gross_import_dependency_pct"],
            y=top_dep["label_it"],
            orientation="h",
            marker_color="#059669",
            hovertemplate="%{y}<br>%{x:.1f}%<extra></extra>",
        ),
    )
    fig2.add_vline(x=100, line_dash="dash", line_color="#9ca3af", annotation_text="100%")
    fig2.update_layout(
        height=420,
        margin={"t": 20, "b": 40, "l": 220},
        xaxis_title="Gross import dependency %",
        showlegend=False,
    )
    st.plotly_chart(fig2, width="stretch")

# ── Story in una riga ─────────────────────────────────────────────────────────
st.subheader("In sintesi")
bullets = []
if gas_dep is not None:
    bullets.append(
        f"- **Gas**: {fmt_pct(gas_dep, decimals=1)} di dipendenza import; "
        f"primo fornitore **{gas_top}**"
        + (f" (~{gas_row['top1_share_pct'].iloc[0]:.0f}%)" if not gas_row.empty and pd.notna(gas_row["top1_share_pct"].iloc[0]) else "")
        + "."
    )
oil = eb[eb["product"].str.contains("Oil & petroleum|Crude oil", case=False, na=False)]
if not oil.empty and oil["gross_import_dependency_pct"].notna().any():
    worst = oil.loc[oil["gross_import_dependency_pct"].idxmax()]
    bullets.append(
        f"- **Petrolio/prodotti**: fino al {fmt_pct(worst['gross_import_dependency_pct'], decimals=1)} "
        f"di dipendenza ({product_label(worst['product_label'])})."
    )
ren = eb[eb["product"] == "RA000"]
if not ren.empty and pd.notna(ren["gross_import_dependency_pct"].iloc[0]):
    bullets.append(
        f"- **Rinnovabili totali**: solo {fmt_pct(ren['gross_import_dependency_pct'].iloc[0], decimals=1)} "
        "di dipendenza — l'unico angolo largamente domestico."
    )
crit = has_trade.nlargest(3, "hhi") if not has_trade.empty else pd.DataFrame()
if not crit.empty:
    names = ", ".join(f"{resource_label(r)} (HHI {h:,.0f})" for r, h in zip(crit["resource"], crit["hhi"]))
    bullets.append(f"- **Concentrazione più alta**: {names}.")
st.markdown("\n".join(bullets) if bullets else "Nessun riepilogo calcolabile.")

with st.expander("Caveat e limiti dei dati", expanded=False):
    st.markdown(
        """
- **Dipendenza fisica (`physical_id_pct`)**: da bilancio energetico Eurostat (gas, carbone, petrolio, rinnovabili…).
  Per metalli critici e risorse solo commerciali non esiste un ID% fisico.
- **HHI / fornitore**: da UN Comtrade (import HS6 per partner). Valori in **USD**, non euro.
- **`copertura dati`**:
  - `Energia + commercio` = entrambi i lati (es. gas);
  - `Solo commercio` = HHI e fornitore, ma non il bilancio fisico (rame, litio, cobalto…);
  - `Solo energia` = dipendenza fisica, spesso senza HHI bilaterale (carbone, rinnovabili).
- **`risk_profile`** (pagina Dipendenze): se manca l'HHI non è "basso rischio" — è "HHI non disponibile".
- **Fertilizzanti**: consumo FAO (tonnellate), non un bilancio di import dependency.
- **Anni dati**: 2020–2024 (fertilizzanti 2018–2023). I parquet pubblicati sono nella cartella toolkit `2026/`.
- **Non è una mappa di rischio geopolitico completa**: non copre ownership, contratti di fornitura, stock strategici o filiere upstream.
        """
    )

st.caption(
    f"Fonti: Eurostat NRG_BAL_C · UN Comtrade · FAO · Anno selezionato: {year} · "
    f"Righe compose: {len(rd)}"
)
