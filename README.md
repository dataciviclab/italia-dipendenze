# Materie Prime

**Quanto dipende l'Italia dall'estero per le risorse che tiene in funzione?**

La Italy Resource & Dependency Map è un sistema aperto che misura le principali risorse strategiche italiane: quanto ne importiamo, da chi dipendiamo, quanto è concentrata la fornitura.

| Risorse coperte | Periodo | Fonti dati | Aggiornamento |
|:---:|:---:|:---:|:---:|
| 9 | 2020–2024 | Eurostat, UN Comtrade, FAO | Pipeline automatica |

---

## Perché questi dati

L'Italia dipende per oltre il 95% dall'estero per gas, rame, ferro, alluminio e terre rare. Capire **da chi** dipendiamo e **quanto è concentrata** quella dipendenza è il primo passo per valutare la resilienza del sistema paese.

Questi dati rendono visibili le catene di dipendenza materiale dell'Italia.

---

## Cosa contengono

| Area | Dati | Righe | Metriche |
|------|------|:---:|----------|
| Gas naturale | Bilancio fisico (produzione, import, export, stock) | 15 | Gross Import Dependency, domestic share |
| Commercio bilaterale | Import/export per HS6 × paese × anno | 599 | HHI, Top-1/3/5 share |
| Fertilizzanti | Consumo Italia + concentrazione fornitori | 6 | Consumo totale, HHI |
| Compose | Matrice unica: ID + concentrazione per risorsa | 47 | Risk profile |

### 9 risorse monitorate

| Risorsa | Import 2024 | Concentrazione (HHI) | Top fornitore |
|---------|---:|:---:|---|
| Gas naturale | $22,5B | 2945 | Algeria (48%) |
| Rame | $1,3B | 3192 | Perù (34%) |
| Ferro/acciaio | $868M | 3998 | Russia (46%) |
| Fertilizzanti | $334M | 2070 | Russia (32%) |
| Alluminio | $328M | 2666 | Russia (40%) |
| Cobalto | $23M | 4172 | Germania (46%) |
| Terre rare | $2,4M | 3651 | Cina (54%) |
| Litio | $1M | 9320 | Germania (96%) |

---

## Esempi di domande

- Da quali paesi dipende l'Italia per il gas naturale?
- Quanto è concentrata la fornitura di rame?
- Quali risorse hanno concentrazione >2500 HHI (alto rischio)?
- Come è cambiata la dipendenza dal gas dopo il 2022?
- Quali metalli critici ha l'Italia e da chi li compra?

---

## Come accedere

**Pipeline locale:**
```bash
COMTRADE_SUBSCRIPTION_KEY=xxx make all
```

**Dati:**
- Parquet in `out/data/mart/` dopo il pipeline
- Registry in `registry/registry.json`

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
