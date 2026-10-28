# Comandi di sviluppo. Richiedono uv e Node 22.
.PHONY: setup dev-backend dev-frontend check test api-types migrate

setup: ## Installa le dipendenze e gli hook di pre-commit
	cd backend && uv sync
	cd frontend && npm ci
	uv run --directory backend pre-commit install

dev-backend: ## API su http://127.0.0.1:8000 (ricarica automatica)
	cd backend && uv run python -m gym_split_planner migrate && \
		uv run python -m gym_split_planner seed && \
		uv run uvicorn gym_split_planner.app:create_app --factory --reload

dev-frontend: ## Frontend su http://127.0.0.1:5173, con /api inoltrato al backend
	cd frontend && npm run dev

check: ## Tutti i controlli della CI
	cd backend && uv run ruff format --check . && uv run ruff check . && uv run mypy && \
		uv run lint-imports && uv run pytest --cov && \
		uv run coverage report --include="src/gym_split_planner/domain/*" --fail-under=90
	cd frontend && npm run lint && npm run format:check && npm run type-check && npm test
	$(MAKE) api-types && git diff --exit-code -- openapi.json frontend/src/api/schema.d.ts

test: ## Solo i test
	cd backend && uv run pytest
	cd frontend && npm test

api-types: ## Rigenera schema OpenAPI e tipi del client
	cd backend && uv run python -m gym_split_planner openapi > ../openapi.json
	cd frontend && npm run -s api:types

migrate: ## Applica le migrazioni e, su database vuoto, i dati iniziali
	cd backend && uv run python -m gym_split_planner migrate && uv run python -m gym_split_planner seed
