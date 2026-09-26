# Materie Prime — Stato e Da Farsi

**Data**: 2026-09-26
**Repo**: `esperimenti-locali/italia-dipendenze` (git, commit 2a9092b)

---

## Stato attuale

Pipeline funzionante: `make clean && make run-all && make test`
- 4/4 dataset SUCCESS, 8/8 test passano
- Fetch dati da API (Eurostat SDMX, Comtrade comtradeapicall, FAO cached)
- Zero CSV committati, tutto script-based

### Ordine esecuzione

```
comtrade (52s) → eurostat (15s) → fao (2s) → compose (0.5s)
```

### Fonti dati

| Fonte | Tipo | Key | Dati |
|-------|------|-----|------|
| Eurostat NRG_BAL_C | script (SDMX API) | No | Bilancio fisico Italia, 2020-2024 |
| UN Comtrade | script (comtradeapicall) | Sì | Commercio bilaterale HS6, 2020-2024, 9 risorse |
| FAO | script (cached) | No | Consumo fertilizzanti, 2018-2023 |

### Matrice dipendenza 2024

| Risorsa | Import ($) | HHI | Top supplier | Concentrazione |
|---------|---:|:---:|---|:---:|
| Gas | $22.5B | 2945 | Algeria 48% | high |
| Rame | $1.3B | 3192 | Peru 34% | high |
| Ferro/acciaio | $868M | 3998 | Russia 46% | high |
| Fertilizzanti | $334M | 2070 | Russia 32% | medium |
| Alluminio | $328M | 2666 | Russia 40% | high |
| Cobalto | $23M | 4172 | Germany 46% | high |
| Terre rare | $2.4M | 3651 | China 54% | high |
| Litio | $1M | 9320 | Germany 96% | high |

---

## Cosa manca

### Prima di pushare su GitHub

| # | Cosa | Sforzo | Note |
|---|------|--------|------|
| 1 | **Aggiornare README** con dati aggiornati e istruzioni `make all` | Basso | |
| 2 | **Aggiornare STATUS.md** (questo file) | Basso | |
| 3 | **Creare repo GitHub** `dataciviclab/italia-dipendenze` | Basso | |

### Dopo il push

| # | Cosa | Sforzo | Note |
|---|------|--------|------|
| 4 | **Estendere gas/fertilizzanti a 2020-2024 con concentrazione** | Basso | Già nel Comtrade, basta verificare |
| 5 | **Aggiungere export data** per trade balance | Basso | Le query Comtrade già chiedono M+X |
| 6 | **OECD TiVA** — FVA/DVA per decomposizione valore | Medio | Bulk download gratuito |
| 7 | **USGS Minerali** — production data per metalli critici | Basso | PDF parsing |
| 8 | **Dashboard Streamlit** | Medio | Dopo consolidatezza |

### backlog

| # | Cosa | Sforzo |
|---|------|--------|
| 9 | Ownership analysis (ISTAT Multinazionali) | Medio |
| 10 | Upstream dependency (IO tables) | Alto |
| 11 | Farmaci/API | Alto |
| 12 | Semiconduttori | Alto |

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
        └── pytest tests/ (8 smoke test)
```

### Dipendenze CI

| Secret | Servizio | Necessario per |
|--------|----------|----------------|
| `COMTRADE_SUBSCRIPTION_KEY` | UN Comtrade API | Fetch dati bilateral |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | GCS | Sync parquet su GCS |
| `GCP_SERVICE_ACCOUNT` | GCS | Auth per sync |
