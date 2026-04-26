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

<div class="arena-filter">
    <form onsubmit={handleSubmit}>
        <header class="filter-head">
            <div class="filter-kicker">FILTER · 검색</div>
            <h1 class="filter-title">
                {title}
                <span class="filter-count">총 {totalCount.toLocaleString()}개</span>
            </h1>
        </header>

        <div class="filter-search">
            <input
                type="text"
                bind:value={name}
                placeholder="대회명 검색..."
                class="filter-input"
            />
            <button type="submit" class="filter-submit">검색 →</button>
        </div>

        <div class="filter-quick">
            <span class="filter-label">상태</span>
            <div class="filter-chips">
                {#each statuses as status}
                    <button
                        type="button"
                        class="filter-chip"
                        class:active={statusValues.includes(status.value)}
                        onclick={() => toggleStatus(status.value)}
                    >
                        {status.label}
                    </button>
                {/each}
            </div>
            <button
                type="button"
                class="filter-toggle"
                class:active={isExpanded}
                aria-expanded={isExpanded}
                onclick={() => isExpanded = !isExpanded}
            >
                <span>상세 필터</span>
                {#if totalSelected > 0}
                    <span class="filter-toggle-badge">{totalSelected}</span>
                {/if}
                <span class="filter-toggle-arrow">{isExpanded ? '−' : '+'}</span>
            </button>
        </div>

        {#if totalSelected > 0}
            <div class="filter-active">
                {#each sportValues as sport}
                    <button type="button" class="active-chip" onclick={() => toggleSport(sport)} aria-label="{getSportLabel(sport)} 필터 제거">
                        <span>{getSportLabel(sport)}</span><span class="x">×</span>
                    </button>
                {/each}
                {#each regionValues as region}
                    <button type="button" class="active-chip" onclick={() => toggleRegion(region)} aria-label="{region} 필터 제거">
                        <span>{region}</span><span class="x">×</span>
                    </button>
                {/each}
                {#each distanceCategoryValues as dc}
                    <button type="button" class="active-chip" onclick={() => toggleDistanceCategory(dc)} aria-label="{getDistanceCategoryLabel(dc)} 필터 제거">
                        <span>{getDistanceCategoryLabel(dc)}</span><span class="x">×</span>
                    </button>
                {/each}
                {#if hasMonthFilter}
                    <button type="button" class="active-chip" onclick={clearMonthFilter} aria-label="개최월 필터 제거">
                        <span>{getMonthRangeLabel()}</span><span class="x">×</span>
                    </button>
                {/if}
                <button type="button" class="filter-clear" onclick={handleReset}>모두 지우기 ↺</button>
            </div>
        {/if}

        {#if isExpanded}
            <div class="filter-expanded" transition:slide={{ duration: 200 }}>
                <div class="filter-group">
                    <div class="filter-label">종목</div>
                    <div class="filter-chips">
                        {#each sports as sport}
                            <button type="button" class="filter-chip" class:active={sportValues.includes(sport.value)} onclick={() => toggleSport(sport.value)}>
                                {sport.label}
                            </button>
                        {/each}
                    </div>
                </div>

                <div class="filter-group">
                    <div class="filter-label">지역</div>
                    <div class="filter-chips">
                        {#each regions as region}
                            <button type="button" class="filter-chip" class:active={regionValues.includes(region)} onclick={() => toggleRegion(region)}>
                                {region}
                            </button>
                        {/each}
                    </div>
                </div>

                {#if availableDistanceCategories.length > 0}
                    <div class="filter-group">
                        <div class="filter-label">거리</div>
                        <div class="filter-chips">
                            {#each availableDistanceCategories as cat}
                                <button type="button" class="filter-chip" class:active={distanceCategoryValues.includes(cat.value)} onclick={() => toggleDistanceCategory(cat.value)}>
                                    {cat.label}
                                </button>
                            {/each}
                        </div>
                    </div>
                {/if}

                <div class="filter-group filter-group-month">
                    <div class="filter-group-head">
                        <div class="filter-label">개최월</div>
                        <div class="filter-range">{getMonthRangeLabel() || '—'}</div>
                    </div>
                    <div class="filter-chips">
                        {#each presets as preset}
                            <button
                                type="button"
                                class="filter-chip"
                                class:active={activePreset === preset.label}
                                onclick={() => applyPreset(preset)}
                            >
                                {preset.label}
                            </button>
                        {/each}
                    </div>
                    <div class="month-range-slider">
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

<style>
    .arena-filter {
        background: var(--arena-paper);
        border: 1px solid var(--arena-line);
        margin-bottom: 24px;
        font-family: var(--arena-f-body);
        color: var(--arena-ink);
    }

    /* ── Head ─────────────────────────── */
    .filter-head {
        padding: 18px 22px 14px;
        border-bottom: 1px solid var(--arena-line-soft);
    }
    .filter-kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .filter-title {
        font-family: var(--arena-f-display);
        font-size: clamp(22px, 3vw, 30px);
        font-weight: 700;
        letter-spacing: -0.5px;
        margin: 0;
        color: var(--arena-ink);
        display: flex;
        align-items: baseline;
        gap: 12px;
        flex-wrap: wrap;
    }
    .filter-count {
        font-family: var(--arena-f-mono);
        font-size: 12px;
        font-weight: 400;
        letter-spacing: 1px;
        color: var(--arena-ink-soft);
    }

    /* ── Search ─────────────────────────── */
    .filter-search {
        display: flex;
        gap: 0;
        padding: 14px 22px;
        border-bottom: 1px solid var(--arena-line-soft);
    }
    .filter-input {
        flex: 1;
        min-width: 0;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
        padding: 10px 14px;
        font-family: var(--arena-f-body);
        font-size: 14px;
        color: var(--arena-ink);
        border-right: none;
    }
    .filter-input:focus {
        outline: none;
        border-color: var(--arena-ink);
        background: var(--arena-paper-alt);
    }
    .filter-input::placeholder {
        color: var(--arena-ink-mute);
    }
    .filter-submit {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border: 1px solid var(--arena-ink);
        padding: 10px 18px;
        font-family: var(--arena-f-mono);
        font-size: 12px;
        letter-spacing: 1px;
        cursor: pointer;
        text-transform: uppercase;
        white-space: nowrap;
    }
    .filter-submit:hover {
        background: var(--arena-ink-soft);
    }

    /* ── Quick row ─────────────────────────── */
    .filter-quick {
        padding: 12px 22px;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 10px 12px;
    }
    .filter-label {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
    }
    .filter-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }
    .filter-quick > .filter-chips {
        flex: 1;
        min-width: 0;
    }
    .filter-chip {
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
        color: var(--arena-ink);
        padding: 6px 12px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.5px;
        cursor: pointer;
        transition: background 0.1s, border-color 0.1s;
        line-height: 1.4;
    }
    .filter-chip:hover {
        border-color: var(--arena-ink);
    }
    .filter-chip.active {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border-color: var(--arena-ink);
    }
    .filter-toggle {
        margin-left: auto;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper-alt);
        color: var(--arena-ink);
        padding: 6px 12px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.5px;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        line-height: 1.4;
    }
    .filter-toggle:hover {
        border-color: var(--arena-ink);
    }
    .filter-toggle.active {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border-color: var(--arena-ink);
    }
    .filter-toggle-arrow {
        font-family: var(--arena-f-mono);
        font-size: 14px;
        line-height: 1;
        opacity: 0.7;
    }
    .filter-toggle-badge {
        background: var(--arena-accent);
        color: var(--arena-ink);
        padding: 0 6px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0;
        line-height: 16px;
        min-width: 16px;
        text-align: center;
    }
    .filter-toggle.active .filter-toggle-badge {
        background: var(--arena-accent);
    }

    /* ── Active filters ─────────────────────────── */
    .filter-active {
        padding: 12px 22px;
        border-top: 1px solid var(--arena-line-soft);
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: center;
    }
    .active-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border: 1px solid var(--arena-ink);
        background: var(--arena-ink);
        color: var(--arena-paper);
        padding: 4px 6px 4px 10px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.5px;
        cursor: pointer;
        line-height: 1.4;
    }
    .active-chip:hover {
        background: var(--arena-ink-soft);
        border-color: var(--arena-ink-soft);
    }
    .active-chip .x {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 14px;
        height: 14px;
        font-size: 14px;
        line-height: 1;
        opacity: 0.7;
        /* Nudge × up to compensate for IBM Plex Mono ×'s low visual center */
        transform: translateY(-1px);
    }
    .active-chip:hover .x {
        opacity: 1;
    }
    .filter-clear {
        margin-left: auto;
        background: transparent;
        border: none;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1px;
        color: var(--arena-ink-soft);
        cursor: pointer;
        text-transform: uppercase;
        padding: 4px 0;
    }
    .filter-clear:hover {
        color: var(--arena-urgent);
    }

    /* ── Expanded ─────────────────────────── */
    .filter-expanded {
        padding: 18px 22px 22px;
        border-top: 1px solid var(--arena-line-soft);
        display: flex;
        flex-direction: column;
        gap: 18px;
    }
    .filter-group {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .filter-group-head {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
    }
    .filter-range {
        font-family: var(--arena-f-mono);
        font-size: 12px;
        color: var(--arena-ink);
        letter-spacing: 0.5px;
    }
    .filter-group-month {
        background: var(--arena-paper-alt);
        border: 1px solid var(--arena-line-soft);
        padding: 14px 16px 22px;
    }
    .month-range-slider {
        margin-top: 14px;
        padding: 0 12px;
    }
    /* slider visual overrides live in app.css (.month-range-slider scope) */

    /* ── Mobile ─────────────────────────── */
    @media (max-width: 640px) {
        .filter-head,
        .filter-search,
        .filter-quick,
        .filter-active,
        .filter-expanded {
            padding-left: 16px;
            padding-right: 16px;
        }
        .filter-toggle {
            margin-left: 0;
        }
        .filter-clear {
            margin-left: 0;
        }
    }
</style>
