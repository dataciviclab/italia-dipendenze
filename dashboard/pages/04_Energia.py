"""Energia — Bilancio fisico Eurostat NRG_BAL_C per prodotto SIEC."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sources import (
    DATA_YEARS,
    fmt_pct,
    load_energy_balance,
    load_fertilizer,
    product_label,
    year_slice,
)

st.title("⚡ Bilancio energetico")
st.caption(
    "Flussi fisici Italia (KTOE) da Eurostat NRG_BAL_C: produzione, import, export, "
    "dipendenza lorda dall'import e quota domestica. "
    "Dipendenza >100% = import + attingimento scorte."
)

year = st.selectbox("Anno dati", DATA_YEARS, index=len(DATA_YEARS) - 1)
eb = year_slice(load_energy_balance(), year)

if eb.empty:
    st.warning(f"Nessun bilancio energetico per {year}.")
    st.stop()

eb = eb.copy()
eb["label_it"] = eb["product_label"].map(product_label)

# ── KPI sistema ───────────────────────────────────────────────────────────────
total_row = eb[eb["product"].isin(["TOTAL", "FE", "FEC"]) | eb["product_label"].str.contains("Total final", case=False, na=False)]
if total_row.empty:
    total_row = eb.nlargest(1, "apparent_consumption_ktoe")

dep_gas = eb[eb["product"] == "G3000"]
k1, k2, k3, k4 = st.columns(4)
with k1:
    if not total_row.empty and pd.notna(total_row["apparent_consumption_ktoe"].iloc[0]):
        k1.metric("Consumo apparente totale", f"{total_row['apparent_consumption_ktoe'].iloc[0]:,.0f} KTOE")
    else:
        k1.metric("Consumo apparente totale", "—")
with k2:
    if not total_row.empty and pd.notna(total_row["gross_import_dependency_pct"].iloc[0]):
        k2.metric("Dipendenza import (totale)", fmt_pct(total_row["gross_import_dependency_pct"].iloc[0]))
    else:
        k2.metric("Dipendenza import (totale)", "—")
with k3:
    if not dep_gas.empty and pd.notna(dep_gas["gross_import_dependency_pct"].iloc[0]):
        k3.metric("Gas — import dep", fmt_pct(dep_gas["gross_import_dependency_pct"].iloc[0]))
    else:
        k3.metric("Gas — import dep", "—")
with k4:
    if not dep_gas.empty and pd.notna(dep_gas["imports_ktoe"].iloc[0]):
        k4.metric("Gas — import", f"{dep_gas['imports_ktoe'].iloc[0]:,.0f} KTOE")
    else:
        k4.metric("Gas — import", "—")

# ── Filtro prodotto ───────────────────────────────────────────────────────────
products = eb.sort_values("label_it")["label_it"].tolist()
default_products = [
    "Gas naturale",
    "Prodotti petroliferi (excl. biofuel)",
    "Petrolio greggio, NGL, feedstock",
    "Carbone e solidi fossili",
    "Rinnovabili e biocarburanti totali",
]
selected = st.multiselect(
    "Prodotti",
    options=products,
    default=[p for p in default_products if p in products],
)
filtered = eb[eb["label_it"].isin(selected)].copy() if selected else eb.copy()

# ── Grafici ───────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.subheader("Dipendenza import %")
    dep = filtered[filtered["gross_import_dependency_pct"].notna()].sort_values("gross_import_dependency_pct", ascending=True)
    if dep.empty:
        st.info("Nessun valore di import dependency per i filtri selezionati.")
    else:
        fig = go.Figure(
            go.Bar(
                x=dep["gross_import_dependency_pct"],
                y=dep["label_it"],
                orientation="h",
                marker_color="#d97706",
                hovertemplate="%{y}<br>%{x:.1f}%<extra></extra>",
            ),
        )
        fig.add_vline(x=100, line_dash="dash", line_color="#6b7280", annotation_text="100%")
        fig.update_layout(
            height=420,
            margin={"t": 20, "b": 40, "l": 220},
            xaxis_title="Gross import dependency %",
            showlegend=False,
        )
        st.plotly_chart(fig, width="stretch")

with c2:
    st.subheader("Quota domestica %")
    dom = filtered[filtered["domestic_share_pct"].notna()].sort_values("domestic_share_pct", ascending=True)
    if dom.empty:
        st.info("Nessun valore di quota domestica.")
    else:
        fig2 = go.Figure(
            go.Bar(
                x=dom["domestic_share_pct"],
                y=dom["label_it"],
                orientation="h",
                marker_color="#059669",
                hovertemplate="%{y}<br>%{x:.1f}%<extra></extra>",
            ),
        )
        fig2.update_layout(
            height=420,
            margin={"t": 20, "b": 40, "l": 220},
            xaxis_title="Domestic share %",
            showlegend=False,
        )
        st.plotly_chart(fig2, width="stretch")

# ── Tabella bilancio ──────────────────────────────────────────────────────────
st.subheader("Tabella bilancio")
show_cols = [
    "label_it",
    "production_ktoe",
    "imports_ktoe",
    "exports_ktoe",
    "apparent_consumption_ktoe",
    "gross_import_dependency_pct",
    "domestic_share_pct",
    "data_quality",
]
view = filtered[[c for c in show_cols if c in filtered.columns]].sort_values(
    "imports_ktoe", ascending=False
)
view = view.rename(columns={"label_it": "Prodotto"})
st.dataframe(view, use_container_width=True, hide_index=True)

# ── Trend dipendenza gas ──────────────────────────────────────────────────────
st.subheader("Trend dipendenza — prodotti chiave")
full = load_energy_balance()
key_products = ["G3000", "O4100_TOT", "C0000X0350-0370", "RA000", "TOTAL"]
trend = full[full["product"].isin(key_products) & full["gross_import_dependency_pct"].notna()]
if trend.empty:
    st.info("Nessuna serie di dipendenza.")
else:
    fig3 = go.Figure()
    labels = {
        "G3000": "Gas naturale",
        "O4100_TOT": "Petrolio greggio",
        "C0000X0350-0370": "Carbone",
        "RA000": "Rinnovabili totali",
        "TOTAL": "Totale",
    }
    for prod in key_products:
        part = trend[trend["product"] == prod].sort_values("year")
        if part.empty:
            continue
        fig3.add_trace(
            go.Scatter(
                x=part["year"],
                y=part["gross_import_dependency_pct"],
                mode="lines+markers",
                name=labels.get(prod, prod),
                hovertemplate="%{y:.1f}%<extra>%{fullData.name}</extra>",
            ),
        )
    fig3.update_layout(
        height=400,
        margin={"t": 20, "b": 40},
        xaxis=dict(dtick=1),
        yaxis_title="Gross import dependency %",
        hovermode="x unified",
        legend_title="Prodotto",
    )
    st.plotly_chart(fig3, width="stretch")

# ── Fertilizzanti (contesto FAO) ──────────────────────────────────────────────
st.subheader("Consumo fertilizzanti (FAO, contesto)")
fert = load_fertilizer()
if fert.empty:
    st.info("Dati fertilizzanti non disponibili.")
else:
    fert = fert.sort_values("year")
    fig4 = go.Figure(
        go.Bar(
            x=fert["year"],
            y=fert["total_consumption_tonnes"],
            marker_color="#6366f1",
            hovertemplate="%{x}<br>%{y:,.0f} t<extra></extra>",
        ),
    )
    fig4.update_layout(
        height=280,
        margin={"t": 20, "b": 40},
        xaxis=dict(dtick=1),
        yaxis_title="Tonnes",
        showlegend=False,
    )
    st.plotly_chart(fig4, width="stretch")
    st.caption("Consumo totale nutrienti — non un bilancio di import dependency. Anni 2018–2023.")

st.caption(f"Eurostat NRG_BAL_C · anno dati {year} · unità volumi KTOE")
