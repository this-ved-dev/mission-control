.PHONY: test test-backend test-frontend lint openapi smoke figures

test: test-backend test-frontend

test-backend:
	cd backend && uv run pytest

test-frontend:
	cd frontend && npm ci --silent && npm test

lint:
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd frontend && npm run lint && npm run typecheck

openapi:
	cd backend && uv run python -m app.export_openapi ../openapi.json
	cd frontend && npm run gen:api

figures:
	cd frontend && npm run figures

smoke:
	cd backend && uv run pytest -m live -p no:socket -o addopts=""
