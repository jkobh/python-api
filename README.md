# coffee-machine-api

Lernprojekt für die Vorlesung **Serverentwicklung** (Semester 7, INFB): eine REST-API für **Kaffeemaschinen** mit FastAPI, SQLAlchemy und PostgreSQL.

## Datenmodell

```mermaid
erDiagram
    STANDORT ||--|| MASCHINE : "hat genau"
    MASCHINE ||--|{ KAFFEEBOHNE : "führt"

    STANDORT {
        int id PK
        string name
        string ort
    }
    MASCHINE {
        int id PK
        string modell
        int standort_id FK
    }
    KAFFEEBOHNE {
        int id PK
        string sorte
        int röstgrad
        int maschine_id FK
    }
```

- **Standort ↔ Maschine (1:1)** – jeder Standort hat genau eine Kaffeemaschine
- **Maschine → Kaffeebohnen (1:N)** – eine Maschine führt mehrere Bohnensorten

## Voraussetzungen

- Python ≥ 3.14
- [uv](https://docs.astral.sh/uv/) (Projekt- und Dependency-Management)
- Docker bzw. Docker-kompatible CLI (hier: Podman mit `docker`-Emulation) für PostgreSQL + pgAdmin

## Schnellstart

```bash
uv sync --dev     # Abhängigkeiten installieren (venv + Lockfile)
make up           # PostgreSQL + pgAdmin starten, auf Bereitschaft warten, dann check (lint, ty, pytest)
make dev          # API-Server mit Hot-Reload starten
```

Zum Herunterfahren aller Systeme:

```bash
make down
```

Nach dem Start:

| Komponente | URL / Zugang |
|---|---|
| API (Swagger UI) | <http://localhost:8000/docs> |
| pgAdmin (DB-Browser) | <http://localhost:5050> – E-Mail `coffee@example.com`, Passwort `coffee` |
| PostgreSQL | `localhost:5432` – User `coffee`, Passwort `coffee`, DB `coffee_machine` |

Die DB-Verbindung wird über die Umgebungsvariable `DATABASE_URL` konfiguriert:

```bash
export DATABASE_URL="postgresql+psycopg://coffee:coffee@localhost:5432/coffee_machine"
```

## Entwicklung

Das Projekt nutzt **GNU Make** als Werkzeug-Menü – alle Targets inkl. Beschreibung zeigt `make help`. Die wichtigsten:

| Target | Zweck |
|---|---|
| `make up` | Alle Systeme starten und testen (DB + lint/ty/pytest) |
| `make down` | Alle Systeme ordentlich herunterfahren |
| `make dev` | API-Server mit Hot-Reload |
| `make check` | lint + typecheck + test |
| `make setup` | Abhängigkeiten synchronisieren |

Weitere Ziele (z. B. `db-psql`, `db-logs`, `format`) stehen im [Makefile](./Makefile).

## Checkliste

<details>
<summary>Anforderungen (aus der Checkliste)</summary>

### Vorbereitet

- Relationale DB mit PostgreSQL 18 oder 19 als Docker Container
  - 1:1 und 1:N-Beziehung
  - DB-Browser
- Leeres GIT-Repository: „Commit early, Commit often“ → inkrementelle Entwicklung durch Prompts
- **Soll nicht umgesetzt werden:** Keycloak (Vorsicht bei 26.8.0 als Hardened Image) als Docker Container: 1 Realm mit 1 Client und dazu mind. 1 User und 1 Rolle

### Infrastruktur

- pyproject.toml einschl. Konfiguration uv, ruff, ty

### Appserver

- REST durch FastAPI einschl. Dependency Injection und Pydantic für Response
  - GET-Requests: Pfad- oder Query-Parameter, auch bedingte GET-Requests
  - POST-Request mit Validierung durch Pydantic
  - PUT-Request mit Validierung und Vermeidung von Lost-Updates
- DB-Zugriff durch SQLAlchemy
- **Soll nicht umgesetzt werden:** Security durch Dependency Injection

### Testen

- GET und POST
  - Empfehlung: Bruno/Postman/Thunder Client oder pytest (Integrationstests genügen)
</details>

## Werkzeuge

- **uv** – Paketverwaltung (`uv sync`, `uv add`, `uv run`)
- **Ruff** – Linter & Formatter (Konfiguration in `pyproject.toml`)
- **ty** – Type-Checker von Astral (Beta; alle Regeln als Fehler)
- **pytest** – Integrationstests (GET & POST gemäß Checkliste)
