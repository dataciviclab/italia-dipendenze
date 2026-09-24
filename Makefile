# Italy Resource & Dependency Map — Makefile
TOOLKIT = toolkit

# --- Dataset del repo -------------------------------------------------------
DATASETS := $(shell find datasets -name dataset.yml 2>/dev/null | sort)

# --- Run toolkit ------------------------------------------------------------

.PHONY: run
run:
	$(TOOLKIT) run --batch batch.txt

.PHONY: run-all
run-all:
	@find datasets -name dataset.yml | sort > batch.txt; \
	$(TOOLKIT) run --batch batch.txt

# --- Validazione config ------------------------------------------------------

.PHONY: check
check:
	@for f in $(DATASETS); do \
		echo "→ $$f"; \
		$(TOOLKIT) run preflight --config "$$f" > /dev/null 2>&1 || exit 1; \
	done
	@echo "✅ All configs valid"

# --- Script analitici -------------------------------------------------------

.PHONY: fetch-comtrade
fetch-comtrade:
	python3 scripts/fetch_comtrade.py --output-dir out/raw/comtrade

.PHONY: fetch-fao
fetch-fao:
	python3 scripts/download_fao_fertilizer.py --output-dir out/raw/fao

.PHONY: concentration
concentration:
	python3 scripts/compute_concentration.py --input out/raw/comtrade/comtrade_bilateral.json --resource gas --output-dir out/mart

# --- Pipeline completa: toolkit + analitici + test ----------------------------

.PHONY: all
all: run-all test

# --- Test --------------------------------------------------------------------

.PHONY: test
test:
	python3 -m pytest tests/ -v

# --- Registry ----------------------------------------------------------------

.PHONY: registry
registry:
	$(TOOLKIT) registry build --prefix dipendenze_risorse --flat

# --- Pulizia -----------------------------------------------------------------

.PHONY: clean
clean:
	rm -rf out/data/_runs out/data/probe out/data/raw out/data/clean out/data/mart

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:' Makefile | sort
