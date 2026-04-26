#!/usr/bin/env bash
# 로컬에서 Django API 서버만 실행 (도커 없이).
# 파일 변경 시 Django runserver가 자동으로 재시작합니다.
# 사용: bash scripts/dev-api.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/api"

# venv 파이썬 경로 (Windows / Unix 모두 지원)
if [[ -x "venv/Scripts/python.exe" ]]; then
	PY="venv/Scripts/python.exe"
	PIP="venv/Scripts/pip.exe"
elif [[ -x "venv/bin/python" ]]; then
	PY="venv/bin/python"
	PIP="venv/bin/pip"
else
	echo "[dev-api] venv 를 찾을 수 없습니다. api/venv 가 존재하는지 확인하세요." >&2
	exit 1
fi

# requirements.txt 가 venv 마지막 설치 시점보다 새로우면 자동 재설치
STAMP="venv/.requirements.stamp"
if [[ ! -f "$STAMP" ]] || [[ "requirements.txt" -nt "$STAMP" ]]; then
	echo "[dev-api] requirements.txt 변경 감지 → pip install"
	"$PIP" install -r requirements.txt
	touch "$STAMP"
fi

# .env 로드 (manage.py 의 python-dotenv 의존성 없이도 동작하도록 직접 파싱)
# - 형식: KEY=VALUE (한 줄). 주석/빈 줄 무시.
# - source 가 아닌 라인별 매칭으로, 값에 < > 공백 등이 있어도 안전.
ENV_FILE="$ROOT/.env"
if [[ -f "$ENV_FILE" ]]; then
	while IFS= read -r line || [[ -n "$line" ]]; do
		[[ "$line" =~ ^[[:space:]]*# ]] && continue
		[[ -z "${line//[[:space:]]/}" ]] && continue
		if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
			export "${BASH_REMATCH[1]}=${BASH_REMATCH[2]}"
		fi
	done < "$ENV_FILE"
fi

# 로컬 전용 오버라이드: 도커 네트워크가 아니므로 호스트에서 직접 접근
# (.env 의 docker 용 값이 있더라도 여기서 덮어씀)

PORT="${API_PORT:-8000}"

echo "[dev-api] http://localhost:${PORT} (변경 감지 자동 재시작)"
exec "$PY" manage.py runserver "0.0.0.0:${PORT}"
