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
    const sport = $derived(data.sport as string | null);
    const sports = $derived(data.sports as SportOption[]);
    const region = $derived((data as { region?: string | null }).region ?? null);
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

    function buildFilterUrl(nextSport: string | null, nextRegion: string | null): string {
        const params = new URLSearchParams();
        params.set('year', String(year));
        params.set('month', String(month));
        if (nextSport) params.set('sport', nextSport);
        if (nextRegion) params.set('region', nextRegion);
        return `/calendar?${params.toString()}`;
    }

    function handleSportFilter(value: string | null) {
        goto(buildFilterUrl(value, region), { replaceState: true });
    }

    function handleRegionFilter(value: string | null) {
        goto(buildFilterUrl(sport, value), { replaceState: true });
    }

    function buildNavQuery(targetYear: number, targetMonth: number): string {
        const params = new URLSearchParams();
        params.set('year', String(targetYear));
        params.set('month', String(targetMonth));
        if (sport) params.set('sport', sport);
        if (region) params.set('region', region);
        return params.toString();
    }

    const todayDate = new Date();
    const currentMonth = todayDate.getMonth() + 1;
    const currentYear = todayDate.getFullYear();
    const todayHref = $derived(() => {
        const params = new URLSearchParams();
        if (sport) params.set('sport', sport);
        if (region) params.set('region', region);
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
</script>

<svelte:head>
    <title>{year}년 {month}월 대회 캘린더 - 엔듀로허브</title>
    <meta name="description" content="{year}년 {month}월 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정" />
    <meta property="og:title" content="{year}년 {month}월 대회 캘린더 - 엔듀로허브" />
    <meta property="og:description" content="{year}년 {month}월 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정" />
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

    <div class="cal-toolbar">
        <div class="toolbar-row">
            <span class="arena-kicker toolbar-label">종목</span>
            <div class="pill-group">
                <button class="pill" class:active={!sport} onclick={() => handleSportFilter(null)}>전체</button>
                {#each sports as s}
                    <button
                        class="pill sport-{s.value}"
                        class:active={sport === s.value}
                        onclick={() => handleSportFilter(s.value)}
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
                    <button class="pill" class:active={!region} onclick={() => handleRegionFilter(null)}>전체</button>
                    {#each regions as r}
                        <button
                            class="pill"
                            class:active={region === r}
                            onclick={() => handleRegionFilter(r)}
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
                                <span class="race-bar"></span>
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
        grid-template-columns: repeat(7, 1fr);
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
        grid-template-columns: repeat(7, 1fr);
    }
    .cal-cell {
        min-height: 96px;
        padding: 5px 5px 7px;
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
            padding: 6px 6px 8px;
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
        padding: 1px 5px;
        border: 1px solid var(--arena-line-soft);
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
        display: grid;
        grid-template-columns: 3px 1fr;
        align-items: center;
        gap: 5px;
        padding: 2px 4px 2px 0;
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
        border-color: var(--arena-ink);
        background: var(--arena-paper-alt);
    }
    .race-bar {
        align-self: stretch;
    }
    .race-name {
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
    .sport-running .race-bar,
    .sport-running .pill-dot {
        background: oklch(48% 0.18 280);
    }
    .sport-swimming .race-bar,
    .sport-swimming .pill-dot {
        background: oklch(50% 0.14 220);
    }
    .sport-cycling .race-bar,
    .sport-cycling .pill-dot {
        background: oklch(55% 0.16 60);
    }
    .sport-triathlon .race-bar,
    .sport-triathlon .pill-dot {
        background: oklch(48% 0.18 320);
    }
    .sport-trail_running .race-bar,
    .sport-trail_running .pill-dot {
        background: oklch(42% 0.14 145);
    }
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
</style>
