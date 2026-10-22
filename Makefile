# Makefile für das coffee-machine-api Projekt
# Zentrale Entwicklungs-Workflows auf Basis von uv, Docker Compose und pytest.
# Aufruf: make <befehl>   (Übersicht: make help)

UV            := uv
COMPOSE       := docker compose
APP_MODULE    := app.main:app
LOG_DIR       := logs
LOG_FILE      := $(LOG_DIR)/api.log
RELEVANT_LOG_LINES := '"(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS) |ERROR|CRITICAL|Traceback|Uvicorn running|Application startup|WatchFiles'

.DEFAULT_GOAL := help

.PHONY: help setup up run logs data check fix down reset _wait-db _init-schema

help: ## Übersicht der verfügbaren Befehle
	@echo "Verfügbare Befehle:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  make %-8s %s\n", $$1, $$2}'

setup: ## Abhängigkeiten installieren und Compose-Datei prüfen
	$(UV) sync --dev
	$(COMPOSE) config --quiet
	@echo "Setup abgeschlossen."

up: ## Container starten, Schema anlegen, Qualitätsgate ausführen
	$(COMPOSE) up -d
	@$(MAKE) --no-print-directory _wait-db
	@$(MAKE) --no-print-directory _init-schema
	@$(MAKE) --no-print-directory check

run: ## Datenbank sicherstellen und API mit Hot-Reload starten
	@$(COMPOSE) up -d
	@$(MAKE) --no-print-directory _wait-db
	@mkdir -p $(LOG_DIR)
	@echo "API: http://localhost:8000/docs – Log: $(LOG_FILE) (Strg+C beendet)"
	$(UV) run uvicorn $(APP_MODULE) --reload 2>&1 | tee $(LOG_FILE)

logs: ## Requests und Fehler der laufenden API verfolgen
	@mkdir -p $(LOG_DIR)
	@touch $(LOG_FILE)
	@echo "Beobachte $(LOG_FILE) – Abbruch mit Strg+C"
	@tail -f -n +1 $(LOG_FILE) | grep --line-buffered -E $(RELEVANT_LOG_LINES)

data: ## Demo-Daten in die Live-Datenbank schreiben (ergänzt nur Fehlendes)
	@$(MAKE) --no-print-directory _wait-db
	@$(MAKE) --no-print-directory _init-schema
	$(UV) run python -m scripts.seed

check: ## Format, Lint, Typecheck und Tests prüfen (ändert nichts)
	$(UV) run ruff format --check .
	$(UV) run ruff check .
	$(UV) run ty check .
	$(UV) run pytest -q

fix: ## Code formatieren und behebbare Lint-Fehler korrigieren
	$(UV) run ruff format .
	$(UV) run ruff check --fix .

down: ## Container stoppen (Daten in den Volumes bleiben erhalten)
	$(COMPOSE) down
	@echo "Container gestoppt, Daten bleiben erhalten."

reset: ## Container und Volumes verwerfen, danach frisch starten
	$(COMPOSE) down -v
	@echo "Container und Volumes entfernt – Datenbank und pgAdmin-Konfiguration sind frisch."
	@$(COMPOSE) up -d
	@$(MAKE) --no-print-directory _wait-db
	@$(MAKE) --no-print-directory _init-schema

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