#!/usr/bin/env bash
# 로컬에서 Django API + SvelteKit 두 서버를 동시에 실행 (도커 없이).
# - API: Django runserver 가 .py 변경 시 자동 재시작
# - Web: Vite dev 가 .ts/.svelte 변경 시 HMR
# 사용: bash scripts/dev-local.sh
# 종료: Ctrl+C (두 프로세스 모두 종료됩니다)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-3001}"
export API_PORT WEB_PORT

API_PID=""
WEB_PID=""

# Windows(MINGW/Git Bash) 인지 감지 — taskkill 로 자식 트리까지 정리
IS_WIN=0
case "$(uname -s 2>/dev/null)" in
	MINGW*|MSYS*|CYGWIN*) IS_WIN=1 ;;
esac

kill_tree() {
	local pid="$1"
	[[ -z "$pid" ]] && return 0
	if [[ "$IS_WIN" == "1" ]] && command -v taskkill >/dev/null 2>&1; then
		# /T = 자식까지, /F = 강제. PID 가 이미 죽었으면 무시.
		taskkill //PID "$pid" //T //F >/dev/null 2>&1 || true
	else
		# Unix: 프로세스 그룹 시그널 시도, 실패 시 단일 PID
		kill -TERM "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
	fi
}

cleanup() {
	echo ""
	echo "[dev-local] 종료 중..."
	kill_tree "$API_PID"
	kill_tree "$WEB_PID"
	wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# 로그를 prefix 와 함께 출력
prefix() {
	local tag="$1"
	while IFS= read -r line; do
		printf '[%s] %s\n' "$tag" "$line"
	done
}

# 백그라운드로 두 서버 실행, 각자의 stdout/stderr 에 prefix 부여
# (Windows 에선 setsid 가 없으므로 직접 bash 호출)
if [[ "$IS_WIN" == "1" ]]; then
	( bash "$ROOT/scripts/dev-api.sh" 2>&1 | prefix api ) &
	API_PID=$!
	( bash "$ROOT/scripts/dev-web.sh" 2>&1 | prefix web ) &
	WEB_PID=$!
else
	( setsid bash "$ROOT/scripts/dev-api.sh" 2>&1 | prefix api ) &
	API_PID=$!
	( setsid bash "$ROOT/scripts/dev-web.sh" 2>&1 | prefix web ) &
	WEB_PID=$!
fi

echo ""
echo "[dev-local] api  pid=$API_PID  →  http://localhost:${API_PORT}"
echo "[dev-local] web  pid=$WEB_PID  →  http://localhost:${WEB_PORT}"
echo "[dev-local] Ctrl+C 로 두 서버 함께 종료"
echo ""

# 둘 중 하나라도 죽으면 같이 정리
wait -n "$API_PID" "$WEB_PID" || true
