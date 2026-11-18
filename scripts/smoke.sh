#!/usr/bin/env bash
# Smoke test against a running app (default http://localhost:8000):
# file a report, wait for the pipeline, restart the container, and check the report survived.
set -euo pipefail
BASE=${BASE:-http://localhost:8000}
json() { python3 -c "import json,sys; print(json.load(sys.stdin)$1)"; }

id=$(curl -sf -X POST "$BASE/api/reports" -H 'content-type: application/json' -d '{
  "name": "Smoke Test", "station": "PROP", "wind_knots": 27, "temp_c": 4, "fuel_pct": 98,
  "note": "LOX vent valve 2 slow to close by 400 ms at 08:12."}' | json '["id"]')
echo "filed report $id"

status=""
for _ in $(seq 30); do
  status=$(curl -sf "$BASE/api/reports/$id" | json '["status"]')
  [ "$status" = pending_approval ] && break
  sleep 1
done
echo "status: $status"
[ "$status" = pending_approval ]
[ "$(curl -sf "$BASE/api/reports/$id" | json '["verdict"]')" = no_go ]

docker compose restart app
docker compose up -d --wait app
[ "$(curl -sf "$BASE/api/reports/$id" | json '["status"]')" = pending_approval ]
echo "report $id survived a restart"
