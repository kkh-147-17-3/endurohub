#!/usr/bin/env python3
"""analytics_events 테이블에서 크롤러/봇이 만든 이벤트를 제거하는 백필 스크립트.

배경
----
봇은 쿠키를 유지하지 않아 페이지 요청마다 새 session_id가 발급된다.
race_view는 SSR(서버사이드)에서 기록되므로, 검색엔진/AI 크롤러가 대회
페이지를 긁을 때마다 1회성 세션 + race_view 1건이 analytics_events에
쌓였다. 2026-04-30 전후로 세션당 이벤트 수가 ~2.7 → ~1.15로 무너진 원인.

식별 방법
---------
nginx 접근 로그(`docker logs`)에서 클라이언트 IP별 User-Agent를 모아,
"봇 UA로만 등장한 IP"(= 순수 봇 IP)를 가려낸다. 사람 UA가 한 번이라도
섞인 IP는 보존한다(보수적 — CGNAT 뒤 실제 사용자 보호). 가려낸 IP를
API와 동일한 방식(SHA256(ip + DJANGO_SECRET_KEY))으로 해싱해
analytics_events.ip_hash와 매칭, 삭제한다.

기본은 dry-run이며, 실제 삭제는 --apply 플래그가 필요하다.

사용 예
-------
    python3 scripts/purge_bot_analytics.py             # 미리보기
    python3 scripts/purge_bot_analytics.py --apply     # 실제 삭제
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile

# Django api/core/utils.py 의 _BOT_UA_RE 와 동일하게 유지할 것.
BOT_UA_RE = re.compile(
    r'bot|crawl|spider|slurp|yeti|daum|facebookexternalhit|mediapartners|'
    r'embedly|bingpreview|google web preview|archive\.org|headlesschrome',
    re.IGNORECASE,
)

# nginx 접근 로그 한 줄의 끝부분: ... "<User-Agent>" "<X-Forwarded-For>"
LOG_TAIL_RE = re.compile(r'"([^"]*)" "([^"]*)"\s*$')

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(REPO_ROOT, '.env')


def load_env(path: str) -> dict[str, str]:
    """단순 KEY=VALUE 형식의 .env 파일을 읽는다."""
    env: dict[str, str] = {}
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            env[key.strip()] = value.strip()
    return env


def hash_ip(ip: str, secret: str) -> str:
    """api/core/utils.py 의 hash_ip 와 동일한 해시."""
    return hashlib.sha256(f'{ip}{secret}'.encode()).hexdigest()


def collect_bot_ips(container: str) -> tuple[set[str], int, int]:
    """nginx 로그를 읽어 (순수 봇 IP 집합, 봇 IP 수, 사람 섞인 IP 수)를 반환."""
    result = subprocess.run(
        ['docker', 'logs', container],
        capture_output=True, text=True, check=True,
    )
    # docker logs 는 stdout/stderr 를 모두 내보낸다. 접근 로그는 둘 중 어디든 올 수 있다.
    lines = (result.stdout + result.stderr).splitlines()

    seen_bot: set[str] = set()
    seen_human: set[str] = set()
    for line in lines:
        m = LOG_TAIL_RE.search(line)
        if not m:
            continue
        ua, xff = m.group(1), m.group(2)
        if xff == '-' or not xff:
            continue  # 내부 요청(헬스체크 등) — 실제 클라이언트 IP 없음
        client_ip = xff.split(',')[0].strip()
        if not client_ip or client_ip.startswith('172.'):
            continue  # docker 내부 게이트웨이 등
        if BOT_UA_RE.search(ua):
            seen_bot.add(client_ip)
        else:
            seen_human.add(client_ip)

    mixed = seen_bot & seen_human
    pure_bot = seen_bot - seen_human
    return pure_bot, len(pure_bot), len(mixed)


def run_psql(env: dict[str, str], sql: str) -> str:
    """psql 을 실행하고 stdout 을 반환한다."""
    cmd = [
        'psql',
        '-h', env.get('DATABASE_HOST_LOCAL', 'localhost'),
        '-p', env.get('DATABASE_PORT', '5432'),
        '-U', env.get('DATABASE_USER', 'postgres'),
        '-d', env.get('DATABASE_NAME', 'endurohub'),
        '-v', 'ON_ERROR_STOP=1',
        '-X', '-q', '-A', '-t',
    ]
    proc = subprocess.run(
        cmd, input=sql, capture_output=True, text=True,
        env={**os.environ, 'PGPASSWORD': env.get('DATABASE_PASSWORD', '')},
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(f'psql failed (exit {proc.returncode})')
    return proc.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--container', default='endurohub-nginx-1',
                        help='nginx 컨테이너 이름 (기본: endurohub-nginx-1)')
    parser.add_argument('--since', default='2026-04-27',
                        help='이 날짜 이후 이벤트만 대상 (기본: 2026-04-27, nginx 로그 보존 시작)')
    parser.add_argument('--apply', action='store_true',
                        help='실제로 삭제한다 (미지정 시 dry-run)')
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    secret = env.get('DJANGO_SECRET_KEY')
    if not secret:
        raise SystemExit('DJANGO_SECRET_KEY 를 .env 에서 찾을 수 없습니다.')
    # 호스트에서 psql 로 접속할 때는 localhost 사용 (.env 의 DATABASE_HOST 는
    # 컨테이너용 host.docker.internal 이므로 별도 키로 덮어쓴다).
    env.setdefault('DATABASE_HOST_LOCAL', 'localhost')

    print(f'[1/3] nginx 로그에서 봇 IP 식별 중 ({args.container})...')
    pure_bot, n_bot, n_mixed = collect_bot_ips(args.container)
    print(f'      순수 봇 IP: {n_bot}개  /  사람 UA 섞인 IP: {n_mixed}개 (보존)')
    if not pure_bot:
        print('삭제 대상 봇 IP가 없습니다.')
        return 0

    bot_hashes = sorted({hash_ip(ip, secret) for ip in pure_bot})

    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False,
                                     encoding='utf-8') as tmp:
        tmp.write('\n'.join(bot_hashes) + '\n')
        hashes_path = tmp.name

    try:
        print('[2/3] 삭제 대상 집계 중...')
        preview_sql = f"""
CREATE TEMP TABLE bot_hashes (h text PRIMARY KEY);
\\copy bot_hashes FROM '{hashes_path}'
\\echo --MATCH--
SELECT event_type, COUNT(*)
FROM analytics_events e JOIN bot_hashes b ON e.ip_hash = b.h
WHERE e.created_at >= '{args.since}'
GROUP BY event_type ORDER BY COUNT(*) DESC;
\\echo --TOTAL--
SELECT COUNT(*) FROM analytics_events e JOIN bot_hashes b ON e.ip_hash = b.h
WHERE e.created_at >= '{args.since}';
"""
        out = run_psql(env, preview_sql)
        print('      삭제될 이벤트 (event_type별):')
        total = '0'
        section = None
        for raw in out.splitlines():
            raw = raw.strip()
            if raw == '--MATCH--':
                section = 'match'
                continue
            if raw == '--TOTAL--':
                section = 'total'
                continue
            if not raw:
                continue
            if section == 'match':
                etype, cnt = raw.split('|')
                print(f'        {etype:<16} {cnt:>8}')
            elif section == 'total':
                total = raw
        print(f'      합계: {total}건')

        if not args.apply:
            print('[3/3] dry-run 입니다. 실제 삭제하려면 --apply 를 붙여 다시 실행하세요.')
            return 0

        print('[3/3] 삭제 실행 중...')
        delete_sql = f"""
CREATE TEMP TABLE bot_hashes (h text PRIMARY KEY);
\\copy bot_hashes FROM '{hashes_path}'
BEGIN;
DELETE FROM analytics_events e USING bot_hashes b
WHERE e.ip_hash = b.h AND e.created_at >= '{args.since}';
COMMIT;
\\echo --REMAINING--
SELECT COUNT(*) FROM analytics_events;
"""
        out = run_psql(env, delete_sql)
        remaining = next((l.strip() for l in out.splitlines()
                          if l.strip() and l.strip() != '--REMAINING--'), '?')
        print(f'      삭제 완료. 남은 analytics_events: {remaining}건')
        return 0
    finally:
        os.unlink(hashes_path)


if __name__ == '__main__':
    sys.exit(main())
