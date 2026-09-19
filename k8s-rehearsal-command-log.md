# k3d 로컬 리허설 — 명령어 실행 로그

k8s-terraform-migration-plan.md 의 Part A(Windows 로컬 리허설)를 진행하며 실행한 모든 명령을 시간순으로 기록한다.
각 항목은 **명령 → 왜 실행했는지 → 결과** 순서다.

> 표기: ✅ 실행 완료 / ⏳ 실행 예정 / ❌ 실패(원인과 대응 병기)

---

## 2026-07-12

### 1. 작업 브랜치 생성 ✅

```powershell
git checkout -b k8s-local-rehearsal
```

- **왜**: K8s 리허설 작업(Helm 차트, values 파일 등 새 파일 다수)이 master 에 섞이지 않도록 격리한다. 실험이 실패해도 브랜치 삭제로 깔끔하게 되돌릴 수 있고, master 로의 자동 배포(deploy.yml 은 master push 에만 반응)도 트리거되지 않는다.
- **결과**: `Switched to a new branch 'k8s-local-rehearsal'`

### 2. 로컬 도구 설치 여부 확인 ⏳

```powershell
docker version --format '{{.Server.Version}}'
kubectl version --client
helm version --short
k3d version
```

- **왜**: Part A 진행에 필요한 4개 도구(Docker Desktop, kubectl, helm, k3d)가 이 Windows 머신에 이미 있는지 확인한다. 없는 것만 골라 `winget install` 하기 위한 사전 조사이며, 전부 읽기 전용 버전 조회라 시스템을 변경하지 않는다.
- **결과**:
  - docker: 클라이언트는 있으나 엔진 연결 실패 (`dockerDesktopLinuxEngine` 파이프 없음) → **Docker Desktop 이 실행 중이 아님, 기동 필요**
  - kubectl: ✅ v1.36.2 설치됨
  - helm: ❌ 미설치
  - k3d: ❌ 미설치

### 3. helm, k3d 설치 ⏳

```powershell
winget install Helm.Helm k3d.k3d
```

- **왜**: 차트 배포(helm)와 로컬 k3s 클러스터 생성(k3d)에 필수. kubectl 은 이미 있으므로 제외.

### 4. Docker Desktop 기동 ⏳

```powershell
Start-Process "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
```

- **왜**: k3d 는 k3s 를 Docker 컨테이너로 띄우므로 Docker 엔진이 선행 조건. 위 확인에서 엔진이 꺼져 있음을 확인했다.

---

## 참고: 명령 외 작업 (파일 읽기/작성)

명령 실행 전에 아래 파일들을 읽어 차트 작성에 필요한 정보를 수집했다 (읽기 전용, 시스템 변경 없음):

| 파일 | 확인한 것 |
|---|---|
| api/Dockerfile | 포트 8000, gunicorn CMD, collectstatic 이 빌드 시점에 실행됨, DJANGO_SETTINGS_MODULE 환경변수 필수 |
| web/Dockerfile | 포트 3000, node non-root 유저(uid 1001), otel.mjs 프리로드 |
| crawler/Dockerfile | celery worker `-Q crawler` 큐 전용, Playwright chromium 포함 |
| api/config/settings.py | STATIC_ROOT=/app/staticfiles, MEDIA_ROOT=/app/storage, Redis 접속 환경변수 구조 (CELERY_BROKER_URL 조립 방식) |
| api/config/urls.py | `/health` 엔드포인트 **없음** 확인 → liveness/readiness probe 는 `/api/v1/races/` 또는 헬스 엔드포인트 신설 필요 |
