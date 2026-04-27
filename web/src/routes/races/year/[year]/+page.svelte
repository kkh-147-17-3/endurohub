<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import RaceRow from '$lib/components/arena/RaceRow.svelte';
    import type { Race, Sport } from '$lib/types';

    let { data } = $props();

    const races = $derived(data.races as Record<string, Race[]>);
    const year = $derived(data.year as number);
    const totalCount = $derived(data.totalCount as number);

    type StatusType = 'registration_open' | 'registration_closed' | 'upcoming' | 'finished';

    const statuses: { key: StatusType; label: string }[] = [
        { key: 'registration_open', label: '접수중' },
        { key: 'upcoming', label: '예정' },
        { key: 'registration_closed', label: '접수마감' },
        { key: 'finished', label: '종료' },
    ];

    const regions = ['서울', '경기', '인천', '강원', '충북', '충남', '대전', '세종', '전북', '전남', '광주', '경북', '경남', '대구', '울산', '부산', '제주'];

    const sports: { key: Sport; label: string }[] = [
        { key: 'running', label: '러닝' },
        { key: 'trail_running', label: '트레일러닝' },
        { key: 'cycling', label: '사이클' },
        { key: 'swimming', label: '수영' },
        { key: 'triathlon', label: '철인3종' },
    ];

    const STORAGE_KEY = 'yearly-filter';
    const ALL_SPORTS: Sport[] = sports.map((s) => s.key);
    const ALL_STATUSES: StatusType[] = statuses.map((s) => s.key);

    const MONTH_LABELS = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];

    let selectedSports = $state<Set<Sport>>(new Set(ALL_SPORTS));
    let selectedRegions = $state<Set<string>>(new Set(regions));
    let selectedStatuses = $state<Set<StatusType>>(new Set(ALL_STATUSES));
    let mobileFilterOpen = $state(false);
    let activeMonth = $state<number | null>(null);

    let observer: IntersectionObserver | null = null;

    let hasActiveFilter = $derived(
        selectedSports.size < ALL_SPORTS.length ||
        selectedStatuses.size < ALL_STATUSES.length ||
        selectedRegions.size < regions.length
    );

    function saveFilter() {
        localStorage.setItem(
            STORAGE_KEY,
            JSON.stringify({
                sports: [...selectedSports],
                statuses: [...selectedStatuses],
                regions: [...selectedRegions],
            })
        );
    }

    onMount(() => {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            try {
                const saved = JSON.parse(stored);
                if (saved.sports?.length > 0)
                    selectedSports = new Set(saved.sports.filter((s: string) => ALL_SPORTS.includes(s as Sport)));
                if (saved.statuses?.length > 0)
                    selectedStatuses = new Set(saved.statuses.filter((s: string) => ALL_STATUSES.includes(s as StatusType)));
                if (saved.regions?.length > 0)
                    selectedRegions = new Set(saved.regions.filter((r: string) => regions.includes(r)));
            } catch { /* ignore */ }
        }

        const sections = document.querySelectorAll('section[id^="month-"]');
        observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        const month = parseInt(entry.target.id.replace('month-', ''));
                        activeMonth = month;
                        document.getElementById(`month-nav-${month}`)?.scrollIntoView({
                            behavior: 'smooth',
                            block: 'nearest',
                            inline: 'center',
                        });
                    }
                });
            },
            { root: null, rootMargin: '-20% 0px -60% 0px', threshold: 0 }
        );
        sections.forEach((section) => observer?.observe(section));
    });

    onDestroy(() => observer?.disconnect());

    function getMonthRaces(month: number): Race[] {
        const monthRaces = races[String(month)] || [];
        return monthRaces.filter((race) => {
            const sportMatch = selectedSports.has(race.sport as Sport);
            const regionMatch =
                !race.region ||
                selectedRegions.size === 0 ||
                Array.from(selectedRegions).some((r) => race.region?.includes(r));
            const statusMatch = selectedStatuses.has(race.status as StatusType);
            return sportMatch && regionMatch && statusMatch;
        });
    }

    function toggleSport(sport: Sport) {
        if (selectedSports.has(sport)) selectedSports.delete(sport);
        else selectedSports.add(sport);
        selectedSports = new Set(selectedSports);
        saveFilter();
    }
    function toggleRegion(region: string) {
        if (selectedRegions.has(region)) selectedRegions.delete(region);
        else selectedRegions.add(region);
        selectedRegions = new Set(selectedRegions);
        saveFilter();
    }
    function toggleStatus(status: StatusType) {
        if (selectedStatuses.has(status)) selectedStatuses.delete(status);
        else selectedStatuses.add(status);
        selectedStatuses = new Set(selectedStatuses);
        saveFilter();
    }
    function resetFilters() {
        selectedSports = new Set(ALL_SPORTS);
        selectedRegions = new Set(regions);
        selectedStatuses = new Set(ALL_STATUSES);
        localStorage.removeItem(STORAGE_KEY);
    }

    function openMobileFilter() {
        mobileFilterOpen = true;
        document.body.style.overflow = 'hidden';
    }
    function closeMobileFilter() {
        mobileFilterOpen = false;
        document.body.style.overflow = '';
    }

    const SCHEDULE_OG_YEARS = [2025, 2026, 2027, 2028];
    let ogImage = $derived(
        SCHEDULE_OG_YEARS.includes(year)
            ? `${data.appUrl}/images/og-schedule-${year}.png`
            : `${data.appUrl}/images/og-image.png`
    );
</script>

<svelte:head>
    <title>{year}년 대회 일정 - 엔듀로허브</title>
    <meta
        name="description"
        content="{year}년 국내 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정을 월별로 확인하세요. 총 {totalCount}개 대회"
    />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="{year}년 대회 일정 - 엔듀로허브" />
    <meta
        property="og:description"
        content="{year}년 국내 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정을 월별로 확인하세요. 총 {totalCount}개 대회"
    />
    <meta property="og:image" content={ogImage} />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta name="twitter:image" content={ogImage} />
</svelte:head>

<div class="year-wrap">
    <!-- HEADER -->
    <header class="year-head">
        <div class="head-left">
            <div class="kicker">시즌 · {year}</div>
            <h1 class="title">{year}년 대회 일정</h1>
            <div class="sub">
                총 <b>{totalCount.toLocaleString()}</b>개 대회 · {ALL_SPORTS.length}개 종목
            </div>
        </div>
        <nav class="year-nav" aria-label="연도 이동">
            <a class="year-nav-btn" href="/races/year/{year - 1}" aria-label="{year - 1}년">
                <span class="arrow">←</span>
                <span class="num">{year - 1}</span>
            </a>
            <span class="year-nav-current">{year}</span>
            <a class="year-nav-btn" href="/races/year/{year + 1}" aria-label="{year + 1}년">
                <span class="num">{year + 1}</span>
                <span class="arrow">→</span>
            </a>
        </nav>
    </header>

    <!-- STICKY MONTH NAV -->
    <nav class="month-nav" aria-label="월 이동">
        <div class="month-nav-inner">
            {#each Array(12) as _, i}
                {@const m = i + 1}
                {@const monthRaces = getMonthRaces(m)}
                {@const empty = monthRaces.length === 0}
                {@const active = activeMonth === m}
                <a
                    id="month-nav-{m}"
                    href="#month-{m}"
                    class="month-chip"
                    class:active
                    class:empty
                    aria-disabled={empty}
                >
                    <span class="month-chip-label">{MONTH_LABELS[i]}</span>
                    {#if monthRaces.length > 0}
                        <span class="month-chip-count">{monthRaces.length}</span>
                    {/if}
                </a>
            {/each}
        </div>
    </nav>

    <div class="year-body">
        <!-- MONTH SECTIONS -->
        <div class="months">
            {#each Array(12) as _, i}
                {@const m = i + 1}
                {@const monthRaces = getMonthRaces(m)}
                <section id="month-{m}" class="month-sec" class:empty={monthRaces.length === 0}>
                    <div class="month-head">
                        <div class="month-head-num">
                            <span class="month-num">{MONTH_LABELS[i]}</span>
                        </div>
                        <div class="month-head-line"></div>
                        {#if monthRaces.length > 0}
                            <span class="month-head-count">{monthRaces.length}개 대회</span>
                        {:else}
                            <span class="month-head-count muted">대회 없음</span>
                        {/if}
                    </div>

                    {#if monthRaces.length > 0}
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
                            {#each monthRaces as race (race.id)}
                                <RaceRow {race} />
                            {/each}
                        </div>
                    {:else}
                        <div class="empty-card">
                            <span class="empty-kicker">결과 없음</span>
                            <p>이 달에 해당하는 대회가 없습니다.</p>
                        </div>
                    {/if}
                </section>
            {/each}
        </div>

        <!-- DESKTOP FILTER SIDEBAR -->
        <aside class="filter-sidebar">
            <div class="filter-panel">
                <div class="filter-panel-head">
                    <span class="kicker">필터</span>
                    {#if hasActiveFilter}
                        <button class="filter-reset" onclick={resetFilters}>초기화 ✕</button>
                    {/if}
                </div>

                <div class="filter-group">
                    <div class="filter-group-label">종목</div>
                    <div class="chip-row">
                        {#each sports as sport}
                            <button
                                class="filter-chip"
                                class:active={selectedSports.has(sport.key)}
                                onclick={() => toggleSport(sport.key)}
                            >
                                {sport.label}
                            </button>
                        {/each}
                    </div>
                </div>

                <div class="filter-group">
                    <div class="filter-group-label">상태</div>
                    <div class="chip-row">
                        {#each statuses as status}
                            <button
                                class="filter-chip"
                                class:active={selectedStatuses.has(status.key)}
                                onclick={() => toggleStatus(status.key)}
                            >
                                {status.label}
                            </button>
                        {/each}
                    </div>
                </div>

                <div class="filter-group">
                    <div class="filter-group-label">지역</div>
                    <div class="chip-row chip-row-wrap">
                        {#each regions as region}
                            <button
                                class="filter-chip"
                                class:active={selectedRegions.has(region)}
                                onclick={() => toggleRegion(region)}
                            >
                                {region}
                            </button>
                        {/each}
                    </div>
                </div>
            </div>
        </aside>
    </div>

    <!-- MOBILE FILTER FAB -->
    <button class="mobile-fab" onclick={openMobileFilter} aria-label="필터 열기">
        <span class="mono">필터</span>
        {#if hasActiveFilter}<span class="fab-dot"></span>{/if}
    </button>
</div>

{#if mobileFilterOpen}
    <div class="mobile-filter">
        <button
            class="mobile-filter-bg"
            onclick={closeMobileFilter}
            aria-label="모달 닫기"
        ></button>
        <div class="mobile-filter-sheet">
            <div class="mobile-filter-head">
                <span class="kicker">필터</span>
                <button class="mobile-filter-close" onclick={closeMobileFilter} aria-label="닫기">✕</button>
            </div>

            <div class="filter-group">
                <div class="filter-group-label">종목</div>
                <div class="chip-row chip-row-wrap">
                    {#each sports as sport}
                        <button
                            class="filter-chip"
                            class:active={selectedSports.has(sport.key)}
                            onclick={() => toggleSport(sport.key)}
                        >
                            {sport.label}
                        </button>
                    {/each}
                </div>
            </div>

            <div class="filter-group">
                <div class="filter-group-label">상태</div>
                <div class="chip-row chip-row-wrap">
                    {#each statuses as status}
                        <button
                            class="filter-chip"
                            class:active={selectedStatuses.has(status.key)}
                            onclick={() => toggleStatus(status.key)}
                        >
                            {status.label}
                        </button>
                    {/each}
                </div>
            </div>

            <div class="filter-group">
                <div class="filter-group-label">지역</div>
                <div class="chip-row chip-row-wrap">
                    {#each regions as region}
                        <button
                            class="filter-chip"
                            class:active={selectedRegions.has(region)}
                            onclick={() => toggleRegion(region)}
                        >
                            {region}
                        </button>
                    {/each}
                </div>
            </div>

            <div class="mobile-filter-actions">
                {#if hasActiveFilter}
                    <button class="arena-btn arena-btn-ghost" onclick={resetFilters}>초기화</button>
                {/if}
                <button class="arena-btn arena-btn-primary mobile-filter-apply" onclick={closeMobileFilter}>
                    적용
                </button>
            </div>
        </div>
    </div>
{/if}

<style>
    .year-wrap {
        max-width: 1400px;
        margin: 0 auto;
        padding: 32px 24px 80px;
    }
    @media (min-width: 1024px) {
        .year-wrap { padding: 40px 32px 100px; }
    }

    /* ── HEADER ── */
    .year-head {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 24px;
        padding-bottom: 24px;
        flex-wrap: wrap;
    }
    .head-left { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
    .kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
    }
    .title {
        font-family: var(--arena-f-display);
        font-size: clamp(32px, 5vw, 52px);
        font-weight: 700;
        letter-spacing: -1.5px;
        line-height: 1;
        margin: 4px 0 6px;
        color: var(--arena-ink);
    }
    .sub {
        font-family: var(--arena-f-mono);
        font-size: 12px;
        letter-spacing: 0.3px;
        color: var(--arena-ink-soft);
    }
    .sub b { color: var(--arena-ink); font-weight: 700; }

    .year-nav {
        display: flex;
        align-items: stretch;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
    }
    .year-nav-btn {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        font-family: var(--arena-f-mono);
        font-size: 12px;
        letter-spacing: 1px;
        color: var(--arena-ink-soft);
        text-decoration: none;
        background: var(--arena-paper);
        transition: background 0.1s, color 0.1s;
    }
    .year-nav-btn:hover { background: var(--arena-paper-alt); color: var(--arena-ink); }
    .year-nav-btn .arrow { font-size: 13px; }
    .year-nav-current {
        padding: 10px 18px;
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: 14px;
        letter-spacing: -0.3px;
        color: var(--arena-paper);
        background: var(--arena-ink);
        display: flex;
        align-items: center;
        border-left: 1px solid var(--arena-line);
        border-right: 1px solid var(--arena-line);
    }

    /* ── STICKY MONTH NAV ── */
    .month-nav {
        position: sticky;
        top: 62px;
        z-index: 20;
        background: var(--arena-paper);
        margin: 0 -24px;
    }
    @media (min-width: 1024px) {
        .month-nav {
             margin: 0 -32px;         
             top: 60px;
        }
    }
    .month-nav-inner {
        max-width: 1400px;
        margin: 0 auto;
        padding: 10px 24px;
        display: flex;
        gap: 6px;
        overflow-x: auto;
        scrollbar-width: none;
    }
    .month-nav-inner::-webkit-scrollbar { display: none; }
    @media (min-width: 1024px) {
        .month-nav-inner { padding: 12px 32px; }
    }
    .month-chip {
        flex-shrink: 0;
        display: inline-flex;
        align-items: baseline;
        gap: 7px;
        padding: 7px 13px;
        border: 1px solid var(--arena-line-soft);
        background: var(--arena-paper);
        font-family: var(--arena-f-mono);
        text-decoration: none;
        color: var(--arena-ink);
        transition: background 0.1s, color 0.1s, border-color 0.1s;
    }
    .month-chip-label {
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.3px;
    }
    .month-chip-count {
        font-size: 11px;
        font-weight: 700;
        padding: 1px 5px;
        margin-left: 2px;
        background: var(--arena-paper-alt);
        color: var(--arena-ink-soft);
    }
    .month-chip:hover {
        border-color: var(--arena-ink);
    }
    .month-chip.active {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border-color: var(--arena-ink);
    }
    .month-chip.active .month-chip-label {
        color: var(--arena-accent);
    }
    .month-chip.active .month-chip-count {
        background: var(--arena-accent);
        color: var(--arena-ink);
    }
    .month-chip.empty {
        color: var(--arena-ink-mute);
        pointer-events: none;
        opacity: 0.5;
    }
    .month-chip.empty .month-chip-label,
    .month-chip.empty .month-chip-num { color: var(--arena-ink-mute); }

    /* ── BODY (months + sidebar) ── */
    .year-body {
        display: grid;
        grid-template-columns: 1fr;
        gap: 32px;
        margin-top: 28px;
    }
    @media (min-width: 1024px) {
        .year-body {
            grid-template-columns: minmax(0, 1fr) 240px;
            gap: 28px;
        }
    }

    .months { min-width: 0; }
    .month-sec { scroll-margin-top: 140px; margin-bottom: 36px; }
    .month-sec:last-child { margin-bottom: 0; }

    .month-head {
        display: flex;
        align-items: baseline;
        gap: 14px;
        margin-bottom: 12px;
    }
    .month-head-num {
        display: flex;
        align-items: baseline;
        gap: 8px;
    }
    .month-num {
        font-family: var(--arena-f-display);
        font-size: 32px;
        font-weight: 700;
        letter-spacing: -1.5px;
        color: var(--arena-ink);
        line-height: 1;
    }
    .month-sec.empty .month-num { color: var(--arena-ink-mute); }
    .month-mono {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 2px;
        color: var(--arena-ink-soft);
    }
    .month-head-line {
        flex: 1;
        height: 1px;
        background: var(--arena-line-soft);
    }
    .month-head-count {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink);
        font-weight: 700;
    }
    .month-head-count.muted { color: var(--arena-ink-mute); font-weight: 500; }

    /* ── RACE TABLE (mirrored from /races) ── */
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
        .race-thead { display: none; }
    }

    .empty-card {
        border: 1px solid var(--arena-line-soft);
        background: var(--arena-paper);
        padding: 32px 20px;
        text-align: center;
        color: var(--arena-ink-soft);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
    }
    .empty-kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        color: var(--arena-ink-mute);
    }
    .empty-card p { margin: 0; font-size: 13px; }

    /* ── FILTER SIDEBAR ── */
    .filter-sidebar { display: none; }
    @media (min-width: 1024px) { .filter-sidebar { display: block; } }
    .filter-panel {
        position: sticky;
        top: 140px;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
        padding: 18px;
        display: flex;
        flex-direction: column;
        gap: 18px;
    }
    .filter-panel-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--arena-line-soft);
    }
    .filter-reset {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-urgent);
        background: transparent;
        border: none;
        cursor: pointer;
        padding: 0;
    }
    .filter-reset:hover { text-decoration: underline; }

    .filter-group { display: flex; flex-direction: column; gap: 8px; }
    .filter-group-label {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
    }
    .chip-row { display: flex; flex-wrap: wrap; gap: 6px; }
    .chip-row-wrap { gap: 5px; }
    .filter-chip {
        display: inline-flex;
        align-items: center;
        padding: 5px 10px;
        border: 1px solid var(--arena-line-soft);
        background: var(--arena-paper);
        color: var(--arena-ink-soft);
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.3px;
        cursor: pointer;
        transition: all 0.1s;
    }
    .filter-chip:hover { border-color: var(--arena-ink); color: var(--arena-ink); }
    .filter-chip.active {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border-color: var(--arena-ink);
    }

    /* ── MOBILE FAB ── */
    .mobile-fab {
        display: flex;
        position: fixed;
        bottom: 24px;
        right: 24px;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        background: var(--arena-ink);
        color: var(--arena-paper);
        border: none;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1.5px;
        cursor: pointer;
        z-index: 30;
    }
    .mobile-fab:active { transform: translateY(1px); }
    .fab-dot {
        width: 6px;
        height: 6px;
        background: var(--arena-accent);
    }
    @media (min-width: 1024px) { .mobile-fab { display: none; } }

    /* ── MOBILE FILTER SHEET ── */
    .mobile-filter {
        position: fixed;
        inset: 0;
        z-index: 9999;
    }
    .mobile-filter-bg {
        position: absolute;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        border: none;
        cursor: pointer;
    }
    .mobile-filter-sheet {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        background: var(--arena-paper);
        border-top: 1px solid var(--arena-line);
        padding: 20px 20px 28px;
        max-height: 80vh;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 18px;
        animation: slide-up 0.25s ease-out;
    }
    .mobile-filter-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--arena-line-soft);
    }
    .mobile-filter-close {
        background: transparent;
        border: none;
        font-family: var(--arena-f-mono);
        font-size: 16px;
        color: var(--arena-ink);
        cursor: pointer;
    }
    .mobile-filter-actions {
        display: flex;
        gap: 8px;
        padding-top: 8px;
        border-top: 1px solid var(--arena-line-soft);
    }
    .mobile-filter-apply { flex: 1; justify-content: center; }

    @keyframes slide-up {
        from { transform: translateY(100%); }
        to { transform: translateY(0); }
    }
</style>
