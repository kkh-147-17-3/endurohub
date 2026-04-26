#!/usr/bin/env bash
# 로컬에서 SvelteKit dev 서버만 실행 (도커 없이).
# Vite HMR 로 파일 변경 시 자동 반영됩니다.
# 사용: bash scripts/dev-web.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/web"

# .env 로드 (라인별 안전 파싱)
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

# .env 의 PUBLIC_* 변수가 없는 경우, 같은 값의 일반 env 변수에서 매핑
# (web 코드는 PUBLIC_ 접두사를 사용; 루트 .env 는 docker-compose 에서 PUBLIC_ 으로 변환되어 들어감)
export PUBLIC_KAKAO_JAVASCRIPT_KEY="${PUBLIC_KAKAO_JAVASCRIPT_KEY:-${KAKAO_JAVASCRIPT_KEY:-}}"
export PUBLIC_NAVER_MAP_CLIENT_ID="${PUBLIC_NAVER_MAP_CLIENT_ID:-${NAVER_MAP_CLIENT_ID:-}}"
export PUBLIC_GOOGLE_ANALYTICS_ID="${PUBLIC_GOOGLE_ANALYTICS_ID:-${GOOGLE_ANALYTICS_ID:-}}"
export PUBLIC_FEEDBACK_FORM_URL="${PUBLIC_FEEDBACK_FORM_URL:-${GOOGLE_FEEDBACK_FORM_URL:-}}"
export PUBLIC_APP_URL="${PUBLIC_APP_URL:-http://localhost:${WEB_PORT:-3001}}"

# 도커가 아니므로 DOCKER 플래그 비우고 로컬 API 주소로 강제
unset DOCKER
export API_URL_INTERNAL="${API_URL_INTERNAL_LOCAL:-http://127.0.0.1:8000}"

# Windows netsh portproxy 가 3000 을 점유하는 환경 회피용 기본값
# 필요시 WEB_PORT=3000 등으로 호출자가 덮어쓸 수 있음
export VITE_PORT="${WEB_PORT:-3001}"

# 의존성 누락 시 자동 설치
if [[ ! -d node_modules ]]; then
	echo "[dev-web] node_modules 없음 → npm install"
	npm install
fi

echo "[dev-web] http://localhost:${VITE_PORT} (HMR)"
# `--` 뒤 인자는 npm 이 vite 로 그대로 전달. config 보다 우선순위가 높음.
exec npm run dev -- --port "${VITE_PORT}" --strictPort
