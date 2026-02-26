<script lang="ts">
    import TrainingWeekCard from '$lib/components/Tools/TrainingWeekCard.svelte';
    import ToolsSidebar from '$lib/components/Tools/ToolsSidebar.svelte';
    import type { TrainingDistance, TrainingWeeks, TargetTimePreset } from '$lib/tools/types';
    import { phaseLabels, phaseColors } from '$lib/tools/types';
    import { generateTrainingPlan, FULL_MARATHON_TARGETS, HALF_MARATHON_TARGETS } from '$lib/tools/training-plans';
    import { formatPace } from '$lib/tools/pace-calculator';

    let targetDistance = $state<TrainingDistance>('full');
    let selectedTargetIndex = $state(2);
    let trainingWeeks = $state<TrainingWeeks>(16);
    let raceDate = $state('');

    let targetPresets = $derived<TargetTimePreset[]>(
        targetDistance === 'full' ? FULL_MARATHON_TARGETS : HALF_MARATHON_TARGETS
    );

    let selectedTarget = $derived(targetPresets[selectedTargetIndex] || targetPresets[0]);

    let prevDistance = $state<TrainingDistance>('full');
    $effect(() => {
        if (targetDistance !== prevDistance) {
            selectedTargetIndex = 2;
            prevDistance = targetDistance;
        }
    });

    let plan = $derived(
        generateTrainingPlan(targetDistance, selectedTarget.totalMinutes, trainingWeeks)
    );

    let distanceKm = $derived(targetDistance === 'full' ? 42.195 : 21.0975);
    let racePaceSeconds = $derived((selectedTarget.totalMinutes * 60) / distanceKm);
    let paceZones = $derived({
        easy: formatPace(racePaceSeconds * 1.25),
        longRun: formatPace(racePaceSeconds * 1.20),
        tempo: formatPace(racePaceSeconds * 1.08),
        racePace: formatPace(racePaceSeconds),
        interval: formatPace(racePaceSeconds * 0.92),
    });

    let weekDateLabels = $derived.by(() => {
        if (!raceDate) return null;
        const race = new Date(raceDate);
        return plan.weeks.map((_, i) => {
            const weekStart = new Date(race);
            weekStart.setDate(race.getDate() - (plan.totalWeeks - i) * 7);
            return `${weekStart.getMonth() + 1}/${weekStart.getDate()}`;
        });
    });

    let phaseSummary = $derived.by(() => {
        const phases = new Map<string, { count: number; phase: string }>();
        plan.weeks.forEach(w => {
            const key = w.phase;
            if (!phases.has(key)) {
                phases.set(key, { count: 0, phase: w.phase });
            }
            phases.get(key)!.count++;
        });
        return Array.from(phases.values());
    });

    let allExpanded = $state(false);
</script>

<svelte:head>
    <title>마라톤 훈련 플랜 - EnduroHub</title>
    <meta name="description" content="마라톤 훈련 플랜 생성기 - 목표 시간에 맞는 12주/16주 훈련 계획을 무료로 만들어 보세요. 풀마라톤, 하프마라톤 서브3, 서브4 훈련 지원." />
    <meta property="og:title" content="마라톤 훈련 플랜 - EnduroHub" />
    <meta property="og:description" content="목표 시간에 맞는 12주/16주 훈련 계획을 무료로 만들어 보세요." />
    {@html `<script type="application/ld+json">${JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebApplication',
        'name': '마라톤 훈련 플랜 - EnduroHub',
        'description': '마라톤 훈련 플랜 생성기 - 목표 시간에 맞는 12주/16주 훈련 계획을 무료로 만들어 보세요.',
        'applicationCategory': 'SportsApplication',
        'operatingSystem': 'Web',
        'offers': { '@type': 'Offer', 'price': '0', 'priceCurrency': 'KRW' },
    })}</script>`}
    {@html `<script type="application/ld+json">${JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            { '@type': 'ListItem', 'position': 1, 'name': '홈', 'item': 'https://www.endurohub.kr' },
            { '@type': 'ListItem', 'position': 2, 'name': '훈련 플랜' },
        ],
    })}</script>`}
</svelte:head>

<div class="container mx-auto px-4 py-8">
    <div class="breadcrumbs text-sm mb-6">
        <ul>
            <li><a href="/">홈</a></li>
            <li>훈련 플랜</li>
        </ul>
    </div>

    <div class="mb-8">
        <h1 class="text-2xl md:text-3xl font-bold">훈련 플랜</h1>
        <p class="text-base-content/60 mt-1">목표 대회에 맞는 맞춤 훈련 계획을 만들어 보세요</p>
    </div>

    <div class="card bg-base-100 border border-base-300 mb-8">
        <div class="card-body">
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <div class="form-control">
                    <label class="label"><span class="label-text font-medium">목표 거리</span></label>
                    <div class="flex gap-2">
                        <button type="button" class="btn flex-1 cursor-pointer transition-colors duration-200 {targetDistance === 'half' ? 'btn-primary' : 'btn-outline'}" onclick={() => targetDistance = 'half'}>하프</button>
                        <button type="button" class="btn flex-1 cursor-pointer transition-colors duration-200 {targetDistance === 'full' ? 'btn-primary' : 'btn-outline'}" onclick={() => targetDistance = 'full'}>풀</button>
                    </div>
                </div>
                <div class="form-control">
                    <label class="label" for="target-time"><span class="label-text font-medium">목표 기록</span></label>
                    <select id="target-time" class="select select-bordered cursor-pointer" bind:value={selectedTargetIndex}>
                        {#each targetPresets as preset, i}
                            <option value={i}>{preset.label}</option>
                        {/each}
                    </select>
                </div>
                <div class="form-control">
                    <label class="label"><span class="label-text font-medium">훈련 기간</span></label>
                    <div class="flex gap-2">
                        <button type="button" class="btn flex-1 cursor-pointer transition-colors duration-200 {trainingWeeks === 12 ? 'btn-primary' : 'btn-outline'}" onclick={() => trainingWeeks = 12}>12주</button>
                        <button type="button" class="btn flex-1 cursor-pointer transition-colors duration-200 {trainingWeeks === 16 ? 'btn-primary' : 'btn-outline'}" onclick={() => trainingWeeks = 16}>16주</button>
                    </div>
                </div>
                <div class="form-control">
                    <label class="label" for="race-date"><span class="label-text font-medium">대회일 <span class="text-base-content/40 font-normal">(선택)</span></span></label>
                    <input id="race-date" type="date" class="input input-bordered cursor-pointer" bind:value={raceDate} />
                </div>
            </div>
        </div>
    </div>

    <div class="card bg-base-100 border border-base-300 mb-8">
        <div class="card-body">
            <h2 class="font-semibold text-base mb-3">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline-block mr-1 -mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                페이스 존
            </h2>
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                <div class="text-center p-3 rounded-lg bg-success/10 border border-success/20">
                    <p class="text-xs text-base-content/50">이지런</p>
                    <p class="font-bold tabular-nums text-success">{paceZones.easy}</p>
                    <p class="text-xs text-base-content/40">/km</p>
                </div>
                <div class="text-center p-3 rounded-lg bg-primary/10 border border-primary/20">
                    <p class="text-xs text-base-content/50">롱런</p>
                    <p class="font-bold tabular-nums text-primary">{paceZones.longRun}</p>
                    <p class="text-xs text-base-content/40">/km</p>
                </div>
                <div class="text-center p-3 rounded-lg bg-warning/10 border border-warning/20">
                    <p class="text-xs text-base-content/50">템포런</p>
                    <p class="font-bold tabular-nums text-warning">{paceZones.tempo}</p>
                    <p class="text-xs text-base-content/40">/km</p>
                </div>
                <div class="text-center p-3 rounded-lg bg-secondary/10 border border-secondary/20">
                    <p class="text-xs text-base-content/50">레이스페이스</p>
                    <p class="font-bold tabular-nums text-secondary">{paceZones.racePace}</p>
                    <p class="text-xs text-base-content/40">/km</p>
                </div>
                <div class="text-center p-3 rounded-lg bg-error/10 border border-error/20">
                    <p class="text-xs text-base-content/50">인터벌</p>
                    <p class="font-bold tabular-nums text-error">{paceZones.interval}</p>
                    <p class="text-xs text-base-content/40">/km</p>
                </div>
            </div>
        </div>
    </div>

    <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
        <div class="flex items-center gap-3 flex-wrap">
            <h2 class="text-xl font-bold">{selectedTarget.label} 훈련 플랜</h2>
            <span class="badge badge-lg badge-outline">{trainingWeeks}주</span>
        </div>
        <button type="button" class="btn btn-ghost btn-sm cursor-pointer" onclick={() => allExpanded = !allExpanded}>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                {#if allExpanded}
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" />
                {:else}
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                {/if}
            </svg>
            {allExpanded ? '모두 접기' : '모두 펼치기'}
        </button>
    </div>

    <div class="flex mb-3 rounded-full overflow-hidden h-3">
        {#each plan.weeks as week}
            <div class="flex-1 {phaseColors[week.phase]} transition-colors duration-200"></div>
        {/each}
    </div>
    <div class="flex justify-between mb-6">
        {#each phaseSummary as ps}
            <span class="text-sm font-medium text-base-content/60">{phaseLabels[ps.phase as keyof typeof phaseLabels]} <span class="text-base-content/40">{ps.count}주</span></span>
        {/each}
    </div>

    <div class="space-y-3">
        {#each plan.weeks as week, i (week.week)}
            <TrainingWeekCard
                trainingWeek={week}
                weekDateLabel={weekDateLabels?.[i] || ''}
                forceOpen={allExpanded}
                initialOpen={i === 0}
            />
        {/each}
    </div>

    <div class="mt-12 max-w-sm mx-auto">
        <ToolsSidebar current="training-plan" />
    </div>
</div>
