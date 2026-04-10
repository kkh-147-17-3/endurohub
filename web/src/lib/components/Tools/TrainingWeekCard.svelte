<script lang="ts">
    import type { TrainingWeek } from '$lib/tools/types';
    import { phaseLabels, phaseBadgeColors, phaseColors, workoutLabels, workoutColors } from '$lib/tools/types';

    let {
        trainingWeek,
        weekDateLabel = '',
        forceOpen = false,
        initialOpen = false,
    }: {
        trainingWeek: TrainingWeek;
        weekDateLabel?: string;
        forceOpen?: boolean;
        initialOpen?: boolean;
    } = $props();

    let expanded = $state(false);
    $effect(() => { expanded = initialOpen; });
    let isOpen = $derived(forceOpen || expanded);

    const dayNames = ['월', '화', '수', '목', '금', '토', '일'];

    let workoutSummary = $derived.by(() => {
        const types = new Set<string>();
        for (const day of trainingWeek.days) {
            if (day.type !== 'rest') types.add(day.type);
        }
        return Array.from(types);
    });
</script>

<div class="border border-base-300 rounded-lg overflow-hidden transition-colors duration-200 hover:border-base-content/20">
    <button
        type="button"
        class="w-full flex items-center justify-between p-4 cursor-pointer bg-base-100 hover:bg-base-200/50 transition-colors duration-200"
        onclick={() => expanded = !expanded}
        aria-expanded={isOpen}
    >
        <div class="flex items-center gap-3 flex-wrap">
            <span class="font-semibold text-base">{trainingWeek.week}주차</span>
            <span class="badge badge-sm {phaseBadgeColors[trainingWeek.phase]}">
                {phaseLabels[trainingWeek.phase]}
            </span>
            <span class="text-sm text-base-content/60">
                주간 {trainingWeek.totalDistanceKm}km
            </span>
            {#if weekDateLabel}
                <span class="text-xs text-base-content/50">{weekDateLabel}~</span>
            {/if}
            {#if !isOpen}
                <div class="hidden sm:block w-20 h-2 bg-base-200 rounded-full overflow-hidden" title="주간 {trainingWeek.totalDistanceKm}km">
                    <div
                        class="h-full {phaseColors[trainingWeek.phase]} rounded-full transition-all duration-300"
                        style="width: {Math.min(100, (trainingWeek.totalDistanceKm / 70) * 100)}%"
                    ></div>
                </div>
                <div class="flex flex-wrap gap-1">
                    {#each workoutSummary as type}
                        <span class="badge badge-sm text-xs {workoutColors[type as keyof typeof workoutColors]}">{workoutLabels[type as keyof typeof workoutLabels]}</span>
                    {/each}
                </div>
            {/if}
        </div>
        <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5 text-base-content/50 transition-transform duration-200 {isOpen ? 'rotate-180' : ''}"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
        >
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
    </button>

    {#if isOpen}
        <div class="border-t border-base-300 p-4">
            <div class="hidden md:grid grid-cols-7 gap-2">
                {#each trainingWeek.days as day, i}
                    <div class="text-center p-3 rounded-lg bg-base-200/50 space-y-1.5">
                        <div class="text-xs font-medium text-base-content/50">{dayNames[i]}</div>
                        <div>
                            <span class="badge badge-sm text-xs {workoutColors[day.type]}">
                                {workoutLabels[day.type]}
                            </span>
                        </div>
                        <div class="text-xs text-base-content/70 leading-tight">{day.description}</div>
                        {#if day.paceGuide}
                            <div class="text-xs text-primary/80 tabular-nums">{day.paceGuide}</div>
                        {/if}
                    </div>
                {/each}
            </div>

            <div class="md:hidden space-y-2">
                {#each trainingWeek.days as day, i}
                    <div class="flex items-start gap-3 p-2 rounded-lg {day.type !== 'rest' ? 'bg-base-200/50' : ''}">
                        <span class="text-xs font-medium text-base-content/50 w-4 pt-0.5">{dayNames[i]}</span>
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-2">
                                <span class="badge badge-sm text-xs {workoutColors[day.type]}">
                                    {workoutLabels[day.type]}
                                </span>
                                <span class="text-sm">{day.description}</span>
                            </div>
                            {#if day.paceGuide}
                                <div class="text-xs text-primary/80 tabular-nums mt-0.5">{day.paceGuide}</div>
                            {/if}
                        </div>
                    </div>
                {/each}
            </div>
        </div>
    {/if}
</div>
