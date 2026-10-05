# Materie Prime — Stato e Da Farsi

**Data**: 2026-09-28
**Repo**: `dataciviclab/italia-dipendenze` (git)

---

## Stato attuale

Pipeline funzionante: `make clean && make run-all && make test`
- 4/4 dataset SUCCESS, 10/10 test passano
- Fetch dati da API (Eurostat SDMX, Comtrade comtradeapicall, FAO cached)
- Zero CSV committati, tutto script-based

### Ordine esecuzione

```
comtrade (4s) → eurostat (84s) → fao (2s) → compose (0.6s)
```

### Fonti dati

| Fonte | Tipo | Key | Dati |
|-------|------|-----|------|
| Eurostat NRG_BAL_C | script (SDMX API) | No | Bilancio fisico Italia, 23 prodotti SIEC, 2020-2024 |
| UN Comtrade | script (comtradeapicall) | Sì | Commercio bilaterale HS6, 2020-2024, 9 risorse |
| FAO | script (cached) | No | Consumo fertilizzanti, 2018-2023 |

### Output

| Dataset | Righe clean | Mart tabelle | Righe mart |
|---------|:-----------:|:------------:|:----------:|
| comtrade_bilateral | 682 | 4 | 808 |
| eurostat_nrg_bal_c | 355 | 1 | 115 |
| fao_fertilizer_consumption | 6 | 1 | 6 |
| resource_dependency_compose | — | 2 | 104 |

### Mart disponibili

**comtrade_bilateral:**
- `mart_trade_bilateral` — bilateral trade by HS6 × partner × flow
- `mart_trade_concentration` — HHI, top-1/3/5 share per risorsa × anno
- `mart_trade_balance` — balance (export - import), trade_position, export_coverage
- `mart_concentration_trend` — HHI trend, YoY change, trend_status

**eurostat_nrg_bal_c:**
- `mart_energy_balance` — production, imports, exports, dependency % per prodotto × anno

**resource_dependency_compose:**
- `mart_resource_dependency` — matrice unica: physical ID + HHI + data_source
- `mart_energy_vs_trade` — risk_profile per prodotti con both energy + trade data

### Dipendenza 2024 — Risorse con energy + trade

| Risorsa | Import ($) | HHI | Top supplier | Conc. | Physical ID % |
|---------|---:|:---:|---|:---:|:---:|
| Gas | $22.5B | 2945 | Algeria 48% | high | 95-102% |
| Rame | $1.3B | 3292 | Peru 34% | high | — |
| Ferro/acciaio | $868M | 3998 | Russia 46% | high | — |
| Fertilizzanti | $334M | 2770 | Russia 32% | medium | — |
| Alluminio | $328M | 2666 | Russia 40% | high | — |
| Elettricita | $2.0B | 10000 | — | high | — |
| Cobalto | $23M | 4172 | Germany 46% | high | — |
| Terre rare | $2.4M | 3651 | China 54% | high | — |
| Litio | $1M | 9320 | Germany 96% | high | — |

### Nuovi energy-only products (2024)

| Prodotto | Production (KTOE) | Import (KTOE) | Import Dep % |
|----------|---:|---:|:---:|
| Petrolio greggio | 5,228 | 71,977 | 95% |
| Gasolio | — | — | — |
| Coke | 0 | 105 | 100% |
| Rinnovabili total | — | — | 8-10% |
| Geotermico | — | — | 0% |
| Eolico | — | — | 0% |

### Trade balance — net exporter/importer

- **Net importer**: gas (-$59B), elettricita (-$1.8B), rame (-$1.2B), ferro (-$976M)
- **Net exporter**: terre rare (+$1.5M), alluminio (variabile)

### Concentration trend (2024 vs 2023)

- **Litio**: +3154 HHI (concentration_increasing)
- **Terre rare**: +856 HHI (concentration_increasing)
- **Rame**: +630 HHI (concentration_increasing)
- **Fertilizzanti**: +340 HHI (newly_concentrated)
- **Cobalto**: -453 HHI (concentration_decreasing)

---

## Cosa manca

### Fatto oggi

| # | Cosa | Stato |
|---|------|-------|
| 1 | Espansione Eurostat: 3 → 23 prodotti SIEC | ✅ |
| 2 | Trade balance mart (export - import) | ✅ |
| 3 | Concentration trend (YoY HHI change) | ✅ |
| 4 | Compose aggiornato con data_source + energy-only | ✅ |

### Prossimi passi

| # | Cosa | Sforzo | Note |
|---|------|--------|------|
| 5 | **OECD TiVA** — FVA/DVA per decomposizione valore | Medio | Bulk download gratuito |
| 6 | **USGS Minerali** — production data per metalli critici | Basso | PDF parsing |
| 7 | **FAO live API** — sostituire hardcoded con dati freschi + breakdown | Medio | API fenixservices attualmente giù (521) |
| 8 | **Dashboard Streamlit** | ✅ v1 | `dashboard/` su branch `feat/dashboard-v1` — 5 pagine, GCS + fallback locale |

### backlog

| # | Cosa | Sforzo |
|---|------|--------|
| 9 | Ownership analysis (ISTAT Multinazionali) | Medio |
| 10 | Upstream dependency (IO tables) | Alto |
| 11 | Farmaci/API | Alto |
| 12 | Semiconduttori | Alto |

---

## Dashboard

Stato: **v1 implementata** su `feat/dashboard-v1` (locale, non ancora PR).

| Voce | Dettaglio |
|------|-----------|
| Path | `dashboard/` |
| Standard | Streamlit + lab-connectors (`infra/lab-ops/standards/dashboard.md`) |
| Pagine | Panoramica · Dipendenze · Commercio · Energia · Query SQL |
| Dati | GCS `italia_dipendenze/` + fallback `out/data/` |
| Anno path | toolkit `2026/` · anni dati 2020–2024 |
| Test | `dashboard/tests/test_dashboard_smoke.py` (py_compile) |
| Avvio | `streamlit run dashboard/app.py` (extra `dashboard` nel pyproject) |

Caveat esposti in UI: `physical_id_pct` solo su prodotti energetici; valori Comtrade in USD; `risk_profile` distingue esplicitamente "HHI non disponibile" da "bassa dipendenza" (fix 2026-10-05 sul SQL compose + rebuild mart locale).

---

## Come funziona il pipeline

```
make all
  ├── make run-all
  │     ├── batch.txt: datasets prima, compose dopo
  │     ├── toolkit run --batch batch.txt
  │     │     ├── raw: script fetch dati da API
  │     │     ├── clean: SQL normalizzazione
  │     │     └── mart: SQL aggregazione + metriche
  │     └── compose: read_parquet dagli upstream
  └── make test
        └── pytest tests/ (10 smoke test)
```

### Dipendenze CI

| Secret | Servizio | Necessario per |
|--------|----------|----------------|
| `COMTRADE_SUBSCRIPTION_KEY` | UN Comtrade API | Fetch dati bilateral |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | GCS | Sync parquet su GCS |
| `GCP_SERVICE_ACCOUNT` | GCS | Auth per sync |
