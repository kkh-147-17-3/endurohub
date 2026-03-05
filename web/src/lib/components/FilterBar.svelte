<script lang="ts">
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { onMount } from 'svelte';
    import { slide } from 'svelte/transition';
    import RangeSlider from 'svelte-range-slider-pips';
    import type { SportOption, DistanceCategory } from '$lib/types';

    const STORAGE_KEY = 'races-filter';

    function getCurrentMonth(): string {
        const now = new Date();
        return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    }

    function generateMonths(start: string, end: string): string[] {
        const months: string[] = [];
        let [y, m] = start.split('-').map(Number);
        const [ey, em] = end.split('-').map(Number);
        while (y < ey || (y === ey && m <= em)) {
            months.push(`${y}-${String(m).padStart(2, '0')}`);
            m++;
            if (m > 12) { m = 1; y++; }
        }
        return months;
    }

    const SLIDER_START = `${new Date().getFullYear()}-01`;
    const SLIDER_END = `${new Date().getFullYear() + 1}-03`;
    const allMonths = generateMonths(SLIDER_START, SLIDER_END);
    const NO_LIMIT_IDX = allMonths.length;

    function monthToIdx(month: string | null | undefined, fallback: number): number {
        if (!month) return fallback;
        const idx = allMonths.indexOf(month);
        return idx >= 0 ? idx : fallback;
    }

    function idxToMonth(idx: number): string | null {
        if (idx >= 0 && idx < allMonths.length) return allMonths[idx];
        return null;
    }

    function sliderLabel(idx: number): string {
        if (idx >= allMonths.length) return '제한없음';
        const [y, m] = allMonths[idx].split('-');
        return `${y}.${m}`;
    }

    type Preset = { label: string; fromIdx: number; toIdx: number };
    function buildPresets(): Preset[] {
        const now = new Date();
        const curFrom = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
        const curFromIdx = monthToIdx(curFrom, 0);
        const curYear = now.getFullYear();
        function addMonths(count: number): string {
            const d = new Date(now.getFullYear(), now.getMonth() + count - 1, 1);
            return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        }
        return [
            { label: '3개월', fromIdx: curFromIdx, toIdx: monthToIdx(addMonths(3), NO_LIMIT_IDX) },
            { label: '6개월', fromIdx: curFromIdx, toIdx: monthToIdx(addMonths(6), NO_LIMIT_IDX) },
            { label: '올해', fromIdx: monthToIdx(`${curYear}-01`, 0), toIdx: monthToIdx(`${curYear}-12`, NO_LIMIT_IDX) },
            { label: '내년', fromIdx: monthToIdx(`${curYear + 1}-01`, 0), toIdx: monthToIdx(`${curYear + 1}-12`, NO_LIMIT_IDX) },
            { label: '전체', fromIdx: 0, toIdx: NO_LIMIT_IDX },
        ];
    }
    const presets = buildPresets();

    function applyPreset(preset: Preset) {
        sliderValues = [preset.fromIdx, preset.toIdx];
    }

    let activePreset = $derived(
        presets.find(p => p.fromIdx === fromIdx && p.toIdx === toIdx)?.label ?? null
    );

    let {
        sports,
        regions,
        distanceCategories = {},
        selectedSport = [],
        selectedRegion = [],
        selectedStatus = [],
        selectedName = null,
        selectedDistanceCategory = [],
        selectedMonthFrom = null,
        selectedMonthTo = null,
        title = '전체 대회',
        totalCount = 0
    }: {
        sports: SportOption[];
        regions: string[];
        distanceCategories?: Record<string, DistanceCategory[]>;
        selectedSport?: string[];
        selectedRegion?: string[];
        selectedStatus?: string[];
        selectedName?: string | null;
        selectedDistanceCategory?: string[];
        selectedMonthFrom?: string | null;
        selectedMonthTo?: string | null;
        title?: string;
        totalCount?: number;
    } = $props();

    const statuses = [
        { value: 'registration_open', label: '접수중' },
        { value: 'closing_soon', label: '마감임박' },
        { value: 'upcoming', label: '예정' },
        { value: 'registration_closed', label: '접수마감' },
    ];

    let name = $state('');
    let sportValues = $state<string[]>([]);
    let regionValues = $state<string[]>([]);
    let statusValues = $state<string[]>([]);
    let distanceCategoryValues = $state<string[]>([]);
    let sliderValues = $state([monthToIdx(getCurrentMonth(), 0), NO_LIMIT_IDX]);
    let isExpanded = $state(false);

    let fromIdx = $derived(sliderValues[0]);
    let toIdx = $derived(sliderValues[1]);
    let monthFrom = $derived(idxToMonth(sliderValues[0]) || getCurrentMonth());
    let monthTo = $derived(idxToMonth(sliderValues[1]) || '');

    let availableDistanceCategories = $derived(
        sportValues.length === 1 ? (distanceCategories[sportValues[0]] ?? []) : []
    );

    let prevSportKey = $state('');
    $effect(() => { prevSportKey = selectedSport.join(','); });
    $effect(() => {
        const key = sportValues.join(',');
        if (key !== prevSportKey) {
            prevSportKey = key;
            distanceCategoryValues = [];
        }
    });

    let hasMonthFilter = $derived(monthFrom !== getCurrentMonth() || monthTo !== '');
    let totalSelected = $derived(sportValues.length + regionValues.length + statusValues.length + distanceCategoryValues.length + (hasMonthFilter ? 1 : 0));

    function hasUrlParams(): boolean {
        if (typeof window === 'undefined') return false;
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.has('sport') || urlParams.has('region') || urlParams.has('status') || urlParams.has('name') || urlParams.has('distance_category') || urlParams.has('month_from') || urlParams.has('month_to') || urlParams.has('reset');
    }

    function saveToStorage() {
        const filterData = {
            name: name || null,
            sport: sportValues,
            region: regionValues,
            status: statusValues,
            distance_category: distanceCategoryValues,
            month_from: monthFrom || null,
            month_to: monthTo || null
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(filterData));
    }

    function loadFromStorage(): { name: string | null; sport: string[]; region: string[]; status: string[]; distance_category?: string[]; month_from?: string | null; month_to?: string | null } | null {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (!stored) return null;
        try {
            return JSON.parse(stored);
        } catch {
            return null;
        }
    }

    function clearStorage() {
        localStorage.removeItem(STORAGE_KEY);
    }

    let hasRouteSport = $derived(selectedSport.length > 0 && !hasUrlParams());

    onMount(() => {
        // ?reset=1 clears saved filters (used by home page "view all" links)
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('reset')) {
            clearStorage();
            urlParams.delete('reset');
            const cleanUrl = urlParams.toString()
                ? `${window.location.pathname}?${urlParams.toString()}`
                : window.location.pathname;
            goto(cleanUrl, { replaceState: true, noScroll: true });
            return;
        }

        if (hasUrlParams()) {
            const filterData = {
                name: selectedName || null,
                sport: Array.isArray(selectedSport) ? [...selectedSport] : [],
                region: Array.isArray(selectedRegion) ? [...selectedRegion] : [],
                status: Array.isArray(selectedStatus) ? [...selectedStatus] : [],
                distance_category: Array.isArray(selectedDistanceCategory) ? [...selectedDistanceCategory] : [],
                month_from: selectedMonthFrom || null,
                month_to: selectedMonthTo || null
            };
            localStorage.setItem(STORAGE_KEY, JSON.stringify(filterData));
        } else if (!hasRouteSport) {
            const saved = loadFromStorage();
            if (saved && (saved.name || saved.sport.length > 0 || saved.region.length > 0 || saved.status.length > 0 || (saved.distance_category && saved.distance_category.length > 0) || saved.month_from || saved.month_to)) {
                name = saved.name || '';
                sportValues = saved.sport || [];
                regionValues = saved.region || [];
                statusValues = saved.status || [];
                distanceCategoryValues = saved.distance_category || [];
                sliderValues = [
                    monthToIdx(saved.month_from, monthToIdx(getCurrentMonth(), 0)),
                    saved.month_to ? monthToIdx(saved.month_to, NO_LIMIT_IDX) : NO_LIMIT_IDX
                ];

                const hasExtraFilters = saved.name || saved.sport.length > 0 || saved.region.length > 0 || saved.status.length > 0
                    || (saved.distance_category && saved.distance_category.length > 0)
                    || (saved.month_from && saved.month_from !== getCurrentMonth()) || saved.month_to;

                if (hasExtraFilters) {
                    const url = new URL(window.location.href);
                    if (saved.name) url.searchParams.set('name', saved.name);
                    for (const s of saved.sport) url.searchParams.append('sport', s);
                    for (const r of saved.region) url.searchParams.append('region', r);
                    for (const s of saved.status) url.searchParams.append('status', s);
                    if (saved.distance_category) {
                        for (const dc of saved.distance_category) url.searchParams.append('distance_category', dc);
                    }
                    if (saved.month_from) url.searchParams.set('month_from', saved.month_from);
                    if (saved.month_to) url.searchParams.set('month_to', saved.month_to);

                    goto(url.toString(), { replaceState: true, noScroll: true });
                }
            }
        }
    });

    $effect(() => {
        name = selectedName || '';
        sportValues = [...selectedSport];
        regionValues = [...selectedRegion];
        statusValues = [...selectedStatus];
        distanceCategoryValues = [...selectedDistanceCategory];
        sliderValues = [
            monthToIdx(selectedMonthFrom, monthToIdx(getCurrentMonth(), 0)),
            selectedMonthTo ? monthToIdx(selectedMonthTo, NO_LIMIT_IDX) : NO_LIMIT_IDX
        ];
    });

    function handleSubmit(e: Event) {
        e.preventDefault();
        const url = new URL(window.location.pathname, window.location.origin);

        if (name) url.searchParams.set('name', name);
        for (const s of sportValues) url.searchParams.append('sport', s);
        for (const r of regionValues) url.searchParams.append('region', r);
        for (const s of statusValues) url.searchParams.append('status', s);
        for (const dc of distanceCategoryValues) url.searchParams.append('distance_category', dc);
        if (monthFrom) url.searchParams.set('month_from', monthFrom);
        if (monthTo) url.searchParams.set('month_to', monthTo);

        saveToStorage();
        isExpanded = false;

        goto(url.toString(), { noScroll: true });
    }

    function handleReset() {
        clearStorage();
        sliderValues = [monthToIdx(getCurrentMonth(), 0), NO_LIMIT_IDX];

        const url = new URL(window.location.pathname, window.location.origin);
        url.searchParams.set('month_from', getCurrentMonth());
        goto(url.toString(), { noScroll: true });
    }

    function toggleSport(value: string) {
        if (sportValues.includes(value)) {
            sportValues = sportValues.filter(v => v !== value);
        } else {
            sportValues = [...sportValues, value];
        }
    }

    function toggleRegion(value: string) {
        if (regionValues.includes(value)) {
            regionValues = regionValues.filter(v => v !== value);
        } else {
            regionValues = [...regionValues, value];
        }
    }

    function toggleStatus(value: string) {
        if (statusValues.includes(value)) {
            statusValues = statusValues.filter(v => v !== value);
        } else {
            statusValues = [...statusValues, value];
        }
    }

    function toggleDistanceCategory(value: string) {
        if (distanceCategoryValues.includes(value)) {
            distanceCategoryValues = distanceCategoryValues.filter(v => v !== value);
        } else {
            distanceCategoryValues = [...distanceCategoryValues, value];
        }
    }

    function getDistanceCategoryLabel(value: string): string {
        for (const cats of Object.values(distanceCategories)) {
            const found = cats.find((c: DistanceCategory) => c.value === value);
            if (found) return found.label;
        }
        return value;
    }

    function getSportLabel(value: string): string {
        return sports.find(s => s.value === value)?.label || value;
    }

    function getStatusLabel(value: string): string {
        return statuses.find(s => s.value === value)?.label || value;
    }

    function formatMonthLabel(ym: string): string {
        const [y, m] = ym.split('-');
        return `${y}.${m}`;
    }

    function getMonthRangeLabel(): string {
        const from = monthFrom ? formatMonthLabel(monthFrom) : '';
        const to = monthTo ? formatMonthLabel(monthTo) : '';
        if (from && to) return `${from} ~ ${to}`;
        if (from) return `${from} ~`;
        if (to) return `~ ${to}`;
        return '';
    }

    function clearMonthFilter() {
        sliderValues = [monthToIdx(getCurrentMonth(), 0), NO_LIMIT_IDX];
    }
</script>

<div class="bg-base-100 rounded-lg shadow mb-6">
    <form onsubmit={handleSubmit}>
        <div class="p-4 pb-3">
            <div class="flex items-center justify-between mb-3">
                <h1 class="text-2xl sm:text-3xl font-bold">
                    {title}
                    <span class="text-base sm:text-lg font-normal text-base-content/70">(총 {totalCount.toLocaleString()}개)</span>
                </h1>
            </div>
            <div class="flex gap-3">
                <div class="flex-1">
                    <input
                        type="text"
                        bind:value={name}
                        placeholder="대회명 검색..."
                        class="input input-bordered w-full"
                    />
                </div>
                <button type="submit" class="btn btn-primary cursor-pointer">검색</button>
            </div>
        </div>

        <div class="px-4 pb-3 flex flex-wrap items-center gap-2">
            {#each statuses as status}
                <button
                    type="button"
                    class="btn btn-sm cursor-pointer {statusValues.includes(status.value) ? 'btn-accent' : 'btn-outline'}"
                    onclick={() => toggleStatus(status.value)}
                >
                    {status.label}
                </button>
            {/each}
            <div class="border-l border-base-300 h-5 mx-1"></div>
            <button
                type="button"
                class="btn btn-outline btn-sm gap-2 cursor-pointer"
                onclick={() => isExpanded = !isExpanded}
            >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 1 1-3 0m3 0a1.5 1.5 0 1 0-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-9.75 0h9.75" />
                </svg>
                <span class="hidden sm:inline">상세필터</span>
                {#if totalSelected > 0}
                    <span class="badge badge-primary badge-sm">{totalSelected}</span>
                {/if}
            </button>
        </div>

        {#if totalSelected > 0}
            <div class="px-4 pb-3 flex flex-wrap gap-2 items-center">
                {#each sportValues as sport}
                    <span class="badge badge-primary gap-1 py-3">
                        {getSportLabel(sport)}
                        <button type="button" onclick={() => toggleSport(sport)} class="hover:opacity-70 cursor-pointer" aria-label="{getSportLabel(sport)} 필터 제거">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-3 h-3"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                        </button>
                    </span>
                {/each}
                {#each regionValues as region}
                    <span class="badge badge-secondary gap-1 py-3">
                        {region}
                        <button type="button" onclick={() => toggleRegion(region)} class="hover:opacity-70 cursor-pointer" aria-label="{region} 필터 제거">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-3 h-3"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                        </button>
                    </span>
                {/each}
                {#each distanceCategoryValues as dc}
                    <span class="badge badge-warning gap-1 py-3">
                        {getDistanceCategoryLabel(dc)}
                        <button type="button" onclick={() => toggleDistanceCategory(dc)} class="hover:opacity-70 cursor-pointer" aria-label="{getDistanceCategoryLabel(dc)} 필터 제거">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-3 h-3"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                        </button>
                    </span>
                {/each}
                {#if hasMonthFilter}
                    <span class="badge badge-info gap-1 py-3">
                        {getMonthRangeLabel()}
                        <button type="button" onclick={clearMonthFilter} class="hover:opacity-70 cursor-pointer" aria-label="개최월 필터 제거">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-3 h-3"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                        </button>
                    </span>
                {/if}
                <button type="button" onclick={handleReset} class="text-sm text-base-content/60 hover:text-error ml-2 cursor-pointer transition-colors">
                    모두 지우기
                </button>
            </div>
        {/if}

        {#if isExpanded}
            <div class="px-4 pb-4 border-t border-base-200 pt-4 space-y-4" transition:slide={{ duration: 200 }}>
                <div>
                    <span class="text-sm font-medium mb-2 block text-base-content/70">종목</span>
                    <div class="flex flex-wrap gap-2">
                        {#each sports as sport}
                            <button type="button" class="btn btn-sm cursor-pointer {sportValues.includes(sport.value) ? 'btn-primary' : 'btn-outline'}" onclick={() => toggleSport(sport.value)}>
                                {sport.label}
                            </button>
                        {/each}
                    </div>
                </div>

                <div>
                    <span class="text-sm font-medium mb-2 block text-base-content/70">지역</span>
                    <div class="flex flex-wrap gap-2">
                        {#each regions as region}
                            <button type="button" class="btn btn-sm cursor-pointer {regionValues.includes(region) ? 'btn-secondary' : 'btn-outline'}" onclick={() => toggleRegion(region)}>
                                {region}
                            </button>
                        {/each}
                    </div>
                </div>

                {#if availableDistanceCategories.length > 0}
                    <div>
                        <span class="text-sm font-medium mb-2 block text-base-content/70">거리</span>
                        <div class="flex flex-wrap gap-2">
                            {#each availableDistanceCategories as cat}
                                <button type="button" class="btn btn-sm cursor-pointer {distanceCategoryValues.includes(cat.value) ? 'btn-warning' : 'btn-outline'}" onclick={() => toggleDistanceCategory(cat.value)}>
                                    {cat.label}
                                </button>
                            {/each}
                        </div>
                    </div>
                {/if}

                <div class="bg-base-200/40 rounded-xl p-4 -mx-0.5">
                    <div class="flex items-center justify-between mb-3">
                        <span class="text-sm font-medium text-base-content/70">개최월</span>
                        <span class="text-sm font-semibold tabular-nums tracking-tight text-primary">{getMonthRangeLabel()}</span>
                    </div>

                    <div class="flex flex-wrap gap-1.5 mb-3">
                        {#each presets as preset}
                            <button
                                type="button"
                                class="btn btn-sm cursor-pointer transition-all duration-200 {activePreset === preset.label ? 'btn-primary shadow-sm' : 'btn-ghost text-base-content/60 hover:text-primary hover:bg-primary/10'}"
                                onclick={() => applyPreset(preset)}
                            >
                                {preset.label}
                            </button>
                        {/each}
                    </div>

                    <div class="month-range-slider px-2">
                        <RangeSlider
                            range
                            pushy
                            float
                            min={0}
                            max={NO_LIMIT_IDX}
                            step={1}
                            bind:values={sliderValues}
                            formatter={sliderLabel}
                            ariaLabels={['시작월', '종료월']}
                        />
                    </div>
                </div>
            </div>
        {/if}
    </form>
</div>
