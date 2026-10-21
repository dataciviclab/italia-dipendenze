"""
Regression tests — Eurostat NRG_BAL_C energy mart.

Protegge tre bug già visti:
1. Etichette SIEC hardcoded (O4640 = Naphtha, non gasolio; O4652 = benzina,
   non olio pesante; O4671 = gasolio, non cherosene).
2. Dipendenza calcolata su PPRD + IMP - EXP senza scorte: gas 2022 a 102,1%.
3. Prodotti secondari (elettricità, gasolio) trattati come primari: dipendenza
   al 100% o NULL invece della quota su disponibilità interna (TO).

Marker: regression (bug già visto, non un contratto generico).
"""

from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parent.parent
MART_DIR = ROOT / "out" / "data" / "mart" / "eurostat_nrg_bal_c"


def _load(table: str):
    files = sorted(MART_DIR.glob(f"*/{table}*.parquet"))
    if not files:
        pytest.skip(f"{table} not built locally")
    con = duckdb.connect()
    return con.execute(f"SELECT * FROM read_parquet('{files[-1]}')").fetchdf()


@pytest.mark.regression
class TestSourceConfig:
    """Eurostat non deve tornare a uno script dedicato."""

    def test_config_uses_sdmx_source(self):
        import yaml

        cfg = yaml.safe_load(
            (ROOT / "datasets" / "eurostat-nrg-bal-c" / "dataset.yml").read_text()
        )
        assert [s["type"] for s in cfg["raw"]["sources"]] == ["sdmx", "sdmx", "sdmx"]
        assert not (ROOT / "scripts" / "fetch_eurostat_energy.py").exists()


@pytest.mark.regression
class TestSiecLabels:
    """Le etichette vengono dalle codelist Eurostat, non da un dizionario a mano."""

    @pytest.mark.parametrize(
        "code,expected",
        [
            ("O4640", "Naphtha"),
            ("O4671XR5220B", "Gas oil and diesel oil"),
            ("O4652XR5210B", "Motor gasoline"),
            ("O4630", "Liquefied petroleum gases"),
            ("C0311", "Coke oven coke"),
        ],
    )
    def test_product_label_matches_siec(self, code: str, expected: str):
        df = _load("mart_energy_balance")
        row = df[df["product"] == code]
        assert not row.empty, f"missing product {code}"
        assert expected in row["product_label"].iloc[0]


@pytest.mark.regression
class TestDependencyFormula:
    """La dipendenza usa le scorte e la disponibilità interna, non il rapporto lordo."""

    def test_gas_2022_does_not_exceed_100(self):
        df = _load("mart_energy_balance")
        gas = df[(df["product"] == "G3000") & (df["year"] == 2022)].iloc[0]
        assert gas["net_import_dependency_pct"] is not None
        assert gas["net_import_dependency_pct"] < 100
        assert gas["net_import_dependency_pct"] == pytest.approx(99.2, abs=0.3)
        assert gas["gross_import_dependency_pct"] == pytest.approx(106.0, abs=0.3)

    def test_gic_uses_official_value_and_positive_stock_sign(self):
        """GIC = PPRD + IMP - EXP + STK_CHG; il segno di STK_CHG era invertito."""
        df = _load("mart_energy_balance")
        gas = df[(df["product"] == "G3000") & (df["year"] == 2022)].iloc[0]
        assert gas["gic_ktoe"] == pytest.approx(gas["gic_reported_ktoe"], abs=0.01)
        assert gas["gic_computed_ktoe"] == pytest.approx(gas["gic_reported_ktoe"], abs=0.01)
        assert gas["gic_computed_ktoe"] == pytest.approx(56103.9, abs=0.5)

    def test_oil_aggregate_uses_reported_gic(self):
        """Sul petrolio il GIC ufficiale include bunker/rettifiche: non ricalcolarlo."""
        df = _load("mart_energy_balance")
        oil = df[(df["product"] == "O4000XBIO") & (df["year"] == 2024)].iloc[0]
        assert oil["gic_ktoe"] == pytest.approx(oil["gic_reported_ktoe"], abs=0.01)
        assert oil["net_import_dependency_pct"] == pytest.approx(93.9, abs=0.3)

    def test_secondary_products_use_transformation_output(self):
        df = _load("mart_energy_balance")
        electricity = df[(df["product"] == "E7000") & (df["year"] == 2024)].iloc[0]
        assert electricity["product_kind"] == "secondary"
        assert electricity["supply_ktoe"] > electricity["gic_ktoe"]
        assert 0 < electricity["net_import_dependency_pct"] < 40

    def test_primary_products_do_not_add_transformation_output(self):
        df = _load("mart_energy_balance")
        gas = df[(df["product"] == "G3000") & (df["year"] == 2024)].iloc[0]
        assert gas["product_kind"] == "primary"
        assert gas["supply_ktoe"] == pytest.approx(gas["gic_ktoe"], abs=0.01)


@pytest.mark.regression
class TestFinalConsumption:
    """I consumi finali per settore esistono e sono coerenti con i prodotti petroliferi."""

    def test_diesel_transport_is_materialized(self):
        df = _load("mart_energy_final_consumption")
        row = df[(df["product"] == "O4671XR5220B") & (df["year"] == 2024)].iloc[0]
        assert row["final_consumption_transport_ktoe"] > 20000
        assert row["final_consumption_transport_road_ktoe"] > 20000

    def test_gasoline_transport_is_materialized(self):
        df = _load("mart_energy_final_consumption")
        row = df[(df["product"] == "O4652XR5210B") & (df["year"] == 2024)].iloc[0]
        assert row["final_consumption_transport_ktoe"] > 8000
