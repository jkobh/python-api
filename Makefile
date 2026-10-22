# Makefile für das coffee-machine-api Projekt
# Zentrale Entwicklungs-Workflows auf Basis von uv, Docker Compose und pytest.
# Aufruf: make <befehl>

UV            := uv
COMPOSE       := docker compose
APP_MODULE    := app.main:app
LOG_DIR       := logs
LOG_FILE      := $(LOG_DIR)/api.log
API_PID_FILE  := $(LOG_DIR)/api.pid
RELEVANT_LOG_LINES := '"(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS) |ERROR|CRITICAL|Traceback|Uvicorn running|Application startup|WatchFiles'

.DEFAULT_GOAL := up

.PHONY: up down logs check data reset _wait-db _init-schema _start-api _stop-api

up: ## Setup, Container starten, Schema anlegen, Qualität sichern, API starten
	$(UV) sync --dev
	@$(COMPOSE) config --quiet
	$(COMPOSE) up -d
	@$(MAKE) --no-print-directory _wait-db
	@$(MAKE) --no-print-directory _init-schema
	@$(MAKE) --no-print-directory check
	@$(MAKE) --no-print-directory _start-api
	@echo ""
	@echo "API:     http://localhost:8000/docs"
	@echo "pgAdmin: http://localhost:5050"
	@echo "Log:     make logs"

down: ## API und Container stoppen (Daten in den Volumes bleiben erhalten)
	@$(MAKE) --no-print-directory _stop-api
	$(COMPOSE) down
	@echo "Alles gestoppt, Daten bleiben erhalten."

logs: ## Requests und Fehler der laufenden API verfolgen
	@mkdir -p $(LOG_DIR)
	@touch $(LOG_FILE)
	@echo "Beobachte $(LOG_FILE) – Abbruch mit Strg+C"
	@tail -f -n +1 $(LOG_FILE) | grep --line-buffered -E $(RELEVANT_LOG_LINES)

check: ## Formatiert, korrigiert Lint, prüft Typen und führt die Tests aus
	$(UV) run ruff format .
	$(UV) run ruff check --fix .
	$(UV) run ty check .
	$(UV) run pytest -q

data: ## Demo-Daten in die Live-Datenbank schreiben (ergänzt nur Fehlendes)
	@$(MAKE) --no-print-directory _wait-db
	@$(MAKE) --no-print-directory _init-schema
	$(UV) run python -m scripts.seed

reset: ## Volumes verwerfen und alles frisch aufbauen
	@$(MAKE) --no-print-directory _stop-api
	$(COMPOSE) down -v
	@echo "Container und Volumes entfernt – Datenbank und pgAdmin-Konfiguration sind frisch."
	@$(MAKE) --no-print-directory up

_wait-db:
	@echo "Warte auf PostgreSQL ..."
	@i=0; until $(COMPOSE) exec -T db pg_isready -U coffee -d coffee_machine >/dev/null 2>&1; do \
		i=$$((i+1)); \
		if [ $$i -ge 30 ]; then echo "FEHLER: PostgreSQL nicht rechtzeitig erreichbar."; exit 1; fi; \
		sleep 2; \
	done; echo "PostgreSQL ist bereit."

_init-schema:
	@$(UV) run python -c "from app.database import database; database.create_schema()"
	@echo "Schema ist angelegt."

_start-api:
	@mkdir -p $(LOG_DIR)
	@if [ -f $(API_PID_FILE) ] && kill -0 "$$(cat $(API_PID_FILE))" 2>/dev/null; then \
		echo "API läuft bereits."; \
	else \
		setsid $(UV) run uvicorn $(APP_MODULE) --reload >$(LOG_FILE) 2>&1 & \
		echo $$! >$(API_PID_FILE); \
		echo "API gestartet."; \
	fi

_stop-api:
	@if [ -f $(API_PID_FILE) ]; then \
		kill -TERM -- -"$$(cat $(API_PID_FILE))" 2>/dev/null || true; \
		rm -f $(API_PID_FILE); \
		echo "API gestoppt."; \
	fi