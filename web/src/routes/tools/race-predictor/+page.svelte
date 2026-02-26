<script lang="ts">
    import DistanceSelector from '$lib/components/Tools/DistanceSelector.svelte';
    import TimeInput from '$lib/components/Tools/TimeInput.svelte';
    import ToolsSidebar from '$lib/components/Tools/ToolsSidebar.svelte';
    import type { DistancePreset } from '$lib/tools/types';
    import { DISTANCES, timeToTotalSeconds } from '$lib/tools/pace-calculator';
    import { predictAllDistances, type PredictionResult } from '$lib/tools/race-predictor';

    let selectedDistance = $state<DistancePreset>('10k');
    let customDistanceKm = $state(10);
    let hours = $state(0);
    let minutes = $state(50);
    let seconds = $state(0);

    let distanceKm = $derived(
        selectedDistance === 'custom' ? customDistanceKm : DISTANCES[selectedDistance]?.km || 10
    );

    let totalSeconds = $derived(timeToTotalSeconds(hours, minutes, seconds));

    let predictions = $derived<PredictionResult[]>(
        totalSeconds > 0 ? predictAllDistances(distanceKm, totalSeconds) : []
    );

    let hasResults = $derived(predictions.length > 0);

    const keyDistances = new Set([5, 10, 21.0975, 42.195]);
</script>

<svelte:head>
    <title>대회 기록 예측기 - EnduroHub</title>
    <meta name="description" content="마라톤 기록 예측기 - 10km 기록으로 하프마라톤, 풀마라톤 예상 기록을 계산하세요. Riegel 공식 기반 과학적 예측." />
    <meta property="og:title" content="대회 기록 예측기 - EnduroHub" />
    <meta property="og:description" content="10km 기록으로 하프마라톤, 풀마라톤 예상 기록을 계산하세요." />
    {@html `<script type="application/ld+json">${JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebApplication',
        'name': '대회 기록 예측기 - EnduroHub',
        'description': '마라톤 기록 예측기 - 현재 대회 기록으로 다른 거리의 예상 완주 시간을 계산하세요.',
        'applicationCategory': 'SportsApplication',
        'operatingSystem': 'Web',
        'offers': { '@type': 'Offer', 'price': '0', 'priceCurrency': 'KRW' },
    })}</script>`}
    {@html `<script type="application/ld+json">${JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            { '@type': 'ListItem', 'position': 1, 'name': '홈', 'item': 'https://www.endurohub.kr' },
            { '@type': 'ListItem', 'position': 2, 'name': '대회 기록 예측기' },
        ],
    })}</script>`}
</svelte:head>

<div class="container mx-auto px-4 py-8">
    <div class="breadcrumbs text-sm mb-6">
        <ul>
            <li><a href="/">홈</a></li>
            <li>대회 기록 예측기</li>
        </ul>
    </div>

    <div class="mb-8">
        <h1 class="text-2xl md:text-3xl font-bold">대회 기록 예측기</h1>
        <p class="text-base-content/60 mt-1">현재 기록으로 다른 거리의 예상 완주 시간을 확인하세요</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div class="lg:col-span-2 space-y-6">
            <div class="card bg-base-100 border border-base-300">
                <div class="card-body space-y-4">
                    <h2 class="font-semibold text-base">기준 기록 입력</h2>
                    <DistanceSelector bind:selected={selectedDistance} bind:customDistance={customDistanceKm} />
                    <TimeInput bind:hours bind:minutes bind:seconds label="완주 기록" />
                </div>
            </div>

            {#if hasResults}
                <div class="card bg-base-100 border border-base-300">
                    <div class="card-body">
                        <h2 class="font-semibold text-lg mb-4">예상 기록</h2>

                        <div class="overflow-x-auto rounded-lg border border-base-300">
                            <table class="table table-sm">
                                <thead>
                                    <tr class="bg-base-200">
                                        <th>거리</th>
                                        <th class="text-center">예상 완주 시간</th>
                                        <th class="text-center">km당 페이스</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {#each predictions as pred (pred.distanceKm)}
                                        <tr class="{keyDistances.has(pred.distanceKm) ? 'bg-primary/5 font-medium' : ''}">
                                            <td>
                                                {pred.distance}
                                                {#if pred.distanceKm === 42.195}
                                                    <span class="badge badge-xs badge-primary ml-1">풀코스</span>
                                                {:else if pred.distanceKm === 21.0975}
                                                    <span class="badge badge-xs badge-secondary ml-1">하프</span>
                                                {/if}
                                            </td>
                                            <td class="text-center tabular-nums">{pred.predictedTime}</td>
                                            <td class="text-center tabular-nums">{pred.pacePerKm}/km</td>
                                        </tr>
                                    {/each}
                                </tbody>
                            </table>
                        </div>

                        <p class="text-xs text-base-content/40 mt-4">
                            * Pete Riegel 공식 (T2 = T1 × (D2/D1)^1.06) 기반 예측. 실제 기록은 코스 난이도, 기상 조건, 훈련 상태에 따라 달라질 수 있습니다.
                        </p>
                    </div>
                </div>
            {/if}
        </div>

        <div class="space-y-6">
            <div class="card bg-base-100 border border-base-300">
                <div class="card-body">
                    <h2 class="font-semibold text-base mb-3">사용 가이드</h2>
                    <div class="space-y-3 text-sm text-base-content/70">
                        <div>
                            <p class="font-medium text-base-content/90 mb-1">가장 정확한 결과를 위해</p>
                            <ul class="list-disc list-inside space-y-1 text-xs">
                                <li>최근 2~3개월 이내 기록을 입력하세요</li>
                                <li>공식 대회 기록을 사용하세요</li>
                                <li>평지 코스 기록이 가장 정확합니다</li>
                            </ul>
                        </div>
                        <div>
                            <p class="font-medium text-base-content/90 mb-1">예측 정확도</p>
                            <ul class="list-disc list-inside space-y-1 text-xs">
                                <li>비슷한 거리: 매우 높음</li>
                                <li>2배 이내 거리: 높음</li>
                                <li>4배 이상 거리: 참고용</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            <ToolsSidebar current="race-predictor" />
        </div>
    </div>
</div>
