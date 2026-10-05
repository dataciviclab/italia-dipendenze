"""Commercio — Bilaterale, concentrazione e balance per risorsa."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sources import (
    DATA_YEARS,
    TREND_LABELS,
    cell,
    fmt_usd,
    load_trade_balance,
    load_trade_bilateral,
    load_trade_concentration,
    position_label,
    resource_label,
    year_slice,
)

st.title("🚢 Commercio bilaterale")
st.caption(
    "Import/export per risorsa (HS6, Italia reporter 380) — UN Comtrade. Valori in **USD**. "
    "HHI alto = pochi fornitori dominano l'import."
)

# Risorse con dato commerciale
conc_all = load_trade_concentration()
if conc_all.empty:
    st.warning("Mart trade concentration non disponibile.")
    st.stop()

resources = sorted(conc_all["resource"].dropna().unique().tolist())
default_res = "gas" if "gas" in resources else resources[0]

c1, c2 = st.columns([2, 1])
with c1:
    resource = st.selectbox("Risorsa", resources, index=resources.index(default_res), format_func=resource_label)
with c2:
    year = st.selectbox("Anno dati", DATA_YEARS, index=len(DATA_YEARS) - 1)

conc = year_slice(load_trade_concentration(), year)
bal = year_slice(load_trade_balance(), year)
bil = year_slice(load_trade_bilateral(), year)

conc_r = conc[conc["resource"] == resource] if not conc.empty else pd.DataFrame()
bal_r = bal[bal["resource"] == resource] if not bal.empty else pd.DataFrame()
bil_r = bil[(bil["resource"] == resource) & (bil["flow"] == "M")].copy() if not bil.empty else pd.DataFrame()

# ── KPI risorsa ───────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
with k1:
    if not conc_r.empty and pd.notna(conc_r["hhi"].iloc[0]):
        hhi = float(conc_r["hhi"].iloc[0])
        k1.metric("HHI", f"{hhi:,.0f}", help="10000 = fornitore unico")
    else:
        k1.metric("HHI", "—")
with k2:
    if not conc_r.empty and pd.notna(conc_r["top1_supplier"].iloc[0]):
        k2.metric(
            "Top fornitore",
            str(conc_r["top1_supplier"].iloc[0]),
            help=f"Quota {conc_r['top1_share_pct'].iloc[0]:.1f}%" if pd.notna(conc_r["top1_share_pct"].iloc[0]) else None,
        )
    else:
        k2.metric("Top fornitore", "—")
with k3:
    if not bal_r.empty and pd.notna(bal_r["balance_usd"].iloc[0]):
        bal_v = float(bal_r["balance_usd"].iloc[0])
        k3.metric(
            "Trade balance",
            fmt_usd(bal_v),
            delta=position_label(bal_r["trade_position"].iloc[0]) if not bal_r.empty and "trade_position" in bal_r else ("net exporter" if bal_v > 0 else "net importer"),
            delta_color="normal" if bal_v > 0 else "inverse",
            help="Export − import. Negativo = compriamo più di quanto vendiamo di questa risorsa.",
        )
    else:
        k3.metric("Trade balance", "—")
with k4:
    if not conc_r.empty and pd.notna(conc_r["total_import_value_usd"].iloc[0]):
        k4.metric("Import", fmt_usd(float(conc_r["total_import_value_usd"].iloc[0])))
    else:
        k4.metric("Import", "—")

# ── Top partner import ────────────────────────────────────────────────────────
st.subheader(f"Top fornitori — {resource_label(resource)} ({year})")
if bil_r.empty:
    st.info("Nessun record bilaterale per questa risorsa/anno.")
else:
    partners = (
        bil_r.groupby("partner_name", as_index=False)["primary_value_usd"]
        .sum()
        .sort_values("primary_value_usd", ascending=False)
        .head(12)
    )
    fig = go.Figure(
        go.Bar(
            x=partners["primary_value_usd"],
            y=partners["partner_name"],
            orientation="h",
            marker_color="#2563eb",
            hovertemplate="%{y}<br>%{x:$,.0f}<extra></extra>",
        ),
    )
    fig.update_layout(
        height=420,
        margin={"t": 10, "b": 40, "l": 180},
        xaxis_title="Import USD",
        yaxis={"autorange": "reversed"},
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch")

    st.dataframe(
        partners.rename(columns={"partner_name": "Fornitore", "primary_value_usd": "Import USD"}),
        width="stretch",
        hide_index=True,
        column_config={"Import USD": st.column_config.NumberColumn(format="$ %.0f")},
    )

# ── Serie HHI + top1 share ────────────────────────────────────────────────────
st.subheader("Concentrazione nel tempo")
series = conc_all[conc_all["resource"] == resource].sort_values("year") if not conc_all.empty else pd.DataFrame()
if series.empty:
    st.info("Nessuna serie di concentrazione.")
else:
    left, right = st.columns(2)
    with left:
        fig2 = go.Figure()
        fig2.add_trace(
            go.Scatter(
                x=series["year"],
                y=series["hhi"],
                mode="lines+markers",
                name="HHI",
                line={"color": "#d97706", "width": 3},
                hovertemplate="%{y:,.0f}<extra>HHI</extra>",
            ),
        )
        fig2.add_hline(y=2500, line_dash="dash", line_color="#6b7280", annotation_text="2500")
        fig2.update_layout(
            height=320,
            margin={"t": 20, "b": 40},
            xaxis=dict(dtick=1),
            yaxis_title="HHI",
            showlegend=False,
        )
        st.plotly_chart(fig2, width="stretch")
    with right:
        fig3 = go.Figure()
        fig3.add_trace(
            go.Scatter(
                x=series["year"],
                y=series["top1_share_pct"],
                mode="lines+markers",
                name="Top-1 %",
                line={"color": "#2563eb", "width": 3},
                hovertemplate="%{y:.1f}%<extra>Top-1</extra>",
            ),
        )
        fig3.add_trace(
            go.Scatter(
                x=series["year"],
                y=series["top3_share_pct"],
                mode="lines+markers",
                name="Top-3 %",
                line={"color": "#059669", "width": 2, "dash": "dot"},
                hovertemplate="%{y:.1f}%<extra>Top-3</extra>",
            ),
        )
        fig3.update_layout(
            height=320,
            margin={"t": 20, "b": 40},
            xaxis=dict(dtick=1),
            yaxis_title="Quota import %",
            legend_title="Share",
        )
        st.plotly_chart(fig3, width="stretch")

    if not series.empty and "trend_status" in series.columns and pd.notna(series["trend_status"].iloc[-1]):
        st.caption(
            f"Trend {year}: {TREND_LABELS.get(str(series['trend_status'].iloc[-1]), series['trend_status'].iloc[-1])} · "
            f"ΔHHI YoY: {series['hhi_change'].iloc[-1]:+,.0f}" if pd.notna(series.get("hhi_change", pd.Series([pd.NA])).iloc[-1])
            else f"Trend {year}: {TREND_LABELS.get(str(series['trend_status'].iloc[-1]), series['trend_status'].iloc[-1])}"
        )

# ── Balance multi-risorsa ─────────────────────────────────────────────────────
st.subheader(f"Balance commerciale — tutte le risorse ({year})")
st.caption(
    "Export − import. Arancione/verde: a destra del zero = net exporter. "
    "Il gas da solo domina il deficit commerciale delle risorse monitorate."
)
if bal.empty:
    st.info("Nessun trade balance per l'anno selezionato.")
else:
    bal_view = bal.sort_values("balance_usd")
    fig4 = go.Figure(
        go.Bar(
            x=bal_view["balance_usd"],
            y=bal_view["resource"].map(resource_label),
            orientation="h",
            marker_color=["#059669" if v >= 0 else "#d97706" for v in bal_view["balance_usd"]],
            hovertemplate="%{y}<br>%{x:$,.0f}<extra></extra>",
        ),
    )
    fig4.update_layout(
        height=420,
        margin={"t": 10, "b": 40, "l": 140},
        xaxis_title="Balance USD (export − import)",
        showlegend=False,
    )
    st.plotly_chart(fig4, width="stretch")

    bal_tbl = bal.sort_values("balance_usd").copy()
    bal_tbl["risorsa"] = bal_tbl["resource"].map(resource_label)
    bal_display = pd.DataFrame(
        {
            "Risorsa": bal_tbl["risorsa"],
            "Import USD": [cell(v, kind="usd") for v in bal_tbl["import_value_usd"]],
            "Export USD": [cell(v, kind="usd") for v in bal_tbl["export_value_usd"]],
            "Balance USD": [cell(v, kind="usd") for v in bal_tbl["balance_usd"]],
            "Posizione": [position_label(v) for v in bal_tbl["trade_position"]],
            "Export coverage %": [cell(v, kind="pct") for v in bal_tbl.get("export_coverage_pct", pd.Series(dtype=float))],
        }
    )
    st.dataframe(bal_display, width="stretch", hide_index=True)

st.caption(
    "Nota: elettricità e alcune risorse possono avere HHI=10000 con un solo partner osservato — "
    "non è necessariamente monopolio reale del mercato, ma del flusso HS coperto."
)
