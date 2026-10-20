# Hasebty Backend — Weeks 1-2

FastAPI REST API for Team 10 Hasebty.

## Week 1 scope

According to the project scope, Week 1 Backend work is:

- PostgreSQL + SQLModel data model.

- Customer/staff JWT login.

- About 50 sample parts across 8 categories.

- Agreed API contract published in `/docs`.

The project currently has 8 categories and 50 sample parts.

## Run

1. Create a PostgreSQL database named `hasebty`.

2. Copy `.env.example` to `.env`.

3. Put your PostgreSQL URL and a real secret key in `.env`.

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Load demo data:

```bash
python seed.py
```

6. Start the API:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

### Demo staff login

The seed creates a staff account for local testing:

```text
phone: 07700000000
password: Staff123!
```

Change/remove this demo credential before real deployment.

## Week 2 scope

- Parts endpoints with filters (`category` name or id, `search`, `in_stock`) and pagination.
- Builds endpoints: `POST /builds`, `GET /builds/{id}`, `PUT /builds/{id}`, `GET /me/builds`.
- Build total price is always calculated by the API (`total` in every build response and in
  `/builds/{id}/check`). If staff change a price, saved builds show the new total.
- Pagination on long lists: `?page=1&limit=50` (limit max 100). The response keeps the same shape
  and adds `meta: {page, limit, total}`.
- Validation errors (422) return `errors` as `{ "field": "message" }`.

## Tests, lint and types

```bash
pytest          # uses an in-memory SQLite database, never your PostgreSQL one
ruff check .
ruff format --check .
mypy app seed.py
```

## Login note for the apps

`POST /auth/login` uses the OAuth2 form (`application/x-www-form-urlencoded`). Send the phone number
in the `username` field and the `password` field.

## API contract

### Public

- `POST /auth/register`

- `POST /auth/login`

- `GET /categories`

- `GET /parts?category=&search=&in_stock=&page=&limit=`

- `GET /parts/{id}`

### Customer

- `POST /builds`

- `GET /builds/{id}`

- `PUT /builds/{id}`

- `GET /me/builds`

- `GET /builds/{id}/check`

- `POST /orders`

- `GET /me/orders`

### Staff

- `POST /parts`

- `PUT /parts/{id}`

- `GET /orders?status=`

- `PATCH /orders/{id}/status`

- `GET /reports/stats`

The compatibility rules (CPU/socket, RAM/motherboard, motherboard/case, PSU margin) are Week 3 work. The `/builds/{id}/check` endpoint already exists as part of the Week 1 API contract so the mobile team can integrate against the agreed shape.

The agreed **PSU safety margin is 20%**. The selected PSU should provide at least 20% more power than the estimated total system consumption.

When a customer selects a part of a type that already exists in the build, the newly selected part **replaces the existing part** instead of creating a duplicate.

For example, if a build already contains a CPU and the customer selects another CPU, the new CPU replaces the existing CPU.

## Response shape

Success:

```json
{
  "success": true,
  "data": {},
  "message": "Request completed successfully"
}
```

Error:

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {}
}
```
## Run with Docker

```bash
docker compose up --build
```

- API: http://localhost:8000 and docs at http://localhost:8000/docs
- PostgreSQL runs in its own container and its data is kept in the `pgdata` volume.
- The seed runs automatically on every start (demo staff `07700000000` / `Staff123!`).
- Optional: copy `.env.example` to `.env` to change the database password or `SECRET_KEY`.
- Stop: `docker compose down` (add `-v` to also delete the database data).

## Future ideas

- Prices from several stores for the same part (new `stores` and `store_prices` tables), so the
  customer can compare and choose where to buy.
