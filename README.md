# AI Face Attendance System

Local-first facial recognition attendance app with FastAPI, MongoDB, FaceNet embeddings, LangChain query tools, and a React dashboard.

## Architecture

```mermaid
flowchart LR
  Teacher[Teacher Dashboard] -->|JWT + multipart frames| API[FastAPI]
  API --> Auth[Simple Teacher Auth]
  API --> Face[FaceNet: MTCNN + InceptionResnetV1]
  Face --> Match[Cosine Similarity Matcher]
  Match --> Mongo[(MongoDB)]
  API --> Audit[Recognition Audit Log]
  API --> Agent[LangChain Agent]
  Agent --> Tools[Mongo Tools]
  Tools --> Mongo
  Mongo --> Export[CSV Report]
```

## Defaults and Assumptions

- No cloud face API is used. Face detection and embeddings run locally with `facenet-pytorch`.
- Embeddings are encrypted at rest in MongoDB as `face_embedding_encrypted`; raw photos are not stored.
- MongoDB Atlas Vector Search can be added later, but this implementation uses manual cosine similarity for local parity.
- Teacher auth is intentionally simple: one username/password from `.env` and JWT for API calls.
- Recognition threshold is configurable with `RECOGNITION_THRESHOLD`, default `0.60`.
- LangChain uses Ollama by default and can switch to OpenAI or Anthropic via env vars.
- Class IDs are free-text values in this prototype; a dedicated `classes` collection can be added when class scheduling is implemented.

## Project Structure

```text
backend/
  app/
    api/          FastAPI routes and auth dependencies
    agent/        LangChain agent and Mongo tools
    core/         config, JWT, encryption, rate limit
    db/           Mongo connection, repositories, reports
    models/       Pydantic schemas
    services/     face embedding, encryption, matching
  scripts/        standalone embedding extraction
frontend/         React + Vite dashboard
  Dockerfile      Production nginx container for the dashboard
models/           reserved for local model artifacts
tests/            matcher and Mongo repository tests
```

## Setup

1. Create `.env`.

```bash
cp .env.example .env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Paste the generated key into `EMBEDDING_ENCRYPTION_KEY`.

2. Start the full Docker stack.

```bash
docker compose up --build
```

This starts MongoDB, the FastAPI backend on `http://localhost:8000`, and the dashboard on `http://localhost:5173`.

For a non-local host, set `FRONTEND_API_BASE` in `.env` before building so the static frontend calls the correct backend URL.

3. Or run the backend locally.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

4. Start the frontend.

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Default login is `teacher` / `teacher123` unless changed in `.env`.

## Build Order Verification

### 1. Face detection + embedding extraction

```bash
PYTHONPATH=backend python backend/scripts/extract_embedding.py path/to/student.jpg --out embedding.json
```

The script outputs a normalized 512-dimensional embedding.

### 2. MongoDB schema + CRUD

Indexes are created at FastAPI startup:

- `students`: unique `(class_id, roll_no)`
- `attendance`: unique `(student_id, class_id, date)`
- `recognition_audit`: newest first

### 3-6. API

Login first:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"teacher","password":"teacher123"}'
```

Use the returned token:

```bash
TOKEN=...
curl -X POST http://localhost:8000/enroll \
  -H "Authorization: Bearer $TOKEN" \
  -F name="Alice" \
  -F roll_no="45" \
  -F class_id="CS101" \
  -F consent=true \
  -F photo=@alice.jpg

curl -X POST http://localhost:8000/recognize \
  -H "Authorization: Bearer $TOKEN" \
  -F class_id="CS101" \
  -F frame=@frame.jpg

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/attendance/CS101/2026-07-02

curl -X POST http://localhost:8000/agent/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"Who was absent in CS101 today?"}'
```

### 7. Frontend Dashboard

The React app supports:

- Teacher login
- Webcam capture and recognition overlay result
- Student enrollment with consent checkbox
- Attendance table per class/date
- Natural-language agent chat
- CSV export button

### 8. Docker

`docker-compose.yml` runs MongoDB, the backend, and the production frontend container. Health checks are configured so the frontend waits for the API and the API waits for MongoDB.

```bash
docker compose up --build
```

The frontend container serves the built React app through nginx. For deployment behind a different hostname, set:

```bash
FRONTEND_API_BASE=https://your-api-host.example.com
CORS_ORIGINS=https://your-dashboard-host.example.com
```

## API Summary

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/auth/login` | Teacher JWT login |
| `POST` | `/enroll` | Detect face, extract embedding, encrypt and store student |
| `POST` | `/recognize` | Detect face, match embedding, mark attendance |
| `GET` | `/attendance/{class_id}/{date}` | Attendance rows for a class/date |
| `POST` | `/agent/query` | LangChain natural language query |
| `GET` | `/report/{class_id}?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` | CSV export |

## Tests

```bash
PYTHONPATH=backend pytest
```

Tests cover embedding cosine matching and Mongo-style student/attendance/absentee queries with `mongomock-motor`.
