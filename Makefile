.PHONY: build up down migrate test lint complexity lock

build:
	docker compose build

up:
	docker compose up

down:
	docker compose down

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
