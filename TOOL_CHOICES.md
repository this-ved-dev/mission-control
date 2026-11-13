# Tool choices

Each choice has a specific reason, one alternative we rejected, and the customer concern it answers. The customer is Meridian Launch Services: a Flight Director 90 minutes from launch, and the engineers filing reports.

## Back end: Python 3.13 + FastAPI (managed with uv)

- **Why:** The Pydantic models that check every report also generate the 422 messages and the OpenAPI spec, so validation, error text and API docs come from one place. Native `async` makes running the three model checks together a single `asyncio.gather`. uv gives a locked, reproducible install in one command.
- **Rejected:** Django. Its ORM, admin and template system bring a lot of machinery this app doesn't need. It also has weaker built-in async and no schema-first validation.
- **Customer concern:** *"A bad reading must never slip in silently."* Every field is checked on the server with a message that names the field (`fuel_pct: Input should be less than or equal to 150`). A reading outside the launch limits is still accepted, because it's real data and the limits code has to judge it.

## Front end: React + Vite + TypeScript, with the anatomy isometric kit

- **Why:** The console is mostly live, animated SVG: the Go/No-Go Bench, dial gauges and countdown rings. React components with refs let the figures move at 60 fps without re-rendering. TypeScript types are generated from `openapi.json`, so the browser and the API can't drift apart without CI failing.
- **Rejected:** Next.js. Server rendering and a second server process add nothing to a single-screen operator console behind a proxy, and they complicate the one-command Docker start.
- **Customer concern:** *"The Flight Director has no time to read raw messages."* The verdict is a large stamp, the brief-by deadline is a draining ring, and the bench shows at a glance which step the report is on, which gauge failed and whether a person has turned the key.

## Database: SQLite (a file on a Docker volume)

- **Why:** One file, no server, part of the Python standard library. Reports survive restarts (there's a test for it), and the approval is one atomic `UPDATE … WHERE status IN (…)`, so two clicks can't approve twice.
- **Rejected:** PostgreSQL. It would need its own container, credentials and migrations for one control room's traffic, and it would add a failure point 90 minutes before launch.
- **Customer concern:** *"We cannot lose a report."* Each report is saved before the pipeline runs. A model outage or a crash leaves it on disk with status `error`, and the console offers **Retry pipeline**.

## Model: a local model in Ollama, through the OpenAI-compatible API

- **Why:** The model runs on the engineer's own 24 GB Apple-silicon laptop, so anomaly data never leaves the site and there's no per-token bill. Ollama serves the de-facto standard `/v1/chat/completions` API with JSON-schema structured output. One adapter (`OpenAICompatClient`) therefore works with Ollama today and with any compatible host tomorrow, changed in `.env`. Every reply is validated with Pydantic and falls back safely, so a smaller local model can't break the pipeline.
- **Rejected:** a vendor SDK tied to one hosted provider. It would lock the code to one company's API and send launch data off site. The tests would also have to mock that SDK instead of one small interface.
- **Customer concern:** *"What does each report cost, and can we trust the model?"* Cost is computed in code from a price table, using `Decimal`. Local models default to $0, and you can set a cloud-equivalent rate to compare. The model never decides the verdict and never approves anything: code sets the verdict and a person approves.
