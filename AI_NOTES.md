            AI Notes

 1. What was AI-generated vs. hand-written

AI-generated: the full initial implementation — `src/main.py`, `src/models.py`,
  `src/storage.py`, `tests/test_api.py`, `tests/conftest.py`, `Dockerfile`,
  `docker-compose.yml`, `requirements.txt`. I built this in conversation with
  Claude, describing the requirements and reviewing/testing what it produced
  rather than writing the initial code by hand.
The test suite initially covered around 19 cases. I asked for additional
  filtering capabilities beyond the base requirements — filtering by date
  range, category, and title search — which brought the total up to 32 tests
  once the corresponding endpoint behavior and edge cases were covered.

 2. What I validated or tested, and why

I manually went through the code and endpoints myself rather than trusting
  the output blindly.
I ran `pytest tests/ -v` on a clean checkout and confirmed all 32 tests pass.
I ran the server locally and exercised every endpoint by hand — through
  both curl and the Swagger UI at `/docs` — covering add, list, filter by
  category/date/search/amount, total (overall and filtered), delete, and
  delete-again (expect 404).
I built and ran the Docker image myself (`docker build` + `docker run`) and
  confirmed the containerized API responds correctly on `localhost:8000`,
  rather than assuming the Dockerfile was correct as generated.

 3. AI suggestions I didn't use, and why

 The AI initially suggested Flask instead of FastAPI, since Flask was the
  technology I already had experience with from a previous project, and using
  a familiar stack would be safer if the project came up in an interview
  discussion. I decided not to take that suggestion. I researched the
  difference and found FastAPI has real advantages over Flask for this kind
  of API — better performance, automatic request validation via Pydantic, and
  auto-generated interactive documentation (Swagger/OpenAPI) with no extra
  setup. I saw this assignment as a good opportunity to learn a new tool
  rather than default to what I already knew, even at the risk of being asked
  harder questions about it later. Working through this project left me
  reasonably confident explaining FastAPI vs. Flask, and HTTP methods/API
  design generally, if asked about it.

  Notes on scope

Bonus feature implemented: "search expenses" — the `q` query parameter on
  `/expenses` and `/expenses/total` does a case-insensitive substring match on
  title. Swagger/OpenAPI docs are also included at `/docs`, but that's a
  built-in FastAPI feature rather than a deliberate "bonus" choice.
Docker support is included (`Dockerfile` + `docker-compose.yml`). I built
  and ran the image myself locally and confirmed the API works correctly
  inside the container.