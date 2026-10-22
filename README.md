# coffee-machine-api

Lernprojekt für die Vorlesung **Serverentwicklung** (Semester 7, INFB): eine REST-API für **Kaffeemaschinen** mit FastAPI, SQLAlchemy und PostgreSQL.

## Datenmodell

```mermaid
erDiagram
    STANDORT ||--|| MASCHINE : "hat genau"
    MASCHINE ||--|{ KAFFEEBOHNE : "führt"

    STANDORT {
        uuid id PK
        string name
        string ort
        int version
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at "NULL = aktiv"
    }
    MASCHINE {
        uuid id PK
        string modell
        uuid standort_id FK
        int version
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at "NULL = aktiv"
    }
    KAFFEEBOHNE {
        uuid id PK
        string sorte
        uuid maschine_id FK
        int version
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at "NULL = aktiv"
    }
```

- **Standort ↔ Maschine (1:1)** – jeder Standort hat genau eine Kaffeemaschine
- **Maschine → Kaffeebohnen (1:N)** – eine Maschine führt mehrere Bohnensorten
- **ID** – alle Primärschlüssel als `uuid` (in der Anwendung als `uuid7` erzeugt, dadurch zeitsortierbar)
- **CRUD-Audit** – jede Entität besitzt `created_at` und `updated_at`
- **Soft Delete** – `deleted_at = NULL` bedeutet aktiv; gesetzt wird der Datensatz bei GET/List ausgeblendet, bleibt aber in der DB erhalten. **Hard Delete** entfernt den Datensatz dauerhaft.

### Optimistic Locking

Jeder Datensatz trägt eine `version`. Ein `PUT` muss die zuletzt gelesene `version` mitschicken; die Änderung wird nur ausgeführt, wenn sie noch aktuell ist (`WHERE id = … AND version = …`). Sonst antwortet die API mit `409 Conflict` und der Hinweis, den Datensatz neu zu laden – so gehen parallele Änderungen nicht verloren.

### Löschkaskade

Ein Soft Delete eines Standorts setzt `deleted_at` für die zugehörige Maschine und deren Kaffeebohnen im selben Schritt mit demselben Zeitstempel.

## Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| `GET` | `/standorte` | Standorte auflisten (Query: `name`, `ort`) |
| `POST` | `/standorte` | Standort anlegen |
| `GET` | `/standorte/{standort_id}` | Standort lesen (inkl. aktiver Maschine) |
| `PUT` | `/standorte/{standort_id}` | Standort ändern (`version` erforderlich) |
| `DELETE` | `/standorte/{standort_id}` | Standort löschen (Kaskade; `hard=true` für endgültig) |
| `GET` | `/standorte/{standort_id}/maschine` | Maschine des Standorts lesen |
| `POST` | `/standorte/{standort_id}/maschine` | Maschine anlegen |
| `PUT` | `/standorte/{standort_id}/maschine` | Maschine ändern (`version` erforderlich) |
| `DELETE` | `/standorte/{standort_id}/maschine` | Maschine soft löschen (Kaskade auf Bohnen) |
| `GET` | `/maschinen/{maschine_id}/kaffeebohnen` | Bohnen auflisten (Query: `sorte`) |
| `POST` | `/maschinen/{maschine_id}/kaffeebohnen` | Kaffeebohne anlegen |
| `GET` | `/maschinen/{maschine_id}/kaffeebohnen/{kaffeebohne_id}` | Kaffeebohne lesen |
| `PUT` | `/maschinen/{maschine_id}/kaffeebohnen/{kaffeebohne_id}` | Kaffeebohne ändern (`version` erforderlich) |
| `DELETE` | `/maschinen/{maschine_id}/kaffeebohnen/{kaffeebohne_id}` | Kaffeebohne soft löschen |

## Voraussetzungen

- Python ≥ 3.15
- [uv](https://docs.astral.sh/uv/) (Projekt- und Dependency-Management)
- Docker bzw. Docker-kompatible CLI (hier: Podman mit `docker`-Emulation) für PostgreSQL + pgAdmin

## Schnellstart

```bash
uv sync --dev     # Abhängigkeiten installieren (venv + Lockfile)
make up           # PostgreSQL + pgAdmin starten, Schema anlegen, dann check (Format, Lint, ty, pytest)
make data         # Demo-Daten in die Live-Datenbank schreiben
make run          # API-Server mit Hot-Reload starten
```

Zum Herunterfahren aller Systeme:

```bash
make down
```

Nach dem Start:

| Komponente | URL / Zugang |
|---|---|
| API (Swagger UI) | <http://localhost:8000/docs> |
| pgAdmin (DB-Browser) | <http://localhost:5050> – kein Login, Server `coffee_machine` ist vorregistriert |
| PostgreSQL | `localhost:5432` – User `coffee`, Passwort `coffee`, DB `coffee_machine` |

pgAdmin läuft im **Desktop-Modus** (`PGADMIN_CONFIG_SERVER_MODE=False`): kein Login, kein Master-Passwort,
und die Datenbank wird beim Start aus `pgadmin/servers.json` importiert. Das Verbindungspasswort liefert
`pgadmin/pgpass` (per `PGPASS_FILE` nach `/var/lib/pgadmin/.pgpass` kopiert). Der Desktop-Modus ist nur für die
lokale Entwicklung gedacht – der Port `5050` ist im Netz erreichbar und damit ohne Anmeldung nutzbar.

Damit Server-Definition und Passwort neu eingelesen werden, muss das pgAdmin-Konfigurations-Volume weg.
`make reset` entfernt **beide** Volumes (Datenbank und pgAdmin) und startet frisch:

```bash
make reset
```

Bei SELinux (Fedora, `getenforce` = `Enforcing`) tragen die Bind-Mounts ein `z`-Label, sonst darf der
Container die Dateien nicht lesen.

Die DB-Verbindung wird über die Umgebungsvariable `DATABASE_URL` konfiguriert:

```bash
export DATABASE_URL="postgresql+psycopg://coffee:coffee@localhost:5432/coffee_machine"
```

## Entwicklung

Das Projekt nutzt **GNU Make** als Werkzeug-Menü – alle Befehle zeigt `make help`. Jeder Befehl fasst
zusammengehörige Schritte zusammen:

| Befehl | Zweck |
|---|---|
| `make setup` | Abhängigkeiten installieren und Compose-Datei prüfen |
| `make up` | Container starten, auf PostgreSQL warten, Qualitätsgate ausführen |
| `make run` | Datenbank sicherstellen und API-Server mit Hot-Reload starten |
| `make logs` | Requests und Fehler der laufenden API verfolgen |
| `make data` | Demo-Daten in die Live-Datenbank schreiben (ergänzt nur Fehlendes) |
| `make check` | Format, Lint, Typecheck und Tests prüfen (ändert nichts) |
| `make fix` | Code formatieren und behebbare Lint-Fehler korrigieren |
| `make down` | Container stoppen (Daten bleiben erhalten) |
| `make reset` | Container und Volumes verwerfen, danach frisch starten |
| `make help` | Übersicht der Befehle |

`make data` schreibt einen festen Katalog aus `scripts/seed.py` in die Live-Datenbank `coffee_machine`:
5 Standorte mit je einer Maschine und 3–5 Kaffeebohnen. Der Befehl ist **idempotent** – er ergänzt nur, was
fehlt, und lässt vorhandene Datensätze unberührt. Ein zweiter Aufruf meldet entsprechend
„Keine Änderungen“. Der Katalog wird nicht zufällig erzeugt, damit die Daten reproduzierbar bleiben.

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

## Tests

Die Integrationstests laufen gegen eine temporäre Datenbank `coffee_machine_test`. Die Fixture in
`tests/conftest.py` legt sie vor dem Lauf an und löscht sie danach wieder (`DROP DATABASE ... WITH (FORCE)`).
Dauerhaft existiert also nur `coffee_machine`. Die Tabellen werden vor jedem Test geleert. Abweichender Zugang
lässt sich über `TEST_DATABASE_URL` setzen – der Name der Wegwerf-Datenbank wird daraus abgeleitet:

```bash
uv run pytest          # gesamte Suite
make check             # Format + Lint + Typecheck + Test
```
