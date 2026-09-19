# EnduroHub: docker-compose → Terraform + k3s 전환 계획 및 노력 산정

## Context

현재 EnduroHub는 홈서버 1대에서 docker compose 2개 프로젝트(앱 + 관측성)로 운영 중이다.

- **앱 스택 (6 서비스)**: api (Django/gunicorn), celery-worker, celery-beat, crawler-worker (Playwright 포함), web (SvelteKit), nginx
- **관측성 스택 (3 서비스)**: lgtm (Grafana 올인원), promtail, otelcol
- **호스트 직접 설치**: PostgreSQL, Redis (compose 밖, `host.docker.internal` 로 접근)
- **인그레스**: Cloudflare Tunnel(cloudflared) → nginx. nginx 가 UA 블랙리스트, JSON access log, static/media 서빙 담당
- **배포**: self-hosted GitHub 러너가 서버에서 `git pull + docker compose up --build` (이미지 레지스트리 없음)

전환 목적은 **학습/포트폴리오** (Terraform·Kubernetes 실무 경험). 타겟은 **기존 홈서버에 k3s 단일 노드**, DB/Redis 도 클러스터 안으로 이전. 클라우드 고정비 0원 유지.

## 총 노력 산정

K8s/Terraform 신규 학습을 병행한다는 가정 하에 **집중 작업일 기준 약 12\~18일, 주말·저녁 파트타임 기준 4\~6주**. 이미 K8s 경험이 있다면 절반 수준.

| 단계 | 작업 | 산정 |
|---|---|---|
| 1 | k3s 설치 + GHCR 레지스트리 + CI 이미지 빌드 전환 | 1.5\~2일 |
| 2 | 스테이트리스 앱 5종 매니페스트/Helm 차트화 | 2\~3일 |
| 3 | nginx + cloudflared 클러스터 이전, static/media PVC | 1.5\~2일 |
| 4 | Postgres/Redis StatefulSet + 데이터 이전 + 백업 CronJob | 2\~3일 |
| 5 | 관측성 스택 K8s 적응 (로그 수집·메트릭 수집 방식 변경) | 2\~3일 |
| 6 | Terraform 코드화 (Cloudflare + helm_release + Secrets) | 1.5\~2일 |
| 7 | CI/CD 재작성 + 컷오버 + 디버깅 버퍼 | 1.5\~3일 |

작업량이 큰 이유 3가지:

1. **관측성 스택이 Docker 전제** — otelcol 의 `docker_stats` receiver, promtail 의 nginx 로그 볼륨 공유는 K8s 에서 kubeletstats / DaemonSet 로그 수집으로 재설계 필요
2. **빌드 파이프라인 구조 변경** — 현재 "서버에서 소스 빌드" 방식은 K8s 와 호환 안 됨. 레지스트리(GHCR) + 이미지 태그 기반 배포로 전환 필수
3. **상태ful 서비스 이전** — Postgres/Redis 를 호스트에서 클러스터 PVC 로 옮기는 데이터 마이그레이션 + 백업 체계 재구축

## 이 상황에서 K8s 의 실질적 프로덕션 가치 (솔직한 평가)

학습 가치를 빼고, 단일 홈서버라는 조건에서 K8s 가 실제로 바꾸는 것과 못 바꾸는 것.

### 실제로 좋아지는 것

| 항목 | 지금 (compose) | K8s 전환 후 |
|---|---|---|
| **배포 다운타임** | `docker compose up --build` 가 컨테이너를 죽이고 새로 만드는 동안 수초\~수십초 단절. 빌드 실패 시 그대로 장애 | 롤링 업데이트 + readiness probe — 새 파드가 "트래픽 받을 준비 완료"를 증명한 뒤에야 구 파드 종료. **무중단 배포** |
| **롤백** | 사실상 없음 — git reset 후 재빌드가 유일한 방법 (수분 소요, 빌드 실패 리스크) | `helm rollback` 또는 이전 이미지 태그 재지정 — **수십초 내 이전 버전 복귀** |
| **프로덕션 서버에서의 빌드 제거** | 배포마다 서버에서 docker build — CPU 스파이크가 라이브 트래픽에 영향, 디스크에 빌드 캐시 누적 | 빌드는 GitHub Actions 로 이동. 서버는 pull 만. 서버 부하·디스크 관리 부담 감소 |
| **행(hang) 감지** | `restart: unless-stopped` 는 프로세스가 죽어야 재시작. gunicorn 이 살아있지만 응답 못 하는 상태는 방치됨 | liveness probe 가 HTTP 응답을 주기 확인 — **좀비 상태 자동 재시작** |
| **배포 이력·가시성** | "지금 뭐가 배포돼 있나" = 서버에 들어가 git log 확인 | 이미지 태그(커밋 SHA)로 배포 버전이 명시적. `kubectl rollout history` 로 이력 조회 |
| **미래 이식성** | 서버 교체/증설 시 수동 재구축 | 같은 차트로 새 노드·클라우드 K8s 에 그대로 배포. 홈서버 → 클라우드 이전이 값싸짐 |

### 좋아지지 **않는** 것 (K8s 의 대표 장점이지만 여기선 해당 없음)

- **고가용성**: 노드가 1대다. 서버가 죽으면 전부 죽는다 — K8s 가 유일하게 못 고치는 단일 장애점이고, 사실 K8s 의 간판 기능이 바로 이것(노드 장애 시 다른 노드로 재스케줄)이다. **이 구조에선 간판 기능이 무효.**
- **오토스케일링**: HPA 로 파드를 늘려봐야 같은 서버의 같은 RAM 을 나눠 쓸 뿐. 무의미.
- **로드밸런싱**: 노드 간 분산이 없으니 실질 효과 없음.

### 냉정한 결론

위 표의 이득 중 **무중단 배포·롤백·빌드 이동은 사실 "K8s" 가 아니라 "이미지 레지스트리 + 헬스체크 기반 교체"에서 온다.** compose 를 유지한 채 GHCR + 헬스체크 + blue-green 스크립트만 도입해도 절반 이상을 훨씬 적은 비용으로 얻을 수 있다. K8s 만이 주는 고유 가치는 (1) 그 패턴들이 검증된 표준 구현으로 내장돼 있다는 것, (2) probe·rollout·CronJob 등을 직접 스크립트로 짜고 유지보수할 필요가 없다는 것, (3) 미래 이식성이다.

따라서 이 전환의 정직한 손익: **운영 품질은 "배포" 영역에서 실질적으로 좋아지고, 가용성은 그대로이며, 시스템 복잡도는 늘어난다 (k3s 오버헤드 약 1GB, 새로운 장애 모드 — PVC 바인딩, DNS, 파드 pending 등).** 학습 목적이 없다면 이 규모에서 권할 전환은 아니고, 학습 목적이 있기에 "실질 이득도 일부 있는 좋은 학습 프로젝트"가 되는 것이 정확한 평가다.

## 권장 아키텍처

```
Cloudflare Tunnel (cloudflared Deployment, Terraform 으로 터널/DNS 관리)
        │
        ▼
nginx Deployment (기존 conf 를 ConfigMap 으로 — UA 차단/JSON 로그/gzip 보존)
   ├─ /api/*, /dj-admin/* → api Service (Django)
   ├─ /static/, /storage/ → PVC 마운트 서빙 (기존과 동일)
   └─ /*                  → web Service (SvelteKit)

api / web / celery-worker / crawler-worker : Deployment
celery-beat                                : Deployment (replicas=1 고정)
postgres / redis                           : StatefulSet + local-path PVC
백업                                        : pg_dump CronJob → PVC(+외부 업로드는 선택)
관측성                                      : lgtm Deployment + alloy(또는 otelcol) DaemonSet
```

- **k3s 내장 Traefik 은 비활성화**하고 기존 nginx 를 그대로 Deployment 로 올린다. UA 블랙리스트·JSON 분석 로그·캐시 헤더 등 커스텀 로직이 많아 Ingress 리소스로 옮기는 것보다 훨씬 저렴하고, 어차피 TLS 는 Cloudflare Tunnel 이 종단하므로 Ingress Controller 의 이점이 거의 없다.
- **스토리지는 k3s 기본 local-path provisioner** (단일 노드라 충분). api_media·static·postgres 데이터가 PVC 로.
- **Secrets**: 1단계는 `kubectl create secret` + Terraform `kubernetes_secret` (tfvars 는 gitignore). sealed-secrets/SOPS 는 학습 스트레치 골.

## 대안 검토: nginx 로직을 Traefik 으로 이식하는 경우

기본 계획은 nginx 유지지만, 학습 목적이라면 Traefik 이식도 검토할 만하다. 항목별 이식 가능성:

| nginx 기능 | Traefik 대응 | 난이도 |
|---|---|---|
| gzip 압축 | `compress` 미들웨어 (gzip/brotli/zstd, `minResponseBodyBytes` 로 최소 크기 지정) | 쉬움 |
| static/media 캐시 헤더 | `headers` 미들웨어로 라우터별 Cache-Control 지정 | 쉬움 |
| `client_max_body_size 20M` | `buffering` 미들웨어의 `maxRequestBodyBytes` | 쉬움 |
| 프록시 타임아웃 (120s/300s) | `serversTransport` 의 forwardingTimeouts | 쉬움 |
| WebSocket 업그레이드 | 별도 설정 없이 자동 지원 | 쉬움 |
| 경로 라우팅 (/api, /dj-admin, /) | IngressRoute 의 `PathPrefix` 매처 — 인그레스 본연의 기능 | 쉬움 |
| JSON 구조화 access log | 내장 JSON access log 지원. 단, **필드 구성이 nginx 커스텀 포맷과 다름** → promtail 파이프라인과 Grafana 대시보드 쿼리 재작성 필요. `blocked` 같은 커스텀 필드는 없어서 라우터 이름으로 대체 집계 | 중간 |
| UA 블랙리스트 + Authorization 예외 | Traefik v3 라우터 매처로 표현 가능: `HeaderRegexp('User-Agent', ...) && !Header('Authorization', ...)` 를 높은 priority 라우터로 잡아 차단. 다만 **"403 반환" 자체가 내장 기능이 아니라** 커뮤니티 플러그인(blockUserAgent 등)이나 에러 서비스로 우회해야 하고, Authorization 예외까지 지원하는 플러그인은 없어 라우터 규칙 방식이 현실적. 40여 개 패턴을 하나의 정규식으로 합치고 차단 여부를 회귀 테스트해야 함 | 어려움 |
| static/media/CDN 파일 서빙 | **불가.** Traefik 은 리버스 프록시일 뿐 파일 서버 기능이 아예 없다 | 별도 해결 필수 |

### 파일 서빙 공백을 메우는 방법

- **Django static** → WhiteNoise 미들웨어로 gunicorn 이 직접 서빙 (K8s 에서 흔한 표준 패턴, collectstatic 만 하면 됨)
- **업로드 media (/storage/)** → 트래픽이 낮으므로 Django 가 직접 서빙하거나, 초소형 nginx/caddy 파드 1개를 파일 전용으로 유지
- **CDN 디렉터리 (/home/kkh/public)** → **hostPath 유지로 결정** (아래 "CDN 디렉터리 처리" 섹션). 따라서 파일 서빙용 nginx 파드는 계속 남는다

CDN 이 hostPath 로 남는 한 파일 서버 파드는 사라지지 않으므로, **Traefik 완전 이식(파일 서버 0개)은 성립하지 않는다.** Traefik 을 도입하더라도 "라우팅은 Traefik + 파일 서빙 전용 미니 nginx" 조합이 현실적인 상한이다. 나중에 CDN 을 R2 로, media 를 django-storages 로 옮기면 그때 완전 이식이 가능해진다.

### CDN 디렉터리 처리 — 결정: hostPath 유지

**결정 (2026-07): `/home/kkh/public` 은 hostPath 볼륨으로 nginx 파드에 그대로 마운트한다.** 지금과 동작이 동일하고, 호스트에서 파일을 넣는 기존 운영 방식도 그대로 유지된다. 아래 R2 이전안은 나중에 홈 대역폭이나 파일 서버 제거가 필요해질 때를 위한 참고로 남긴다.

#### (참고) Cloudflare R2 로 통째로 이전하는 방법

`cdn.endurohub.kr` 은 `/home/kkh/public` 을 nginx 가 읽기 전용으로 서빙하는 단순 정적 호스트다 (채팅 클라이언트 이미지 임베드용 CORS + 1시간 캐시). **앱 코드는 이 디렉터리를 전혀 참조하지 않으므로** 결합도가 낮아 독립적으로 이전할 수 있다.

**이전 방법 (Cloudflare R2 + 커스텀 도메인):**

1. R2 버킷 생성 → `rclone sync /home/kkh/public r2:endurohub-cdn` 으로 1회 업로드
2. 버킷에 커스텀 도메인 `cdn.endurohub.kr` 연결 (DNS 가 이미 Cloudflare 에 있으므로 클릭 몇 번)
3. CORS 정책(`Access-Control-Allow-Origin: *`)은 버킷 CORS 설정으로, 캐시는 Cloudflare 엣지 캐시 룰로 대체
4. cloudflared 터널의 `cdn.endurohub.kr` 라우팅 제거

**장점:**

- 파일 서버 파드가 통째로 사라짐 — K8s 이전 대상에서 CDN 이 제외되어 Phase 3 이 단순해짐
- **홈 ISP 업로드 대역폭 절약** — 이미지가 홈서버를 거치지 않고 Cloudflare 엣지에서 직접 서빙됨 (현재는 터널을 통해 매번 홈서버가 업로드)
- 홈서버 장애와 무관하게 CDN 은 계속 동작
- 비용: R2 는 10GB 저장 + 무제한 이그레스 무료 — 이 용도로는 사실상 0원
- Terraform 학습 소재 추가: `cloudflare_r2_bucket` + DNS 레코드를 코드로 관리

**확인 필요한 것 1가지:** 이 디렉터리에 새 파일을 **누가/무엇이 쓰는지** (레포 안에는 쓰는 코드가 없음 → 수동 업로드 또는 호스트 스크립트로 추정). 쓰기 주체를 `rclone copy`(cron) 또는 R2 S3 API 업로드로 바꿔야 한다. 수동 업로드라면 Cloudflare 대시보드 드래그앤드롭으로 충분.

**노력: 약 0.5일** (파일 이전 자체는 몇 분, 대부분 도메인 전환·CORS 검증·쓰기 경로 정리)

**대안 비교 — 클러스터 안에 두는 두 가지 방식:**

| 방식 | 동작 | 평가 |
|---|---|---|
| **hostPath** | `/home/kkh/public` 을 nginx 파드에 그대로 읽기 전용 마운트 | 지금과 동작 동일. 호스트에서 파일을 쓰는 기존 방식(수동/스크립트)도 그대로 유지됨. 클러스터 안에 둘 거라면 이게 최선 |
| **PVC (local-path)** | 파일을 PVC 로 복사해 넣고 nginx 파드에 마운트 | 가능은 하지만 **단일 노드 local-path 에서는 실익이 없다.** local-path PVC 의 실체도 결국 같은 호스트의 디렉터리(`/var/lib/rancher/k3s/storage/pvc-...`)인데, 경로가 불투명한 랜덤 이름이라 **호스트에서 새 파일을 넣는 작업이 오히려 어려워진다** (provisioner 내부 경로를 직접 찾아 쓰거나 `kubectl cp`/업로드 파드 같은 우회 필요). PVC 삭제 시 데이터가 같이 지워지는 라이프사이클 리스크와 백업 대상 추가도 따라온다 |

PVC 가 의미 있어지는 건 나중에 멀티 노드로 확장해 "어느 노드에서든 마운트"가 필요해질 때인데, 그 시점에는 어차피 네트워크 스토리지나 오브젝트 스토리지(R2)로 옮겨야 한다. 정리하면 이 용도의 우선순위는 **R2 이전 > hostPath 유지 > PVC** 순이다. 두 클러스터 내 방식 모두 파일 서버 파드가 계속 필요하고 이미지 트래픽이 홈서버 터널을 계속 통과한다는 한계는 동일하다.

### 노력·판단

- 추가 노력: Phase 3 이 1.5\~2일 → **4\~5일**로 증가 (UA 차단 규칙 재작성·검증 + 로그 파이프라인 재작성 + WhiteNoise 전환 + 파일 서버 분리)
- **최소 노력이 목표면**: nginx 유지 (기본 계획)
- **학습 가치가 목표면**: 이식할 만하다. IngressRoute·미들웨어 체인은 실무에서 실제로 쓰는 K8s 패턴이고, 포트폴리오 관점에서도 "nginx conf 를 ConfigMap 으로 복사"보다 이야깃거리가 된다. 절충안으로 **라우팅·gzip·바디 제한·타임아웃만 Traefik 으로 옮기고(쉬움 항목 전부), UA 차단은 Cloudflare WAF 커스텀 룰로 밀어올리는** 방법도 있다 — 차단이 서버에 도달하기 전에 일어나므로 오히려 개선이고, Traefik 의 가장 어려운 이식 항목이 사라진다

## Terraform 담당 범위

홈서버라 클라우드 리소스가 없으므로 Terraform 은 다음을 관리한다 (학습 가치가 있는 실제 사용 패턴):

- `cloudflare` provider: Tunnel, DNS 레코드, (선택) Access 정책
- `helm` / `kubernetes` provider: 네임스페이스, Secrets, 앱 Helm 차트 `helm_release`
- state 는 로컬 → 나중에 Cloudflare R2/Terraform Cloud 백엔드로 이전 (스트레치)

디렉터리 구조 제안:

```
infra/
├── terraform/            # cloudflare 리소스 + helm_release
├── charts/endurohub/     # 앱 우산(umbrella) 차트
└── charts/observability/ # 관측성 차트
```

## 로컬 리허설과 개발 워크플로 (Windows)

### Windows 에서 미리 해볼 수 있나? → 가능 (k3d 사용)

k3s 자체는 리눅스 전용이라 Windows 네이티브로는 안 돌지만, **k3d** (k3s-in-Docker)를 쓰면 Docker Desktop(WSL2) 위에서 **진짜 k3s** 를 띄울 수 있다. 서버 타겟과 같은 배포판이므로 리허설 환경으로 최적이다.

```powershell
# Traefik 비활성 옵션까지 서버와 동일하게 재현
k3d cluster create endurohub --k3s-arg "--disable=traefik@server:0"
```

- Helm 차트, StatefulSet, CronJob, ConfigMap 등 **Phase 2\~5 의 매니페스트 작업 전부를 로컬에서 먼저 개발·검증**할 수 있다. 서버에서는 검증된 차트를 배포만 하면 되므로 서버 작업 리스크가 크게 줄어든다
- local-path provisioner 도 k3d 에 기본 포함 — PVC 동작도 동일하게 테스트 가능
- 이미지는 GHCR 없이도 `k3d image import` 로 로컬 빌드 이미지를 클러스터에 직접 주입해 테스트 가능
- 차이 나는 부분만 주의: hostPath 경로(WSL2 경로로 매핑됨), cloudflared(테스트용 터널을 따로 만들거나 로컬에서는 port-forward 로 대체), 호스트 Postgres 접근 주소(`host.k3d.internal`)

### k3s 환경에서 개발·디버깅? → 가능하지만 일상 개발은 기존 방식 유지 권장

- **일상 개발 (inner loop)**: 현재 방식(`scripts/dev-*.sh` — runserver + vite HMR, 소스 마운트)이 압도적으로 빠르다. K8s 안에서 핫 리로드를 하려면 Tilt/Skaffold 같은 도구로 파일 sync·이미지 리빌드 파이프라인을 추가로 구축해야 하고, 저장→반영 지연이 늘어난다. 업계 표준도 "개발 루프는 로컬, K8s 는 배포·통합 검증"이다. **기존 개발 스크립트는 전환 후에도 그대로 유지한다** — docker-compose.dev.yml 은 삭제 대상이 아니다
- **디버깅 (운영)**: `kubectl logs / exec / port-forward` 가 지금의 `docker compose logs / exec` 와 거의 동일한 경험이다. k9s(터미널 UI)를 쓰면 더 편하다. 프로덕션 디버깅 경험은 나빠지지 않는다
- **k3d 클러스터의 용도**: 일상 개발이 아니라 ① Helm 차트 개발·수정, ② 배포 전 리허설, ③ K8s 학습 실험장

## 단계별 실행 계획 (무중단 병행 전략)

기존 compose 스택을 유지한 채 k3s 를 병행 기동하고, 마지막에 cloudflared 타겟만 전환한다. 실패 시 롤백은 cloudflared 를 되돌리면 끝.

### Phase 1: 기반 (k3s + 레지스트리)
- 서버에 k3s 설치 (`--disable traefik`), 로컬 kubeconfig 연결
- GHCR 레지스트리 사용 설정, `.github/workflows/` 에 이미지 빌드·푸시 잡 추가 (api/web/crawler 3개 이미지)
- **선행 확인**: 서버 가용 RAM. 현재 mem_limit 합계 약 9GB + k3s 오버헤드 약 1GB. 병행 기동 기간에는 관측성 스택을 잠시 내리는 것도 방법

### Phase 2: 스테이트리스 앱
- Helm 차트 작성: api(+migrate Job, collectstatic initContainer), web, celery-worker, celery-beat, crawler-worker
- 이 단계에서 DB/Redis 는 아직 호스트 것을 사용 (`host.docker.internal` 대신 노드 IP)
- `kubectl port-forward` 로 동작 검증

### Phase 3: 인그레스
- nginx conf → ConfigMap, nginx Deployment + static/media PVC
- cloudflared Deployment 추가 (신규 터널로 테스트 도메인 먼저)

### Phase 4: 데이터 (가장 신중해야 할 단계)
- Postgres/Redis StatefulSet 기동 → `pg_dump | pg_restore` 로 데이터 이전 (수 분 다운타임 허용)
- 앱의 DATABASE_HOST/REDIS_HOST 를 클러스터 서비스로 전환
- pg_dump CronJob 백업 구성 후에 컷오버할 것
- **컷오버**: cloudflared 를 프로덕션 도메인으로 전환 → 구 compose 스택 정지 (즉시 삭제하지 말고 1주 보관)

### Phase 5: 관측성
- lgtm Deployment + PVC, Grafana 프로비저닝 ConfigMap 화
- promtail → Alloy(또는 promtail) DaemonSet 으로 파드 로그 수집 (nginx JSON 로그 포함)
- otelcol 의 docker_stats → kubeletstats receiver, hostmetrics 는 DaemonSet 유지

### Phase 6: Terraform + CI/CD 마무리
- Cloudflare 터널/DNS 를 Terraform import, helm_release 코드화
- deploy.yml 재작성: 이미지 빌드·푸시 → `helm upgrade` (러너에서). GitOps(Argo CD)는 스트레치 골

## 구체적 진행 시나리오 (커맨드 수준)

전체 흐름은 2부로 나뉜다: **Part A — Windows(k3d)에서 차트를 완성**하고, **Part B — 서버에서는 검증된 차트를 배포만** 한다.

### Part A: Windows 리허설 (Phase 2\~4 를 로컬에서 완성)

#### A-0. 도구 설치 (최초 1회)

```powershell
winget install Kubernetes.kubectl Helm.Helm k3d.k3d Derailed.k9s
# Docker Desktop 이 WSL2 백엔드로 실행 중이어야 함
```

#### A-1. 클러스터 생성 + 이미지 주입

```powershell
k3d cluster create endurohub --k3s-arg "--disable=traefik@server:0" -p "8080:80@loadbalancer"
kubectl create namespace endurohub

# GHCR 없이 로컬 빌드 이미지를 직접 주입
docker build -t endurohub-api:dev ./api
docker build -t endurohub-web:dev ./web
docker build -t endurohub-crawler:dev ./crawler
k3d image import endurohub-api:dev endurohub-web:dev endurohub-crawler:dev -c endurohub
```

#### A-2. Helm 차트 스캐폴드 작성

새로 만들 디렉터리 구조:

```
infra/
├── charts/endurohub/
│   ├── Chart.yaml
│   ├── values.yaml           # 공통 기본값 (이미지 태그, 리소스, 환경변수 키 목록)
│   ├── values.local.yaml     # k3d 용 (이미지 :dev, replicas 최소)
│   ├── values.prod.yaml      # 서버용 (ghcr.io 이미지, mem limits = 기존 mem_limit 이식)
│   └── templates/
│       ├── api-deployment.yaml        # + collectstatic initContainer
│       ├── api-service.yaml
│       ├── web-deployment.yaml / web-service.yaml
│       ├── celery-worker-deployment.yaml
│       ├── celery-beat-deployment.yaml   # replicas: 1 고정, strategy: Recreate
│       ├── crawler-deployment.yaml
│       ├── nginx-configmap.yaml          # 기존 nginx/conf.d/*.conf 내용 이식
│       ├── nginx-deployment.yaml / nginx-service.yaml
│       ├── postgres-statefulset.yaml / postgres-service.yaml
│       ├── redis-statefulset.yaml / redis-service.yaml
│       ├── migrate-job.yaml              # helm hook (pre-upgrade) 로 manage.py migrate
│       ├── backup-cronjob.yaml           # pg_dump → PVC
│       └── secrets.yaml                  # 또는 kubectl 로 수동 생성 (values 에 안 넣음)
└── terraform/                # Part B 후반에 작성
```

환경변수는 기존 `docker-compose.yml` 의 environment 블록을 그대로 ConfigMap(비밀 아닌 것) + Secret(비밀)으로 옮긴다. `DATABASE_HOST` 는 `postgres` (클러스터 서비스명), `REDIS_HOST` 는 `redis` 로 바뀌는 것이 핵심 변경점.

#### A-3. 데이터 계층부터 기동 (로컬엔 호스트 DB가 없으므로 순서 반전)

```powershell
helm upgrade --install endurohub ./infra/charts/endurohub -n endurohub -f infra/charts/endurohub/values.local.yaml

# 서버에서 받아온 덤프(또는 로컬 dev 데이터)를 클러스터 Postgres 로 복원
kubectl exec -i -n endurohub postgres-0 -- pg_restore -U enduro -d endurohub --clean < endurohub.dump
```

#### A-4. 앱 검증 루프 (차트 수정 → 반영 → 확인 반복)

```powershell
kubectl port-forward -n endurohub svc/nginx 8080:80
# http://localhost:8080 (web), http://localhost:8080/api/v1/races/ (api), /dj-admin/ (어드민)

k9s -n endurohub                # 파드 상태·로그 실시간 확인
kubectl logs -n endurohub deploy/celery-worker -f
kubectl create job --from=cronjob/backup backup-test -n endurohub   # 백업 CronJob 수동 트리거 테스트
```

여기서 확인할 체크리스트: 8개 테이블 데이터 정상 조회, 어드민 로그인, 이미지 업로드 → media PVC 반영, celery 태스크 실행(beat 로그에 스케줄 등록 확인), nginx UA 차단(`curl -A "AhrefsBot"` → 403), static/storage 캐시 헤더.

**Part A 완료 기준: `helm upgrade --install` 한 방으로 전체 스택이 뜨고 위 체크리스트가 통과하는 상태.** 여기까지가 전체 노력의 절반 이상이며, 서버는 아직 건드리지 않았다.

### Part B: 서버 이전 (검증된 차트 배포)

#### B-1. 서버에 k3s 설치 + kubeconfig 연결

```bash
# 서버(SSH)에서
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable traefik" sh -
sudo cat /etc/rancher/k3s/k3s.yaml   # 내용을 Windows ~/.kube/config 에 병합 (server 주소를 서버 IP로 수정)
```

#### B-2. GHCR 이미지 파이프라인 (deploy.yml 개편 1단계)

`.github/workflows/` 에 이미지 빌드·푸시 잡 추가 — 기존 compose 배포와 병행 운영:

```yaml
# 요지: docker/login-action (GITHUB_TOKEN) → docker/build-push-action
# 태그: ghcr.io/kkh-147-17-3/endurohub-api:${{ github.sha }} + :latest
# api / web / crawler 3개 이미지를 paths 필터로 변경된 것만 빌드
```

private 이미지로 갈 경우 서버에 imagePullSecret 생성:

```bash
kubectl create secret docker-registry ghcr --docker-server=ghcr.io \
  --docker-username=kkh-147-17-3 --docker-password=<PAT> -n endurohub
```

#### B-3. 앱 배포 (아직 호스트 DB 사용 → 트래픽 무영향)

`values.prod.yaml` 에서 처음에는 `DATABASE_HOST`/`REDIS_HOST` 를 노드 IP(호스트 Postgres/Redis)로 두고 배포한다. 기존 compose 스택과 **같은 DB를 보는 읽기 검증**이 가능하다 (celery-beat 는 replicas 0 으로 — 중복 실행 방지).

```bash
helm upgrade --install endurohub ./infra/charts/endurohub -n endurohub -f values.prod.yaml
kubectl port-forward svc/nginx 8080:80   # 서버 로컬에서 스모크 테스트
```

#### B-4. 데이터 이전 + 컷오버 (유일한 다운타임 구간, 예상 10\~30분)

```bash
# 1. 백업 2벌
pg_dump -Fc -U enduro endurohub > /backup/pre-cutover.dump   # 호스트에서
scp server:/backup/pre-cutover.dump .                        # 로컬에도 1벌

# 2. 구 스택 쓰기 중지 (compose 정지) → 최종 덤프 → 클러스터 PG 복원
docker compose stop
pg_dump -Fc -U enduro endurohub | kubectl exec -i postgres-0 -n endurohub -- pg_restore -U enduro -d endurohub --clean

# 3. 앱을 클러스터 DB 로 전환 + beat 기동
helm upgrade endurohub ./infra/charts/endurohub -n endurohub -f values.prod.yaml \
  --set env.DATABASE_HOST=postgres --set env.REDIS_HOST=redis --set celeryBeat.replicas=1

# 4. cloudflared Deployment 의 터널 라우팅을 클러스터 nginx 서비스로 전환 → 프로덕션 도메인 확인
# 5. row count 대조 + 스모크 테스트 → 이상 시 롤백: cloudflared 라우팅 원복 + docker compose start
```

구 compose 스택과 호스트 Postgres 는 1주 뒤 문제 없으면 제거.

#### B-5. 관측성 스택 (Phase 5 내용대로, 컷오버와 분리해 여유 있게)

lgtm Deployment + PVC → Alloy DaemonSet(파드 로그) → otelcol 의 docker_stats 를 kubeletstats 로 교체 → Grafana 대시보드 쿼리 조정.

#### B-6. Terraform 코드화 + deploy.yml 마무리

```bash
cd infra/terraform && terraform init
terraform import cloudflare_zero_trust_tunnel_cloudflared.main <tunnel-id>   # 기존 리소스 흡수
terraform import cloudflare_dns_record.www <zone-id>/<record-id>
terraform plan   # no-op 이 될 때까지 코드 보정
```

deploy.yml 최종형: `push to master` → 이미지 빌드·GHCR push → self-hosted 러너에서 `helm upgrade --install ... --set image.tag=${{ github.sha }}` → `kubectl rollout status` 로 성공 확인. 기존 "Rebuild api/web only" 분기·`docker compose` 스텝은 이 시점에 삭제.

## 검증 방법

- 각 Phase 종료 시: `kubectl get pods -A` 전원 Running, `curl` 로 api(`/api/v1/races/`)·web(`/`) 응답 확인
- Phase 4 후: 데이터 row count 대조 (`races`, `posts`, `race_reviews` 등 8개 테이블), 어드민 로그인, 이미지 업로드 → PVC 반영 확인
- 컷오버 후: 프로덕션 도메인 스모크 테스트, Celery beat 스케줄 태스크(크롤러 08:00 잡) 다음날 실행 확인, Grafana 대시보드 데이터 유입 확인
- Terraform: `terraform plan` 이 no-op 인 상태(드리프트 없음)가 완료 기준

## 리스크

| 리스크 | 대응 |
|---|---|
| 단일 서버 RAM 부족 (병행 기동 시) | 병행 기간 관측성 스택 중지, requests/limits 를 기존 mem_limit 그대로 이식 |
| Postgres 데이터 손실 | 이전 직전 pg_dump 2벌 (호스트 + 로컬 다운로드), 구 인스턴스 1주 보관 |
| celery-beat 중복 실행 (전환 과도기) | 구 스택 beat 정지 후 신규 beat 기동 (동시 기동 금지) |
| /home/kkh/public CDN 경로 | **hostPath 볼륨으로 그대로 마운트 (결정됨)**. 추후 필요 시 R2 이전 (참고 섹션) |

## 부록: 용어 설명

### GHCR (GitHub Container Registry)

GitHub 이 운영하는 **컨테이너 이미지 저장소**다. Docker Hub 와 같은 역할을 하며, 주소는 `ghcr.io`. 이미지는 `ghcr.io/kkh-147-17-3/endurohub-api:latest` 같은 형태로 GitHub 계정/레포에 귀속된다.

**왜 이 프로젝트에 필요한가:**

- 지금은 self-hosted 러너가 서버에서 `docker compose up --build` 로 **소스를 직접 빌드**해서 쓴다. 이미지가 서버 로컬에만 존재하고, 어디에도 저장(push)되지 않는다.
- Kubernetes 는 이 방식을 지원하지 않는다. 파드를 띄울 때 **"레지스트리에서 이미지를 pull"** 하는 것이 유일한 표준 동작이다. 즉 어딘가에 이미지를 올려둘 저장소가 반드시 필요하다.
- 선택지 중 GHCR 을 권장하는 이유:
  - **무료**: public 이미지는 무제한, private 도 개인 계정 기준 넉넉한 무료 용량
  - **GitHub Actions 와 통합**: 별도 계정/시크릿 없이 워크플로에 자동 주입되는 `GITHUB_TOKEN` 으로 바로 push 가능 (`docker/login-action` + `docker/build-push-action` 두 스텝이면 끝)
  - 이미 코드가 GitHub 에 있으므로 관리 지점이 늘지 않음
- 전환 후 배포 흐름: `git push` → Actions 가 이미지 빌드 → GHCR 에 push (커밋 SHA 태그) → 서버의 k3s 가 해당 태그를 pull 해서 파드 교체. **"어떤 커밋이 배포됐는지"가 이미지 태그로 남고, 이전 태그로 즉시 롤백 가능**해지는 것이 지금 방식 대비 실질적 이점이다.

### Traefik

Go 로 만들어진 오픈소스 **리버스 프록시 / 인그레스 컨트롤러**다. nginx 와 같은 계층의 소프트웨어라고 보면 된다 — 외부 요청을 받아 경로/도메인 규칙에 따라 내부 서비스로 라우팅한다.

**Kubernetes 에서의 역할 (인그레스 컨트롤러):**

- K8s 에는 "외부 트래픽을 어느 서비스로 보낼지"를 선언하는 `Ingress` 라는 리소스가 있다. 예: "`/api/*` 는 api 서비스로, 나머지는 web 서비스로".
- 이 선언을 읽어서 **실제로 프록시 동작을 수행하는 프로그램**이 인그레스 컨트롤러이고, Traefik 은 그 대표적 구현체 중 하나다 (다른 구현체: ingress-nginx 등).
- **k3s 는 Traefik 을 기본 내장**하고 있어서, 설치하면 자동으로 함께 뜬다.

**왜 이 프로젝트에서는 비활성화(`--disable traefik`)를 권장하는가:**

1. **기존 nginx 설정의 재현 비용** — 현재 nginx conf 에는 UA 블랙리스트 차단(40여 개 패턴 + Authorization 헤더 예외), JSON 구조화 access log(Grafana 분석용), gzip 튜닝, static/media 캐시 헤더 같은 커스텀 로직이 많다. 이를 Traefik 의 미들웨어/설정으로 전부 옮기는 것은 상당한 재작업이고, 옮기다 빠뜨리면 조용히 기능이 사라진다. 기존 conf 파일을 ConfigMap 으로 그대로 넣은 nginx Deployment 가 훨씬 저렴하고 안전하다.
2. **TLS 종단이 이미 Cloudflare 에 있음** — 인그레스 컨트롤러의 주요 가치 중 하나가 TLS 인증서 관리(Let's Encrypt 자동 갱신 등)인데, 이 프로젝트는 Cloudflare Tunnel 이 TLS 를 종단하므로 클러스터 안에서는 평문 HTTP 만 오간다. Traefik 이 해줄 일이 별로 없다.
3. **진입 경로가 하나뿐** — 노드 1대 + 터널 1개 구조라 Ingress 리소스의 유연함(여러 도메인/서비스 동적 라우팅)이 필요 없다. cloudflared → nginx 서비스로 직결하면 충분하다.

정리하면: **GHCR 은 "이미지를 올려둘 창고"로 새로 도입**하는 것이고, **Traefik 은 k3s 가 끼워주는 기본 프록시인데 우리는 기존 nginx 를 계속 쓸 것이므로 꺼두는 것**이다.
