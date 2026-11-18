# Mission Control

Go/No-Go launch console. Engineers file anomaly reports; plain code checks launch limits and sets
the verdict; Claude (on Azure AI Foundry) sorts the report, runs safety checks and drafts a
briefing; only the Flight Director can approve it.

Work in progress: see the plan in the PR history.

## Test

```bash
uv run pytest
```
