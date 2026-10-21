"""QA of the refinery output (`TO`) used for secondary oil products.

The energy mart uses Eurostat `TO` (transformation output) as domestic supply
for gas oil, gasoline, jet fuel, etc. This script checks that number against:

- `RI_OBS` / `RI_CAL` from Eurostat `NRG_CB_OILM` (monthly refinery intake,
  thousand tonnes) for crude oil;
- the sum of `TO` for the main refined products in `mart_energy_balance`.

It is an internal consistency check, not a replacement for the external QA
with ISPRA / UNFCCC CRF tables. The external check is still needed because
`TO` and `RI` sit on different boundaries (crude intake vs all refinery
outputs/feedstocks).

Usage:
    python scripts/qa_refinery.py --year 2024
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import requests

ROOT = Path(__file__).resolve().parent.parent
MART_GLOB = "out/data/mart/eurostat_nrg_bal_c/*/mart_energy_balance.parquet"
BASE = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/NRG_CB_OILM"
MAIN_PRODUCTS = (
    "O4630",  # LPG
    "O4640",  # naphtha
    "O4652XR5210B",  # motor gasoline
    "O4671XR5220B",  # gas oil / diesel
    "O4661XR5230B",  # jet fuel
    "O4680",  # fuel oil
)


def _mart_path() -> Path:
    paths = sorted(ROOT.glob(MART_GLOB))
    if not paths:
        raise SystemExit("mart_energy_balance.parquet not found; run the pipeline first")
    return paths[-1]


def _fetch_monthly(indicator: str, year: int) -> float:
    """Sum monthly refinery intake for crude oil, in thousand tonnes."""
    url = f"{BASE}/M.{indicator}.O4100_TOT.THS_T.IT"
    resp = requests.get(
        url,
        params={"format": "TSV", "startPeriod": f"{year}-01", "endPeriod": f"{year}-12"},
        timeout=60,
    )
    resp.raise_for_status()
    lines = resp.text.splitlines()
    values: list[str] = []
    for line in lines[1:]:
        cols = line.split("\t")
        dims = cols[0].split(",")
        if len(dims) > 1 and dims[1] == indicator:
            values = [c.strip() for c in cols[1:]]
            break
    return sum(float(v) for v in values if v not in (":", ""))


def _mart_values(year: int) -> tuple[float, float, list[tuple[str, float]]]:
    con = duckdb.connect()
    path = _mart_path()
    agg = con.execute(
        f"SELECT domestic_output_ktoe FROM read_parquet('{path}') "
        f"WHERE year = {year} AND product = 'O4000XBIO'"
    ).fetchone()
    main = con.execute(
        f"SELECT sum(domestic_output_ktoe) FROM read_parquet('{path}') "
        f"WHERE year = {year} AND product IN {MAIN_PRODUCTS}"
    ).fetchone()
    rows = con.execute(
        f"SELECT product, domestic_output_ktoe FROM read_parquet('{path}') "
        f"WHERE year = {year} AND product IN {MAIN_PRODUCTS} ORDER BY product"
    ).fetchall()
    return (
        float(agg[0] or 0) if agg else 0.0,
        float(main[0] or 0) if main else 0.0,
        [(str(p), float(v or 0)) for p, v in rows],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2024)
    args = parser.parse_args()

    ri_obs = _fetch_monthly("RI_OBS", args.year)
    ri_cal = _fetch_monthly("RI_CAL", args.year)
    agg_to, main_to, rows = _mart_values(args.year)

    print(f"QA raffinazione — {args.year}")
    print(f"  crude intake RI_OBS: {ri_obs:,.1f} THS_T")
    print(f"  crude intake RI_CAL: {ri_cal:,.1f} THS_T")
    print(f"  TO aggregato O4000XBIO: {agg_to:,.1f} KTOE")
    print(f"  TO prodotti principali: {main_to:,.1f} KTOE")
    for product, value in rows:
        print(f"    {product}: {value:,.1f}")

    if ri_obs > 0:
        print(f"  main products / crude intake: {main_to / ri_obs:.3f}")
        print(f"  aggregate TO / crude intake: {agg_to / ri_obs:.3f}")
    if ri_cal > 0:
        print(f"  main products / RI_CAL: {main_to / ri_cal:.3f}")

    print()
    if ri_obs > 0 and 0.95 <= main_to / ri_obs <= 1.05:
        print("OK: i TO dei prodotti principali sono coerenti con il crude intake")
        print("    (assumendo 1 t ≈ 1 toe; il confronto è indicativo).")
    else:
        print("WARN: i TO dei prodotti principali non chiudono con il crude intake.")

    if ri_obs > 0 and agg_to / ri_obs > 1.10:
        print(
            "WARN: l'aggregato O4000XBIO include altri prodotti/feedstock oltre ai "
            "principali; per il QA esterno usare ISPRA/UNFCCC CRF (refinery input/output)."
        )


if __name__ == "__main__":
    main()
