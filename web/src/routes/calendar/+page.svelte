<script lang="ts">
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';
    import type { Race, SportOption } from '$lib/types';
    import { track } from '$lib/analytics';
    import { arenaSportShort } from '$lib/arena';
    import RaceRow from '$lib/components/arena/RaceRow.svelte';

    let { data } = $props();

    onMount(() => {
        track('calendar_view', { year: data.year as number, month: data.month as number });
    });

    const year = $derived(data.year as number);
    const month = $derived(data.month as number);
    const startOfMonth = $derived(data.startOfMonth as string);
    const racesGrouped = $derived(data.racesGrouped as Record<string, Race[]>);
    const previousMonth = $derived(data.previousMonth);
    const nextMonth = $derived(data.nextMonth);
    const sport = $derived((Array.isArray(data.sport) ? data.sport : data.sport ? [data.sport] : []) as string[]);
    const sports = $derived(data.sports as SportOption[]);
    const region = $derived(
        (Array.isArray(data.region) ? data.region : data.region ? [data.region] : []) as string[],
    );
    const regions = $derived(((data as { regions?: string[] }).regions ?? []) as string[]);

    type StatusType = 'registration_open' | 'registration_closed' | 'upcoming' | 'finished';

    const statusOptions: { key: StatusType; label: string }[] = [
        { key: 'registration_open', label: '접수중' },
        { key: 'upcoming', label: '예정' },
        { key: 'registration_closed', label: '접수마감' },
        { key: 'finished', label: '종료' },
    ];

    let selectedStatuses = $state<Set<StatusType>>(
        new Set(['registration_open', 'registration_closed', 'upcoming', 'finished']),
    );

    function toggleStatus(status: StatusType) {
        if (selectedStatuses.has(status)) selectedStatuses.delete(status);
        else selectedStatuses.add(status);
        selectedStatuses = new Set(selectedStatuses);
    }

    const dayNames = ['일', '월', '화', '수', '목', '금', '토'];

    const startDate = $derived(new Date(startOfMonth));
    const firstDayOfMonth = $derived(startDate.getDay());
    const daysInMonth = $derived(new Date(year, month, 0).getDate());
    const today = $derived(new Date().toISOString().split('T')[0]);
    const filteredRaces = $derived(
        Object.values(racesGrouped).flat().filter((r) => selectedStatuses.has(r.status as StatusType)),
    );
    const totalRacesThisMonth = $derived(filteredRaces.length);
    const sortedMonthRaces = $derived(
        [...filteredRaces].sort((a, b) => (a.raceDate || '').localeCompare(b.raceDate || '')),
    );

    function getDateString(day: number): string {
        return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    }

    function getDayRaces(day: number): Race[] {
        const dateStr = getDateString(day);
        const races = racesGrouped[dateStr] || [];
        return races.filter((race) => selectedStatuses.has(race.status as StatusType));
    }

    function buildFilterUrl(nextSport: string[], nextRegion: string[]): string {
        const params = new URLSearchParams();
        params.set('year', String(year));
        params.set('month', String(month));
        for (const s of nextSport) params.append('sport', s);
        for (const r of nextRegion) params.append('region', r);
        return `/calendar?${params.toString()}`;
    }

    function toggleArrayValue(arr: string[], value: string): string[] {
        return arr.includes(value) ? arr.filter((v) => v !== value) : [...arr, value];
    }

    function toggleSportFilter(value: string) {
        goto(buildFilterUrl(toggleArrayValue(sport, value), region), { replaceState: true, keepFocus: true });
    }

    function clearSportFilter() {
        goto(buildFilterUrl([], region), { replaceState: true, keepFocus: true });
    }

    function toggleRegionFilter(value: string) {
        goto(buildFilterUrl(sport, toggleArrayValue(region, value)), { replaceState: true, keepFocus: true });
    }

    function clearRegionFilter() {
        goto(buildFilterUrl(sport, []), { replaceState: true, keepFocus: true });
    }

    function buildNavQuery(targetYear: number, targetMonth: number): string {
        const params = new URLSearchParams();
        params.set('year', String(targetYear));
        params.set('month', String(targetMonth));
        for (const s of sport) params.append('sport', s);
        for (const r of region) params.append('region', r);
        return params.toString();
    }

    const todayDate = new Date();
    const currentMonth = todayDate.getMonth() + 1;
    const currentYear = todayDate.getFullYear();
    const todayHref = $derived(() => {
        const params = new URLSearchParams();
        for (const s of sport) params.append('sport', s);
        for (const r of region) params.append('region', r);
        const qs = params.toString();
        return qs ? `/calendar?${qs}` : '/calendar';
    });

    let dayModalOpen = $state(false);
    let dayModalTitle = $state('');
    let dayModalRaces = $state<Race[]>([]);

    function openDayModal(title: string, races: Race[]) {
        if (races.length === 0) return;
        dayModalTitle = title;
        dayModalRaces = races;
        dayModalOpen = true;
    }

    function closeDayModal() {
        dayModalOpen = false;
    }

    type FilterSheet = 'sport' | 'region' | 'status' | null;
    let openSheet = $state<FilterSheet>(null);

    function openFilterSheet(type: Exclude<FilterSheet, null>) {
        openSheet = type;
    }
    function closeFilterSheet() {
        openSheet = null;
    }

    function summaryLabel(values: string[], lookup: (v: string) => string): string {
        if (values.length === 0) return '전체';
        if (values.length === 1) return lookup(values[0]);
        return `${values.length}개`;
    }
    const sportLabel = $derived(
        summaryLabel(sport, (v) => sports.find((s) => s.value === v)?.label ?? v),
    );
    const regionLabel = $derived(summaryLabel(region, (v) => v));
    const statusLabel = $derived(
        selectedStatuses.size === statusOptions.length
            ? '전체'
            : selectedStatuses.size === 0
              ? '없음'
              : `${selectedStatuses.size}개`,
    );
    const sheetTitle = $derived(
        openSheet === 'sport' ? '종목' : openSheet === 'region' ? '지역' : openSheet === 'status' ? '상태' : '',
    );
</script>

<svelte:head>
    <title>{year}년 {month}월 대회 캘린더 - 엔듀로허브</title>
    <meta name="description" content="{year}년 {month}월 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정" />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="{year}년 {month}월 대회 캘린더 - 엔듀로허브" />
    <meta property="og:description" content="{year}년 {month}월 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정" />
    <meta property="og:image" content="{data.appUrl}/images/og-image.png" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta name="twitter:image" content="{data.appUrl}/images/og-image.png" />
</svelte:head>

<div class="cal-wrap">
    <header class="cal-head">
        <div class="head-left">
            <div class="arena-kicker">엔듀로허브 · 캘린더</div>
            <h1 class="head-title">
                {year}<span class="head-sep">·</span><span class="head-month">{String(month).padStart(2, '0')}</span>
            </h1>
            <div class="head-meta mono">대회 {totalRacesThisMonth}개</div>
        </div>

        <nav class="month-nav" aria-label="월 이동">
            <a
                class="nav-btn"
                href="/calendar?{buildNavQuery(previousMonth.year, previousMonth.month)}"
                aria-label="이전 달"
            >← {previousMonth.month}월</a>
            <a
                class="nav-btn nav-today"
                class:active={year === currentYear && month === currentMonth}
                href={todayHref()}
            >{currentMonth}월</a>
            <a
                class="nav-btn"
                href="/calendar?{buildNavQuery(nextMonth.year, nextMonth.month)}"
                aria-label="다음 달"
            >{nextMonth.month}월 →</a>
        </nav>
    </header>

    <div class="cal-filter-mobile">
        <button
            type="button"
            class="filter-trigger"
            class:active={sport.length > 0}
            onclick={() => openFilterSheet('sport')}
            aria-haspopup="dialog"
        >
            <span class="trigger-label arena-kicker">종목</span>
            <span class="trigger-value">
                <span class="trigger-text">{sportLabel}</span>
                <span class="trigger-arrow mono">▾</span>
            </span>
        </button>
        <button
            type="button"
            class="filter-trigger"
            class:active={region.length > 0}
            onclick={() => openFilterSheet('region')}
            aria-haspopup="dialog"
            disabled={regions.length === 0}
        >
            <span class="trigger-label arena-kicker">지역</span>
            <span class="trigger-value">
                <span class="trigger-text">{regionLabel}</span>
                <span class="trigger-arrow mono">▾</span>
            </span>
        </button>
        <button
            type="button"
            class="filter-trigger"
            class:active={selectedStatuses.size > 0 && selectedStatuses.size < statusOptions.length}
            onclick={() => openFilterSheet('status')}
            aria-haspopup="dialog"
        >
            <span class="trigger-label arena-kicker">상태</span>
            <span class="trigger-value">
                <span class="trigger-text">{statusLabel}</span>
                <span class="trigger-arrow mono">▾</span>
            </span>
        </button>
    </div>

    <div class="cal-toolbar">
        <div class="toolbar-row">
            <span class="arena-kicker toolbar-label">종목</span>
            <div class="pill-group">
                <button class="pill" class:active={sport.length === 0} onclick={clearSportFilter}>전체</button>
                {#each sports as s}
                    <button
                        class="pill sport-{s.value}"
                        class:active={sport.includes(s.value)}
                        onclick={() => toggleSportFilter(s.value)}
                    >
                        <span class="pill-dot"></span>
                        {s.label}
                    </button>
                {/each}
            </div>
        </div>
        {#if regions.length > 0}
            <div class="toolbar-row">
                <span class="arena-kicker toolbar-label">지역</span>
                <div class="pill-group">
                    <button class="pill" class:active={region.length === 0} onclick={clearRegionFilter}>전체</button>
                    {#each regions as r}
                        <button
                            class="pill"
                            class:active={region.includes(r)}
                            onclick={() => toggleRegionFilter(r)}
                        >
                            {r}
                        </button>
                    {/each}
                </div>
            </div>
        {/if}
        <div class="toolbar-row">
            <span class="arena-kicker toolbar-label">상태</span>
            <div class="pill-group">
                {#each statusOptions as status}
                    <button
                        class="pill check"
                        class:active={selectedStatuses.has(status.key)}
                        onclick={() => toggleStatus(status.key)}
                        aria-pressed={selectedStatuses.has(status.key)}
                    >
                        {status.label}
                        <span class="pill-check mono">{selectedStatuses.has(status.key) ? '×' : '+'}</span>
                    </button>
                {/each}
            </div>
        </div>
    </div>

    <section class="cal-frame">
        <div class="cal-dow">
            {#each dayNames as dayName, index}
                <div class="dow-cell" class:sun={index === 0} class:sat={index === 6}>
                    {dayName}
                </div>
            {/each}
        </div>

        <div class="cal-cells">
            {#each Array(firstDayOfMonth) as _}
                <div class="cal-cell empty"></div>
            {/each}

            {#each Array(daysInMonth) as _, i}
                {@const day = i + 1}
                {@const dateStr = getDateString(day)}
                {@const dayRaces = getDayRaces(day)}
                {@const isToday = dateStr === today}
                {@const dayOfWeek = (firstDayOfMonth + i) % 7}
                {@const hasRaces = dayRaces.length > 0}
                {@const visible = dayRaces.slice(0, 2)}
                {@const overflow = dayRaces.length - visible.length}

                <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
                <div
                    class="cal-cell"
                    class:today={isToday}
                    class:clickable={hasRaces}
                    onclick={() => hasRaces && openDayModal(`${month}월 ${day}일`, dayRaces)}
                    onkeydown={(e) => {
                        if (hasRaces && (e.key === 'Enter' || e.key === ' ')) {
                            e.preventDefault();
                            openDayModal(`${month}월 ${day}일`, dayRaces);
                        }
                    }}
                    tabindex={hasRaces ? 0 : undefined}
                    role={hasRaces ? 'button' : undefined}
                    aria-label={hasRaces ? `${month}월 ${day}일 대회 ${dayRaces.length}개 보기` : undefined}
                >
                    <div class="cell-head">
                        <span class="day-num mono" class:sun={dayOfWeek === 0 && !isToday} class:sat={dayOfWeek === 6 && !isToday}>
                            {String(day).padStart(2, '0')}
                        </span>
                        {#if overflow > 0}
                            <span class="overflow mono">+{overflow}</span>
                        {/if}
                    </div>

                    <div class="cell-body">
                        {#each visible as race}
                            <a
                                class="race-chip sport-{race.sport}"
                                href={race.url}
                                title="{race.title}"
                                onclick={(e) => e.stopPropagation()}
                            >
                                <span class="race-name">{race.title}</span>
                            </a>
                        {/each}
                    </div>
                </div>
            {/each}
        </div>
    </section>

    {#if sortedMonthRaces.length > 0}
        <section class="month-list">
            <div class="list-head">
                <span class="arena-kicker">{month}월 일정</span>
                <span class="list-count mono">{sortedMonthRaces.length}개</span>
            </div>

            <div class="race-table">
                <div class="race-thead">
                    <span>접수마감</span>
                    <span>대회명</span>
                    <span>일정</span>
                    <span>종목</span>
                    <span>거리</span>
                    <span>지역</span>
                    <span>참가비</span>
                </div>
                {#each sortedMonthRaces as race (race.id)}
                    <RaceRow {race} />
                {/each}
            </div>
        </section>
    {/if}
</div>

{#if openSheet}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
        class="sheet-overlay"
        role="dialog"
        aria-modal="true"
        aria-label="{sheetTitle} 필터"
        tabindex="-1"
        onclick={closeFilterSheet}
    >
        <div class="sheet-box" onclick={(e) => e.stopPropagation()}>
            <div class="sheet-grabber" aria-hidden="true"></div>
            <div class="sheet-head">
                <h3 class="sheet-title">{sheetTitle}</h3>
                <button class="sheet-close mono" onclick={closeFilterSheet} aria-label="닫기">✕</button>
            </div>
            <div class="sheet-body">
                {#if openSheet === 'sport'}
                    <div class="sheet-pill-group">
                        <button
                            class="pill"
                            class:active={sport.length === 0}
                            onclick={clearSportFilter}
                        >전체</button>
                        {#each sports as s}
                            <button
                                class="pill sport-{s.value}"
                                class:active={sport.includes(s.value)}
                                onclick={() => toggleSportFilter(s.value)}
                                aria-pressed={sport.includes(s.value)}
                            >
                                <span class="pill-dot"></span>
                                {s.label}
                            </button>
                        {/each}
                    </div>
                {:else if openSheet === 'region'}
                    <div class="sheet-pill-group">
                        <button
                            class="pill"
                            class:active={region.length === 0}
                            onclick={clearRegionFilter}
                        >전체</button>
                        {#each regions as r}
                            <button
                                class="pill"
                                class:active={region.includes(r)}
                                onclick={() => toggleRegionFilter(r)}
                                aria-pressed={region.includes(r)}
                            >{r}</button>
                        {/each}
                    </div>
                {:else if openSheet === 'status'}
                    <div class="sheet-pill-group">
                        {#each statusOptions as status}
                            <button
                                class="pill check"
                                class:active={selectedStatuses.has(status.key)}
                                onclick={() => toggleStatus(status.key)}
                                aria-pressed={selectedStatuses.has(status.key)}
                            >
                                {status.label}
                                <span class="pill-check mono">{selectedStatuses.has(status.key) ? '×' : '+'}</span>
                            </button>
                        {/each}
                    </div>
                {/if}
            </div>
            <div class="sheet-foot">
                <button class="sheet-apply" onclick={closeFilterSheet}>적용</button>
            </div>
        </div>
    </div>
{/if}

{#if dayModalOpen}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
        class="cal-modal-overlay"
        role="dialog"
        aria-modal="true"
        aria-label={dayModalTitle}
        tabindex="-1"
        onclick={closeDayModal}
    >
        <div class="cal-modal-box" onclick={(e) => e.stopPropagation()}>
            <div class="cal-modal-head">
                <span class="arena-kicker">{year}.{String(month).padStart(2, '0')}</span>
                <h3 class="cal-modal-title">{dayModalTitle}</h3>
                <button class="cal-modal-close mono" onclick={closeDayModal} aria-label="닫기">✕</button>
            </div>
            <ul class="cal-modal-list">
                {#each dayModalRaces as race}
                    <li>
                        <a class="cal-modal-row sport-{race.sport}" href={race.url}>
                            <span class="cal-modal-bar"></span>
                            <div class="cal-modal-text">
                                <div class="cal-modal-row-title">{race.title}</div>
                                <div class="cal-modal-row-meta mono">
                                    <span class="sport-text-{race.sport}">{arenaSportShort[race.sport]}</span>
                                    {#if race.location}<span class="dot-sep">·</span><span>{race.location}</span>{/if}
                                </div>
                            </div>
                            <span class="mono cal-modal-arrow">→</span>
                        </a>
                    </li>
                {/each}
            </ul>
        </div>
    </div>
{/if}

<style>
    .cal-wrap {
        max-width: 1400px;
        margin: 0 auto;
        padding: 24px 16px 40px;
        color: var(--arena-ink);
    }
    @media (min-width: 1024px) {
        .cal-wrap {
            padding: 36px 32px 60px;
        }
    }
    .mono {
        font-family: var(--arena-f-mono);
    }

    /* ── Header ─────────────────────────── */
    .cal-head {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 16px;
        flex-wrap: wrap;
        margin-bottom: 20px;
    }
    .head-title {
        font-family: var(--arena-f-display);
        font-size: 44px;
        font-weight: 700;
        letter-spacing: -1.5px;
        line-height: 1;
        margin: 6px 0 6px;
        display: inline-flex;
        align-items: baseline;
        gap: 8px;
    }
    @media (min-width: 720px) {
        .head-title {
            font-size: 56px;
            letter-spacing: -2px;
        }
    }
    .head-sep {
        color: var(--arena-ink-mute);
        font-weight: 400;
    }
    .head-month {
        color: var(--arena-accent-deep);
    }
    .head-meta {
        font-size: 11px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
    }

    .month-nav {
        display: inline-flex;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
    }
    .nav-btn {
        padding: 9px 14px;
        font-family: var(--arena-f-mono);
        font-size: 12px;
        letter-spacing: 0.5px;
        color: var(--arena-ink);
        border-right: 1px solid var(--arena-line-soft);
        text-decoration: none;
        white-space: nowrap;
    }
    .nav-btn:last-child {
        border-right: none;
    }
    .nav-btn:hover {
        background: var(--arena-paper-alt);
    }
    .nav-today {
        background: var(--arena-ink);
        color: var(--arena-paper);
        letter-spacing: 1.5px;
        font-weight: 600;
    }
    .nav-today:hover {
        background: var(--arena-ink);
        color: var(--arena-accent);
    }

    /* ── Mobile filter trigger row ─────────────────────────── */
    .cal-filter-mobile {
        display: none;
    }
    @media (max-width: 640px) {
        .cal-filter-mobile {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            border: 1px solid var(--arena-line);
            background: var(--arena-paper);
            margin-bottom: 12px;
        }
        .cal-toolbar {
            display: none;
        }
    }
    .filter-trigger {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;
        padding: 10px 12px;
        background: var(--arena-paper);
        border: none;
        border-right: 1px solid var(--arena-line-soft);
        cursor: pointer;
        text-align: left;
        min-width: 0;
        font-family: var(--arena-f-body);
    }
    .filter-trigger:last-child {
        border-right: none;
    }
    .filter-trigger:hover {
        background: var(--arena-paper-alt);
    }
    .filter-trigger:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
    .filter-trigger .trigger-label {
        font-size: 10px;
    }
    .filter-trigger .trigger-value {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 13px;
        font-weight: 600;
        color: var(--arena-ink);
        max-width: 100%;
    }
    .filter-trigger .trigger-text {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        min-width: 0;
    }
    .filter-trigger .trigger-arrow {
        font-size: 10px;
        color: var(--arena-ink-soft);
        flex-shrink: 0;
    }
    .filter-trigger.active .trigger-value {
        color: var(--arena-accent-deep);
    }

    /* ── Toolbar ─────────────────────────── */
    .cal-toolbar {
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
        margin-bottom: 16px;
    }
    .toolbar-row {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 14px;
        border-bottom: 1px solid var(--arena-line-soft);
        flex-wrap: wrap;
    }
    .toolbar-row:last-child {
        border-bottom: none;
    }
    .toolbar-label {
        min-width: 56px;
    }
    .pill-group {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }
    .pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 10px;
        border: 1px solid var(--arena-line-soft);
        background: var(--arena-paper);
        font-family: var(--arena-f-body);
        font-size: 12px;
        color: var(--arena-ink);
        cursor: pointer;
        line-height: 1.4;
    }
    .pill:hover {
        border-color: var(--arena-line);
        background: var(--arena-paper-alt);
    }
    .pill.active {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border-color: var(--arena-ink);
    }
    .pill-dot {
        display: inline-block;
        width: 7px;
        height: 7px;
    }
    .pill-check {
        font-size: 11px;
        line-height: 1;
        opacity: 0.6;
    }
    .pill.check.active .pill-check {
        opacity: 1;
    }

    /* ── Calendar frame ─────────────────────────── */
    .cal-frame {
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
    }
    .cal-dow {
        display: grid;
        grid-template-columns: repeat(7, minmax(0, 1fr));
        border-bottom: 1px solid var(--arena-line);
        background: var(--arena-paper-alt);
    }
    .dow-cell {
        padding: 8px 10px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        border-right: 1px solid var(--arena-line-soft);
        text-align: center;
    }
    .dow-cell:last-child {
        border-right: none;
    }
    .dow-cell.sun {
        color: var(--arena-urgent);
    }
    .dow-cell.sat {
        color: oklch(50% 0.14 220);
    }

    .cal-cells {
        display: grid;
        grid-template-columns: repeat(7, minmax(0, 1fr));
    }
    .cal-cell {
        min-height: 96px;
        min-width: 0;
        padding: 0;
        border-right: 1px solid var(--arena-line-soft);
        border-bottom: 1px solid var(--arena-line-soft);
        background: var(--arena-paper);
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    @media (min-width: 720px) {
        .cal-cell {
            min-height: 120px;
        }
    }
    .cal-cell:nth-child(7n) {
        border-right: none;
    }
    .cal-cell.empty {
        background: var(--arena-paper-alt);
    }
    .cal-cell.clickable {
        cursor: pointer;
    }
    .cal-cell.clickable:hover {
        background: var(--arena-paper-alt);
    }
    .cal-cell.today {
        outline: 1.5px solid var(--arena-accent-deep);
        outline-offset: -1.5px;
        background: oklch(96% 0.04 145);
        position: relative;
    }
    .cell-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 4px;
        min-height: 18px;
        padding: 5px 5px 0;
    }
    @media (min-width: 720px) {
        .cell-head {
            padding: 6px 6px 0;
        }
    }
    .day-num {
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.3px;
        color: var(--arena-ink);
    }
    .day-num.sun {
        color: var(--arena-urgent);
    }
    .day-num.sat {
        color: oklch(50% 0.14 220);
    }
    .today .day-num {
        background: var(--arena-ink);
        color: var(--arena-paper);
        padding: 1px 5px;
    }
    .overflow {
        font-size: 10px;
        font-weight: 600;
        color: var(--arena-ink-soft);
        background: var(--arena-paper);
        padding: 0 3px;
        text-align: center;
        border: 1px solid var(--arena-line-soft);
        flex-shrink: 0;
    }

    .cell-body {
        display: flex;
        flex-direction: column;
        gap: 2px;
        flex: 1;
        min-height: 0;
        overflow: hidden;
    }
    .race-chip {
        display: block;
        padding: 0;
        font-family: var(--arena-f-body);
        font-size: 11px;
        line-height: 1.3;
        background: var(--arena-paper);
        color: var(--arena-ink);
        text-decoration: none;
        border: 1px solid var(--arena-line-soft);
        overflow: hidden;
    }
    .race-chip:hover {
        background: var(--arena-paper-alt);
    }
    .race-name {
        display: block;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    @media (max-width: 640px) {
        .race-name {
            font-size: 10px;
        }
    }

    /* Sport color mapping (matches RaceRow) */
    .sport-running .pill-dot {
        background: oklch(48% 0.18 280);
    }
    .sport-swimming .pill-dot {
        background: oklch(50% 0.14 220);
    }
    .sport-cycling .pill-dot {
        background: oklch(55% 0.16 60);
    }
    .sport-triathlon .pill-dot {
        background: oklch(48% 0.18 320);
    }
    .sport-trail_running .pill-dot {
        background: oklch(42% 0.14 145);
    }
    .race-chip.sport-running { border-color: oklch(48% 0.18 280); }
    .race-chip.sport-swimming { border-color: oklch(50% 0.14 220); }
    .race-chip.sport-cycling { border-color: oklch(55% 0.16 60); }
    .race-chip.sport-triathlon { border-color: oklch(48% 0.18 320); }
    .race-chip.sport-trail_running { border-color: oklch(42% 0.14 145); }
    .pill.active .pill-dot {
        outline: 1px solid var(--arena-paper);
        outline-offset: 1px;
    }
    .sport-text-running { color: oklch(48% 0.18 280); }
    .sport-text-swimming { color: oklch(50% 0.14 220); }
    .sport-text-cycling { color: oklch(55% 0.16 60); }
    .sport-text-triathlon { color: oklch(48% 0.18 320); }
    .sport-text-trail_running { color: oklch(42% 0.14 145); }

    /* ── Month list ─────────────────────────── */
    .month-list {
        margin-top: 32px;
    }
    .list-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 8px;
        margin-bottom: 12px;
        border-bottom: 1px solid var(--arena-line-soft);
    }
    .list-count {
        font-size: 11px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
    }
    .race-table {
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
    }
    .race-thead {
        display: grid;
        grid-template-columns: 56px 1fr 90px 60px 100px 110px 90px;
        gap: 16px;
        padding: 10px 20px;
        background: var(--arena-paper-alt);
        border-bottom: 1px solid var(--arena-line);
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.3px;
        color: var(--arena-ink-soft);
    }
    @media (max-width: 879px) {
        .race-thead {
            display: none;
        }
    }

    /* ── Modal ─────────────────────────── */
    .cal-modal-overlay {
        position: fixed;
        inset: 0;
        z-index: 9999;
        background: rgba(0, 0, 0, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 16px;
        cursor: pointer;
    }
    .cal-modal-box {
        background: var(--arena-paper);
        border: 1px solid var(--arena-ink);
        box-shadow: 6px 6px 0 var(--arena-ink);
        max-width: 460px;
        width: 100%;
        max-height: 80vh;
        overflow: auto;
        cursor: default;
    }
    .cal-modal-head {
        padding: 14px 18px;
        border-bottom: 1px solid var(--arena-line);
        background: var(--arena-paper-alt);
        position: relative;
    }
    .cal-modal-title {
        font-family: var(--arena-f-display);
        font-size: 22px;
        font-weight: 700;
        letter-spacing: -0.6px;
        margin: 4px 0 0;
    }
    .cal-modal-close {
        position: absolute;
        top: 12px;
        right: 14px;
        background: transparent;
        border: 1px solid var(--arena-line);
        padding: 3px 8px;
        font-size: 12px;
        cursor: pointer;
        color: var(--arena-ink);
        line-height: 1;
    }
    .cal-modal-close:hover {
        background: var(--arena-ink);
        color: var(--arena-paper);
    }
    .cal-modal-list {
        list-style: none;
        margin: 0;
        padding: 0;
    }
    .cal-modal-row {
        display: grid;
        grid-template-columns: 4px 1fr auto;
        align-items: center;
        gap: 12px;
        padding: 12px 18px;
        text-decoration: none;
        color: var(--arena-ink);
        border-bottom: 1px solid var(--arena-line-soft);
    }
    .cal-modal-row:hover {
        background: var(--arena-paper-alt);
    }
    .cal-modal-list li:last-child .cal-modal-row {
        border-bottom: none;
    }
    .cal-modal-bar {
        align-self: stretch;
    }
    .sport-running.cal-modal-row > .cal-modal-bar { background: oklch(48% 0.18 280); }
    .sport-swimming.cal-modal-row > .cal-modal-bar { background: oklch(50% 0.14 220); }
    .sport-cycling.cal-modal-row > .cal-modal-bar { background: oklch(55% 0.16 60); }
    .sport-triathlon.cal-modal-row > .cal-modal-bar { background: oklch(48% 0.18 320); }
    .sport-trail_running.cal-modal-row > .cal-modal-bar { background: oklch(42% 0.14 145); }
    .cal-modal-row-title {
        font-weight: 600;
        font-size: 14px;
    }
    .cal-modal-row-meta {
        margin-top: 2px;
        font-size: 11px;
        color: var(--arena-ink-soft);
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: center;
    }
    .dot-sep {
        color: var(--arena-line);
    }
    .cal-modal-arrow {
        font-size: 14px;
        color: var(--arena-ink-soft);
    }

    /* ── Bottom sheet (mobile filter) ─────────────────────────── */
    .sheet-overlay {
        position: fixed;
        inset: 0;
        z-index: 9999;
        background: rgba(0, 0, 0, 0.4);
        display: flex;
        align-items: flex-end;
        justify-content: center;
        cursor: pointer;
        animation: sheet-fade 180ms ease-out;
    }
    .sheet-box {
        width: 100%;
        max-width: 540px;
        max-height: 82vh;
        display: flex;
        flex-direction: column;
        background: var(--arena-paper);
        border-top: 1px solid var(--arena-ink);
        box-shadow: 0 -6px 0 var(--arena-ink);
        cursor: default;
        animation: sheet-up 220ms cubic-bezier(0.16, 1, 0.3, 1);
    }
    @keyframes sheet-up {
        from { transform: translateY(100%); }
        to { transform: translateY(0); }
    }
    @keyframes sheet-fade {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    .sheet-grabber {
        width: 40px;
        height: 4px;
        background: var(--arena-line);
        margin: 8px auto 0;
        border-radius: 2px;
    }
    .sheet-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 18px 12px;
        border-bottom: 1px solid var(--arena-line-soft);
    }
    .sheet-title {
        font-family: var(--arena-f-display);
        font-size: 18px;
        font-weight: 700;
        letter-spacing: -0.4px;
        margin: 0;
        color: var(--arena-ink);
    }
    .sheet-close {
        background: transparent;
        border: 1px solid var(--arena-line);
        padding: 4px 10px;
        font-size: 12px;
        line-height: 1;
        cursor: pointer;
        color: var(--arena-ink);
    }
    .sheet-close:hover {
        background: var(--arena-ink);
        color: var(--arena-paper);
    }
    .sheet-body {
        padding: 16px 18px 8px;
        overflow-y: auto;
        flex: 1;
    }
    .sheet-pill-group {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }
    .sheet-pill-group .pill {
        font-size: 13px;
        padding: 8px 14px;
    }
    .sheet-foot {
        padding: 12px 18px 16px;
        border-top: 1px solid var(--arena-line-soft);
        background: var(--arena-paper-alt);
    }
    .sheet-apply {
        width: 100%;
        padding: 12px;
        background: var(--arena-ink);
        color: var(--arena-paper);
        border: 1px solid var(--arena-ink);
        font-family: var(--arena-f-mono);
        font-size: 12px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        font-weight: 600;
        cursor: pointer;
    }
    .sheet-apply:hover {
        background: var(--arena-ink-soft);
    }
</style>
