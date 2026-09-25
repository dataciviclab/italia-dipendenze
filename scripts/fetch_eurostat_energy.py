"""Fetch Eurostat NRG_BAL_C for Italy — imports, exports, production, stocks.

Uses Eurostat SDMX API (no key needed).
Filters to Italy only, specific indicators and products.

Usage:
    python scripts/fetch_eurostat_energy.py --output-dir out/raw/eurostat
"""

import argparse
import io
import time
from pathlib import Path

import pandas as pd
import requests

SDMX_BASE = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data"
DATASET = "NRG_BAL_C"
GEO = "IT"
INDICATORS = ["IMP", "EXP", "PPRD", "STK_CHG"]
PRODUCTS = ["G3000", "C0000X0350-0370", "O4630"]

INDICATOR_NAMES = {
    "IMP": "Imports",
    "EXP": "Exports",
    "PPRD": "Primary production",
    "STK_CHG": "Stock changes",
}

PRODUCT_NAMES = {
    "G3000": "Natural gas",
    "C0000X0350-0370": "Coal and other solid fossil fuels",
    "O4630": "Oil products",
}


def fetch_nrg_bal(indicator: str, product: str, start_year: int, end_year: int) -> pd.DataFrame:
    """Fetch a single indicator x product from Eurostat NRG_BAL_C."""
    key = f"A.{indicator}.{product}.KTOE.{GEO}"
    params = {
        "format": "SDMX-CSV",
        "startPeriod": str(start_year),
        "endPeriod": str(end_year),
    }
    url = f"{SDMX_BASE}/{DATASET}/{key}"

    try:
        resp = requests.get(url, params=params, timeout=60)
        if resp.status_code != 200:
            print(f"  HTTP {resp.status_code} for {indicator}/{product}")
            return pd.DataFrame()

        df = pd.read_csv(io.StringIO(resp.text))

        col_map = {}
        for col in df.columns:
            lower = col.lower().strip()
            if "time_period" in lower:
                col_map[col] = "time_period"
            elif "obs_value" in lower:
                col_map[col] = "obs_value"
        df = df.rename(columns=col_map)

        tp = df["time_period"]
        df["year"] = tp.astype(int) if tp.dtype in ("int64", "float64") else pd.to_numeric(tp.str[:4], errors="coerce")
        df["value"] = pd.to_numeric(df["obs_value"], errors="coerce")

        df["indicator"] = indicator
        df["indicator_name"] = INDICATOR_NAMES.get(indicator, indicator)
        df["product"] = product
        df["product_name"] = PRODUCT_NAMES.get(product, product)
        df["unit"] = "KTOE"
        df["geo"] = GEO
        df["source"] = "eurostat_nrg_bal_c"
        df["method"] = "observed"
        df["data_quality"] = "verified"

        return df[["year", "product", "product_name", "indicator", "indicator_name",
                    "value", "unit", "geo", "source", "method", "data_quality"]]

    except Exception as e:
        print(f"  Error: {e}")
        return pd.DataFrame()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="out/raw/eurostat")
    parser.add_argument("--start-year", type=int, default=2020)
    parser.add_argument("--end-year", type=int, default=2024)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_dfs = []
    total = len(INDICATORS) * len(PRODUCTS)
    count = 0

    for indicator in INDICATORS:
        for product in PRODUCTS:
            count += 1
            print(f"[{count}/{total}] {indicator} {product} ({args.start_year}-{args.end_year})...", end=" ")
            df = fetch_nrg_bal(indicator, product, args.start_year, args.end_year)
            if not df.empty:
                all_dfs.append(df)
                print(f"OK ({len(df)} rows)")
            else:
                print("no data")
            time.sleep(0.5)

    if not all_dfs:
        print("No data fetched")
        return

    result = pd.concat(all_dfs, ignore_index=True)
    out_file = output_dir / "eurostat_energy_balance.csv"
    result.to_csv(out_file, index=False)
    print(f"\nWrote {len(result)} rows to {out_file}")


if __name__ == "__main__":
    main()
