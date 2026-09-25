# Italy Resource & Dependency Map — Stato e Da Farsi

**Data**: 2026-09-25
**Repo**: `esperimenti-locali/dipendenze-risorse` (git, commit d963c6f)

---

## Cosa c'è adesso

Pipeline completa con toolkit, 4 dataset, 9 risorse, dati reali 2020-2024.

### Architettura

```
eurostat-nrg-bal-c ─────┐
comtrade-bilateral ──────┼──→ resource-dependency-compose
fao-fertilizer-consumption┘
```

### Fonti dati

| Fonte | Accesso | Dati |
|-------|---------|------|
| Eurostat NRG_BAL_C | local_file (pre-fetched) | Bilancio fisico Italia, 2020-2024 |
| UN Comtrade API | `comtradeapicall` + key | Commercio bilaterale HS6, 2020-2024, 9 risorse |
| FAO | script (cached data) | Consumo fertilizzanti, 2018-2023 |

### Risorse coperte

| Risorsa | Import ($) 2024 | HHI | Top supplier | Concentrazione |
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

### Metriche calcolate

| Metrica | Formula | Stato |
|---------|---------|:---:|
| Gross Import Dependency | Imports / (P + I - X) | ✅ Gas |
| HHI (Herfindahl) | Σ(share_i²) | ✅ 9 risorse |
| Top-N Share | Quota primi N fornitori | ✅ 9 risorse |
| Risk Profile | ID + HHI → critical/moderate/low | ✅ |
| Import Coverage Ratio | Production / Imports | ✅ Gas |

### Qualità dati

| Risorsa | Physical ID | Concentrazione | Data Quality |
|---------|:---:|:---:|---|
| Gas | ✅ Eurostat | ✅ Comtrade | A (verified) |
| Fertilizzanti | — | ✅ Comtrade | B (constructed) |
| Rame | — | ✅ Comtrade | B (constructed) |
| Alluminio | — | ✅ Comtrade | B (constructed) |
| Ferro/acciaio | — | ✅ Comtrade | B (constructed) |
| Cobalto | — | ✅ Comtrade | B (constructed) |
| Terre rare | — | ✅ Comtrade | B (constructed) |
| Litio | — | ✅ Comtrade | B (constructed) |
| Elettricità | — | ⚠️ 4 righe | C (incomplete) |

### Infrastruttura

- ✅ Toolkit pipeline (4 dataset, clean/mart SQL)
- ✅ 8/8 smoke test (marker @pytest.mark.smoke)
- ✅ Makefile (run, check, test, clean)
- ✅ CI workflow (.github/workflows/ci.yml)
- ✅ pyproject.toml (template 2 Data+SQL)
- ✅ LICENSE (MIT), CONTRIBUTING.md, PR template
- ✅ .gitignore

---

## Cosa manca

### Priorità alta

| # | Cosa | Sforzo | Bloccato da |
|---|------|--------|-------------|
| 1 | **Metrica gas corretta** — documentare che `gross_import_dependency` può >100% per stock changes | Basso | Niente |
| 2 | **Estendere serie gas/fertilizzanti a 2020-2024** — gas 2020-2021 ha solo physical ID, non ha concentrazione | Basso | Niente |
| 3 | **Aggiungere export al Comtrade** — calcolare trade balance (import - export) | Basso | Niente |
| 4 | **Fix elettricità** — HS 2716 restituisce pochi dati, probabilmente non è la fonte giusta (ENTSO-G o Eurostat meglio) | Medio | Scelta fonte |

### Priorità media

| # | Cosa | Sforzo | Note |
|---|------|--------|------|
| 5 | **OECD TiVA** — aggiungere FVA/DVA per decomposizione valore | Medio | Dataset gratuito, bulk download |
| 6 | **USGS Minerali** — dati production per metalli critici | Basso | PDF, non API — va parsato |
| 7 | **Physical ID per tutte le risorse** — aggiungere produzione/consumo da fonti nazionali o stime | Alto | Dati frammentati |
| 8 | **Dashboard Streamlit** — visualizzazione interattiva | Medio | Dopo consolidatezza dati |

### Priorità bassa

| # | Cosa | Sforzo | Note |
|---|------|--------|------|
| 9 | **Ownership analysis** — ISTAT Multinazionali per dipendenza proprietaria | Medio | Lag 2-3 anni |
| 10 | **Upstream dependency** — IO tables per FID/UD | Alto | Richiede FIGARO, lag 2-5 anni |
| 11 | **Farmaci/API** — dati frammentati, supply chain complessa | Alto | Ricerca manuale |
| 12 | **Semiconduttori** — dati frammentati, supply chain estrema | Alto | Ricerca manuale |

---

## Problema aperto: Comtrade API

Il nostro `comtradeapicall` funziona, ma il fetch delle 6 nuove risorse ha prodotto solo dati 2020-2024 (non 2022-2024 come il gas iniziale). Il dataset `comtrade_bilateral.csv` ha ora 599 righe su 9 risorse × 5 anni.

**Da verificare**: il fetch del gas e fertilizzanti con il nuovo metodo (`comtradeapicall.getFinalData`) ha sovrascritto i dati precedenti. I dati 2020-2021 per gas e fertilizzanti ora hanno anche exports, ma la concentrazione (HHI) si calcola solo sulle imports.

---

## Decisioni aperte

1. **Repository GitHub**: creare `dataciviclab/dipendenze-risorse` o tenere locale?
2. **Comtrade key**: salvare in `.env` (già in .gitignore) o usare variabile d'ambiente CI?
3. **Fisical ID per metalli**: da fonti nazionali (USGS, ISTAT) o da trade balance calcolato?
4. **Dashboard**: quandola costruiamo?

---

## Prossimo passo concreto

Il più utile adesso è:
1. Verificare che il pipeline completo funzioni da zero (`make clean && make run-all && make test`)
2. Aggiungere export al dataset comtrade
3. Estendere gas/fertilizzanti a 2020-2024 con concentrazione
