# Hasebty Backend

FastAPI REST API for Team 10 Hasebty (PC building service).

Stack: Python, FastAPI, SQLModel, PostgreSQL, Pydantic, JWT login with roles, Pytest, Ruff, MyPy.

## Scope by week

**Week 1**

- PostgreSQL + SQLModel data model.
- Customer/staff JWT login.
- 50 sample parts across 8 categories.
- Agreed API contract published in `/docs`.

**Week 2**

- Parts endpoints with filters (`category` name or id, `search`, `in_stock`) and pagination.
- Builds endpoints: `POST /builds`, `GET /builds/{id}`, `PUT /builds/{id}`, `GET /me/builds`.
- The build total price is always calculated by the API (`total` in every build response and in
  `/builds/{id}/check`). If staff change a price, saved builds show the new total.
- Pagination on long lists: `?page=1&limit=50` (limit max 100). The response keeps the same shape
  and adds `meta: {page, limit, total}`.
- Validation errors (422) return `errors` as `{ "field": "message" }`.

**Week 3**

- Compatibility checks (rules 2-5) and ordering protection (rule 6). Details below.
- CI workflow that runs Ruff, MyPy and pytest.

## Decisions agreed in Week 1

- **8 categories and 50 sample parts**: loaded by `seed.py`.
- **PSU safety margin is 20%**: the power supply must give at least 20% more power than the
  estimated consumption of the build.
- **Second part in the same category**: the newly selected part **replaces** the existing one
  (it is not refused). For example, a second CPU replaces the first CPU.

## Run locally

1. Create a PostgreSQL database named `hasebty`.
2. Copy `.env.example` to `.env` and put your PostgreSQL URL and a real secret key in it.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Load the demo data (safe to run more than once):

```bash
python seed.py
```

5. Start the API:

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`. If Windows blocks port 8000, add `--port 8001`.

### Demo accounts (created by `python seed.py`)

| Role | Phone | Password |
|---|---|---|
| Staff | 07700000000 | Staff123! |
| Customer | 07711111111 | Customer123! |

Only a customer can save builds and place orders. A staff login gets 403 on `POST /builds`.
Change or remove these demo accounts before a real deployment.

### Login note for the apps

`POST /auth/login` uses the OAuth2 form (`application/x-www-form-urlencoded`). Send the phone
number in the `username` field and the password in the `password` field.

## Run with Docker

```bash
docker compose up --build
```

- API: http://localhost:8000 (docs at http://localhost:8000/docs).
- PostgreSQL runs in its own container and its data is kept in the `pgdata` volume.
- The seed runs automatically on every start.
- Optional: copy `.env.example` to `.env` to change the database password or `SECRET_KEY`.
- Stop: `docker compose down` (add `-v` to also delete the database data).

## Tests, lint and types

```bash
pytest          # uses an in-memory SQLite database, never your PostgreSQL one
ruff check .
ruff format --check .
mypy app seed.py
```

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

### Response shape

Success:

```json
{
  "success": true,
  "data": {},
  "message": "Request completed successfully"
}
```

List endpoints also return `"meta": {"page": 1, "limit": 50, "total": 120}`.

Error:

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {}
}
```

Status codes: 200/201 success, 400 a business rule was broken, 401 not logged in, 403 wrong role,
404 not found, 422 invalid input.

## Business rules

| # | Rule | Where |
|---|---|---|
| 1 | A build has one part per category (a second part replaces the first) | `build_service.validate_part_ids` |
| 2 | The CPU must fit the motherboard socket | `compatibility.py` |
| 3 | The RAM type must match the motherboard | `compatibility.py` |
| 4 | The motherboard must fit the case | `compatibility.py` |
| 5 | The power supply must be strong enough (20% margin) | `compatibility.py` |
| 6 | A build with any problem can't be ordered | `order_service.create_order` |
| 7 | The total price is calculated by the API | `build_service.calculate_total` |
| 8 | A part with zero stock can't be ordered | `order_service.create_order` |
| 9 | Order status only moves forward | `order_service.change_status` |

Every rule has its own pytest.

### Compatibility checks (rules 2-5)

They live in `app/services/compatibility.py` as plain functions (no database, no HTTP).

| Rule | What is checked | Example warning |
|---|---|---|
| 2 | CPU `socket` = motherboard `socket` | The CPU socket (AM5) does not match the motherboard socket (LGA1700) |
| 3 | RAM `ram_type` = motherboard `ram_type` | The RAM type (DDR4) does not match the motherboard (DDR5) |
| 4 | Motherboard `form_factor` is not bigger than the case `form_factor` (Mini-ITX < mATX < ATX < E-ATX) | The motherboard (ATX) is too big for the case (Mini-ITX) |
| 5 | PSU `wattage` >= (sum of the other parts' `wattage`) x 1.2 | The power supply (300 W) is too weak: the build needs about 450 W, and with the margin at least 540 W |

- `GET /builds/{id}/check` returns `warnings` (a list of messages, empty = no problems) and `total`.
  Build responses (`POST/PUT/GET /builds`, `GET /me/builds`) also include `warnings`.
- A rule is only checked when the parts it needs are in the build, and a part with an empty field
  is skipped. An unfinished build is not a problem, but an **empty** build can't be ordered.
- Rule 6: `POST /orders` for a build with any warning returns **400** with the warnings in the message.
- Estimated consumption = the `wattage` of every part except the PSU (CPU and GPU in the sample data).

## Part images

- Every part has an optional `image_url`, returned by `GET /parts` and `GET /parts/{id}` as a full
  link (or `null`). Staff set it with `POST /parts` and `PUT /parts/{id}`: an `https://` link, or a
  picture on our server such as `/static/parts/cpu.png`.
- The API serves 8 category pictures from `app/static/parts/` at `/static/parts/<name>.png`.
  `python seed.py` gives every sample part the picture of its category (existing parts too).
- Set `PUBLIC_BASE_URL` to the API's public address (for example `https://api.example.com`) so
  `/static/...` paths are returned as full links. Without it the response keeps the path.
- Existing databases get the new column automatically when the API starts
  (`add_missing_columns` in `app/database.py`).

## CI

`.github/workflows/ci.yml` runs Ruff, MyPy and pytest on every pull request. It needs no
PostgreSQL because the tests use an in-memory SQLite database.

## Future ideas

- Prices from several stores for the same part (new `stores` and `store_prices` tables), so the
  customer can compare and choose where to buy.