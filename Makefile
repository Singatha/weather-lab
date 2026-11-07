.PHONY: dev up down web-install web-dev web-test web-coverage web-e2e web-check api-install api-dev api-test api-coverage api-check performance-smoke compose-config

dev: up

up:
	docker compose up --build

down:
	docker compose down

web-install:
	npm install

web-dev:
	npm run dev:web

web-test:
	npm run test:web

web-coverage:
	npm run test:coverage:web

web-e2e:
	npm run test:e2e

web-check:
	npm run lint:web
	npm run typecheck:web
	npm run test:web
	npm run build:web
	npm run test:e2e

api-install:
	python3.12 -m venv .venv
	.venv/bin/pip install -e 'apps/api[dev]'

api-dev:
	.venv/bin/uvicorn app.main:app --reload --app-dir apps/api

api-test:
	cd apps/api && ../../.venv/bin/pytest

api-coverage:
	cd apps/api && ../../.venv/bin/pytest --cov=app --cov-report=term-missing --cov-report=xml:coverage.xml

api-check:
	cd apps/api && ../../.venv/bin/ruff check app tests performance
	cd apps/api && ../../.venv/bin/ruff format --check app tests performance
	cd apps/api && ../../.venv/bin/mypy app tests performance
	cd apps/api && ../../.venv/bin/pytest

compose-config:
	docker compose config --quiet

performance-smoke:
	docker compose exec -T api python -m performance.smoke --base-url http://127.0.0.1:8000

