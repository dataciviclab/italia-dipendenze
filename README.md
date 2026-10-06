# Italia Dipendenze

**Quanto dipende l'Italia dall'estero per le risorse che tiene in funzione?**

La Italy Resource & Dependency Map è un sistema aperto che misura le principali risorse strategiche italiane: quanto ne importiamo, da chi dipendiamo, quanto è concentrata la fornitura.

| Risorse coperte | Periodo | Fonti dati | Aggiornamento |
|:---:|:---:|:---:|:---:|
| 23 prodotti energetici + 9 risorse commerciali | 2020–2024 | Eurostat, UN Comtrade, FAO | Pipeline automatica |

---

## Perché questi dati

L'Italia dipende per oltre il 95% dall'estero per gas, petrolio, carbone e metalli critici. Capire **da chi** dipendiamo e **quanto è concentrata** quella dipendenza è il primo passo per valutare la resilienza del sistema paese.

Questi dati rendono visibili le catene di dipendenza materiale dell'Italia.

---

## Cosa contengono

| Area | Dati | Righe | Metriche |
|------|------|:---:|----------|
| Bilancio energetico | 23 prodotti SIEC × 4 indicatori (produzione, import, export, stocks) | 115 | Gross Import Dependency, domestic share |
| Commercio bilaterale | Import/export per HS6 × paese × anno | 682 | HHI, Top-1/3/5 share |
| Trade balance | Balance = export - import per risorsa × anno | 45 | trade_position, export_coverage |
| Concentration trend | HHI trend + YoY change | 45 | trend_status, hhi_change |
| Fertilizzanti | Consumo Italia | 6 | Consumo totale |
| Compose | Matrice unica: ID + concentrazione per risorsa | 104 | data_source, risk_profile |

### Risorse monitorate

| Risorsa | Import 2024 | Concentrazione (HHI) | Top fornitore |
|---------|---:|:---:|---|
| Gas naturale | $22.5B | 2945 | Algeria (48%) |
| Rame | $1.3B | 3292 | Perù (34%) |
| Ferro/acciaio | $868M | 3998 | Russia (46%) |
| Fertilizzanti | $334M | 2770 | Russia (32%) |
| Alluminio | $328M | 2666 | Russia (40%) |
| Elettricita | $2.0B | 10000 | — |
| Cobalto | $23M | 4172 | Germany (46%) |
| Terre rare | $2.4M | 3651 | China (54%) |
| Litio | $1M | 9320 | Germany (96%) |

### Bilancio energetico (2024)

| Prodotto | Import dep % | Import (KTOE) |
|----------|:---:|---:|
| Petrolio (excl. biofuel) | 143% | 73,674 |
| Gas naturale | 102% | 48,699 |
| Carbone | 111% | 2,481 |
| Rinnovabili | 8% | 2,233 |
| Coke | 100% | 105 |

---

## Esempi di domande

- Da quali paesi dipende l'Italia per il gas naturale?
- Quanto è concentrata la fornitura di rame?
- Quali risorse hanno concentrazione >2500 HHI (alto rischio)?
- Come è cambiata la dipendenza dal gas dopo il 2022?
- Quali metalli critici ha l'Italia e da chi li compra?
- L'Italia è net exportatrice o importatrice di alluminio?
- La concentrazione del litio è in aumento?

---

## Come accedere

**Dashboard:**
```bash
pip install -e ".[dashboard]"
streamlit run dashboard/app.py
# oppure: make dashboard
```
Pagine: Panoramica, Dipendenze, Commercio, Energia, Query SQL. Dati da GCS (`italia_dipendenze/`) con fallback su `out/data/`.

**Pipeline locale:**
```bash
COMTRADE_SUBSCRIPTION_KEY=xxx make all
```

**Dati:**
- Parquet in `out/data/mart/` dopo il pipeline
- Registry in `registry/registry.json`
- GCS: `gs://dataciviclab-mart/italia_dipendenze/` e `gs://dataciviclab-clean/italia_dipendenze/`

**Fonti:**
- Eurostat NRG_BAL_C (SDMX API, no key)
- UN Comtrade (API con key gratuita)
- FAO (dati cached)

---

## Come funziona

```
comtrade (script) ────────┐
eurostat (script) ─────────┼──→ compose
fao (script) ──────────────┘
```

Lo script fetcha i dati freschi dalle API, il toolkit li processa (clean → mart), il compose li unisce in una matrice unica.

---

## Approfondimenti

- [Discussion](https://github.com/dataciviclab/italia-dipendenze/discussions) — domande, idee, contribuzioni
- [STATUS.md](STATUS.md) — stato dettagliato e da farsi

---

## Partecipa

- Apri una [Discussion](https://github.com/dataciviclab/italia-dipendenze/discussions) per segnalare fonti, suggerire risorse, o chiedere analisi
- Leggi [CONTRIBUTING.md](CONTRIBUTING.md) per contribuire al codice

---

## License

[MIT](LICENSE)

[![check](https://github.com/dataciviclab/italia-dipendenze/actions/workflows/check.yml/badge.svg)](https://github.com/dataciviclab/italia-dipendenze/actions/workflows/check.yml)
