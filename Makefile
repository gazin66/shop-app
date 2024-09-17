# Переменные окружения
POSTGRES_USER ?= postgres
POSTGRES_PASSWORD ?= admin
POSTGRES_DB ?= postgres
POSTGRES_HOST ?= 127.0.0.1
POSTGRES_PORT ?= 5432

# Команды
.PHONY: help install_dependencies run_tests run_service create_migration up down logs migrate upgrade_db downgrade_db

help: ## Показать это сообщение
	@powershell -Command "Get-Content Makefile | Select-String -Pattern '^[a-zA-Z_-]+:.*?## .*$$' | ForEach-Object { $$_.Line.Split(':')[0] + ' ' + $$_.Line.Split(':')[1].Trim().Split('##')[1].Trim() } | ForEach-Object { Write-Host ('\033[36m' + $$_.Split(' ')[0].PadRight(30) + '\033[0m' + $$_.Split(' ')[1]) }"

install_dependencies: ## Подтянуть все зависимости из Poetry
	poetry install

run_tests: ## Локально прогнать тесты
	poetry run pytest

run_service: ## Локально запустить сервис с автоматической перезагрузкой
	poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

create_migration: ## Создать новую миграцию
	poetry run alembic revision --autogenerate -m "$(message)"

up: ## Запустить контейнеры
	docker-compose --env-file .env up -d

down: ## Остановить и удалить контейнеры
	docker-compose down

logs: ## Показать логи контейнеров
	docker-compose logs -f

migrate: ## Выполнить миграции
	docker-compose exec web alembic upgrade head

upgrade_db: ## Обновить базу данных до последней версии
	docker-compose exec web alembic upgrade head

downgrade_db: ## Откатить базу данных на одну версию назад
	docker-compose exec web alembic downgrade -1