"""Data access layer — Italia Dipendenze dashboard.

Multi-dataset via lab_connectors: GCS default, out/ locale come fallback.
Anno toolkit (cartella path contract) = 2026; anni dati nei parquet = 2020–2024.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
from lab_connectors.duckdb.queries import (
    detect_local_root,
    load_mart_table as _load_mart_table,
    query_clean as _query_clean,
)
from lab_connectors.formatters import fmt_num, fmt_pct
from lab_connectors.registry import load_registry

ROOT = Path(__file__).parent.parent
PREFIX = "italia_dipendenze/"
TOOLKIT_YEAR = 2026
DATA_YEARS = list(range(2020, 2025))
COMPOSE_SLUG = "resource_dependency_compose"
LOCAL_ROOT = detect_local_root(repo_root=ROOT)

# Etichette leggibili per risorse / codici SIEC del compose
RESOURCE_LABELS = {
    "gas": "Gas naturale",
    "petrolio_greggio": "Petrolio greggio",
    "carbone": "Carbone",
    "coke": "Coke",
    "elettricita": "Elettricità",
    "prodotti_petroliferi": "Prodotti petroliferi",
    "gasolio": "Gasolio",
    "cherosene": "Cherosene",
    "olio_pesante": "Olio pesante",
    "rinnovabili_total": "Rinnovabili totali",
    "eolico": "Eolico",
    "geotermico": "Geotermico",
    "solare_termico": "Solare termico",
    "solare_fotovoltaico": "Solare FV",
    "idroelettrico": "Idroelettrico",
    "biocarburanti_liquidi": "Biocarburanti liquidi",
    "biocombustibili_solidi": "Biocombustibili solidi",
    "nucleare": "Nucleare",
    "rame": "Rame",
    "litio": "Litio",
    "cobalto": "Cobalto",
    "terre_rare": "Terre rare",
    "alluminio": "Alluminio",
    "ferro_acciaio": "Ferro e acciaio",
    "fertilizzanti": "Fertilizzanti",
    "R5110-5150_W6000RI": "Rinnovabili / rifiuti (SIEC)",
    "R5220P": "Elettricità da rinnovabili",
}

RISK_LABELS = {
    "critical_high_concentration": "Critica · alta concentrazione",
    "critical_diversified": "Critica · fornitura diversificata",
    "moderate_high_concentration": "Moderata · alta concentrazione",
    "moderate_diversified": "Moderata · fornitura diversificata",
    "high_dependency_trade_missing": "Alta dipendenza · HHI non disponibile",
    "moderate_dependency_trade_missing": "Dipendenza media · HHI non disponibile",
    "low_dependency_trade_missing": "Dipendenza bassa · HHI non disponibile",
    "trade_high_concentration_only": "Solo HHI · concentrazione alta (ID% n/d)",
    "trade_only": "Solo HHI commerciale (ID% n/d)",
    "insufficient_data": "Dati insufficienti (ID% e HHI n/d)",
    "low_dependency": "Bassa dipendenza",
}

DATA_SOURCE_LABELS = {
    "energy_and_trade": "Energia + commercio",
    "trade_only": "Solo commercio",
    "energy_only": "Solo energia",
}

CONC_LABELS = {
    "high": "Alta",
    "medium": "Media",
    "low": "Bassa",
}

POSITION_LABELS = {
    "net_importer": "Net importer",
    "net_exporter": "Net exporter",
}

# Etichette prodotti Eurostat (product_label) per UI in italiano
PRODUCT_LABELS = {
    "Natural gas": "Gas naturale",
    "Oil & petroleum products (excl. biofuel): see O4630": "Prodotti petroliferi",
    "Oil & petroleum products (excl. biofuel)": "Prodotti petroliferi (excl. biofuel)",
    "Crude oil, NGL, feedstocks": "Petrolio greggio, NGL, feedstock",
    "Coal and other solid fossil fuels": "Carbone e solidi fossili",
    "Coke oven coke": "Coke di fornace",
    "Total renewables and biofuels": "Rinnovabili e biocarburanti totali",
    "Total bioenergy": "Bioenergia totale",
    "Total final energy consumption": "Consumo finale totale",
    "Electricity": "Elettricità",
    "Wind": "Eolico",
    "Geothermal": "Geotermico",
    "Solar photovoltaico": "Solare fotovoltaico",
    "Solar thermal": "Solare termico",
    "Non-renewable waste": "Rifiuti non rinnovabili",
    "Renewable waste": "Rifiuti rinnovabili",
    "Primary solid biofuels": "Biocombustibili solidi primari",
    "Gas/diesel oil": "Gasolio",
    "Heavy fuel oil": "Olio pesante",
    "Kerosene-type jet fuel": "Cherosene per jet",
}


def product_label(label: str | None) -> str:
    if label is None or (isinstance(label, float) and pd.isna(label)):
        return "—"
    key = str(label)
    return PRODUCT_LABELS.get(key, key)

TREND_LABELS = {
    "concentration_increasing": "Concentrazione in aumento",
    "concentration_decreasing": "Concentrazione in diminuzione",
    "newly_concentrated": "Nuovamente concentrata",
    "stable": "Stabile",
}


def resource_label(resource: str | None) -> str:
    if resource is None or (isinstance(resource, float) and pd.isna(resource)):
        return "—"
    key = str(resource)
    return RESOURCE_LABELS.get(key, key.replace("_", " "))


def risk_label(profile: str | None) -> str:
    if profile is None or (isinstance(profile, float) and pd.isna(profile)):
        return "—"
    return RISK_LABELS.get(str(profile), str(profile))


def fmt_usd(value: float | int | None, *, compact: bool = True) -> str:
    """Valore in USD (Comtrade) con formattazione italiana."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    v = float(value)
    if compact:
        if abs(v) >= 1e9:
            return f"$ {v / 1e9:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " mld"
        if abs(v) >= 1e6:
            return f"$ {v / 1e6:,.0f}".replace(",", ".") + " mln"
        if abs(v) >= 1e3:
            return f"$ {v / 1e3:,.0f}".replace(",", ".") + " k"
    return f"$ {v:,.0f}".replace(",", ".")


def cell(value, *, kind: str = "auto") -> str:
    """Cella tabella: mai 'None' / NaN a schermo."""
    if value is None:
        return "—"
    try:
        if pd.isna(value):
            return "—"
    except (TypeError, ValueError):
        pass
    if kind == "usd":
        return fmt_usd(value)
    if kind == "pct":
        return fmt_pct(float(value), decimals=1)
    if kind == "int":
        return f"{int(value):,}".replace(",", ".")
    if kind == "conc":
        return conc_label(value)
    if kind == "position":
        return position_label(value)
    return str(value)


def conc_label(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return CONC_LABELS.get(str(value), str(value))


def position_label(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return POSITION_LABELS.get(str(value), str(value))


def load_registry_obj():
    return load_registry(ROOT / "registry" / "registry.json")


@st.cache_data(ttl=3600, show_spinner=False)
def load_mart(slug: str, table: str, year: int = TOOLKIT_YEAR) -> pd.DataFrame:
    """Carica un mart table da GCS (o out/ locale se presente)."""
    return _load_mart_table(slug, table, year, prefix=PREFIX, local_root=LOCAL_ROOT)


@st.cache_data(ttl=3600, show_spinner=False)
def load_resource_dependency() -> pd.DataFrame:
    """Matrice unica: physical ID + concentrazione per risorsa."""
    return load_mart(COMPOSE_SLUG, "mart_resource_dependency")


@st.cache_data(ttl=3600, show_spinner=False)
def load_energy_vs_trade() -> pd.DataFrame:
    """Prodotti con dati energia + commercio e risk_profile."""
    return load_mart(COMPOSE_SLUG, "mart_energy_vs_trade")


@st.cache_data(ttl=3600, show_spinner=False)
def load_energy_balance() -> pd.DataFrame:
    return load_mart("eurostat_nrg_bal_c", "mart_energy_balance")


@st.cache_data(ttl=3600, show_spinner=False)
def load_trade_concentration() -> pd.DataFrame:
    return load_mart("comtrade_bilateral", "mart_trade_concentration")


@st.cache_data(ttl=3600, show_spinner=False)
def load_trade_balance() -> pd.DataFrame:
    return load_mart("comtrade_bilateral", "mart_trade_balance")


@st.cache_data(ttl=3600, show_spinner=False)
def load_trade_bilateral() -> pd.DataFrame:
    return load_mart("comtrade_bilateral", "mart_trade_bilateral")


@st.cache_data(ttl=3600, show_spinner=False)
def load_fertilizer() -> pd.DataFrame:
    return load_mart("fao_fertilizer_consumption", "mart_fertilizer_consumption")


@st.cache_data(ttl=3600, show_spinner=False)
def query(slug: str, sql: str, years: tuple[int, ...] = (TOOLKIT_YEAR,)) -> pd.DataFrame:
    """SQL sul clean layer (anni toolkit, non anni dati)."""
    return _query_clean(slug, sql, list(years), prefix=PREFIX, local_root=LOCAL_ROOT)


def year_slice(df: pd.DataFrame, year: int) -> pd.DataFrame:
    if df is None or df.empty or "year" not in df.columns:
        return pd.DataFrame()
    return df[df["year"] == year].copy()


__all__ = [
    "COMPOSE_SLUG",
    "CONC_LABELS",
    "DATA_SOURCE_LABELS",
    "DATA_YEARS",
    "PREFIX",
    "POSITION_LABELS",
    "PRODUCT_LABELS",
    "RESOURCE_LABELS",
    "RISK_LABELS",
    "ROOT",
    "TREND_LABELS",
    "TOOLKIT_YEAR",
    "cell",
    "conc_label",
    "fmt_num",
    "fmt_pct",
    "fmt_usd",
    "load_energy_balance",
    "load_energy_vs_trade",
    "load_fertilizer",
    "load_mart",
    "load_registry_obj",
    "load_resource_dependency",
    "load_trade_balance",
    "load_trade_bilateral",
    "load_trade_concentration",
    "position_label",
    "product_label",
    "query",
    "resource_label",
    "risk_label",
    "year_slice",
]
