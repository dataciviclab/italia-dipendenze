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

# All partner countries, no curated panel: HHI and top-supplier shares must be
# computed on total Italian imports, not on 8 pre-selected partners.
# partnerCode=None returns every partner plus the World aggregate row
# (partnerCode 0), which is skipped below to avoid double counting.
RESOURCES = {
    # Gas split by transport mode: pipeline (271121) vs LNG (271111),
    # plus LPG (271112/113/119) and residual gaseous hydrocarbons (271129).
    # The old 2711 aggregate hid two distinct supplier risks.
    "gas_pipeline": {"hs": "271121"},
    "gas_lng": {"hs": "271111"},
    "gpl": {"hs": "271112,271113,271119"},
    "petrolio_greggio": {"hs": "2709"},
    "prodotti_petroliferi": {"hs": "2710"},
    "fertilizzanti": {"hs": "3102,3103,3104,3105"},
    "rame": {"hs": "7403,2603,7404"},
    "terre_rare": {"hs": "280530,2846"},
    "litio": {"hs": "282520"},
    "cobalto": {"hs": "8105"},
    "alluminio": {"hs": "7601"},
    "ferro_acciaio": {"hs": "7207"},
    "elettricita": {"hs": "2716"},
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
                partnerCode=None,
                partner2Code=None, customsCode=None, motCode=None,
                maxRecords=50000, format_output="JSON",
                aggregateBy=None, breakdownMode="classic",
                countOnly=None, includeDesc=True,
            )
            if df is not None and len(df) > 0:
                for _, row in df.iterrows():
                    # World aggregate row (partnerCode 0) would double count.
                    if row.get("partnerCode") in (0, "0"):
                        continue
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
