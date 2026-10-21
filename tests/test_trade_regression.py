"""
Regression tests — UN Comtrade partner universe and oil trade coverage.

Protegge due bug già visti:
1. HHI/top-1 calcolati su 8 partner pre-selezionati, non sul totale import.
2. Petrolio assente dal lato commerciale: nessun HS 2709/2710.

Marker: regression.
"""

from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parent.parent
TRADE_DIR = ROOT / "out" / "data" / "mart" / "comtrade_bilateral"
ENERGY_DIR = ROOT / "out" / "data" / "mart" / "eurostat_nrg_bal_c"
COMPOSE_DIR = ROOT / "out" / "data" / "mart" / "resource_dependency_compose"


def _load(directory: Path, table: str):
    files = sorted(directory.glob(f"*/{table}*.parquet"))
    if not files:
        pytest.skip(f"{table} not built locally")
    con = duckdb.connect()
    return con.execute(f"SELECT * FROM read_parquet('{files[-1]}')").fetchdf()


@pytest.mark.regression
class TestPartnerUniverse:
    """Il denominatore HHI è il totale import, non un paniere di 8 partner."""

    def test_gas_split_uses_all_partners_and_unit_values(self):
        df = _load(TRADE_DIR, "mart_trade_concentration")
        pipe = df[(df["resource"] == "gas_pipeline") & (df["year"] == 2024)].iloc[0]
        lng = df[(df["resource"] == "gas_lng") & (df["year"] == 2024)].iloc[0]
        assert pipe["num_suppliers"] >= 5
        assert pipe["hhi"] > 2500
        assert pipe["top1_supplier"] == "Algeria"
        assert 45 <= pipe["top1_share_pct"] <= 55
        assert lng["num_suppliers"] >= 20
        assert lng["hhi"] > 2500
        assert lng["top1_supplier"] == "Qatar"
        assert 38 <= lng["top1_share_pct"] <= 48
        assert pipe["import_unit_value_usd_per_kg"] > 0
        assert lng["import_unit_value_usd_per_kg"] > 0
        assert pipe["import_unit_value_usd_per_kg"] < 2
        assert lng["import_unit_value_usd_per_kg"] < 2

    def test_oil_trade_resources_are_present(self):
        df = _load(TRADE_DIR, "mart_trade_concentration")
        for resource in ("petrolio_greggio", "benzina", "distillati_medi"):
            row = df[(df["resource"] == resource) & (df["year"] == 2024)]
            assert not row.empty, f"missing trade resource {resource}"
            assert row["hhi"].iloc[0] is not None
            assert row["num_suppliers"].iloc[0] >= 30

    def test_clean_has_no_world_aggregate_row(self):
        files = sorted(
            (ROOT / "out" / "data" / "clean" / "comtrade_bilateral").glob("*/*.parquet")
        )
        if not files:
            pytest.skip("comtrade clean not built locally")
        con = duckdb.connect()
        n = con.execute(
            f"SELECT count(*) FROM read_parquet('{files[-1]}') WHERE partner_code = 0"
        ).fetchone()[0]
        assert n == 0


@pytest.mark.regression
class TestTransformationOutputQa:
    """TO elettricità Eurostat vs produzione netta Terna (stesso perimetro)."""

    def test_electricity_to_matches_terna(self):
        energy = _load(ENERGY_DIR, "mart_energy_balance")
        row = energy[(energy["product"] == "E7000") & (energy["year"] == 2024)]
        if row.empty:
            pytest.skip("electricity row not available")
        eurostat_ktoe = float(row["domestic_output_ktoe"].iloc[0])

        terna_dir = (
            ROOT.parents[1]
            / "ambiente-energia"
            / "energia-italia"
            / "out"
            / "data"
            / "clean"
            / "terna_elettricita_per_fonte"
            / "2024"
        )
        terna_files = sorted(terna_dir.glob("*.parquet")) if terna_dir.exists() else []
        if not terna_files:
            pytest.skip("Terna clean not available in this workspace")

        con = duckdb.connect()
        gwh = con.execute(
            f"SELECT sum(produzione_gwh) FROM read_parquet('{terna_files[-1]}') "
            "WHERE tipo_produzione = 'Netta'"
        ).fetchone()[0]
        terna_ktoe = float(gwh) * 0.086
        assert abs(eurostat_ktoe - terna_ktoe) / terna_ktoe < 0.02


@pytest.mark.regression
class TestDistillatiAggregate:
    """L'aggregato fisico distillati medi è accoppiato al trade 271019."""

    def test_distillati_medi_has_physical_and_trade(self):
        df = _load(COMPOSE_DIR, "mart_energy_vs_trade")
        row = df[(df["resource"] == "distillati_medi") & (df["year"] == 2024)]
        assert not row.empty
        assert -15 < row["physical_id_pct"].iloc[0] < 0
        assert row["trade_hhi"].iloc[0] == pytest.approx(985.6, abs=2)
        assert row["risk_profile"].iloc[0] == "low_dependency_diversified"
