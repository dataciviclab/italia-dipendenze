# Italia Dipendenze

**Quanto dipende l'Italia dall'estero per le risorse che tiene in funzione?**

La Italy Resource & Dependency Map è un sistema aperto che misura le principali risorse strategiche italiane: quanto ne importiamo, da chi dipendiamo, quanto è concentrata la fornitura.

| Risorse coperte | Periodo | Fonti dati | Aggiornamento |
|:---:|:---:|:---:|:---:|
| 25 prodotti energetici + 14 risorse commerciali + 4 gruppi raffinati Comext | energia 1990–2024 · commercio 2020–2024 | Eurostat, Eurostat Comext, UN Comtrade, FAO | Pipeline automatica |

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
| Commercio bilaterale | Import/export per HS6 × paese × anno | 8596 | HHI, Top-1/3/5 share, prezzo $/kg |
| Trade balance | Balance = export - import per risorsa × anno | 70 | trade_position, export_coverage, unit value |
| Concentration trend | HHI trend + YoY change | 70 | trend_status, hhi_change |
| Fertilizzanti | Consumo Italia | 6 | Consumo totale |
| Raffinati Comext | 4 gruppi CN8 × anno × partner | 2086 clean · 40 mart | HHI, top fornitori, prezzo €/kg |
| Compose | Matrice unica: ID + concentrazione per risorsa | 906 + 315 + 105 | data_source, risk_profile |

### Risorse monitorate

| Risorsa | Import 2024 | Concentrazione (HHI) | Top fornitore | Prezzo $/kg |
|---------|---:|:---:|---|---:|
| Petrolio greggio | $33.6B | 1215 | Libia (21%) | 0,615 |
| Gas pipeline | $18.6B | 3315 | Algeria (51%) | 0,585 |
| Distillati medi | $10.6B | 986 | Arabia Saudita (25%) | 0,795 |
| Rame | $6.2B | 874 | Bulgaria (15%) | — |
| Elettricità | $5.6B | 3198 | Svizzera (41%) | — |
| Gas LNG | $5.5B | 3180 | Qatar (43%) | 0,516 |
| Alluminio | $3.4B | 562 | Mozambico (11%) | — |
| Ferro/acciaio | $1.6B | 1463 | Russia (25%) | 0,602 |
| Benzina | $1.36B | 1046 | Grecia (21%) | 0,866 |
| GPL | $1.3B | 3892 | Algeria (59%) | — |
| Fertilizzanti | $1.1B | 853 | Egitto (19%) | — |
| Cobalto | $44M | 1595 | Germania (24%) | 46,64 |
| Terre rare | $6.1M | 1247 | Cina (21%) | 15,96 |
| Litio | $1.9M | 3561 | Germania (54%) | 12,88 |

**Nota HHI.** Il calcolo usa tutti i partner Comtrade (7 per il gas pipeline, 26 per l'LNG, 39 per il GPL): il denominatore è il totale import italiano, non un paniere pre-selezionato.

**Nota gas.** Il gas è split in pipeline (`271121`), LNG (`271111`) e GPL (`271112/113/119`). La dipendenza fisica del gas resta 95,2% (bilancio), ma i due segmenti commerciali hanno HHI **3315** e **3180**, entrambi sopra 2500: l'aggregato precedente (2397) nascondeva questa differenza.

**Nota prezzo.** Il prezzo è il valore unitario medio all'import: valore / peso netto Comtrade. Non è un prezzo di mercato e non è disponibile per risorse senza peso (es. elettricità).

**Nota raffinati.** I raffinati sono split HS6: `271012` benzina (light oils) e `271019` distillati medi (gasolio/jet/fuel oil). L'aggregato fisico `distillati_medi` (gasolio+jet+fuel oil) è accoppiato al trade `271019`: **-7,8% netto**, HHI 986. `271019` resta un aggregato merceologico: **Comext** lo separa in gasolio, jet, olio combustibile e lubrificanti (tabella sotto). Benzina è net exporter (+$5,4 mld), distillati medi net importer (-$0,9 mld).

### Raffinati — Comext (2024)

| Gruppo | Import | Volume import | HHI import | Top import | Prezzo €/kg | Saldo |
|---|---:|---:|---:|---|---:|---:|
| Gasolio | €5,66 mld | 7,38 Mt | **1984** | Arabia Saudita 41% | 0,766 | +€0,21 mld |
| Jet | €2,13 mld | 2,87 Mt | 1127 | UAE 22% | 0,743 | -€1,91 mld |
| Olio combustibile | €0,97 mld | 2,28 Mt | 1649 | Algeria 35% | 0,423 | +€0,63 mld |
| Lubrificanti | €0,93 mld | 0,66 Mt | 1309 | Belgio 19% | 1,403 | +€0,30 mld |

**Nota Comext.** Fonte Eurostat `DS-045409`, valori in **euro** (Comtrade è in USD). Il solo HS6 `271019` (HHI 986, Arabia 25%) era una media: il **gasolio import** è il gruppo più concentrato (Arabia 41%, HHI 1984), il jet è più diversificato (HHI 1127). Gasolio e olio combustibile sono net exporter; il jet è net importer.

**Compose: dipendenza fisica + partner.** Il mart `mart_refined_dependency` unisce il fisico NRG_BAL_C e la concentrazione Comext per prodotto:

| Prodotto | Dipendenza fisica | HHI | Top fornitore |
|---|---:|---:|---|
| Gasolio | -8,2% | 1984 | Arabia Saudita 41% |
| Jet | 47,6% | 1127 | UAE 22% |
| Olio combustibile | -210,2% | 1649 | Algeria 35% |

**QA volumi (Comext vs bilancio energetico).** Import 2024: gasolio 7,38 Mt (Comext) vs 5,94 Mtoe (NRG_BAL_C), jet 2,87 vs 2,68, olio combustibile 2,28 vs 0,73. Il confronto mescola unità: **Mt = massa** (Comext) e **Mtoe = energia** (NRG_BAL_C); per i prodotti petroliferi 1 t ≈ 1,02 toe, quindi il rapporto è **indicativo**, non una quadratura di massa. I perimetri non coincidono (CN8 vs SIEC): sugli export l'olio combustibile combacia (3,43 vs 3,53 Mt), sull'import il divario è di perimetro. Inoltre i 4 gruppi non coprono tutto `271019`: restano fuori `2710 19 11-19` (medium oils) e `2710 19 29` (altro cherosene), quindi il confronto con l'HHI HS6 986 è illustrativo. **Cross-check con Comtrade HS6 `271019`:** import Comext €9,69 mld ≈ $10,46 mld vs Comtrade $10,58 mld; export €8,91 mld ≈ $9,62 mld vs $9,65 mld (scarto ~1%, cambio ~1,08): la copertura CN8 dei gruppi è buona. Script: `scripts/qa_comext_vs_energy.py`.

### Bilancio energetico (2024)

| Prodotto | Dip. netta % | Dip. lorda % | Import (KTOE) |
|----------|:---:|:---:|---:|
| Petrolio e prodotti (excl. biofuel) | 93,9 | 142,9 | 73,674 |
| Gas naturale | 95,2 | 96,2 | 48,699 |
| Carbone e solidi fossili | 96,5 | 107,7 | 2,481 |
| Rinnovabili e biocarburanti | 6,1 | 7,5 | 2,233 |
| Coke | -22,4 | 9,5 | 70 |

**Come si legge.** Dipendenza netta = (import − export) / disponibilità interna. La disponibilità usa il **GIC ufficiale Eurostat** e, per i prodotti secondari (elettricità, gasolio, benzina, GPL, cherosene, olio combustibile, coke), aggiunge la produzione delle trasformazioni (`TO`). La dipendenza lorda = import / disponibilità è solo diagnostica: sul petrolio somma greggio importato e prodotti raffinati esportati, quindi non è una misura di dipendenza. Il 102,1% del gas 2022 della versione precedente era un artefatto del segno delle scorte: il valore corretto è **99,2% netto** (106,0% lordo). Totale energia 2024: **75,1% netto**.

**Nota di quadratura.** Per il petrolio il ricalcolo `PPRD + IMP − EXP + STK_CHG` dà 89,8%, il GIC ufficiale 93,9%: la differenza (≈2.356 KTOE) sono bunker internazionali e rettifiche statistiche. Il mart usa il GIC ufficiale.

**QA raffinazione (interno).** La somma dei `TO` dei prodotti principali è 60.019 KTOE = **99,3%** del crude intake 2024 (60.431 THS_T). Il rapporto è **indicativo**: numeratore in KTOE, denominatore in THS_T (1 t ≈ 1 toe), quindi non è una quadratura di massa. L'aggregato `O4000XBIO` (75.497 KTOE) include altri prodotti/feedstock. Script: `scripts/qa_refinery.py`. Resta il confronto esterno con ISPRA/UNFCCC CRF.

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
- Eurostat NRG_CB_OILM (solo QA raffinazione, mensile)
- Eurostat Comext DS-045409 (endpoint dedicato, no key)
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
