.PHONY: build up down migrations migrate test lint complexity lock simulate report all

build:
	docker compose build

up:
	docker compose up

down:
	docker compose down

migrations:
	docker compose run --rm web python manage.py makemigrations

migrate:
	docker compose run --rm web python manage.py migrate

test:
	docker compose run --rm web pytest

lint:
	docker compose run --rm web ruff check --fix .
	docker compose run --rm web ruff format .

complexity:
	docker compose run --rm web complexipy .

lock:
	docker compose run --rm web uv lock

simulate:
	docker compose run --rm web python scripts/client_simulator.py

report:
	docker compose run --rm web python scripts/generate_report.py

all:
	docker compose down -v --remove-orphans
	docker compose build
	docker compose run --rm web python manage.py makemigrations
	docker compose run --rm web python manage.py migrate
	docker compose up -d
