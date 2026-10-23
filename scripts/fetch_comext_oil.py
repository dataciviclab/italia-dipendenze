"""Fetch Eurostat Comext DS-045409 — Italy oil products by CN8 group and partner.

Comext uses a dedicated endpoint (`/api/comext/dissemination/sdmx/2.1`), not
the standard Eurostat dissemination API. Dimensions:
    freq.reporter.partner.product.flow.indicators
with flow 1 = imports, 2 = exports; indicators VALUE_IN_EUROS and
QUANTITY_IN_100KG.

The script groups the CN8 codes of HS 2710 19 into gasolio, jet, olio
combustibile and lubrificanti, fetches Italy by partner, and writes a long CSV.

Usage:
    python scripts/fetch_comext_oil.py --output-dir out/raw/comext --start-year 2020 --end-year 2024
"""

from __future__ import annotations

import argparse
import csv
import re
import time
from pathlib import Path

import requests

BASE = "https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1"
DATA = f"{BASE}/data/ds-045409"
PARTNER_CODELIST = f"{BASE}/codelist/estat/CXT_FREE_ISO"

PRODUCT_GROUPS = {
    "gasolio": [
        "27101931", "27101935", "27101941", "27101942", "27101943",
        "27101944", "27101945", "27101946", "27101947", "27101948", "27101949",
    ],
    "jet": ["27101921", "27101925"],
    "olio_combustibile": [
        "27101951", "27101955", "27101961", "27101962", "27101963",
        "27101964", "27101965", "27101966", "27101967", "27101968", "27101969",
    ],
    "lubrificanti": [
        "27101971", "27101975", "27101981", "27101983", "27101985",
        "27101987", "27101991", "27101993", "27101999",
    ],
}

FLOW_LABELS = {"1": "imports", "2": "exports"}
# 2-letter codes that are aggregates, not countries.
AGGREGATE_PARTNERS = {"WORLD", "EU", "EA", "XX"}
PARTNER_RE = re.compile(r"^[A-Z]{2}$")


def _get(url: str, params: dict | None = None, *, timeout: int = 180, attempts: int = 3) -> requests.Response:
    """GET with retry/backoff on transient errors (5xx, timeouts)."""
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            if resp.status_code >= 500:
                raise requests.HTTPError(f"HTTP {resp.status_code}")
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last = exc
            if attempt == attempts:
                break
            time.sleep(2 * attempt)
    raise SystemExit(f"Comext request failed after {attempts} attempts: {last}")

OUTPUT_COLUMNS = [
    "year", "product_group", "flow", "flow_label",
    "partner_code", "partner_name", "value_eur", "quantity_100kg",
    "unit_value_eur_per_kg", "source", "method", "data_quality",
]


def fetch_partner_names() -> dict[str, str]:
    """Return {ISO2: English name} from the Comext partner codelist."""
    resp = _get(PARTNER_CODELIST, timeout=120)
    if "<s:Code" not in resp.text:
        raise SystemExit("Comext partner codelist: unexpected response (not SDMX XML)")
    names: dict[str, str] = {}
    for match in re.finditer(r'<s:Code id="([^"]+)"[^>]*>(.*?)</s:Code>', resp.text, re.S):
        code = match.group(1)
        label = re.search(r'<c:Name xml:lang="en">([^<]*)</c:Name>', match.group(2))
        names[code] = label.group(1) if label else code
    if not names:
        raise SystemExit("Comext partner codelist returned no codes")
    return names


def _clean_name(name: str) -> str:
    """Drop the long parenthetical notes Comext adds to some partner names."""
    return re.sub(r"\s*\(.*$", "", name).strip()


def _is_country(partner: str) -> bool:
    return bool(PARTNER_RE.match(partner)) and partner not in AGGREGATE_PARTNERS


def fetch_group(codes: list[str], flow: str, indicator: str, start: int, end: int) -> dict[tuple[int, str], float]:
    """Sum a group's CN8 codes by (year, partner)."""
    key = f"A.IT..{'+'.join(codes)}.{flow}.{indicator}"
    resp = _get(
        f"{DATA}/{key}",
        params={"format": "TSV", "startPeriod": str(start), "endPeriod": str(end)},
    )
    lines = resp.text.splitlines()
    if not lines or "TIME_PERIOD" not in lines[0]:
        raise SystemExit(f"Comext data: unexpected response for {key}")
    years = [y.strip() for y in lines[0].split("\t")[1:]]
    totals: dict[tuple[int, str], float] = {}
    for line in lines[1:]:
        cols = line.split("\t")
        dims = cols[0].split(",")
        if len(dims) != 6:
            continue
        partner = dims[2]
        if not _is_country(partner):
            continue
        for i, year in enumerate(years):
            if i + 1 >= len(cols):
                continue
            raw = cols[i + 1].strip()
            if raw in (":", ""):
                continue
            try:
                value = float(raw)
            except ValueError:
                continue
            totals[(int(year), partner)] = totals.get((int(year), partner), 0.0) + value
    return totals


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="out/raw/comext")
    parser.add_argument("--start-year", type=int, default=2020)
    parser.add_argument("--end-year", type=int, default=2024)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "comext_oil.csv"

    partner_names = fetch_partner_names()
    rows: list[dict[str, object]] = []

    for group, codes in PRODUCT_GROUPS.items():
        for flow in ("1", "2"):
            values = fetch_group(codes, flow, "VALUE_IN_EUROS", args.start_year, args.end_year)
            time.sleep(0.3)
            quantities = fetch_group(codes, flow, "QUANTITY_IN_100KG", args.start_year, args.end_year)
            time.sleep(0.3)
            keys = set(values) | set(quantities)
            for year, partner in sorted(keys):
                value = values.get((year, partner), 0.0)
                quantity = quantities.get((year, partner), 0.0)
                rows.append({
                    "year": year,
                    "product_group": group,
                    "flow": flow,
                    "flow_label": FLOW_LABELS[flow],
                    "partner_code": partner,
                    "partner_name": _clean_name(partner_names.get(partner, partner)),
                    "value_eur": round(value, 2),
                    "quantity_100kg": round(quantity, 2),
                    "unit_value_eur_per_kg": round(value / (quantity * 100), 4) if quantity > 0 else "",
                    "source": "eurostat_comext",
                    "method": "observed",
                    "data_quality": "verified",
                })
            print(f"{group} {FLOW_LABELS[flow]}: {len(keys)} year/partner rows")

    with output_file.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {output_file}")


if __name__ == "__main__":
    main()
