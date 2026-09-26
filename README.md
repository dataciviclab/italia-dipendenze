# Materie Prime

Pipeline dati sulle dipendenze strategiche dell'Italia.

## Quick start

```bash
# Prima run (fetch + pipeline + test)
COMTRADE_SUBSCRIPTION_KEY=xxx make all

# Solo pipeline (dati già fetchati)
make run-all

# Solo test
make test

# Pulizia
make clean
```

## Pipeline

```
comtrade (script) ────────┐
eurostat (script) ─────────┼──→ compose
fao (script) ──────────────┘
```

| Dataset | Source | Mart | Test |
|---------|--------|:---:|:---:|
| `eurostat-nrg-bal-c` | Eurostat SDMX API | 1 | ✅ |
| `comtrade-bilateral` | UN Comtrade API | 2 | ✅ |
| `fao-fertilizer-consumption` | FAO cached | 1 | ✅ |
| `resource-dependency-compose` | Compose (join) | 2 | ✅ |

## Dati

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

### Metriche

| Metrica | Formula | Stato |
|---------|---------|:---:|
| Gross Import Dependency | Imports / (P + I - X) | ✅ Gas |
| HHI | Σ(share_i²) | ✅ 9 risorse |
| Top-N Share | Quota primi N fornitori | ✅ 9 risorse |
| Risk Profile | ID + HHI | ✅ |

## Struttura

```
materie-prime/
├── datasets/
│   ├── eurostat-nrg-bal-c/          script → clean → mart
│   ├── comtrade-bilateral/          script → clean → mart + concentration
│   └── fao-fertilizer-consumption/  script → clean → mart
├── compose/
│   └── resource-dependency-compose/ join dei 3 upstream
├── scripts/
│   ├── fetch_eurostat_energy.py     Eurostat SDMX → CSV
│   ├── fetch_comtrade.py            Comtrade API → CSV
│   └── download_fao_fertilizer.py   FAO cached data
├── tests/test_smoke.py
├── conftest.py
├── Makefile
├── pyproject.toml
├── .github/workflows/
│   ├── check.yml                    config validation
│   ├── pipeline.yml                 run + GCS sync + registry
│   └── test-audit.yml               marker audit
└── registry/registry.json
```

## Dipendenze

| Secret | Per |
|--------|-----|
| `COMTRADE_SUBSCRIPTION_KEY` | Fetch dati Comtrade (gratuita con registrazione) |

## License

MIT
