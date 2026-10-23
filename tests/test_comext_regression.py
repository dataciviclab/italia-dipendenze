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
COMPOSE_DIR = ROOT / "out" / "data" / "mart" / "resource_dependency_compose"


def _load(table: str):
    files = sorted(MART_DIR.glob(f"*/{table}*.parquet"))
    if not files:
        pytest.skip(f"{table} not built locally")
    con = duckdb.connect()
    return con.execute(f"SELECT * FROM read_parquet('{files[-1]}')").fetchdf()


def _load_compose(table: str):
    files = sorted(COMPOSE_DIR.glob(f"*/{table}*.parquet"))
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

    def test_import_volumes_are_present(self):
        df = _load("mart_comext_oil_concentration")
        for group in ("gasolio", "jet", "olio_combustibile"):
            row = df[(df["product_group"] == group) & (df["year"] == 2024)].iloc[0]
            assert row["import_quantity_kg"] > 0

    def test_comext_totals_match_comtrade_hs6(self):
        """I gruppi CN8 coprono il 271019 di Comtrade entro ~10% (cambio ~1,08)."""
        comext = _load("mart_comext_oil_balance")
        comtrade_files = sorted(
            (ROOT / "out" / "data" / "mart" / "comtrade_bilateral").glob(
                "*/mart_trade_balance*.parquet"
            )
        )
        if not comtrade_files:
            pytest.skip("comtrade balance not built locally")
        con = duckdb.connect()
        comtrade = con.execute(
            f"SELECT * FROM read_parquet('{comtrade_files[-1]}')"
        ).fetchdf()
        cx = comext[comext["year"] == 2024]
        ct = comtrade[
            (comtrade["year"] == 2024) & (comtrade["resource"] == "distillati_medi")
        ].iloc[0]
        assert abs(cx["import_value_eur"].sum() * 1.08 - ct["import_value_usd"]) / ct[
            "import_value_usd"
        ] < 0.10
        assert abs(cx["export_value_eur"].sum() * 1.08 - ct["export_value_usd"]) / ct[
            "export_value_usd"
        ] < 0.10


@pytest.mark.regression
class TestRefinedDependency:
    """Il compose unisce dipendenza fisica e partner Comext per prodotto."""

    def test_gasolio_physical_and_partner(self):
        df = _load_compose("mart_refined_dependency")
        row = df[(df["resource"] == "gasolio") & (df["year"] == 2024)].iloc[0]
        assert row["physical_id_pct"] == pytest.approx(-8.2, abs=0.3)
        assert 1900 < row["hhi"] < 2100
        assert row["top1_supplier"] == "Saudi Arabia"

    def test_jet_is_mapped_to_cherosene(self):
        df = _load_compose("mart_refined_dependency")
        row = df[(df["resource"] == "cherosene") & (df["year"] == 2024)].iloc[0]
        assert row["top1_supplier"] == "United Arab Emirates"
        assert row["hhi"] < 1300
