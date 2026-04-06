#!/usr/bin/env bash
# 한 번 실행: compose 기동 + .env 변경 시 자동으로 `docker compose up -d` 재실행.
# 사용: bash scripts/dev-up-with-env-watch.sh
# 로그만 보고 싶으면 이미 compose가 떠 있는 상태에서 watch-env-recreate.sh 만 써도 됨.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.dev.yml}"

docker compose -f "$COMPOSE_FILE" up -d

cleanup() {
	if [[ -n "${WATCH_PID:-}" ]] && kill -0 "$WATCH_PID" 2>/dev/null; then
		kill "$WATCH_PID" 2>/dev/null || true
	fi
}
trap cleanup EXIT INT TERM

bash "$ROOT/scripts/watch-env-recreate.sh" &
WATCH_PID=$!

echo ""
echo ".env watcher PID $WATCH_PID — 파일 바뀌면 자동으로 compose up -d 가 다시 돌아갑니다."
echo "아래는 컨테이너 로그입니다. 끝내려면 Ctrl+C (watcher도 같이 종료됩니다)."
echo ""

docker compose -f "$COMPOSE_FILE" logs -f
