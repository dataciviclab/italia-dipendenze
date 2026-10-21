# Materie Prime — Stato e Da Farsi

**Data**: 2026-10-21
**Repo**: `dataciviclab/italia-dipendenze` (git)

---

## Stato attuale

Pipeline funzionante: `make clean && make run-all && make test`
- 4/4 dataset SUCCESS, 40 test (38 pass, 2 skip)
- Eurostat **dichiarativo** (`type: sdmx` + codelist SIEC/NRG_BAL); Comtrade e FAO via script
- Zero CSV committati

### Ordine esecuzione

```
comtrade (~48s) → eurostat (~4s) → fao (~1.5s) → compose (~0.5s)
```

### Fonti dati

| Fonte | Tipo | Key | Dati |
|-------|------|-----|------|
| Eurostat NRG_BAL_C | `sdmx` (ESTAT, dichiarativo) | No | Bilancio fisico Italia, 25 prodotti SIEC, 16 indicatori, 1990-2024 |
| UN Comtrade | script (comtradeapicall) | Sì | Commercio bilaterale HS6, 2020-2024, 13 risorse (gas split, petrolio, tutti i partner) |
| FAO | script (cached) | No | Consumo fertilizzanti, 2018-2023 |

### Output

| Dataset | Righe clean | Mart tabelle | Righe mart |
|---------|:-----------:|:------------:|:----------:|
| comtrade_bilateral | 8.064 | 3 | 8.194 |
| eurostat_nrg_bal_c | 11.235 | 2 | 1.645 |
| fao_fertilizer_consumption | 6 | 1 | 6 |
| resource_dependency_compose | — | 2 | 1.091 |

### Mart disponibili

**comtrade_bilateral:**
- `mart_trade_bilateral` — bilateral trade by HS6 × partner × flow
- `mart_trade_concentration` — HHI, top-1/3/5 share, trend e YoY change per risorsa × anno
- `mart_trade_balance` — balance (export - import), trade_position, export_coverage

**eurostat_nrg_bal_c:**
- `mart_energy_balance` — produzione, import, export, scorte, GIC, `TO`, disponibilità interna, dipendenza netta/lorda, quota domestica
- `mart_energy_final_consumption` — consumi finali per prodotto × settore (industria, trasporti, famiglie, servizi, agricoltura, pesca, altro, non-energy)

**resource_dependency_compose:**
- `mart_resource_dependency` — matrice unica: dipendenza netta + HHI + data_source
- `mart_energy_vs_trade` — risk_profile per prodotti con energy e/o trade

### Dipendenza 2024 — Risorse con dati commerciali

| Risorsa | Import ($) | HHI | Top supplier | Conc. | Dipendenza netta % | Prezzo $/kg |
|---------|---:|:---:|---|:---:|:---:|---:|
| Petrolio greggio | $33.6B | 1215 | Libia 21% | low | 91,8 | 0,615 |
| Gas pipeline | $18.6B | 3315 | Algeria 51% | high | 95,2 | 0,585 |
| Prodotti petroliferi | $11.9B | 843 | Arabia Saudita 23% | low | 93,9 | 0,803 |
| Rame | $6.2B | 874 | Bulgaria 15% | low | — | — |
| Elettricità | $5.6B | 3198 | Svizzera 41% | high | 15,8 | — |
| Gas LNG | $5.5B | 3180 | Qatar 43% | high | 95,2 | 0,516 |
| Alluminio | $3.4B | 562 | Mozambico 11% | low | — | — |
| Ferro/acciaio | $1.6B | 1463 | Russia 25% | low | — | 0,602 |
| GPL | $1.3B | 3892 | Algeria 59% | high | 56,1 | — |
| Fertilizzanti | $1.1B | 853 | Egitto 19% | low | — | — |
| Cobalto | $44M | 1595 | Germania 24% | medium | — | 46,64 |
| Terre rare | $6.1M | 1247 | Cina 21% | low | — | 15,96 |
| Litio | $1.9M | 3561 | Germania 54% | high | — | 12,88 |

**Nota HHI**: tutti i partner Comtrade (7 pipeline, 26 LNG, 39 GPL); il denominatore è il totale import italiano, non un paniere pre-selezionato.

**Nota gas**: pipeline e LNG condividono la dipendenza fisica del gas (95,2%) ma hanno concentrazioni diverse (HHI 3315 vs 3180, entrambe >2500). GPL è un prodotto separato (56,1%). Il prezzo è valore/peso netto Comtrade, non un prezzo di mercato.

### Prodotti energetici 2024 — dipendenza e consumi

| Prodotto | Dipendenza netta % | Import (KTOE) | Consumo finale (KTOE) |
|----------|---:|---:|---:|
| Petrolio e prodotti (excl. biofuel) | 93,9 | 73.674 | 40.918 |
| Petrolio greggio | 91,8 | 56.051 | — |
| Gas naturale | 95,2 | 48.699 | 29.899 |
| Carbone e solidi fossili | 96,5 | 2.481 | — |
| Gasolio | -8,2 (net exporter raffinati) | 5.943 | 25.647 |
| Benzina | -60,4 (net exporter raffinati) | 742 | 8.956 |
| GPL | 56,1 | 2.802 | — |
| Cherosene jet | 47,6 | 2.678 | — |
| Olio combustibile | -210,2 (net exporter) | 726 | — |
| Coke | -22,4 | 70 | — |
| Elettricità | 15,8 | 4.807 | — |
| Rinnovabili e biocarburanti | 6,1 | 2.233 | — |
| **Totale energia** | **75,1** | 131.894 | — |

Il gasolio e la benzina sono **prodotti secondari**: la loro disponibilità è la produzione delle raffinerie (`TO`), non la produzione primaria. La dipendenza netta negativa indica che l'Italia esporta più raffinati di quanti ne importi; la vulnerabilità esterna resta sul **greggio** (91,8%). La quota domestica può superare 100% per i prodotti esportati.

**Nota di quadratura.** Per il petrolio il ricalcolo `PPRD + IMP − EXP + STK_CHG` dà 89,8%, il GIC ufficiale 93,9%: la differenza (≈2.356 KTOE) sono bunker internazionali e rettifiche statistiche. Il mart usa il GIC ufficiale.

### Trade balance — net exporter/importer

- **Net importer**: petrolio greggio (-$32,9 mld), gas pipeline (-$18,4 mld), LNG (-$5,4 mld), elettricità (-$5,1 mld), rame (-$4,6 mld), GPL (-$1,2 mld), alluminio (-$1,7 mld), ferro/acciaio (-$1,3 mld)
- **Net exporter**: prodotti petroliferi (+$4,9 mld), terre rare (+$3 mln)

### Concentration trend (2024 vs 2023)

- **Litio**: +1367 HHI (newly_concentrated)
- **GPL**: +568 HHI (concentration_increasing)
- **Gas LNG**: +529 HHI (concentration_increasing)
- **Prodotti petroliferi**: -186 HHI (diversification_improving)
- **Terre rare**: -169 HHI (diversification_improving)

---

## Cosa manca

### Fatto oggi (2026-10-20)

| # | Cosa | Stato |
|---|------|-------|
| 1 | Migrazione Eurostat da script a `type: sdmx` (3 richieste, 176 LOC rimosse) | ✅ |
| 2 | Etichette SIEC/NRG_BAL da codelist (niente più O4640 = "gasolio") | ✅ |
| 3 | Dipendenza su GIC ufficiale + `TO`; segno `STK_CHG` corretto | ✅ |
| 4 | Consumi finali per prodotto × settore (`mart_energy_final_consumption`) | ✅ |
| 5 | Compose allineato a dipendenza netta e nuove etichette | ✅ |
| 6 | Trade balance + concentration trend | ✅ |
| 7 | **Comtrade tutti i partner** — HHI su totale import, non su 8 | ✅ | 7 pipeline, 26 LNG, 39 GPL, 36 greggio, 73 raffinati |
| 8 | **HS 2709/2710** — valore, peso, prezzo implicito, concentrazione petrolio | ✅ | greggio + raffinati separati |
| 9 | **QA `TO` elettricità vs Terna** | ✅ | 23.303 vs 23.302 KTOE (2024) |
| 10 | **Fix segno `STK_CHG`** — GIC ufficiale (`+ STK_CHG`) | ✅ | gas 2022 99,2%, carbone 96,5% |
| 11 | **Split gas pipeline/LNG/GPL + prezzo $/kg** | ✅ | HHI 3315 pipeline, 3180 LNG |

### Prossimi passi

| # | Cosa | Sforzo | Note |
|---|------|--------|------|
| 12 | **QA `TO` raffinazione** — confronto con ISPRA/UNFCCC | Medio | benzina, gasolio, jet, olio combustibile |
| 13 | **OECD TiVA** — FVA/DVA per decomposizione valore | Medio | Bulk download gratuito |
| 14 | **USGS Minerali** — production data per metalli critici | Basso | PDF parsing |
| 15 | **FAO live API** — sostituire hardcoded con dati freschi + breakdown | Medio | API fenixservices attualmente giù (521) |

### Backlog

| # | Cosa | Sforzo |
|---|------|--------|
| 16 | Ownership analysis (ISTAT Multinazionali) | Medio |
| 17 | Upstream dependency (IO tables) | Alto |
| 18 | Farmaci/API | Alto |
| 19 | Semiconduttori | Alto |

---

## Dashboard

Stato: **v1 merged** (dashboard Streamlit + lab-connectors).

| Voce | Dettaglio |
|------|-----------|
| Path | `dashboard/` |
| Standard | Streamlit + lab-connectors (`infra/lab-ops/standards/dashboard.md`) |
| Pagine | Panoramica · Dipendenze · Commercio · Energia · Query SQL |
| Dati | GCS `italia_dipendenze/` + fallback `out/data/` |
| Anno path | toolkit `2026/` · energia 1990–2024 · commercio 2020–2024 |
| Test | `dashboard/tests/` + `tests/test_energy_regression.py` + `tests/test_trade_regression.py` + `tests/test_risk_profile.py` |
| CI | `check.yml`: pytest tests + dashboard smoke + dataset-config-check |
| Avvio | `streamlit run dashboard/app.py` (extra `dashboard` nel pyproject) |

Caveat esposti in UI: `physical_id_pct` = dipendenza **netta**; prodotti secondari calcolati su `TO`; valori Comtrade in USD e su tutti i partner; `risk_profile` distingue "HHI non disponibile", "dati insufficienti" e "bassa dipendenza".

**Post-merge**: registry e GCS vengono rigenerati dalla CI; il PR non include `registry/registry.json`.

---

## Come funziona il pipeline

```
make all
  ├── make run-all
  │     ├── batch.txt: datasets prima, compose dopo
  │     ├── toolkit run --batch batch.txt
  │     │     ├── raw: sdmx/script fetch dati da API
  │     │     ├── clean: SQL normalizzazione + codelist
  │     │     └── mart: SQL aggregazione + metriche
  │     └── compose: read_parquet dagli upstream
  └── make test
        └── pytest tests/ dashboard/tests/ (40 test)
```

### Dipendenze CI

| Secret | Servizio | Necessario per |
|--------|----------|----------------|
| `COMTRADE_SUBSCRIPTION_KEY` | UN Comtrade API | Fetch dati bilateral |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | GCS | Sync parquet su GCS |
| `GCP_SERVICE_ACCOUNT` | GCS | Auth per sync |
