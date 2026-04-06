#!/usr/bin/env bash
# .env 변경 시 docker compose up -d 로 다시 올림.
# Compose가 설정 차이를 보면 필요한 컨테이너를 알아서 recreate 하므로
# 보통 --force-recreate 없이도 환경변수가 반영됨.
# 억지로 전부 다시 만들려면: FORCE_RECREATE=1 ./scripts/watch-env-recreate.sh
# 한 번에 기동+감시: bash scripts/dev-up-with-env-watch.sh
# Windows: Git Bash에서 실행. COMPOSE_FILE / SERVICES / INTERVAL 로 조정 가능.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.dev.yml}"
SERVICES="${SERVICES:-api web nginx}"
INTERVAL="${INTERVAL:-2}"
ENV_FILE="${ENV_FILE:-$ROOT/.env}"
FORCE_RECREATE="${FORCE_RECREATE:-0}"

hash_env() {
	if command -v md5sum >/dev/null 2>&1; then
		md5sum "$ENV_FILE" | awk '{print $1}'
	elif command -v md5 >/dev/null 2>&1; then
		md5 -q "$ENV_FILE"
	else
		# fallback: mtime
		stat -c '%Y' "$ENV_FILE" 2>/dev/null || stat -f '%m' "$ENV_FILE"
	fi
}

if [[ ! -f "$ENV_FILE" ]]; then
	echo "No file: $ENV_FILE" >&2
	exit 1
fi

UP_ARGS=(up -d)
if [[ "$FORCE_RECREATE" == "1" ]]; then
	UP_ARGS+=(--force-recreate)
fi

echo "Watching $ENV_FILE (every ${INTERVAL}s)"
echo "→ docker compose -f $COMPOSE_FILE ${UP_ARGS[*]} $SERVICES"
LAST="$(hash_env)"

while true; do
	sleep "$INTERVAL"
	NOW="$(hash_env)"
	if [[ "$NOW" != "$LAST" ]]; then
		LAST="$NOW"
		echo "[$(date '+%F %T')] .env changed — compose up: $SERVICES"
		docker compose -f "$COMPOSE_FILE" "${UP_ARGS[@]}" $SERVICES
	fi
done
