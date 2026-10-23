"""QA — Comext physical volumes vs the Eurostat energy balance.

Comext (CN8) and NRG_BAL_C (SIEC) have different perimeters: this script
prints imports/exports in Mt (Comext) and Mtoe (energy balance) for gasolio,
jet and olio combustibile, so the gap is visible instead of being averaged away.

Usage:
    python scripts/qa_comext_vs_energy.py --year 2024
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
COMEXT_MART = "out/data/mart/comext_oil/*/mart_comext_oil_balance.parquet"
ENERGY_MART = "out/data/mart/eurostat_nrg_bal_c/*/mart_energy_balance.parquet"

# Comext group -> SIEC product in the energy balance.
MAPPING = {
    "gasolio": "O4671XR5220B",
    "jet": "O4661XR5230B",
    "olio_combustibile": "O4680",
}


def _latest(pattern: str) -> Path:
    paths = sorted(ROOT.glob(pattern))
    if not paths:
        raise SystemExit(f"missing mart: {pattern}")
    return paths[-1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2024)
    args = parser.parse_args()

    con = duckdb.connect()
    comext = _latest(COMEXT_MART)
    energy = _latest(ENERGY_MART)

    print(f"QA volumi Comext vs NRG_BAL_C — {args.year}")
    print(f"  {'gruppo':18s} {'import Comext':>14s} {'import bilancio':>16s} {'export Comext':>14s} {'export bilancio':>16s}")
    for group, siec in MAPPING.items():
        c = con.execute(
            f"SELECT import_quantity_kg / 1e9, export_quantity_kg / 1e9 "
            f"FROM read_parquet('{comext}') WHERE year = {args.year} AND product_group = '{group}'"
        ).fetchone()
        e = con.execute(
            f"SELECT imports_ktoe / 1000, exports_ktoe / 1000 "
            f"FROM read_parquet('{energy}') WHERE year = {args.year} AND product = '{siec}'"
        ).fetchone()
        if not c or not e:
            print(f"  {group:18s} (dati mancanti)")
            continue
        print(
            f"  {group:18s} {c[0]:>11.2f} Mt {e[0]:>13.2f} Mtoe "
            f"{c[1]:>11.2f} Mt {e[1]:>13.2f} Mtoe"
        )

    print()
    print("Mt = massa (Comext), Mtoe = energia (NRG_BAL_C): per i prodotti petroliferi 1 t ≈ 1,02 toe.")
    print("Il confronto è indicativo, non una quadratura di massa.")
    print("I 4 gruppi non coprono tutto 271019: esclusi 2710 19 11-19 e 2710 19 29.")


if __name__ == "__main__":
    main()
