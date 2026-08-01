# Smart Expense Tracker API

A REST API for tracking personal expenses, built with **FastAPI**. Supports adding,
listing, filtering, totaling, and deleting expenses. Filters (category, title search,
date range, amount range) apply consistently to both the listing endpoint and the
totals endpoint, so you can ask "how much did I spend on Food in January?" as easily
as "show me all expenses."

## What was built

- `POST /expenses` — add an expense (`title`, `amount`, `category`, `date`)
- `GET /expenses` — list expenses, with optional filters:
  - `category` — exact match, case-insensitive
  - `q` — substring search on title (this is the "search expenses" bonus)
  - `date_from`, `date_to` — inclusive date range
  - `min_amount`, `max_amount` — inclusive amount range
  - Filters combine with AND logic, e.g. `?category=Food&date_from=2026-01-01`
- `GET /expenses/total` — total spend + per-category breakdown, **honoring the same
  filters as `/expenses`**. This is how "total by category" and "total for a filtered
  view" both work — apply filters and hit this endpoint.
- `GET /expenses/{id}` — fetch a single expense
- `DELETE /expenses/{id}` — delete an expense
- Interactive API docs (Swagger UI) auto-generated at `/docs`, and ReDoc at `/redoc`

Data is stored in a local JSON file (`data/expenses.json`), not a database, per the
assignment's storage options. A thread lock guards reads/writes.

## Project structure

```
your-repo/
  README.md
  AI_NOTES.md
  src/
    main.py       # FastAPI app and route handlers
    models.py     # Pydantic request/response models
    storage.py    # JSON-file backed storage + filtering logic
  tests/
    conftest.py   # pytest fixtures (isolated temp-file storage per test)
    test_api.py   # 32 tests covering CRUD, filters, totals, edge cases
  data/           # expenses.json lives here at runtime (gitignored)
  Dockerfile
  docker-compose.yml
  requirements.txt
```

## Install

Requires Python 3.11+.

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run the server

From the repo root:

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Then visit `http://localhost:8000/docs` for interactive Swagger docs, or use curl:

```bash
curl -X POST localhost:8000/expenses \
  -H "Content-Type: application/json" \
  -d '{"title":"Coffee","amount":5.5,"category":"Food","date":"2026-01-05"}'

curl "localhost:8000/expenses?category=Food"

curl "localhost:8000/expenses/total?category=Food&date_from=2026-01-01&date_to=2026-01-31"
```

## Run the tests

From the repo root:

```bash
pytest tests/ -v
```

Tests use FastAPI's `TestClient` and a temporary JSON file per test (via a `tmp_path`
fixture), so they never touch your real `data/expenses.json` and each test starts
from a clean slate. All 32 tests pass on a clean checkout.

## Run with Docker (bonus)

```bash
docker build -t expense-api .
docker run -p 8000:8000 -v $(pwd)/data:/app/data expense-api
```

or with Docker Compose:

```bash
docker-compose up --build
```

The `-v`/volume mount persists `expenses.json` on the host across container restarts;
omit it if you're fine with data resetting each time the container is recreated.

## API reference (quick)

| Method | Path              | Description                                   |
|--------|-------------------|------------------------------------------------|
| POST   | `/expenses`       | Add an expense                                 |
| GET    | `/expenses`       | List expenses (optional filters, see below)    |
| GET    | `/expenses/{id}`  | Get one expense                                |
| DELETE | `/expenses/{id}`  | Delete an expense                              |
| GET    | `/expenses/total` | Total + by-category breakdown (same filters)   |

Filter query params (all optional, usable on both `/expenses` and `/expenses/total`):
`category`, `q`, `date_from`, `date_to`, `min_amount`, `max_amount`.

Full request/response schemas are available at `/docs` once the server is running.

## Design notes

- **IDs** are server-assigned auto-incrementing integers, tracked in the JSON file
  alongside the expense records.
- **Validation**: `amount` must be `> 0`, `title`/`category` can't be blank, `date`
  must be a valid ISO date (`YYYY-MM-DD`). Invalid input returns `422`.
- **Filter validation**: an inverted range (`date_from` after `date_to`, or
  `min_amount` above `max_amount`) returns `400` rather than silently returning
  an empty list.
- **Totals always reflect the active filter set** — there's no separate
  "totals for category X" endpoint; instead `/expenses/total` accepts the exact
  same query params as `/expenses`, so the same filter (category, date range,
  search term, amount range, or any combination) narrows both what you see and
  what gets summed.
