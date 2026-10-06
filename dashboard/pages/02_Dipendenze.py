"""Dipendenze — Matrice ID fisico × concentrazione commerciale."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sources import (
    DATA_SOURCE_LABELS,
    DATA_YEARS,
    RISK_LABELS,
    cell,
    conc_label,
    load_energy_vs_trade,
    load_resource_dependency,
    product_label,
    resource_label,
    risk_label,
    year_slice,
)

st.title("🌐 Dipendenze")
st.caption(
    "Dove si incrociano **quanto importiamo** (dipendenza fisica) e **da chi compriamo** "
    "(concentrazione fornitura). Spesso i due lati non sono disponibili insieme."
)

year = st.selectbox("Anno dati", DATA_YEARS, index=len(DATA_YEARS) - 1)
rd = year_slice(load_resource_dependency(), year)
evt = year_slice(load_energy_vs_trade(), year)

if rd.empty:
    st.warning(f"Nessun dato compose per l'anno {year}.")
    st.stop()

sources_available = sorted(rd["data_source"].dropna().unique().tolist()) if "data_source" in rd.columns else []
selected_sources = st.multiselect(
    "Copertura dati",
    options=sources_available,
    default=sources_available,
    format_func=lambda s: DATA_SOURCE_LABELS.get(s, s),
)

filtered = rd.copy()
if selected_sources and "data_source" in filtered.columns:
    filtered = filtered[filtered["data_source"].isin(selected_sources)]

# ── Scatter con lati parziali ─────────────────────────────────────────────────
st.subheader("Dipendenza fisica vs concentrazione fornitori")
st.caption(
    "In alto a destra = peggio (import alti + pochi fornitori). "
    "I punti mancanti non sono un bug: quel lato del dato non esiste per quella risorsa."
)

both = filtered[filtered["physical_id_pct"].notna() & filtered["hhi"].notna()].copy()
only_phys = filtered[filtered["physical_id_pct"].notna() & filtered["hhi"].isna()].copy()
only_trade = filtered[filtered["physical_id_pct"].isna() & filtered["hhi"].notna()].copy()

if both.empty and only_phys.empty and only_trade.empty:
    st.info("Nessuna risorsa con metriche per i filtri selezionati.")
else:
    fig = go.Figure()
    y_max = 10500.0

    if not only_phys.empty:
        part = only_phys.copy()
        part["risorsa"] = part["resource"].map(resource_label)
        fig.add_trace(
            go.Scatter(
                x=part["physical_id_pct"],
                y=[0] * len(part),
                mode="markers+text",
                name="Solo dipendenza fisica",
                text=part["risorsa"],
                textposition="top center",
                marker={"size": 11, "color": "#6b7280", "symbol": "diamond"},
                hovertemplate="%{text}<br>ID% %{x:.1f}<br>HHI: n/d<extra></extra>",
            )
        )

    if not only_trade.empty:
        part = only_trade.copy()
        part["risorsa"] = part["resource"].map(resource_label)
        y_max = max(y_max, float(part["hhi"].max()) * 1.15)
        fig.add_trace(
            go.Scatter(
                x=[0] * len(part),
                y=part["hhi"],
                mode="markers+text",
                name="Solo HHI commerciale",
                text=part["risorsa"],
                textposition="middle right",
                marker={"size": 11, "color": "#2563eb", "symbol": "square"},
                hovertemplate="%{text}<br>ID%: n/d<br>HHI %{y:,.0f}<extra></extra>",
            )
        )

    if not both.empty:
        part = both.copy()
        part["risorsa"] = part["resource"].map(resource_label)
        y_max = max(y_max, float(part["hhi"].max()) * 1.15)
        fig.add_trace(
            go.Scatter(
                x=part["physical_id_pct"],
                y=part["hhi"],
                mode="markers+text",
                name="Entrambi i lati",
                text=part["risorsa"],
                textposition="top center",
                marker={"size": 14, "color": "#d97706"},
                hovertemplate="%{text}<br>ID% %{x:.1f}<br>HHI %{y:,.0f}<extra></extra>",
            )
        )

    fig.add_hline(y=2500, line_dash="dash", line_color="#9ca3af", annotation_text="HHI 2500")
    fig.add_vline(x=90, line_dash="dot", line_color="#9ca3af", annotation_text="ID% 90")
    fig.update_layout(
        height=480,
        margin={"t": 30, "b": 40},
        xaxis_title="Dipendenza fisica % (asse 0 = solo HHI, senza ID%)",
        yaxis_title="HHI fornitori (asse 0 = solo ID%, senza HHI)",
        legend_title="Tipo di dato",
        xaxis={"range": [-8, 125]},
        yaxis={"range": [-400, y_max]},
    )
    st.plotly_chart(fig, width="stretch")

    c1, c2, c3 = st.columns(3)
    c1.metric("Entrambi i lati", len(both))
    c2.metric("Solo fisica", len(only_phys))
    c3.metric("Solo commercio", len(only_trade))

# ── Tabella compose ───────────────────────────────────────────────────────────
st.subheader("Matrice risorse")
st.caption("`—` = metrica non disponibile per quel tipo di risorsa (non zero).")

show = filtered.copy()
show["risorsa"] = show["resource"].map(resource_label)
show["copertura"] = show["data_source"].map(DATA_SOURCE_LABELS) if "data_source" in show.columns else "—"
show["conc"] = show["concentration_level"].map(conc_label) if "concentration_level" in show.columns else "—"

numeric_sort = show.sort_values(
    by=[c for c in ["hhi", "physical_id_pct", "total_import_value_usd"] if c in show.columns],
    ascending=False,
)

display = pd.DataFrame(
    {
        "Risorsa": numeric_sort["risorsa"],
        "ID% fisico": [cell(v, kind="pct") for v in numeric_sort.get("physical_id_pct", pd.Series(dtype=float))],
        "Quota domestica %": [cell(v, kind="pct") for v in numeric_sort.get("domestic_share_pct", pd.Series(dtype=float))],
        "Import USD": [cell(v, kind="usd") for v in numeric_sort.get("total_import_value_usd", pd.Series(dtype=float))],
        "HHI": [cell(v, kind="int") for v in numeric_sort.get("hhi", pd.Series(dtype=float))],
        "Conc.": numeric_sort["conc"],
        "Top fornitore": [cell(v) for v in numeric_sort.get("top1_supplier", pd.Series(dtype=object))],
        "Top-1 %": [cell(v, kind="pct") for v in numeric_sort.get("top1_share_pct", pd.Series(dtype=float))],
        "Top-3 %": [cell(v, kind="pct") for v in numeric_sort.get("top3_share_pct", pd.Series(dtype=float))],
        "N. fornitori": [cell(v, kind="int") for v in numeric_sort.get("num_suppliers", pd.Series(dtype=float))],
        "Copertura dati": numeric_sort["copertura"],
        "Qualità": [cell(v) for v in numeric_sort.get("data_quality", pd.Series(dtype=object))],
    }
)
st.dataframe(display, width="stretch", hide_index=True)

# ── Risk profile ──────────────────────────────────────────────────────────────
st.subheader("Risk profile (bilancio energetico)")
st.caption(
    "Combinazione di dipendenza fisica e HHI. "
    "Se manca l'HHI il profilo dice «HHI non disponibile» — non «basso rischio»."
)
if evt.empty:
    st.info(f"Nessun prodotto con bilancio energetico per {year}.")
else:
    evt = evt.copy()
    evt["risorsa"] = evt["resource"].map(resource_label)
    evt["profilo"] = evt["risk_profile"].map(risk_label)
    risk_display = pd.DataFrame(
        {
            "Risorsa": evt["risorsa"],
            "Prodotto": [product_label(v) for v in evt.get("product_label", pd.Series(dtype=object))],
            "ID% fisico": [cell(v, kind="pct") for v in evt.get("physical_id_pct", pd.Series(dtype=float))],
            "HHI commerciale": [cell(v, kind="int") for v in evt.get("trade_hhi", pd.Series(dtype=float))],
            "Top fornitore": [cell(v) for v in evt.get("top1_supplier", pd.Series(dtype=object))],
            "Top-1 %": [cell(v, kind="pct") for v in evt.get("top1_share_pct", pd.Series(dtype=float))],
            "N. fornitori": [cell(v, kind="int") for v in evt.get("num_suppliers", pd.Series(dtype=float))],
            "Profilo": evt["profilo"],
        }
    )
    st.dataframe(risk_display, width="stretch", hide_index=True)
    with st.expander("Legenda profili", expanded=False):
        for key, label in RISK_LABELS.items():
            st.markdown(f"- `{key}` → {label}")

# ── Trend HHI ─────────────────────────────────────────────────────────────────
st.subheader("Evoluzione HHI per risorsa (2020–2024)")
full_rd = load_resource_dependency()
if full_rd.empty or full_rd["hhi"].dropna().empty:
    st.info("Nessuna serie HHI disponibile.")
else:
    trend = full_rd[full_rd["hhi"].notna()][["year", "resource", "hhi"]].copy()
    top_resources = (
        trend[trend["year"] == year]
        .sort_values("hhi", ascending=False)["resource"]
        .head(8)
        .tolist()
    )
    if not top_resources:
        top_resources = trend.sort_values("hhi", ascending=False)["resource"].head(8).tolist()
    trend = trend[trend["resource"].isin(top_resources)]
    fig2 = go.Figure()
    for res in top_resources:
        part = trend[trend["resource"] == res].sort_values("year")
        if part.empty:
            continue
        fig2.add_trace(
            go.Scatter(
                x=part["year"],
                y=part["hhi"],
                mode="lines+markers",
                name=resource_label(res),
                hovertemplate="%{y:,.0f}<extra>%{fullData.name}</extra>",
            )
        )
    fig2.add_hline(y=2500, line_dash="dash", line_color="#9ca3af", annotation_text="HHI 2500")
    fig2.update_layout(
        height=400,
        margin={"t": 20, "b": 40},
        xaxis={"dtick": 1},
        yaxis_title="HHI",
        legend_title="Risorsa",
        hovermode="x unified",
    )
    st.plotly_chart(fig2, width="stretch")
    st.caption(
        "Esempio di lettura: il litio sale verso ~9k nel 2024 = dipendenza da un fornitore "
        "quasi unico (Germania). Il gas scende nel 2022 (diversificazione di crisi) e poi risale."
    )

st.caption(f"Compose `resource_dependency_compose` · anno toolkit 2026 · anno dati {year}")
