"""
Regression test — risk_profile in mart_energy_vs_trade.

Protegge:
1. Il SQL compose gestisce dual-null (physical_id_pct AND trade_hhi) senza
   cadere in low_dependency (bug già visto su O4630 / E7000).
2. Se il mart locale è presente, i valori osservati restano coerenti.

Marker: regression (protegge un bug già visto, non un contratto generico).
"""

from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parent.parent
SQL_PATH = (
    ROOT
    / "compose"
    / "resource-dependency-compose"
    / "sql"
    / "mart_energy_vs_trade.sql"
)
MART_GLOB = ROOT / "out" / "data" / "mart" / "resource_dependency_compose"


@pytest.mark.regression
class TestRiskProfileSqlContract:
    """Il CASE SQL deve dichiarare esplicitamente dual-null e HHI mancante."""

    def test_sql_has_dual_null_branch(self):
        sql = SQL_PATH.read_text(encoding="utf-8")
        assert "physical_id_pct IS NULL AND t.hhi IS NULL" in sql
        assert "insufficient_data" in sql

    def test_sql_does_not_map_missing_hhi_to_low_dependency_alone(self):
        """Un ramo con solo ID%>90 e HHI NULL non deve usare low_dependency."""
        sql = SQL_PATH.read_text(encoding="utf-8")
        assert "high_dependency_trade_missing" in sql
        # ramo critico senza HHI non deve cadere in ELSE low_dependency
        assert "physical_id_pct > 90 AND t.hhi IS NULL THEN 'high_dependency_trade_missing'" in sql

    def test_sql_has_all_missing_side_branches(self):
        sql = SQL_PATH.read_text(encoding="utf-8")
        for token in [
            "high_dependency_trade_missing",
            "moderate_dependency_trade_missing",
            "low_dependency_trade_missing",
            "trade_high_concentration_only",
            "insufficient_data",
        ]:
            assert token in sql, f"missing risk_profile branch: {token}"


def _load_energy_vs_trade():
    files = sorted(MART_GLOB.glob("*/mart_energy_vs_trade.parquet"))
    if not files:
        pytest.skip("mart_energy_vs_trade not built locally")
    con = duckdb.connect()
    return con.execute(
        f"SELECT * FROM read_parquet('{files[-1]}')"
    ).fetchdf()


@pytest.mark.regression
class TestRiskProfileMartValues:
    """Valori sul mart prodotto: dual-null ≠ low_dependency."""

    def test_dual_null_is_insufficient_data(self):
        df = _load_energy_vs_trade()
        dual = df[df["physical_id_pct"].isna() & df["trade_hhi"].isna()]
        assert not dual.empty, "expected rows with both metrics missing"
        values = set(dual["risk_profile"].unique())
        assert values == {"insufficient_data"}, (
            f"dual-null rows must be insufficient_data, got {values}: "
            f"{dual[['year', 'product', 'risk_profile']].to_dict('records')}"
        )

    def test_carbone_high_id_null_hhi(self):
        df = _load_energy_vs_trade()
        carbone = df[(df["resource"] == "carbone") & df["physical_id_pct"].notna()]
        if carbone.empty:
            pytest.skip("no carbone rows")
        assert (carbone["risk_profile"] == "high_dependency_trade_missing").all()

    def test_gas_with_both_metrics_is_critical_when_hhi_high(self):
        df = _load_energy_vs_trade()
        gas = df[(df["resource"] == "gas") & df["physical_id_pct"].notna() & df["trade_hhi"].notna()]
        if gas.empty:
            pytest.skip("no gas rows with both metrics")
        high = gas[gas["trade_hhi"] > 2500]
        assert (high["risk_profile"] == "critical_high_concentration").all()
