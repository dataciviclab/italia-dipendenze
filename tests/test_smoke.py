"""
test_smoke.py — Smoke test per dipendenze-risorse

Verifica:
- Esistenza e integrita' dei mart parquet
- Contratti colonne (required_columns)
- Min rows per mart
"""

from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parent.parent
MART_DIR = ROOT / "out" / "data" / "mart"


# ── Contratti mart ──────────────────────────────────────────────────────────

MART_CONTRACTS = {
    "fao_fertilizer_consumption": {
        "mart_fertilizer_consumption": {
            "min_rows": 3,
            "required_columns": ["year", "country", "total_consumption_tonnes"],
        },
    },
    "eurostat_nrg_bal_c": {
        "mart_energy_balance": {
            "min_rows": 10,
            "required_columns": ["year", "product", "gross_import_dependency_pct"],
        },
    },
    "comtrade_bilateral": {
        "mart_trade_bilateral": {
            "min_rows": 10,
            "required_columns": ["year", "hs_code", "flow", "primary_value_usd"],
        },
        "mart_trade_concentration": {
            "min_rows": 1,
            "required_columns": ["year", "resource", "hhi", "top1_supplier"],
        },
    },
    "resource_dependency_compose": {
        "mart_resource_dependency": {
            "min_rows": 10,
            "required_columns": ["year", "resource", "physical_id_pct", "hhi", "top1_supplier"],
        },
        "mart_energy_vs_trade": {
            "min_rows": 5,
            "required_columns": ["year", "product", "physical_id_pct", "risk_profile"],
        },
    },
}


def _find_mart_files(dataset: str, mart_name: str) -> list[Path]:
    """Trova i parquet di un mart specifico (handles year subdirs)."""
    pattern = MART_DIR / f"{dataset}"
    if not pattern.exists():
        return []
    files = []
    for year_dir in pattern.iterdir():
        if year_dir.is_dir():
            for f in year_dir.glob(f"{mart_name}*.parquet"):
                files.append(f)
    return files


@pytest.mark.smoke
class TestMartContracts:
    """Verifica contratti dei mart per ogni dataset."""

    @pytest.mark.parametrize(
        "dataset,mart_name,contract",
        [
            (ds, mart, contract)
            for ds, marts in MART_CONTRACTS.items()
            for mart, contract in marts.items()
        ],
        ids=[
            f"{ds}-{mart}"
            for ds, marts in MART_CONTRACTS.items()
            for mart in marts
        ],
    )
    def test_mart_exists_and_valid(self, dataset: str, mart_name: str, contract: dict):
        files = _find_mart_files(dataset, mart_name)
        if not files:
            pytest.skip(f"No mart files found for {dataset}/{mart_name}")

        con = duckdb.connect()
        all_rows = 0
        for f in files:
            df = con.execute(f"SELECT * FROM read_parquet('{f}')").fetchdf()
            all_rows += len(df)
            # Check required columns
            for col in contract["required_columns"]:
                assert col in df.columns, f"Missing column {col} in {f.name}"

        assert all_rows >= contract["min_rows"], (
            f"{dataset}/{mart_name}: {all_rows} rows < {contract['min_rows']}"
        )


@pytest.mark.smoke
class TestDataQuality:
    """Verifica data_quality nei mart."""

    def test_fertilizer_data_quality(self):
        files = _find_mart_files("fao_fertilizer_consumption", "mart_fertilizer_consumption")
        if not files:
            pytest.skip("Fertilizer mart not built yet")
        con = duckdb.connect()
        for f in files:
            df = con.execute(f"SELECT * FROM read_parquet('{f}')").fetchdf()
            assert "data_quality" in df.columns
            assert df["data_quality"].isin(["verified", "partial", "constructed"]).all()

    def test_energy_balance_data_quality(self):
        files = _find_mart_files("eurostat_nrg_bal_c", "mart_energy_balance")
        if not files:
            pytest.skip("Energy balance mart not built yet")
        con = duckdb.connect()
        for f in files:
            df = con.execute(f"SELECT * FROM read_parquet('{f}')").fetchdf()
            assert "data_quality" in df.columns
            assert df["data_quality"].isin(["verified", "partial", "constructed"]).all()
