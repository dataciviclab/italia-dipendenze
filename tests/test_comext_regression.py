"""
Regression tests — Eurostat Comext oil products (DS-045409).

Protegge lo split per gruppo CN8: il solo HS6 271019 nascondeva il gasolio
(concentrato su Arabia Saudita) dietro una media.

Marker: regression.
"""

from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parent.parent
MART_DIR = ROOT / "out" / "data" / "mart" / "comext_oil"


def _load(table: str):
    files = sorted(MART_DIR.glob(f"*/{table}*.parquet"))
    if not files:
        pytest.skip(f"{table} not built locally")
    con = duckdb.connect()
    return con.execute(f"SELECT * FROM read_parquet('{files[-1]}')").fetchdf()


@pytest.mark.regression
class TestComextOil:
    def test_gasolio_import_is_concentrated(self):
        df = _load("mart_comext_oil_concentration")
        row = df[(df["product_group"] == "gasolio") & (df["year"] == 2024)].iloc[0]
        assert 1900 < row["hhi"] < 2100
        assert row["top1_supplier"] == "Saudi Arabia"
        assert 38 <= row["top1_share_pct"] <= 45
        assert row["import_unit_value_eur_per_kg"] > 0

    def test_jet_import_is_more_diversified(self):
        df = _load("mart_comext_oil_concentration")
        row = df[(df["product_group"] == "jet") & (df["year"] == 2024)].iloc[0]
        assert row["hhi"] < 1300
        assert row["top1_supplier"] == "United Arab Emirates"

    def test_balance_positions(self):
        df = _load("mart_comext_oil_balance")
        gasolio = df[(df["product_group"] == "gasolio") & (df["year"] == 2024)].iloc[0]
        jet = df[(df["product_group"] == "jet") & (df["year"] == 2024)].iloc[0]
        assert gasolio["trade_position"] == "net_exporter"
        assert jet["trade_position"] == "net_importer"

    def test_partner_names_are_clean(self):
        df = _load("mart_comext_oil_concentration")
        assert not df["top1_supplier"].str.contains(r"\(", regex=True, na=False).any()
