<script lang="ts">
    import DistanceSelector from '$lib/components/Tools/DistanceSelector.svelte';
    import TimeInput from '$lib/components/Tools/TimeInput.svelte';
    import ToolsSidebar from '$lib/components/Tools/ToolsSidebar.svelte';
    import type { DistancePreset } from '$lib/tools/types';
    import type { Gender } from '$lib/tools/vo2max';
    import { DISTANCES } from '$lib/tools/pace-calculator';
    import { calculateVO2max, getVO2maxRating, estimatePercentile, getTrainingPaces } from '$lib/tools/vo2max';

    let selectedDistance = $state<DistancePreset>('10k');
    let customDistanceKm = $state(10);
    let hours = $state(0);
    let minutes = $state(50);
    let seconds = $state(0);
    let gender = $state<Gender>('male');

    let distanceKm = $derived(
        selectedDistance === 'custom' ? customDistanceKm : DISTANCES[selectedDistance]?.km || 10
    );

    let distanceMeters = $derived(distanceKm * 1000);
    let timeMinutes = $derived(hours * 60 + minutes + seconds / 60);

    let vo2max = $derived(calculateVO2max(distanceMeters, timeMinutes));
    let hasResult = $derived(vo2max > 0 && isFinite(vo2max) && vo2max < 100);
    let rating = $derived(hasResult ? getVO2maxRating(vo2max, gender) : null);
    let percentile = $derived(hasResult ? estimatePercentile(vo2max, gender) : 0);
    let paces = $derived(hasResult ? getTrainingPaces(vo2max) : null);

    let gaugePercent = $derived(hasResult ? Math.min(100, Math.max(0, (vo2max / 80) * 100)) : 0);
</script>

<svelte:head>
    <title>VO2max 계산기 - 엔듀로허브</title>
    <meta name="description" content="VO2max 계산기 - 대회 기록으로 최대산소섭취량을 추정하고 체력 등급과 훈련 페이스를 확인하세요. Jack Daniels VDOT 공식 기반." />
    <meta property="og:title" content="VO2max 계산기 - 엔듀로허브" />
    <meta property="og:description" content="대회 기록으로 최대산소섭취량을 추정하고 체력 등급을 확인하세요." />
    {@html `<script type="application/ld+json">${JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebApplication',
        'name': 'VO2max 계산기 - 엔듀로허브',
        'description': '대회 기록으로 VO2max(최대산소섭취량)를 추정하고 체력 등급을 확인하세요.',
        'applicationCategory': 'SportsApplication',
        'operatingSystem': 'Web',
        'offers': { '@type': 'Offer', 'price': '0', 'priceCurrency': 'KRW' },
    })}</script>`}
    {@html `<script type="application/ld+json">${JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            { '@type': 'ListItem', 'position': 1, 'name': '홈', 'item': 'https://www.endurohub.kr' },
            { '@type': 'ListItem', 'position': 2, 'name': 'VO2max 계산기' },
        ],
    })}</script>`}
</svelte:head>

<div class="container mx-auto px-4 py-8">
    <div class="breadcrumbs text-sm mb-6">
        <ul>
            <li><a href="/">홈</a></li>
            <li>VO2max 계산기</li>
        </ul>
    </div>

    <div class="mb-8">
        <h1 class="text-2xl md:text-3xl font-bold">VO2max 계산기</h1>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div class="lg:col-span-2 space-y-6">
            <div class="card bg-base-100 border border-base-300">
                <div class="card-body space-y-4">
                    <div class="form-control">
                        <div class="label"><span class="label-text font-medium">성별</span></div>
                        <div class="flex gap-2">
                            <button type="button" class="btn btn-sm cursor-pointer transition-colors duration-200 {gender === 'male' ? 'btn-primary' : 'btn-outline'}" onclick={() => gender = 'male'}>남성</button>
                            <button type="button" class="btn btn-sm cursor-pointer transition-colors duration-200 {gender === 'female' ? 'btn-primary' : 'btn-outline'}" onclick={() => gender = 'female'}>여성</button>
                        </div>
                    </div>

                    <DistanceSelector bind:selected={selectedDistance} bind:customDistance={customDistanceKm} />
                    <TimeInput bind:hours bind:minutes bind:seconds label="완주 기록" />
                </div>
            </div>

            {#if hasResult}
                <div class="card bg-base-100 border border-base-300">
                    <div class="card-body">
                        <h2 class="font-semibold text-lg mb-4">측정 결과</h2>

                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                            <div class="bg-primary/5 border border-primary/20 rounded-xl p-5 text-center">
                                <p class="text-xs text-base-content/50 mb-1">VO2max</p>
                                <p class="text-3xl font-bold text-primary tabular-nums">{vo2max.toFixed(1)}</p>
                                <p class="text-xs text-base-content/50 mt-1">ml/kg/min</p>
                            </div>
                            <div class="bg-base-200/60 rounded-xl p-5 text-center">
                                <p class="text-xs text-base-content/50 mb-1">등급</p>
                                <p class="mt-1">
                                    <span class="badge badge-lg {rating?.color}">{rating?.label}</span>
                                </p>
                                <p class="text-xs text-base-content/50 mt-2">{rating?.description}</p>
                            </div>
                            <div class="bg-base-200/60 rounded-xl p-5 text-center">
                                <p class="text-xs text-base-content/50 mb-1">상위</p>
                                <p class="text-3xl font-bold tabular-nums">{100 - percentile}<span class="text-lg">%</span></p>
                                <p class="text-xs text-base-content/50 mt-1">동성 일반인 기준</p>
                            </div>
                        </div>

                        <div class="mb-6">
                            <div class="flex justify-between text-xs text-base-content/50 mb-1">
                                <span>20</span><span>30</span><span>40</span><span>50</span><span>60</span><span>70+</span>
                            </div>
                            <div class="w-full h-3 rounded-full bg-base-200 relative overflow-hidden">
                                <div class="h-full rounded-full bg-gradient-to-r from-info via-success via-warning to-error transition-all duration-500 ease-out" style="width: {gaugePercent}%"></div>
                            </div>
                        </div>

                        {#if paces}
                            <h3 class="font-semibold text-base mb-3">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline-block mr-1 -mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                                추천 훈련 페이스 (Jack Daniels VDOT)
                            </h3>
                            <div class="grid grid-cols-2 sm:grid-cols-5 gap-3">
                                <div class="text-center p-3 rounded-lg bg-success/10 border border-success/20">
                                    <p class="text-xs text-base-content/50">이지런</p>
                                    <p class="font-bold tabular-nums text-success">{paces.easy}</p>
                                    <p class="text-xs text-base-content/50">/km</p>
                                </div>
                                <div class="text-center p-3 rounded-lg bg-primary/10 border border-primary/20">
                                    <p class="text-xs text-base-content/50">마라톤</p>
                                    <p class="font-bold tabular-nums text-primary">{paces.marathon}</p>
                                    <p class="text-xs text-base-content/50">/km</p>
                                </div>
                                <div class="text-center p-3 rounded-lg bg-warning/10 border border-warning/20">
                                    <p class="text-xs text-base-content/50">템포</p>
                                    <p class="font-bold tabular-nums text-warning">{paces.tempo}</p>
                                    <p class="text-xs text-base-content/50">/km</p>
                                </div>
                                <div class="text-center p-3 rounded-lg bg-error/10 border border-error/20">
                                    <p class="text-xs text-base-content/50">인터벌</p>
                                    <p class="font-bold tabular-nums text-error">{paces.interval}</p>
                                    <p class="text-xs text-base-content/50">/km</p>
                                </div>
                                <div class="text-center p-3 rounded-lg bg-secondary/10 border border-secondary/20">
                                    <p class="text-xs text-base-content/50">반복</p>
                                    <p class="font-bold tabular-nums text-secondary">{paces.repetition}</p>
                                    <p class="text-xs text-base-content/50">/km</p>
                                </div>
                            </div>
                        {/if}
                    </div>
                </div>
            {/if}
        </div>

        <div class="space-y-6">
            <div class="card bg-base-100 border border-base-300">
                <div class="card-body">
                    <h2 class="font-semibold text-base mb-3">VO2max란?</h2>
                    <p class="text-sm text-base-content/70 leading-relaxed">
                        VO2max(최대산소섭취량)는 운동 중 몸이 사용할 수 있는 최대 산소량으로, 유산소 체력의 가장 중요한 지표입니다.
                    </p>
                    <div class="divider my-2"></div>
                    <p class="text-xs text-base-content/50 mb-2">일반적인 VO2max 범위</p>
                    <ul class="text-sm space-y-1.5">
                        <li class="flex justify-between"><span class="text-base-content/60">비활동 성인</span><span class="tabular-nums font-medium">30~40</span></li>
                        <li class="flex justify-between"><span class="text-base-content/60">활동적 성인</span><span class="tabular-nums font-medium">40~50</span></li>
                        <li class="flex justify-between"><span class="text-base-content/60">시민 러너</span><span class="tabular-nums font-medium">45~55</span></li>
                        <li class="flex justify-between"><span class="text-base-content/60">준엘리트</span><span class="tabular-nums font-medium">55~65</span></li>
                        <li class="flex justify-between"><span class="text-base-content/60">엘리트 선수</span><span class="tabular-nums font-medium">70~85</span></li>
                    </ul>
                </div>
            </div>

            <ToolsSidebar current="vo2max" />
        </div>
    </div>
</div>
