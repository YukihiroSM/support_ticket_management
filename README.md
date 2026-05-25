# Support Ticket Manager

FastAPI service for customer support tickets with async processing via SQS (LocalStack).

> _This README was drafted and formatted with AI assistance; all content reflects actual decisions and behavior of the codebase._

## Run

```bash
cp .env.example .env
# set LOCALSTACK_AUTH_TOKEN in .env — free token from
# https://app.localstack.cloud/getting-started
docker compose up --build
```

- UI:   http://localhost:8101/
- Docs: http://localhost:8101/docs
- Seed: `docker compose exec api python -m scripts.seed`

The UI (single HTML file under [frontend/](frontend/)) exercises every endpoint and shows an activity log of each request/response.

> **Note:** the frontend is AI-generated and exists purely as a manual testing console — it is not part of the assignment deliverable and was not hand-reviewed for production use.

## Stack

FastAPI · SQLAlchemy (async) · PostgreSQL · Alembic · aioboto3 + SQS · Docker Compose

## Endpoints

All under `/api/v1`.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST`  | `/tickets` | create |
| `GET`   | `/tickets` | list (filters: `status`, `priority`, `category`, `customer_id`, `agent_id`; `page`, `page_size`) |
| `GET`   | `/tickets/{id}` | retrieve with processing result |
| `PATCH` | `/tickets/{id}/status` | update status (validates transitions) |
| `PATCH` | `/tickets/{id}/assignment` | assign / unassign agent |
| `POST`  | `/agents` | create agent |
| `GET`   | `/agents` | list agents (filter: `is_active`; `page`, `page_size`) |
| `GET`   | `/agents/{id}` | get agent |
| `PATCH` | `/agents/{id}` | update name / active flag |
| `DELETE`| `/agents/{id}` | soft-delete (sets `is_active=false`) |
| `GET`   | `/health`, `/health/ready` | liveness / readiness |

Allowed status transitions: `OPEN ↔ IN_PROGRESS → RESOLVED → CLOSED` (closed is terminal). Defined in `app/enums.py`.

## Layout

```
app/
  api/           routers, deps, error handlers
  schemas/       pydantic DTOs
  services/      business logic, owns the transaction
  repositories/  data access
  models/        SQLAlchemy models
  queue/         SQS client + publisher
  worker.py      SQS consumer
migrations/      Alembic
scripts/         seed.py, localstack-init.sh
```

## Async flow

`POST /tickets` → commit → publish `ticket.created` to SQS → worker consumes → writes `ticket_processing_results` + `PROCESSED` event. Failed messages stay in flight and redrive to the DLQ after 3 attempts.

## Architecture decisions

Why it looks the way it does:

- **Async FastAPI + SQLAlchemy 2.0 + asyncpg, end-to-end.** One driver in both API and worker — no `run_in_executor` surprises, no mixing sync and async greenlets in the same session.
- **SQS (LocalStack locally) instead of Redis + Celery/RQ.** SQS lets you get DLQ + redrive policy out of the box — no need to roll your own retry/backoff. The worker is just a long-poll loop. This service is a new one for me as I was using GCP mostly, so it just sounds as a proper decision for me.
- **Clear service / repository split.** Repos only query and `flush`; **commits live in the service**. That makes it easy to extend a transaction (e.g. status change + `ticket_events` row atomically) and keeps the router thin.
- **`ticket_events` as an append-only audit log.** Every change (`CREATED`, `STATUS_CHANGED`, `ASSIGNED`, `PROCESSED`, …) is its own row with `from_status` / `to_status` / `actor_id`. No separate snapshot table — history reconstructs from a single query.
- **Publish after commit.** `session.commit()` first, then `publisher.publish_created(...)`. Otherwise the worker could read an SQS message for a ticket that doesn't exist in the DB yet. If the publish itself fails, we log it but the ticket is safely persisted (a re-publisher walking `processing_status=PENDING` can be added later).
- **Status transitions validated in the service, not in the DB.** The map lives in `app/enums.py::ALLOWED_STATUS_TRANSITIONS` and raises `InvalidStatusTransitionError` (422 with an `allowed` list). Easier to evolve than a CHECK constraint and gives the client a useful error.
- **Native PostgreSQL enums.** Not `varchar + check`. Type-safe, reads cleanly in `psql`, and Alembic creates/drops the types explicitly in the migration.
- **Soft-delete for agents (`is_active=false`).** `tickets.agent_id` references users with `SET NULL` — hard delete would work, but you'd lose the audit (who assigned a ticket to whom). So DELETE = deactivation.
- **`session.refresh()` after commit on mutations.** Columns with `onupdate=func.now()` are server-side expressions — SQLAlchemy doesn't know the new value without a re-read. Without `refresh`, Pydantic hits `MissingGreenlet` when reading `updated_at`.
- **Auto-provision customer by email.** The assignmnent asks for `customer_name + customer_email` (not `customer_id`). If no user exists with that email, we create a `CUSTOMER`.
- **No auth.** Instead of JWT, payloads accept an optional `actor_id` for audit. When auth is added, `actor_id` is derived from the request context and dropped from the schemas.

## Environment variables

| Var | Default | Notes |
| --- | --- | --- |
| `APP_ENV` | `local` | `local` / `test` / `staging` / `production` |
| `LOG_LEVEL` | `INFO` | stdlib level name |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@postgres:5432/support_tickets` | asyncpg DSN |
| `AWS_ENDPOINT_URL` | `http://localstack:4566` | unset against real AWS |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | `test` | dummy creds for LocalStack |
| `AWS_DEFAULT_REGION` | `us-east-1` | |
| `SQS_QUEUE_URL` | LocalStack URL | main processing queue |
| `WORKER_POLL_WAIT_SECONDS` | `20` | SQS long-poll window |
| `WORKER_MAX_MESSAGES` | `10` | max messages per `receive_message` |
| `LOCALSTACK_AUTH_TOKEN` | _(required)_ | LocalStack Pro token; consumed by the `localstack` compose service, not the app. Free token: https://app.localstack.cloud/getting-started |

All vars are read in `app/config.py` via `pydantic-settings`. Defaults come from `.env`.
