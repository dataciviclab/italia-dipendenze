# Materie Prime — Makefile
TOOLKIT = toolkit
export TOOLKIT_ALLOW_SCRIPT_SOURCE = 1

# --- Dataset del repo -------------------------------------------------------
DATASETS := $(shell find datasets -name dataset.yml 2>/dev/null | sort)
COMPOSES := $(shell find compose -name dataset.yml 2>/dev/null | sort)

# --- Run toolkit ------------------------------------------------------------

.PHONY: run
run:
	$(TOOLKIT) run --batch batch.txt

.PHONY: run-all
run-all:
	@find datasets -name dataset.yml 2>/dev/null | sort > batch.txt; \
	find compose -name dataset.yml 2>/dev/null | sort >> batch.txt; \
	$(TOOLKIT) run --batch batch.txt

# --- Validazione config ------------------------------------------------------

.PHONY: check
check:
	@for f in $(DATASETS) $(COMPOSES); do \
		echo "→ $$f"; \
		$(TOOLKIT) run preflight --config "$$f" > /dev/null 2>&1 || exit 1; \
	done
	@echo "✅ All configs valid"

# --- Pipeline completa: fetch + toolkit + test --------------------------------

.PHONY: all
all: run-all test

# --- Verify (dopo pipeline) -------------------------------------------------

.PHONY: verify
verify:
	@echo "Verify: checking mart parquet files exist"
	@test -d out/data/mart || (echo "❌ No mart output" && exit 1)
	@echo "✅ Mart output present"

# --- Test --------------------------------------------------------------------

.PHONY: test
test:
	python3 -m pytest tests/ dashboard/tests/ -v

.PHONY: dashboard
dashboard:
	streamlit run dashboard/app.py

# --- Registry ----------------------------------------------------------------

.PHONY: registry
registry:
	$(TOOLKIT) registry build --prefix italia_dipendenze

.PHONY: registry-write
registry-write:
	$(TOOLKIT) registry build --prefix italia_dipendenze --write

# --- Pulizia -----------------------------------------------------------------

.PHONY: clean
clean:
	rm -rf out/data/_runs out/data/probe out/data/raw out/data/clean out/data/mart

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:' Makefile | sort
