# Personal Recommender Agent

Ovaj projekt implementira inteligentnog softverskog agenta za personalizirane preporuke sadržaja, koristeći Clean Architecture i Sense→Think→Act→Learn ciklus.

## Setup

1. **Virtual Environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Baza Podataka:**
   - Koristi SQLite za pohranu events i modela.
   - Lokacija: `data/events.db` (automatski se kreira).
   - Nema potrebe za vanjski SQL server; sve je lokalno.

3. **Pokretanje:**
   ```bash
   uvicorn src.interface.api:app --reload
   ```
   - API na http://localhost:8000
   - Dokumentacija: http://localhost:8000/docs

## Struktura Projekta (Clean Architecture)

- `src/domain/` - Core business logic (entities, interfaces)
- `src/application/` - Use cases, orchestrator
- `src/infrastructure/` - DB, external services
- `src/interface/` - Web API, CLI
- `tests/` - Unit i integration testovi
- `data/` - SQLite baza i modeli

## API Endpoints

- **GET /recommend?user_id={}&session_id={}&n=10**
  - Vraća top-N preporuka.
  - Primjer response: `{"recommendations": [{"item_id": "item1", "score": 0.9, "reason": "Popular"}]}`
- **POST /events** (body: JSON event)
  - Ingestira user event za learning.
  - Primjer body: `{"user_id": "123", "event_type": "click", "item_id": "movie1"}`

## Demo

Pokreni server i testiraj:
```bash
curl "http://localhost:8000/recommend?user_id=test&session_id=test"
```

## GitHub

Preporučujem pushati projekt na GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
# Kreiraj repo na GitHub i pushaj
```

## Testovi

```bash
pytest tests/
```

## Specifikacija

Vidi `specifikacija.md` za detalje o ideji, S→T→A→L ciklusu i acceptance kriterijima.