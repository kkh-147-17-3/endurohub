# k3d 로컬 리허설 부트스트랩 — 계획서 Part A-1/A-3 자동화
# 사용법: 레포 루트에서  powershell -File infra/local/k3d-up.ps1
# 재실행해도 안전 (이미 있는 리소스는 건너뜀)

$ErrorActionPreference = "Stop"
$cluster = "endurohub"

# 1. 클러스터 (서버와 동일하게 Traefik 비활성, 호스트 8080 → 클러스터 LB 80)
$existing = k3d cluster list -o json | ConvertFrom-Json
if ($existing.name -notcontains $cluster) {
    k3d cluster create $cluster --k3s-arg "--disable=traefik@server:0" -p "8080:80@loadbalancer"
} else {
    Write-Host "cluster '$cluster' already exists - skipping create"
}

# 2. 이미지 빌드 + 클러스터 주입 (GHCR 없이 로컬 이미지 사용)
docker build -t endurohub-api:dev ./api
docker build -t endurohub-web:dev ./web
k3d image import endurohub-api:dev endurohub-web:dev -c $cluster

# crawler 는 Playwright 포함이라 빌드가 오래 걸림 — 필요할 때 주석 해제
# docker build -t endurohub-crawler:dev ./crawler
# k3d image import endurohub-crawler:dev -c $cluster

# 3. 배포
helm upgrade --install endurohub ./infra/charts/endurohub `
    --namespace endurohub --create-namespace `
    -f ./infra/charts/endurohub/values.local.yaml

Write-Host ""
Write-Host "done. next steps:"
Write-Host "  kubectl get pods -n endurohub -w"
Write-Host "  kubectl port-forward -n endurohub svc/nginx 8080:80"
Write-Host "  start http://localhost:8080"
