"""Comext raffinati — dipendenza e concentrazione per gruppo CN8."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sources import (
    DATA_YEARS,
    comext_product_label,
    load_comext_balance,
    load_comext_concentration,
    load_comext_partners,
)


def fmt_eur(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    v = float(value)
    if abs(v) >= 1e9:
        return f"€ {v / 1e9:,.2f} mld".replace(",", "X").replace(".", ",").replace("X", ".")
    if abs(v) >= 1e6:
        return f"€ {v / 1e6:,.0f} mln".replace(",", ".")
    return f"€ {v:,.0f}".replace(",", ".")


st.title("🛢️ Raffinati — Comext")
st.caption(
    "Prodotti raffinati italiani per gruppo CN8 (Eurostat Comext DS-045409): "
    "gasolio, jet, olio combustibile, lubrificanti. Valori in euro."
)

conc = load_comext_concentration()
bal = load_comext_balance()
part = load_comext_partners()

if conc.empty:
    st.warning("Nessun dato Comext disponibile.")
    st.stop()

groups = sorted(conc["product_group"].dropna().unique())
c1, c2 = st.columns(2)
with c1:
    year = st.selectbox("Anno", DATA_YEARS, index=len(DATA_YEARS) - 1)
with c2:
    group = st.selectbox("Gruppo", groups, format_func=comext_product_label)

conc_r = conc[(conc["year"] == year) & (conc["product_group"] == group)]
bal_r = bal[(bal["year"] == year) & (bal["product_group"] == group)]
part_r = part[(part["year"] == year) & (part["product_group"] == group) & (part["flow"] == "1")]

if conc_r.empty:
    st.info("Nessun dato per la selezione.")
    st.stop()

conc_r = conc_r.iloc[0]
bal_r = bal_r.iloc[0] if not bal_r.empty else None

# ── KPI ───────────────────────────────────────────────────────────────────────
import_mt = conc_r["import_quantity_kg"] / 1e9 if pd.notna(conc_r["import_quantity_kg"]) else None
export_mt = (
    bal_r["export_quantity_kg"] / 1e9
    if bal_r is not None and pd.notna(bal_r["export_quantity_kg"])
    else None
)

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Import", fmt_eur(conc_r["total_import_value_eur"]))
with k2:
    st.metric("Volume import", f"{import_mt:,.2f} Mt" if import_mt is not None else "—")
with k3:
    st.metric("HHI import", f"{conc_r['hhi']:,.0f}", help=">2500 = alta concentrazione")
with k4:
    st.metric("Top fornitore", str(conc_r["top1_supplier"]), help=f"Quota {conc_r['top1_share_pct']:.1f}%")

k5, k6, k7, k8 = st.columns(4)
with k5:
    unit = conc_r["import_unit_value_eur_per_kg"]
    st.metric("Prezzo medio import", f"€ {unit:,.3f}/kg" if pd.notna(unit) else "—")
with k6:
    if bal_r is not None:
        st.metric(
            "Saldo commerciale",
            fmt_eur(bal_r["balance_eur"]),
            delta="net exporter" if bal_r["balance_eur"] > 0 else "net importer",
            delta_color="normal" if bal_r["balance_eur"] > 0 else "inverse",
        )
    else:
        st.metric("Saldo commerciale", "—")
with k7:
    st.metric("Volume export", f"{export_mt:,.2f} Mt" if export_mt is not None else "—")
with k8:
    coverage = bal_r["export_coverage_pct"] if bal_r is not None else None
    st.metric("Export / import", f"{coverage:,.0f}%" if coverage is not None and pd.notna(coverage) else "—")

# ── Top partner import ────────────────────────────────────────────────────────
st.subheader(f"Top fornitori — {comext_product_label(group)} ({year})")
if part_r.empty:
    st.info("Nessun dato partner per la selezione.")
else:
    top = part_r.sort_values("value_eur", ascending=False).head(12)
    fig = go.Figure(
        go.Bar(
            x=top["value_eur"],
            y=top["partner_name"],
            orientation="h",
            marker_color="#2563eb",
            hovertemplate="%{y}<br>€ %{x:,.0f}<extra></extra>",
        ),
    )
    fig.update_layout(
        height=420,
        margin={"t": 10, "b": 40, "l": 180},
        xaxis_title="Import EUR",
        yaxis={"autorange": "reversed"},
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch")

# ── Trend ─────────────────────────────────────────────────────────────────────
st.subheader("Trend")
trend = conc[conc["product_group"] == group].sort_values("year")
t1, t2 = st.columns(2)
with t1:
    fig2 = go.Figure(
        go.Scatter(
            x=trend["year"],
            y=trend["hhi"],
            mode="lines+markers",
            name="HHI",
            hovertemplate="%{y:,.0f}<extra>HHI</extra>",
        ),
    )
    fig2.add_hline(y=2500, line_dash="dash", line_color="#9ca3af", annotation_text="HHI 2500")
    fig2.update_layout(height=360, margin={"t": 10, "b": 40}, xaxis={"dtick": 1}, yaxis_title="HHI")
    st.plotly_chart(fig2, width="stretch")
with t2:
    fig3 = go.Figure(
        go.Bar(
            x=trend["year"],
            y=trend["total_import_value_eur"],
            marker_color="#d97706",
            hovertemplate="€ %{y:,.0f}<extra></extra>",
        ),
    )
    fig3.update_layout(height=360, margin={"t": 10, "b": 40}, xaxis={"dtick": 1}, yaxis_title="Import EUR")
    st.plotly_chart(fig3, width="stretch")

with st.expander("Caveat e limiti"):
    st.markdown(
        """
- **Fonte**: Eurostat Comext `DS-045409`, endpoint dedicato (non il dissemination standard).
- **Gruppi CN8**: gasolio, jet, olio combustibile, lubrificanti. I codici CN8 possono cambiare per anno.
- **Valori in euro** (Comtrade è in USD): non sommare le due fonti.
- **Partner**: solo paesi ISO2, esclusi gli aggregati (`WORLD`, `EU`, `EA`, `EXT_*`).
- **Prezzo**: valore / quantità (`QUANTITY_IN_100KG`), non è un prezzo di mercato.
- **Anni**: 2020–2024.
        """
    )

st.caption(f"Comext DS-045409 · anno {year} · gruppo {comext_product_label(group)}")
