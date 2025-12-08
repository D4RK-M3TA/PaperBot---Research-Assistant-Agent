.PHONY: help install migrate runserver worker test setup

help:
	@echo "PaperBot Makefile Commands:"
	@echo "  make install     - Install Python dependencies"
	@echo "  make migrate     - Run database migrations"
	@echo "  make setup       - Initial setup (migrate + create superuser + setup models)"
	@echo "  make runserver   - Run Django development server"
	@echo "  make worker      - Run Celery worker"
	@echo "  make test        - Run tests"
	@echo "  make docker-up   - Start Docker containers"
	@echo "  make docker-down - Stop Docker containers"

install:
	pip install -r requirements.txt

migrate:
	python manage.py migrate

setup: migrate
	python manage.py setup_models
	@echo "Creating superuser..."
	python manage.py createsuperuser --noinput || echo "Superuser already exists or interactive creation needed"

runserver:
	python manage.py runserver

worker:
	celery -A paperbot worker -l info

test:
	python manage.py test

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f





