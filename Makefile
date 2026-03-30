.PHONY: up down lint typecheck schema-check test check

up:
	docker compose up --build

down:
	docker compose down -v

lint:
	ruff check .

typecheck:
	mypy backend collectors

schema-check:
	PYTHONPATH=. python scripts/validate_schema.py

test:
	PYTHONPATH=. pytest -q

check: lint typecheck schema-check
