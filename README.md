# Italy Resource & Dependency Map — Pilot Dataset v0.1

**Data**: 2026-09-24
**Status**: MVP completo — 3 fonti, 4 dataset, 9 risorse, 8/8 test passano

---

## Pipeline

```
eurostat-nrg-bal-c ─────┐
comtrade-bilateral ──────┼──→ resource-dependency-compose
fao-fertilizer-consumption┘
```

| Dataset | Source type | Toolkit | Mart | Test |
|---------|-----------|:---:|:---:|:---:|
| `eurostat-nrg-bal-c` | local_file | ✅ | 1 | ✅ |
| `comtrade-bilateral` | local_file | ✅ | 2 | ✅ |
| `fao-fertilizer-consumption` | script | ✅ | 1 | ✅ |
| `resource-dependency-compose` | compose | ✅ | 2 | ✅ |

### Note su Comtrade

UN Comtrade: `comtradeapicall` (pip, MIT license). Con subscription key gratuita: 5000 calls/giorno, multi-periodo, 250K record/call.

---

## Dati prodotti

### Matrice dipendenza 2024 (9 risorse, 2020-2024)

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
| Carbone | — | — | — | — |

### Gas (2020-2024, physical ID)

| Anno | Import (KTOE) | Prod (KTOE) | Disponibilità | Import Dep | HHI | Top supplier |
|:---:|---:|---:|---:|:---:|:---:|---|
| 2020 | 54.375 | 3.287 | 57.405 | 94.7% | — | — |
| 2021 | 59.784 | 2.608 | 61.127 | 97.8% | — | — |
| 2022 | 59.453 | 2.544 | 58.218 | 102.1% | 2090 | Algeria 29% |
| 2023 | 50.634 | 2.215 | 50.703 | 99.9% | 2971 | Algeria 49% |
| 2024 | 48.699 | 2.124 | 50.316 | 96.8% | 2945 | Algeria 48% |

### Fertilizzanti (2022-2024)

| Anno | Import ($) | Consumo (t) | HHI | Top supplier |
|:---:|---:|---:|:---:|---|
| 2022 | $478M | 807K | 2242 | Russia 29% |
| 2023 | $320M | 808K | 2431 | Germany 37% |
| 2024 | $268M | 808K | 2458 | Russia 39% |

### Rame (2022-2024)

| Anno | Import ($) | HHI | Top supplier | Top-3 share |
|:---:|---:|:---:|---|---:|
| 2022 | $1.264M | 2963 | DRC 43% | 85% |
| 2023 | $1.035M | 3608 | Peru 48% | 99% |
| 2024 | $1.307M | 3314 | Peru 35% | 100% |

### Risk Profile (compose)

| Risorsa | Risk Profile | ID fisica | HHI |
|---------|-------------|:---:|:---:|
| Gas 2023-2024 | critical_high_concentration | >90% | >2500 |
| Gas 2022 | critical_diversified | >90% | <2500 |
| Fertilizzanti | moderate (no physical ID) | — | 2070-2458 |
| Rame | high_concentration | — | 2963-3608 |
| Ferro/acciaio | high_concentration | — | 3785-4077 |
| Alluminio | high_concentration | — | 2666-3073 |
| Cobalto | high_concentration | — | 4172-5351 |
| Terre rare | high_concentration | — | 2796-3670 |
| Litio | extreme_concentration | — | 5452-9320 |

---

## Limitazioni note

### Comtrade API

L'API free tier ha limiti stretti (500 calls/giorno, 1 periodo alla volta). Con la subscription key (gratuita) si accede a `getFinalData` con 5000 calls/giorno e multi-periodo. Il package `comtradeapicall` gestisce tutto.

### Dati mancanti

| Gap | Impatto | Workaround |
|-----|---------|------------|
| Elettricità: solo 4 righe | Dati HS 2716 incompleti | Usare Eurostat NRG_BAL_C o ENTSO-G |
| Fertilizzanti: Marocco/Tunisia mancanti | Concentrazione sottostimata | Aggiungere supplier |
| Rame: produzione/consumo non disponibile | ID non calcolabile | Ricostruire da trade balance |
| Carbone: nessun dato Comtrade | Concentrazione non calcolabile | Usare solo Eurostat |
| Nessun dato upstream | FID/UD non calcolabili | Richiede IO tables |

### Fonti non incluse

| Fonte | Status | Nota |
|-------|--------|------|
| OECD TiVA | Non incluso | FVA/DVA disponibile, da aggiungere |
| USGS Minerali | Non incluso | Production data per metalli critici |
| ISTAT Multinazionali | Non incluso | Ownership analysis, da aggiungere |

---

## File struttura

```
dipendenze-risorse/
├── datasets/
│   ├── eurostat-nrg-bal-c/
│   │   ├── dataset.yml
│   │   └── sql/{clean,mart_energy_balance}.sql
│   ├── comtrade-bilateral/
│   │   ├── dataset.yml
│   │   └── sql/{clean,mart_trade_bilateral,mart_trade_concentration}.sql
│   ├── fao-fertilizer-consumption/
│   │   ├── dataset.yml
│   │   └── sql/{clean,mart_fertilizer_consumption}.sql
│   └── resource-dependency-compose/
│       ├── dataset.yml
│       └── sql/{mart_resource_dependency,mart_energy_vs_trade}.sql
├── scripts/
│   ├── fetch_comtrade.py (custom, per reference)
│   ├── fetch_comtrade_incremental.py (per fetch lunghi)
│   ├── fetch_eurostat_energy.py
│   ├── download_fao_fertilizer.py
│   └── compute_concentration.py
├── tests/test_smoke.py
├── Makefile
├── batch.txt
├── pyproject.toml
├── README.md
├── CONTRIBUTING.md
├── LICENSE (MIT)
├── .github/workflows/ci.yml
└── out/
    ├── raw/{comtrade,eurostat,fao}/
    └── data/mart/*/
```

---

## Prossimi passi

1. **Aggiungere export data** — calcolare trade balance (import - export)
2. **OECD TiVA** — aggiungere FVA/DVA per decomposizione valore
3. **USGS Minerali** — dati production per metalli critici
4. **Ownership analysis** — ISTAT Multinazionali per dipendenza proprietaria
5. **Dashboard** — Streamlit per visualizzazione interattiva

---

*Dati generati da script riproducibili. Ogni numero ha source + method + data_quality.*
