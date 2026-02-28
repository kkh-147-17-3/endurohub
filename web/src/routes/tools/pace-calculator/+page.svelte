<script lang="ts">
    import { page } from '$app/stores';
    import DistanceSelector from '$lib/components/Tools/DistanceSelector.svelte';
    import TimeInput from '$lib/components/Tools/TimeInput.svelte';
    import PaceInput from '$lib/components/Tools/PaceInput.svelte';
    import SplitTable from '$lib/components/Tools/SplitTable.svelte';
    import ToolsSidebar from '$lib/components/Tools/ToolsSidebar.svelte';
    import type { CalculationMode, DistancePreset, SplitStrategy } from '$lib/tools/types';
    import {
        DISTANCES, timeToPaceSeconds, paceToTotalSeconds, paceToSpeed,
        formatTime, formatPace, generateSplits,
        FULL_MARATHON_PRESETS, HALF_MARATHON_PRESETS
    } from '$lib/tools/pace-calculator';

    let activeTab = $state<CalculationMode>('time-to-pace');

    let selectedDistance = $state<DistancePreset>('full');
    let customDistanceKm = $state(10);

    let targetHours = $state(3);
    let targetMinutes = $state(59);
    let targetSeconds = $state(59);

    let paceMinutes = $state(5);
    let paceSeconds = $state(30);

    let splitStrategy = $state<SplitStrategy>('even');
    let splitInterval = $state(5);

    let distanceKm = $derived(
        selectedDistance === 'custom' ? customDistanceKm : DISTANCES[selectedDistance]?.km || 42.195
    );

    let mode1PaceSeconds = $derived(
        timeToPaceSeconds(targetHours, targetMinutes, targetSeconds, distanceKm)
    );
    let mode1PaceFormatted = $derived(formatPace(mode1PaceSeconds));
    let mode1SpeedKmH = $derived(paceToSpeed(mode1PaceSeconds).toFixed(2));

    let mode2TotalSeconds = $derived(
        paceToTotalSeconds(paceMinutes, paceSeconds, distanceKm)
    );
    let mode2TimeFormatted = $derived(formatTime(mode2TotalSeconds));
    let mode2SpeedKmH = $derived(paceToSpeed(paceMinutes * 60 + paceSeconds).toFixed(2));

    let currentPaceSeconds = $derived(
        activeTab === 'pace-to-time'
            ? paceMinutes * 60 + paceSeconds
            : mode1PaceSeconds
    );

    let splits = $derived(
        generateSplits(distanceKm, currentPaceSeconds, splitStrategy, splitInterval)
    );

    let showSplitTable = $derived(splits.length > 0 && splits.length <= 100);

    let currentPresets = $derived(
        selectedDistance === 'half' ? HALF_MARATHON_PRESETS
        : selectedDistance === 'full' ? FULL_MARATHON_PRESETS
        : null
    );

    function applyPreset(preset: { hours: number; minutes: number; seconds: number }) {
        targetHours = preset.hours;
        targetMinutes = preset.minutes;
        targetSeconds = preset.seconds;
        activeTab = 'time-to-pace';
    }

    let copied = $state(false);
    function copyResults() {
        const lines = splits.map(s => `${s.label}\t${s.pace}/km\t${s.splitTime}\t${s.cumulativeTime}`);
        const header = '구간\t페이스\t구간시간\t누적시간';
        navigator.clipboard.writeText([header, ...lines].join('\n'));
        copied = true;
        setTimeout(() => copied = false, 2000);
    }

    const tabs: { key: CalculationMode; label: string }[] = [
        { key: 'time-to-pace', label: '목표시간 → 페이스' },
        { key: 'pace-to-time', label: '페이스 → 완주시간' },
    ];
</script>

<svelte:head>
    <title>마라톤 페이스 계산기 - 엔듀로허브</title>
    <meta name="description" content="마라톤 페이스 계산기 - 목표 시간에 맞는 km당 페이스, 평균 속도, 구간별 스플릿을 계산하세요. 5km, 10km, 하프마라톤, 풀마라톤 지원." />
    <meta property="og:title" content="마라톤 페이스 계산기 - 엔듀로허브" />
    <meta property="og:description" content="목표 시간에 맞는 km당 페이스, 평균 속도, 구간별 스플릿을 계산하세요." />
    {@html `<script type="application/ld+json">${JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebApplication',
        'name': '마라톤 페이스 계산기 - 엔듀로허브',
        'description': '마라톤 페이스 계산기 - 목표 시간으로 km당 페이스를 계산하고, 구간별 스플릿 테이블을 확인하세요.',
        'applicationCategory': 'SportsApplication',
        'operatingSystem': 'Web',
        'offers': { '@type': 'Offer', 'price': '0', 'priceCurrency': 'KRW' },
    })}</script>`}
    {@html `<script type="application/ld+json">${JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            { '@type': 'ListItem', 'position': 1, 'name': '홈', 'item': 'https://www.endurohub.kr' },
            { '@type': 'ListItem', 'position': 2, 'name': '페이스 계산기' },
        ],
    })}</script>`}
</svelte:head>

<div class="container mx-auto px-4 py-8">
    <div class="breadcrumbs text-sm mb-6">
        <ul>
            <li><a href="/">홈</a></li>
            <li>페이스 계산기</li>
        </ul>
    </div>

    <div class="mb-8">
        <h1 class="text-2xl md:text-3xl font-bold">페이스 계산기</h1>
        <p class="text-base-content/60 mt-1">목표 시간과 페이스를 계산하고 구간별 스플릿을 확인하세요</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div class="lg:col-span-2 space-y-6">
            <div class="card bg-base-100 border border-base-300">
                <div class="card-body">
                    <div role="tablist" class="flex gap-2 mb-6 p-1 bg-base-200 rounded-lg">
                        {#each tabs as tab (tab.key)}
                            <button
                                role="tab"
                                class="flex-1 py-2.5 px-4 text-sm font-medium rounded-md cursor-pointer transition-all duration-200
                                    {activeTab === tab.key ? 'bg-base-100 text-primary shadow-sm' : 'text-base-content/60 hover:text-base-content'}"
                                onclick={() => activeTab = tab.key}
                                aria-selected={activeTab === tab.key}
                            >
                                {tab.label}
                            </button>
                        {/each}
                    </div>

                    <DistanceSelector bind:selected={selectedDistance} bind:customDistance={customDistanceKm} />

                    <div class="divider my-2"></div>

                    {#if activeTab === 'time-to-pace'}
                        <TimeInput bind:hours={targetHours} bind:minutes={targetMinutes} bind:seconds={targetSeconds} />

                        {#if mode1PaceSeconds > 0 && isFinite(mode1PaceSeconds)}
                            <div class="grid grid-cols-2 gap-4 mt-6">
                                <div class="bg-primary/10 border-2 border-primary/30 rounded-xl p-5 text-center">
                                    <p class="text-sm text-base-content/50 mb-2">km당 페이스</p>
                                    <p class="text-3xl md:text-4xl font-extrabold text-primary tabular-nums">{mode1PaceFormatted}</p>
                                    <p class="text-sm text-base-content/40 mt-1">/km</p>
                                </div>
                                <div class="bg-base-200/60 border border-base-300 rounded-xl p-5 text-center">
                                    <p class="text-sm text-base-content/50 mb-2">평균 속도</p>
                                    <p class="text-3xl md:text-4xl font-extrabold tabular-nums">{mode1SpeedKmH}</p>
                                    <p class="text-sm text-base-content/40 mt-1">km/h</p>
                                </div>
                            </div>
                        {/if}
                    {:else}
                        <PaceInput bind:minutes={paceMinutes} bind:seconds={paceSeconds} />

                        {#if mode2TotalSeconds > 0 && isFinite(mode2TotalSeconds)}
                            <div class="grid grid-cols-2 gap-4 mt-6">
                                <div class="bg-primary/10 border-2 border-primary/30 rounded-xl p-5 text-center">
                                    <p class="text-sm text-base-content/50 mb-2">예상 완주 시간</p>
                                    <p class="text-3xl md:text-4xl font-extrabold text-primary tabular-nums">{mode2TimeFormatted}</p>
                                </div>
                                <div class="bg-base-200/60 border border-base-300 rounded-xl p-5 text-center">
                                    <p class="text-sm text-base-content/50 mb-2">평균 속도</p>
                                    <p class="text-3xl md:text-4xl font-extrabold tabular-nums">{mode2SpeedKmH}</p>
                                    <p class="text-sm text-base-content/40 mt-1">km/h</p>
                                </div>
                            </div>
                        {/if}
                    {/if}
                </div>
            </div>

            {#if showSplitTable}
                <div class="card bg-base-100 border border-base-300">
                    <div class="card-body">
                        <div class="flex items-center justify-between mb-4">
                            <h2 class="text-lg font-semibold">구간별 스플릿</h2>
                            <div class="flex items-center gap-2">
                                <button
                                    type="button"
                                    class="btn btn-ghost btn-xs cursor-pointer"
                                    onclick={copyResults}
                                    aria-label="스플릿 테이블 복사"
                                >
                                    {#if copied}
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                                        <span class="text-success">복사됨</span>
                                    {:else}
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                                        복사
                                    {/if}
                                </button>
                            </div>
                        </div>

                        <div class="flex flex-wrap items-center gap-3 mb-4">
                            <div class="flex gap-1" role="radiogroup" aria-label="스플릿 전략">
                                <button type="button" role="radio" aria-checked={splitStrategy === 'even'} class="btn btn-xs cursor-pointer transition-colors duration-200 {splitStrategy === 'even' ? 'btn-primary' : 'btn-outline'}" onclick={() => splitStrategy = 'even'} title="모든 구간을 동일한 페이스로 달리는 전략">이븐 페이스</button>
                                <button type="button" role="radio" aria-checked={splitStrategy === 'negative'} class="btn btn-xs cursor-pointer transition-colors duration-200 {splitStrategy === 'negative' ? 'btn-primary' : 'btn-outline'}" onclick={() => splitStrategy = 'negative'} title="후반부를 전반부보다 빠르게 달리는 전략 (엘리트 선수들이 선호)">네거티브 스플릿</button>
                            </div>
                            <div class="flex gap-1" role="radiogroup" aria-label="스플릿 간격">
                                <button type="button" role="radio" aria-checked={splitInterval === 1} class="btn btn-xs cursor-pointer transition-colors duration-200 {splitInterval === 1 ? 'btn-neutral' : 'btn-outline'}" onclick={() => splitInterval = 1}>1km</button>
                                <button type="button" role="radio" aria-checked={splitInterval === 5} class="btn btn-xs cursor-pointer transition-colors duration-200 {splitInterval === 5 ? 'btn-neutral' : 'btn-outline'}" onclick={() => splitInterval = 5}>5km</button>
                            </div>
                        </div>

                        <SplitTable {splits} highlightHalf={splitStrategy === 'negative'} />
                    </div>
                </div>
            {/if}
        </div>

        <div class="space-y-6">
            {#if currentPresets}
                <div class="card bg-base-100 border border-base-300">
                    <div class="card-body">
                        <h2 class="font-semibold text-base mb-3">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline-block mr-1 -mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                            빠른 설정
                        </h2>

                        {#if selectedDistance === 'full'}
                            <p class="text-xs text-base-content/50 mb-2">풀 마라톤 (42.195km)</p>
                            <div class="space-y-1.5">
                                {#each FULL_MARATHON_PRESETS as preset}
                                    <button type="button" class="btn btn-outline btn-sm btn-block justify-start cursor-pointer transition-colors duration-200 hover:btn-primary" onclick={() => { selectedDistance = 'full'; applyPreset(preset); }}>{preset.label}</button>
                                {/each}
                            </div>
                        {/if}

                        {#if selectedDistance === 'half'}
                            <p class="text-xs text-base-content/50 mb-2">하프 마라톤 (21.0975km)</p>
                            <div class="space-y-1.5">
                                {#each HALF_MARATHON_PRESETS as preset}
                                    <button type="button" class="btn btn-outline btn-sm btn-block justify-start cursor-pointer transition-colors duration-200 hover:btn-primary" onclick={() => { selectedDistance = 'half'; applyPreset(preset); }}>{preset.label}</button>
                                {/each}
                            </div>
                        {/if}

                        {#if selectedDistance === 'full'}
                            <div class="divider my-2"></div>
                            <p class="text-xs text-base-content/50 mb-2">하프 마라톤</p>
                            <div class="space-y-1.5">
                                {#each HALF_MARATHON_PRESETS as preset}
                                    <button type="button" class="btn btn-outline btn-sm btn-block justify-start cursor-pointer transition-colors duration-200 hover:btn-primary" onclick={() => { selectedDistance = 'half'; applyPreset(preset); }}>{preset.label}</button>
                                {/each}
                            </div>
                        {:else if selectedDistance === 'half'}
                            <div class="divider my-2"></div>
                            <p class="text-xs text-base-content/50 mb-2">풀 마라톤</p>
                            <div class="space-y-1.5">
                                {#each FULL_MARATHON_PRESETS as preset}
                                    <button type="button" class="btn btn-outline btn-sm btn-block justify-start cursor-pointer transition-colors duration-200 hover:btn-primary" onclick={() => { selectedDistance = 'full'; applyPreset(preset); }}>{preset.label}</button>
                                {/each}
                            </div>
                        {/if}
                    </div>
                </div>
            {/if}

            <ToolsSidebar current="pace-calculator" />
        </div>
    </div>
</div>
