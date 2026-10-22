# Makefile für das coffee-machine-api Projekt
# Zentrale Entwicklungs-Workflows auf Basis von uv, Docker Compose und pytest.
# Aufruf: make <target>   (alle Targets: make help)

UV     := uv
COMPOSE := docker compose
APP_MODULE := app.main:app
LOG_DIR := logs
LOG_FILE := $(LOG_DIR)/api.log
RELEVANT_LOG_LINES := '"(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS) |ERROR|CRITICAL|Traceback|Uvicorn running|Application startup|WatchFiles'

.PHONY: help setup up down wait-db dev logs db-up db-down db-down-clean db-logs db-validate db-psql lint format typecheck test check clean

help: ## Zeigt alle verfügbaren Targets
	@echo "Verfügbare Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  %-14s %s\n", $$1, $$2}'

setup: ## Synchronisiert Abhängigkeiten (uv sync --dev)
	$(UV) sync --dev
	@echo "Setup abgeschlossen."

up: ## Startet alle Systeme (PostgreSQL + pgAdmin) und führt die Tests aus
	$(COMPOSE) up -d
	$(MAKE) wait-db
	$(MAKE) check

wait-db: ## Wartet, bis PostgreSQL bereit ist
	@echo "Warte auf PostgreSQL ..."
	@i=0; until $(COMPOSE) exec db pg_isready -U coffee -d coffee_machine >/dev/null 2>&1; do \
		i=$$((i+1)); \
		[ $$i -ge 30 ] && echo "FEHLER: PostgreSQL nicht rechtzeitig erreichbar." && exit 1; \
		sleep 2; \
	done; echo "PostgreSQL ist bereit."

down: ## Fährt alle Systeme ordentlich herunter
	$(COMPOSE) down
	@echo "Alle Systeme wurden beendet."

dev: ## Startet den API-Server mit Hot-Reload (uvicorn --reload, Log in logs/api.log)
	@mkdir -p $(LOG_DIR)
	$(UV) run uvicorn $(APP_MODULE) --reload 2>&1 | tee $(LOG_FILE)

logs: ## Zeigt Requests, Fehler und Startmeldungen der laufenden API (folgt der Datei)
	@mkdir -p $(LOG_DIR)
	@touch $(LOG_FILE)
	@echo "Beobachte $(LOG_FILE) – Requests und Fehler (Abbruch mit Strg+C)"
	@tail -f -n +1 $(LOG_FILE) | grep --line-buffered -E $(RELEVANT_LOG_LINES)

db-up: ## Startet PostgreSQL + pgAdmin (Docker Compose)
	$(COMPOSE) up -d

db-down: ## Stoppt die Datenbank-Container (Daten im Volume bleiben erhalten)
	$(COMPOSE) down

db-down-clean: ## Stoppt Container und entfernt das Daten-Volume
	$(COMPOSE) down -v

db-logs: ## Zeigt die Container-Logs
	$(COMPOSE) logs -f

db-validate: ## Prüft die docker-compose.yml auf Gültigkeit
	$(COMPOSE) config --quiet

db-psql: ## Öffnet eine psql-Shell im db-Container
	$(COMPOSE) exec db psql -U coffee -d coffee_machine

lint: ## Führt den Ruff-Linter aus
	$(UV) run ruff check .

format: ## Formatiert den Code mit Ruff
	$(UV) run ruff format .

typecheck: ## Führt den Type-Checker ty aus
	$(UV) run ty check .

test: ## Führt die pytest-Integrationstests aus
	$(UV) run pytest -q

check: lint typecheck test ## Führt Lint, Typecheck und Tests aus

clean: ## Entfernt Build-, Cache- und Log-Artefakte
	rm -rf .ruff_cache .pytest_cache .ty_cache .venv $(LOG_DIR)
	@echo "Aufgeräumt."
