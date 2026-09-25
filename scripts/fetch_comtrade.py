"""Fetch bilateral trade data from UN Comtrade for all resources.

Uses comtradeapicall package (pip install comtradeapicall).
Requires COMTRADE_SUBSCRIPTION_KEY env var for getFinalData.

Usage:
    python scripts/fetch_comtrade.py --output-dir out/raw/comtrade
    COMTRADE_SUBSCRIPTION_KEY=xxx python scripts/fetch_comtrade.py
"""

import argparse
import csv
import os
from pathlib import Path

import comtradeapicall

RESOURCES = {
    "gas": {"hs": "2711", "partners": "012,031,634,842,643,434,528,276"},
    "fertilizzanti": {"hs": "3102,3103,3104,3105", "partners": "156,356,643,112,124,842,276,528"},
    "rame": {"hs": "7403,2603,7404", "partners": "152,604,180,156,842,360,036,643,124"},
    "terre_rare": {"hs": "280530,2846", "partners": "156,842,276,724,616,528,826,380"},
    "litio": {"hs": "282520", "partners": "036,152,156,842,724,276,826,380"},
    "cobalto": {"hs": "8105", "partners": "180,156,124,842,724,276,360,710"},
    "alluminio": {"hs": "7601", "partners": "156,124,360,036,842,276,724,643"},
    "ferro_acciaio": {"hs": "7207", "partners": "156,643,276,124,842,724,826,710"},
    "elettricita": {"hs": "2716", "partners": "276,756,724,752,528,250,826,643"},
}

CSV_COLUMNS = [
    "year", "hs_code", "reporter_code", "partner_code", "flow",
    "net_wgt_kg", "primary_value_usd", "classification",
    "resource", "hs_code_name", "partner_name", "flow_label",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="out/raw/comtrade")
    parser.add_argument("--years", default="2020,2021,2022,2023,2024")
    parser.add_argument("--flows", default="M,X")
    args = parser.parse_args()

    key = os.environ.get("COMTRADE_SUBSCRIPTION_KEY", "")
    if not key:
        print("ERROR: COMTRADE_SUBSCRIPTION_KEY not set")
        return

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "comtrade_bilateral.csv"

    periods = args.years
    flows = args.flows.split(",")
    all_rows = []

    for resource_name, cfg in RESOURCES.items():
        for flow in flows:
            df = comtradeapicall.getFinalData(
                key,
                typeCode="C", freqCode="A", clCode="HS",
                period=periods,
                reporterCode="380",
                cmdCode=cfg["hs"],
                flowCode=flow,
                partnerCode=cfg["partners"],
                partner2Code=None, customsCode=None, motCode=None,
                maxRecords=50000, format_output="JSON",
                aggregateBy=None, breakdownMode="classic",
                countOnly=None, includeDesc=True,
            )
            if df is not None and len(df) > 0:
                for _, row in df.iterrows():
                    all_rows.append({
                        "year": row.get("period"),
                        "hs_code": row.get("cmdCode"),
                        "reporter_code": row.get("reporterCode"),
                        "partner_code": row.get("partnerCode"),
                        "flow": row.get("flowCode"),
                        "net_wgt_kg": row.get("netWgt"),
                        "primary_value_usd": row.get("primaryValue"),
                        "classification": row.get("classificationCode"),
                        "resource": resource_name,
                        "hs_code_name": row.get("cmdDesc", ""),
                        "partner_name": row.get("partnerDesc", ""),
                        "flow_label": "imports" if flow == "M" else "exports",
                    })
                print(f"{resource_name} {flow}: {len(df)} rows")
            else:
                print(f"{resource_name} {flow}: no data")

    with open(output_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        w.writerows(all_rows)

    print(f"\nWrote {len(all_rows)} rows to {output_file}")


if __name__ == "__main__":
    main()
