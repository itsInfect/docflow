.PHONY: api web test lint format compose-up compose-down

api:
	cd apps/api && uvicorn docflow.main:app --reload

web:
	cd apps/web && npm run dev

test:
	cd apps/api && pytest
	cd apps/web && npm run build

lint:
	cd apps/api && ruff check . && mypy src
	cd apps/web && npm run lint

format:
	cd apps/api && ruff format .
	cd apps/web && npm run format

compose-up:
	docker compose up --build

compose-down:
	docker compose down

