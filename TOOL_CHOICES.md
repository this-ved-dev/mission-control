# Tool Choices

The customer is Meridian Launch Services: a control room 90 minutes from launch, where a wrong
or late briefing has real consequences. Every choice below was made for that room.

## Back end: Python 3.13 + FastAPI

**Why.** Each report needs validation with plain-English errors, three model calls in parallel,
and a documented API. FastAPI does all three without extra libraries: Pydantic models produce
field-level validation errors that we turn into messages such as `wind_knots must be between 0 and 200`,
`asyncio.gather` runs the injection, missing-details and panic checks at the same time, and the
OpenAPI 3.1 spec is generated from the same code, so it can't fall out of date (CI checks this).

**Rejected: Django.** Its ORM, admin site and template system are built for content sites. We'd
carry them without using them, and async views plus an OpenAPI spec would need extra packages.

**Customer concern: "A bad report must be rejected clearly, never half-saved."** Validation is
declared once on `ReportIn`, it runs before anything touches the database, and each field gets its
own message in both the API and the form.

## Front end: server-rendered Jinja templates, hand-written CSS, vanilla JS

**Why.** The console is a list, a detail view, a form and an Approve button. Rendering it on the
server means one language, one test runner (`pytest` asserts on the HTML), and no build step. The
only JavaScript is about 50 lines for countdowns and a refresh while a report is processing. The
font is vendored, so the page loads with no CDN, which matters on a control-room network.

**Rejected: React + Vite.** It's a fine tool, but it would add a second toolchain (npm), a
second test runner, a generated API client, and a build step to break on launch day, for a UI with
two screens.

**Customer concern: "The console must load instantly and work offline in the control room."** Each
page is plain HTML and CSS served by the app, with nothing fetched from the internet. It still works
with JavaScript off; only the live countdowns stop.

## Database: SQLite (WAL mode, standard library `sqlite3`)

**Why.** One control room files a few dozen reports in a countdown. SQLite stores them in a
single file with transactions. It ships with Python, so there's no server to run. In Docker the
file lives on a named volume (`mc-data`), and CI checks that a report survives a container restart.
Approval is one atomic `UPDATE ... WHERE status IN (...)`, so two clicks can't approve twice.

**Rejected: PostgreSQL.** It's the right choice for many writers across many sites, but here it
would mean a second container, credentials and migrations, and it would break the one-command start.

**Customer concern: "We cannot lose a report."** Each report is committed to disk before any model
runs. If the server restarts mid-pipeline, the report is still there and is re-run on startup.

## Model: Claude Sonnet 5.5 on Azure AI Foundry

**Why.** The model has to understand terse, sometimes panicked engineering notes, spot text that
tries to instruct the system, and write a calm 60-word briefing. Sonnet 5.5 is strong at that kind
of judgment, and it supports **structured outputs**, so classifications and checks come back in
a JSON schema that code then validates. Running it through Meridian's Azure AI Foundry deployment
keeps billing and data handling under the existing Azure subscription. Cost is $2 / $10 per million
input / output tokens. Cheap steps (classify and the three checks) run at `effort: low`; drafting
and reviewing run at `medium`.

**Rejected: a local open-weights model through Ollama.** It's free per token, but it's weaker at
following a JSON schema and at spotting injection, and it ties the app to one laptop's GPU.

**Customer concern: "What does each report cost, and could the AI make the launch call?"** Every
model step records its tokens and its cost, computed in code, and the console shows the total per
report. The model never decides: the verdict comes from code before any model sees the note, and
only a named person can approve a briefing.

## Staying model-agnostic

Every model call goes through one `LLMClient` interface (`app/llm.py`). There are two adapters
today: `FoundryClaudeClient` (official `anthropic` SDK, `AsyncAnthropicFoundry`) and `FakeClient`
(scripted, used by the tests and the `MC_LLM=fake` demo). Moving to another provider means writing
one adapter class; the pipeline, its prompts and the tests don't change.

## Supporting tools

| Tool | Why |
|---|---|
| `uv` | One lockfile, reproducible installs, fast in CI and Docker |
| `ruff` | Lint and format in one fast tool |
| `pytest` + `pytest-socket` | Tests prove they need no network or key: sockets are blocked |
| Docker (multi-stage) + compose | The README's one start command and one test command; non-root runtime image with a healthcheck |
| GitHub Actions | Lint, offline tests with a 90% coverage gate, OpenAPI contract check, Docker smoke and restart test, all required before merge |
