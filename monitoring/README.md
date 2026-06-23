# 관측성(Observability) — OpenTelemetry + LGTM

EnduroHub 의 트레이스/메트릭/로그를 OpenTelemetry 로 수집해 **LGTM 올인원**
(`grafana/otel-lgtm`: OTel Collector + Loki + Tempo + Prometheus + Grafana)
에서 보는 구성이다.

## 데이터 흐름

```
                          ┌────────────────────────────────────────┐
  api (Django/gunicorn) ──┤                                        │
  celery-worker ──────────┤  OTLP/HTTP :4318                       │
  celery-beat ────────────┤  (트레이스·메트릭·로그)                 │
  web (SvelteKit SSR) ────┤                                        │
                          │            lgtm 컨테이너                │
  nginx (JSON access log) │   Collector→Loki/Tempo/Prometheus      │
        │                 │            Grafana :3000               │
        └─ promtail ──────┤  Loki push :3100                       │
                          └────────────────────────────────────────┘
```

- **api / celery / web**: `opentelemetry-instrument`(Python) 와 `otel.mjs`(Node) 로
  자동계측. `OTEL_EXPORTER_OTLP_ENDPOINT=http://lgtm:4318` 로 전송.
- **nginx**: JSON access log(`/var/log/nginx/access.json`)를 promtail 이 tail → Loki push.
- **컨테이너 CPU/메모리 + 호스트 디스크**: `otelcol`(OTel Collector)이 `docker_stats`(컨테이너
  CPU/메모리/네트워크/블록IO) 와 `hostmetrics`(호스트 디스크 사용량) 를 OTLP 로 전송.
- **에러 추적**은 기존 Sentry 를 그대로 사용(중복 제거). OTel 은 메트릭·로그집계·전구간
  트레이싱을 담당한다.

## 서비스 이름 (Grafana 에서 필터)

| 컨테이너 | `service.name` |
|---|---|
| api | `endurohub-api` |
| celery-worker | `endurohub-celery-worker` |
| celery-beat | `endurohub-celery-beat` |
| web (SSR) | `endurohub-web` |
| nginx (로그) | `endurohub-nginx` |

## 접속

- Grafana: http://localhost:3001  (기본 계정 admin / admin — 최초 로그인 후 변경)
  - 데이터소스(Loki/Tempo/Prometheus)는 이미지에 사전 구성되어 있다.

## 구성: 앱 / 관측성 분리

관측성 스택은 앱과 **별도 compose 프로젝트**로 분리되어 라이프사이클이 독립적이다.

| | 파일 | 프로젝트 | 서비스 | 배포 |
|---|---|---|---|---|
| 앱 | `docker-compose.yml` | `endurohub` | api, celery×2, web, nginx | CI(deploy.yml) |
| 관측성 | `docker-compose.observability.yml` | `endurohub-obs` | lgtm, promtail, otelcol | obs 변경 시 독립 |

- **공유 네트워크** `endurohub_obs`: 앱 서비스가 `lgtm:4318` 로 OTLP 전송.
- **공유 볼륨** `endurohub_nginx_logs`: 앱 nginx 가 기록 → 관측성 promtail 이 읽음.
- 앱 배포가 관측성을 재시작하지 않고, 관측성 변경도 앱을 건드리지 않는다.

## 기동 / 검증

```bash
# ── 최초 1회: 공유 네트워크/볼륨 부트스트랩 ──
docker network create endurohub_obs
docker volume  create endurohub_nginx_logs

# 관측성 스택 기동
docker compose -f docker-compose.observability.yml up -d

# 앱 기동(+ 전환 시 옛 관측성 컨테이너 정리)
docker compose up -d --build --remove-orphans

# 컨테이너 상태
docker compose ps
docker compose -f docker-compose.observability.yml ps

# OTLP 수집 로그 확인(lgtm)
docker compose -f docker-compose.observability.yml logs -f lgtm

# 트래픽 발생 후 Grafana(:3001) → Explore 에서
#   - Tempo:      service.name = endurohub-web 트레이스가 endurohub-api 까지 이어지는지
#   - Prometheus: http.server.* / 프로세스 메트릭이 들어오는지
#   - Loki:       {service_name="endurohub-nginx"} 로 nginx 로그, {service_name="endurohub-api"} 로 앱 로그
```

## 컨테이너 CPU/메모리 (otelcol → docker_stats)

`otelcol` 서비스가 컨테이너별 리소스를 OTLP 로 보낸다. `compose_service` 라벨로 컨테이너를
구분한다. (정확한 메트릭 이름은 Grafana metrics browser 로 확인 — 버전에 따라 `container_*`
접미사가 다를 수 있다.)

```promql
# 컨테이너별 CPU 사용률
sum by (compose_service) (container_cpu_utilization)

# 컨테이너별 메모리 사용량(바이트)
sum by (compose_service) (container_memory_usage_total_bytes)

# 메모리 사용률(%)
container_memory_percent

# 컨테이너별 디스크 I/O (읽기/쓰기 속도)
sum by (compose_service) (rate(container_blockio_io_service_bytes_recursive[5m]))
```

## 호스트 디스크 사용량 (otelcol → hostmetrics)

`lgtm_data` 등 볼륨이 디스크를 채워 앱을 죽이는 #1 다운타임 위험을 자동 감지한다.

```promql
# 루트 파일시스템 사용률(0~1). 0.8 초과 시 알림 권장.
system_filesystem_utilization{mountpoint="/"}

# 마운트별 used/free 바이트
system_filesystem_usage_bytes
```

> 볼륨 **개별** 크기(예: lgtm_data 몇 GB)는 메트릭으로 안 나온다 — 호스트에서
> `docker system df -v` 로 확인. hostmetrics 는 "디스크가 차는 추세"와 알림용이다.

## 알림 (Grafana Alerting, 프로비저닝)

`monitoring/grafana/provisioning/alerting/` 의 파일을 lgtm 컨테이너의 Grafana provisioning
경로(`/otel-lgtm/grafana/conf/provisioning/alerting/`)에 마운트해 **선언적으로** 알림을 건다.

- **contactpoints.yaml** — Telegram 수신처(기존 에러알림 채널 재사용)
- **policies.yaml** — 루트 정책 → Telegram 라우팅
- **rules.yaml** — 규칙 3종:
  - `Disk usage > 80% / > 90% (root fs)` — 디스크 풀 → 앱 다운 사전 감지
  - `Container memory > 90% of limit` — 컨테이너 OOM-kill 임박 경고

### 필수 설정 / 배포 후 확인

1. **Telegram 환경변수**: 운영 `.env` 에 `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` 가
   있어야 알림이 실제로 전송된다(없으면 규칙은 떠도 메시지 미발송).
2. **메트릭 이름 확인**: `rules.yaml` 의 `system_filesystem_utilization` /
   `container_memory_percent` 는 OTLP→Prometheus 변환으로 접미사가 다를 수 있다.
   Grafana metrics browser 에서 실제 이름 확인 후 `expr` 을 맞춘다.
3. **프로비저닝 로드 확인**:
   ```bash
   docker compose -f docker-compose.observability.yml logs lgtm | grep -i provision   # 에러 없이 로드됐는지
   ```
   Grafana(:3001) → Alerting → Alert rules 에 `EnduroHub/resource-alerts` 그룹이 보이면 성공.
4. **발화 테스트**: 임시로 임계값을 현재값보다 낮게(예: 디스크 0.01) 바꿔 재배포 → Telegram
   수신 확인 후 원복.

## 비계측 환경

`OTEL_EXPORTER_OTLP_ENDPOINT` 가 비어 있으면 각 SDK 가 사실상 비활성화되므로
LGTM 없이도 앱은 정상 동작한다(로컬 개발/CI).

## 알려진 한계 / 후속 개선

- **gunicorn 멀티워커 메트릭**: 워커마다 동일 `service.instance.id` 로 메트릭을 내보내
  일부 메트릭 시계열이 겹칠 수 있다. 워커별 고유 인스턴스 ID가 필요하면 gunicorn
  `post_fork` 훅에서 `OTEL_RESOURCE_ATTRIBUTES` 에 `service.instance.id` 를 주입한다.
- **올인원 이미지**는 개발·소규모 운영용(SPOF, 단일노드). 트래픽/보존 요구가 커지면
  Loki/Tempo/Mimir 분리형 + 오브젝트 스토리지로 이전한다.
- **데이터 영속화**는 `lgtm_data` 볼륨(`/data`)에 의존. 이미지 버전에 따라 보존 경로가
  다를 수 있으니 업그레이드 시 확인할 것.
