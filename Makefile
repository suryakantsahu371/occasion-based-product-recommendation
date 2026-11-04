PY ?= backend/.venv/bin/python
ifeq ($(OS),Windows_NT)
PY = backend/.venv/Scripts/python.exe
endif

.PHONY: setup index enrich-llm run run-api run-ui test lint eval audit screenshots

setup:  ## create venv, install backend + frontend deps
	python -m venv backend/.venv
	$(PY) -m pip install -r backend/requirements-dev.txt
	cd frontend && npm install

audit:  ## data-audit summary of the catalog
	cd backend && ../$(PY) scripts/audit.py

index:  ## enrich (LLM if ANTHROPIC_API_KEY set, else rules) + build FAISS/BM25/TF-IDF
	cd backend && ../$(PY) scripts/enrich.py --method auto && ../$(PY) scripts/build_index.py

enrich-llm:  ## force the LLM enrichment path (needs ANTHROPIC_API_KEY)
	cd backend && ../$(PY) scripts/enrich.py --method llm && ../$(PY) scripts/build_index.py

run-api:
	cd backend && ../$(PY) -m uvicorn app.main:app --port 8000

run-ui:
	cd frontend && npm run dev

run:  ## API + UI together (Ctrl+C stops both)
	$(MAKE) -j2 run-api run-ui

test:
	cd backend && ../$(PY) -m pytest -q

lint:
	cd backend && ../$(PY) -m ruff check . && ../$(PY) -m black --check .
	cd frontend && npm run lint && npm run format:check

eval:  ## Precision@5 / nDCG@10 for the five variants
	cd backend && ../$(PY) scripts/evaluate.py

screenshots:  ## needs API + UI running
	cd frontend && npm run screenshots
