# Contribuire a Italy Resource & Dependency Map

## Come contribuire

1. Fork il repo
2. Crea un branch (`git checkout -b feat/nuova-risorsa`)
3. Fai le tue modifiche
4. Apri una PR

## Struttura del progetto

```
datasets/           Config e SQL per ogni dataset
compose/            Join multi-source (resource_dependency_compose)
scripts/            Script di fetch dati
dashboard/          Dashboard Streamlit (Lab standard)
tests/              Test smoke pipeline
out/                Output pipeline (gitignored)
```

## Aggiungere una nuova risorsa

1. Crea `datasets/<nome-risorsa>/dataset.yml`
2. Aggiungi `sql/clean.sql` e `sql/mart_*.sql`
3. Aggiungi lo script di fetch in `scripts/` se necessario
4. Aggiungi il dataset a `batch.txt`
5. Aggiungi contratto test in `tests/test_smoke.py`
6. Esegui `make run` e `make test`

## Standard

- Segui gli standard in `analysis/lab-ops/standards/`
- Ogni test ha un marker (`@pytest.mark.smoke`)
- Ogni numero ha source + method + data_quality
- Non inventare dati mancanti
