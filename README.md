# Italia Dipendenze

**Quanto dipende l'Italia dall'estero per le risorse che tiene in funzione?**

La Italy Resource & Dependency Map è un sistema aperto che misura le principali risorse strategiche italiane: quanto ne importiamo, da chi dipendiamo, quanto è concentrata la fornitura.

| Risorse coperte | Periodo | Fonti dati | Aggiornamento |
|:---:|:---:|:---:|:---:|
| 25 prodotti energetici + 11 risorse commerciali | energia 1990–2024 · commercio 2020–2024 | Eurostat, UN Comtrade, FAO | Pipeline automatica |

---

## Perché questi dati

L'Italia dipende dall'estero per oltre il 90% di gas e petrolio e per circa il 100% del carbone. Capire **da chi** dipendiamo e **quanto è concentrata** quella dipendenza è il primo passo per valutare la resilienza del sistema paese.

Questi dati rendono visibili le catene di dipendenza materiale dell'Italia.

---

## Cosa contengono

| Area | Dati | Righe | Metriche |
|------|------|:---:|----------|
| Bilancio energetico | 25 prodotti SIEC × 16 indicatori (flussi, GIC, TO, consumi finali) | 875 | dipendenza netta/lorda, disponibilità interna, quota domestica |
| Consumi finali | 25 prodotti × 10 settori (industria, trasporti, famiglie, …) | 770 | consumi finali per prodotto e settore |
| Commercio bilaterale | Import/export per HS6 × paese × anno | 7389 | HHI, Top-1/3/5 share |
| Trade balance | Balance = export - import per risorsa × anno | 55 | trade_position, export_coverage |
| Concentration trend | HHI trend + YoY change | 55 | trend_status, hhi_change |
| Fertilizzanti | Consumo Italia | 6 | Consumo totale |
| Compose | Matrice unica: ID + concentrazione per risorsa | 801 + 210 | data_source, risk_profile |

### Risorse monitorate

| Risorsa | Import 2024 | Concentrazione (HHI) | Top fornitore |
|---------|---:|:---:|---|
| Petrolio greggio | $33.6B | 1215 | Libia (21%) |
| Gas naturale | $25.3B | 2397 | Algeria (43%) |
| Prodotti petroliferi | $11.9B | 843 | Arabia Saudita (23%) |
| Rame | $6.2B | 874 | Bulgaria (15%) |
| Elettricità | $5.6B | 3198 | Svizzera (41%) |
| Alluminio | $3.4B | 562 | Mozambico (11%) |
| Ferro/acciaio | $1.6B | 1463 | Russia (25%) |
| Fertilizzanti | $1.1B | 853 | Egitto (19%) |
| Cobalto | $44M | 1595 | Germania (24%) |
| Terre rare | $6.1M | 1247 | Cina (21%) |
| Litio | $1.9M | 3561 | Germania (54%) |

**Nota HHI.** Il calcolo usa tutti i partner Comtrade (47 per il gas, 36 per il greggio, 73 per i raffinati): il denominatore è il totale import italiano, non un paniere pre-selezionato.

### Bilancio energetico (2024)

| Prodotto | Dip. netta % | Dip. lorda % | Import (KTOE) |
|----------|:---:|:---:|---:|
| Petrolio e prodotti (excl. biofuel) | 92,7 | 141,1 | 73,674 |
| Gas naturale | 96,4 | 97,4 | 48,699 |
| Carbone e solidi fossili | 103,7 | 115,7 | 2,481 |
| Rinnovabili e biocarburanti | 6,1 | 7,5 | 2,233 |
| Coke | -27,1 | 11,5 | 70 |

**Come si legge.** Dipendenza netta = (import − export) / disponibilità interna. La disponibilità include la produzione primaria e, per i prodotti secondari (elettricità, gasolio, benzina, GPL, cherosene, olio combustibile, coke), la produzione delle trasformazioni (`TO`). La dipendenza lorda = import / disponibilità è solo diagnostica: sul petrolio somma greggio importato e prodotti raffinati esportati, quindi non è una misura di dipendenza. Il 102,1% del gas 2022 della versione precedente era un artefatto della formula senza scorte: il valore corretto è **92,3% netto** (98,5% lordo). Totale energia 2024: **75,2% netto**.

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
eurostat (sdmx) ──────────┼──→ compose
fao (script) ──────────────┘
```

Il toolkit fetcha i dati freschi dalle API (Eurostat via `type: sdmx`, con codelist SIEC/NRG_BAL), li processa (clean → mart), il compose li unisce in una matrice unica.

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
