.PHONY: build up test lint

build:
	docker-compose build

up:
	docker-compose up --build

test:
	pytest -q

lint:
	ruff check .
