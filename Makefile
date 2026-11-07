.PHONY: dev up down web-install web-dev web-test web-e2e web-check api-install api-dev api-test api-check compose-config

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

api-check:
	cd apps/api && ../../.venv/bin/ruff check app tests
	cd apps/api && ../../.venv/bin/mypy app tests
	cd apps/api && ../../.venv/bin/pytest

compose-config:
	docker compose config --quiet

