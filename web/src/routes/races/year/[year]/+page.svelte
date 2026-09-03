<script lang="ts">
    import { onMount } from 'svelte';
    import FilterChip from '$lib/components/eh/FilterChip.svelte';
    import Badge from '$lib/components/eh/Badge.svelte';
    import SportTag from '$lib/components/eh/SportTag.svelte';
    import Button from '$lib/components/eh/Button.svelte';
    import { SPORT_META, appSportToDs, type DsSport } from '$lib/components/eh/meta';
    import { arenaDistLabel, arenaFeeRange, arenaFeeShort, arenaDday } from '$lib/arena';
    import type { Race } from '$lib/types';

    let { data } = $props();

    const racesByMonth = $derived(data.races as Record<string, Race[]>);
    const year = $derived(data.year as number);
    const totalCount = $derived(data.totalCount as number);

    // ── Constants ─────────────────────────────────────────────────────────────
    const EN_MONTH = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER'];
    const DOW = ['일', '월', '화', '수', '목', '금', '토'];
    const pad = (n: number) => String(n).padStart(2, '0');

    const SPORTS: DsSport[] = ['run', 'trail', 'ride', 'swim', 'tri'];

    // 상태 패싯 — 접수중·예정·접수마감·종료
    const STATUS_FACETS = [
        { id: 'open', label: '접수중', match: (r: Race) => r.status === 'registration_open' },
        { id: 'upcoming', label: '예정', match: (r: Race) => r.status === 'upcoming' },
        { id: 'closed', label: '접수마감', match: (r: Race) => r.status === 'registration_closed' },
        { id: 'done', label: '종료', match: (r: Race) => r.status === 'finished' }
    ];
    const statusMatch = (r: Race, id: string) => STATUS_FACETS.find((s) => s.id === id)?.match(r) ?? true;

    const REGION_ORDER = ['서울', '경기', '인천', '강원', '충북', '충남', '대전', '세종', '대구', '경북', '울산', '부산', '경남', '전북', '전남', '광주', '제주'];
    const regionIdx = (x: string) => {
        const i = REGION_ORDER.indexOf(x);
        return i === -1 ? 99 : i;
    };

    // ── Row helpers ───────────────────────────────────────────────────────────
    function dayOf(race: Race): number {
        const p = race.raceDate?.split('-');
        return p && p.length >= 3 ? Number(p[2]) : 1;
    }
    function dowOf(month: number, day: number): string {
        return DOW[new Date(year, month - 1, day).getDay()];
    }
    function feeLabel(race: Race): string {
        const { min, max } = arenaFeeRange(race);
        if (min == null) return '—';
        return max != null && max !== min ? `${arenaFeeShort(min)}~` : arenaFeeShort(min);
    }

    // ── Filter state (single-select per facet) ────────────────────────────────
    type Facet = 'all' | string;
    let fSport = $state<Facet>('all');
    let fStatus = $state<Facet>('all');
    let fRegion = $state<Facet>('all');
    let sheetOpen = $state(false);

    function reset() {
        fSport = 'all';
        fStatus = 'all';
        fRegion = 'all';
    }
    function removeChip(k: string) {
        if (k === 'sport') fSport = 'all';
        else if (k === 'status') fStatus = 'all';
        else if (k === 'region') fRegion = 'all';
    }

    // ── Data shaping ──────────────────────────────────────────────────────────
    interface MonthRace {
        race: Race;
        month: number;
    }
    const allRaces = $derived<MonthRace[]>(
        Object.entries(racesByMonth).flatMap(([m, list]) => list.map((race) => ({ race, month: Number(m) })))
    );

    const regions = $derived(
        [...new Set(allRaces.map((x) => x.race.region).filter((r): r is string => !!r))].sort(
            (a, b) => regionIdx(a) - regionIdx(b)
        )
    );

    // 한 조건(except)만 빼고 적용 — 패싯 카운트용
    function matchExcept(x: MonthRace, except: string | null): boolean {
        const r = x.race;
        if (except !== 'sport' && fSport !== 'all' && appSportToDs[r.sport] !== fSport) return false;
        if (except !== 'status' && fStatus !== 'all' && !statusMatch(r, fStatus)) return false;
        if (except !== 'region' && fRegion !== 'all' && r.region !== fRegion) return false;
        return true;
    }

    const filtered = $derived(allRaces.filter((x) => matchExcept(x, null)));
    const sportPool = $derived(allRaces.filter((x) => matchExcept(x, 'sport')));
    const statusPool = $derived(allRaces.filter((x) => matchExcept(x, 'status')));
    const regionPool = $derived(allRaces.filter((x) => matchExcept(x, 'region')));

    const byMonth = $derived.by(() => {
        const map: Record<number, MonthRace[]> = {};
        for (const x of filtered) (map[x.month] ||= []).push(x);
        for (const m of Object.keys(map)) map[Number(m)].sort((a, b) => dayOf(a.race) - dayOf(b.race));
        return map;
    });

    const sumChips = $derived.by(() => {
        const out: { k: string; label: string }[] = [];
        if (fSport !== 'all') out.push({ k: 'sport', label: SPORT_META[fSport as DsSport].ko });
        if (fStatus !== 'all') out.push({ k: 'status', label: STATUS_FACETS.find((s) => s.id === fStatus)?.label ?? '' });
        if (fRegion !== 'all') out.push({ k: 'region', label: fRegion });
        return out;
    });

    // ── Current-month highlight (set client-side to avoid hydration mismatch) ──
    let nowMonth = $state<number | null>(null);

    // ── Scroll-spy: which month section is under the sticky index right now ──
    let activeMonth = $state<number | null>(null);

    function stickyOffset(): number {
        const idx = document.querySelector('.yr-index') as HTMLElement | null;
        return (window.innerWidth <= 768 ? 52 : 64) + (idx?.offsetHeight ?? 0) + 8;
    }

    onMount(() => {
        const d = new Date();
        if (d.getFullYear() === year) nowMonth = d.getMonth() + 1;

        let raf = 0;
        const compute = () => {
            raf = 0;
            const line = stickyOffset();
            const sections = document.querySelectorAll<HTMLElement>('.yr-month');
            let current: number | null = null;
            for (const sec of sections) {
                if (sec.getBoundingClientRect().top - line <= 0) {
                    current = Number(sec.id.replace('yr-m-', ''));
                } else break;
            }
            if (current == null && sections.length) current = Number(sections[0].id.replace('yr-m-', ''));
            if (current !== activeMonth) activeMonth = current;
        };
        const onScroll = () => {
            if (!raf) raf = requestAnimationFrame(compute);
        };
        compute();
        window.addEventListener('scroll', onScroll, { passive: true });
        window.addEventListener('resize', onScroll);
        return () => {
            window.removeEventListener('scroll', onScroll);
            window.removeEventListener('resize', onScroll);
            if (raf) cancelAnimationFrame(raf);
        };
    });

    // Keep the active month cell visible in the horizontally-scrolling index.
    $effect(() => {
        if (activeMonth == null) return;
        const idx = document.querySelector('.yr-index') as HTMLElement | null;
        const cell = idx?.children[activeMonth - 1] as HTMLElement | undefined;
        if (!idx || !cell) return;
        const cellRect = cell.getBoundingClientRect();
        const boxRect = idx.getBoundingClientRect();
        const left = idx.scrollLeft + (cellRect.left - boxRect.left) - (idx.clientWidth - cell.offsetWidth) / 2;
        idx.scrollTo({ left, behavior: 'smooth' });
    });

    // ── Sheet behaviour: lock scroll + ESC ────────────────────────────────────
    $effect(() => {
        if (!sheetOpen) return;
        const prev = document.body.style.overflow;
        document.body.style.overflow = 'hidden';
        const onKey = (e: KeyboardEvent) => {
            if (e.key === 'Escape') sheetOpen = false;
        };
        window.addEventListener('keydown', onKey);
        return () => {
            document.body.style.overflow = prev;
            window.removeEventListener('keydown', onKey);
        };
    });

    // ── Month jump ────────────────────────────────────────────────────────────
    // Land the section top just above the scroll-spy line so the clicked month
    // registers as active (not the one before it).
    function jump(m: number) {
        const el = document.getElementById('yr-m-' + m);
        if (!el) return;
        const off = stickyOffset() - 6;
        window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - off, behavior: 'smooth' });
    }

    // ── SEO / OG ──────────────────────────────────────────────────────────────
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

{#snippet countSlot()}
    <span class="eh-micro eh-data count-slot">{filtered.length} / {allRaces.length} RACES</span>
{/snippet}

{#snippet filterRows()}
    <div class="fil-row">
        <span class="eh-micro fil-label">SPORT</span>
        <div class="fil-chips">
            <FilterChip selected={fSport === 'all'} onclick={() => (fSport = 'all')}>전체</FilterChip>
            {#each SPORTS as s (s)}
                <FilterChip
                    selected={fSport === s}
                    dotColor={SPORT_META[s].color}
                    count={sportPool.filter((x) => appSportToDs[x.race.sport] === s).length}
                    onclick={() => (fSport = fSport === s ? 'all' : s)}
                >
                    {SPORT_META[s].ko}
                </FilterChip>
            {/each}
        </div>
    </div>
    <div class="fil-row">
        <span class="eh-micro fil-label">STATUS</span>
        <div class="fil-chips">
            <FilterChip selected={fStatus === 'all'} onclick={() => (fStatus = 'all')}>전체</FilterChip>
            {#each STATUS_FACETS as s (s.id)}
                <FilterChip
                    selected={fStatus === s.id}
                    count={statusPool.filter((x) => s.match(x.race)).length}
                    onclick={() => (fStatus = fStatus === s.id ? 'all' : s.id)}
                >
                    {s.label}
                </FilterChip>
            {/each}
        </div>
    </div>
    <div class="fil-row">
        <span class="eh-micro fil-label">REGION</span>
        <div class="fil-chips">
            <FilterChip selected={fRegion === 'all'} onclick={() => (fRegion = 'all')}>전국</FilterChip>
            {#each regions as rg (rg)}
                <FilterChip
                    selected={fRegion === rg}
                    count={regionPool.filter((x) => x.race.region === rg).length}
                    onclick={() => (fRegion = fRegion === rg ? 'all' : rg)}
                >
                    {rg}
                </FilterChip>
            {/each}
        </div>
    </div>
{/snippet}

<div class="v-container yr-page">
    <!-- HERO -->
    <div class="hero">
        <div class="eh-micro"><span class="acc">{year} INDEX</span> · 전국 <span class="eh-data">{totalCount}</span> RACES</div>
        <h1 class="hero-title">{year} 대회 캘린더</h1>
        <p class="hero-sub">
            {year}년 전국 마라톤·트레일러닝·자전거·수영·철인3종 대회 {totalCount}개를 월별로 모았습니다.
            종목, 접수 상태, 지역으로 원하는 대회를 골라보세요.
        </p>
    </div>

    <!-- MONTH INDEX (sticky) -->
    <section class="yr-index" aria-label="월별 바로가기">
        {#each Array(12) as _, i (i)}
            {@const m = i + 1}
            {@const n = (byMonth[m] || []).length}
            <button
                type="button"
                disabled={n === 0}
                class="yr-cell"
                class:off={n === 0}
                class:now={m === activeMonth}
                onclick={() => jump(m)}
            >
                <span class="yr-num eh-data">{m}<span class="yr-suf">월</span></span>
            </button>
        {/each}
    </section>

    <!-- FILTER BAR + SHEET -->
    <section class="fil compactbar" aria-label="필터">
        <div class="fil-bar">
            <button
                type="button"
                class="fil-toggle"
                aria-haspopup="dialog"
                aria-expanded={sheetOpen}
                onclick={() => (sheetOpen = true)}
            >
                필터
                {#if sumChips.length > 0}<span class="fil-cnt eh-data">{sumChips.length}</span>{/if}
            </button>
            {#if sumChips.length > 0}
                <div class="fil-sum">
                    {#each sumChips as chip (chip.k)}
                        <FilterChip selected onclick={() => removeChip(chip.k)}>{chip.label} ×</FilterChip>
                    {/each}
                    {#if sumChips.length > 1}
                        <button class="reset-link" onclick={reset}>초기화</button>
                    {/if}
                </div>
            {/if}
            <div class="fil-end">{@render countSlot()}</div>
        </div>
    </section>

    {#if sheetOpen}
        <div class="v-scrim fil-scrim">
            <button class="fil-scrim-bg" aria-label="필터 닫기" onclick={() => (sheetOpen = false)}></button>
            <div class="v-modal fil-sheet" role="dialog" aria-modal="true" aria-label="필터">
                <div class="fil-sheet-head">
                    <span class="eh-micro"><span class="acc">FILTER</span> · {year} INDEX</span>
                    <button type="button" class="fil-x" aria-label="닫기" onclick={() => (sheetOpen = false)}>×</button>
                </div>
                <div class="fil-sheet-body">
                    {@render filterRows()}
                </div>
                <div class="fil-sheet-foot">
                    <button class="reset-link" onclick={reset}>초기화</button>
                    <Button variant="primary" onclick={() => (sheetOpen = false)}>결과 {filtered.length}개 보기 →</Button>
                </div>
            </div>
        </div>
    {/if}

    <!-- MONTH SECTIONS -->
    {#if filtered.length === 0}
        <p class="yr-empty">조건에 맞는 대회가 없습니다. 필터를 줄여보세요.</p>
    {:else}
        {#each Array(12) as _, i (i)}
            {@const m = i + 1}
            {@const list = byMonth[m] || []}
            {#if list.length > 0}
                <section class="yr-month" id={'yr-m-' + m}>
                    <h2 class="yr-mhead" aria-label={`${year}년 ${m}월 대회 ${list.length}개`}>
                        <span class="yr-mnum eh-data">{pad(m)}</span>
                        <span class="eh-micro">{EN_MONTH[m - 1]}</span>
                        {#if m === nowMonth}<span class="eh-micro yr-thismonth">THIS MONTH</span>{/if}
                        <span class="eh-micro eh-data yr-mcount">{list.length} RACES</span>
                    </h2>
                    <div class="v-table">
                        {#each list as { race } (race.slug)}
                            {@const day = dayOf(race)}
                            <a class="v-trow click yr-row" class:done={race.status === 'finished'} href={`/races/${race.slug}`}>
                                <span class="eh-data yr-date">{m}.{pad(day)} {dowOf(m, day)}</span>
                                <span class="hide-m"><SportTag sport={appSportToDs[race.sport]} /></span>
                                <span class="yr-name">{race.title}</span>
                                <span class="hide-m yr-dim eh-data">{arenaDistLabel(race)}</span>
                                <span class="hide-m yr-dim">{race.region || '—'}</span>
                                <span class="hide-m yr-dim eh-data">{feeLabel(race)}</span>
                                <span class="yr-badge">
                                    {#if race.status === 'finished'}
                                        <span class="eh-micro yr-done">종료</span>
                                    {:else if race.status === 'registration_open'}
                                        {@const dday = arenaDday(race).value}
                                        <Badge status={dday != null && dday >= 0 && dday <= 7 ? 'closing' : 'open'}>
                                            <span class="eh-data">{dday != null && dday >= 0 ? `접수 중 D-${dday}` : '접수 중'}</span>
                                        </Badge>
                                    {:else if race.status === 'upcoming'}
                                        <Badge status="upcoming" />
                                    {:else}
                                        <Badge status="closed" />
                                    {/if}
                                </span>
                            </a>
                        {/each}
                    </div>
                </section>
            {/if}
        {/each}
    {/if}
</div>

<style>
    .yr-page {
        padding-top: var(--sp-2);
        padding-bottom: var(--sp-16);
    }

    /* ── HERO (Search와 동일한 패턴, 컴팩트) ── */
    .hero {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: var(--sp-4);
        padding: 48px 0 8px;
    }
    .hero-title {
        font-size: clamp(30px, 4vw, 42px);
        font-weight: var(--w-display);
        letter-spacing: var(--track-display);
        line-height: var(--leading-display);
        color: var(--text-strong);
        margin: 0;
    }
    .hero-sub {
        color: var(--text-muted);
        font-size: 15px;
        line-height: 1.7;
        max-width: 680px;
        margin: 0;
    }

    /* ── 필터 바 (컴팩트) ── */
    .fil {
        border-top: var(--border-rule);
    }
    .reset-link {
        background: none;
        border: 0;
        padding: 2px 0;
        font-size: 13px;
        font-weight: 600;
        color: var(--text-muted);
        border-bottom: 1px solid var(--line);
        cursor: pointer;
    }
    .reset-link:hover {
        color: var(--text-strong);
        border-bottom-color: var(--ink-900);
    }

    .fil-bar {
        display: flex;
        align-items: center;
        gap: 12px;
        row-gap: 10px;
        padding: 12px 0;
        border-bottom: 1px solid var(--line);
        flex-wrap: wrap;
    }
    .fil-toggle {
        appearance: none;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        height: 40px;
        padding: 0 16px;
        flex: none;
        background: var(--paper-0);
        border: 1px solid var(--ink-900);
        border-radius: 2px;
        font: inherit;
        font-size: 13px;
        font-weight: 600;
        color: var(--text-strong);
        cursor: pointer;
        transition: background 140ms var(--ease-out);
    }
    .fil-toggle:hover,
    .fil-toggle[aria-expanded='true'] {
        background: var(--paper-50);
    }
    .fil-cnt {
        min-width: 18px;
        height: 18px;
        padding: 0 5px;
        border-radius: 999px;
        background: var(--ink-900);
        color: var(--paper-0);
        font-size: 11px;
        font-weight: 700;
        display: grid;
        place-items: center;
    }
    .fil-sum {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        min-width: 0;
    }
    .fil-end {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-left: auto;
    }
    .count-slot {
        color: var(--text-faint);
    }

    /* ── 필터 행 (시트 내부) ── */
    .fil-row {
        display: flex;
        align-items: flex-start;
        gap: 16px;
        padding: 13px 0;
        border-bottom: 1px solid var(--line);
    }
    .fil-row:last-child {
        border-bottom: 0;
    }
    .fil-label {
        flex: none;
        width: 84px;
        padding-top: 8px;
        color: var(--text-faint);
    }
    .fil-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        flex: 1;
    }

    /* ── 필터 모달 / 바텀시트 ── */
    .fil-scrim {
        place-items: center;
    }
    .fil-scrim-bg {
        position: absolute;
        inset: 0;
        background: none;
        border: 0;
        padding: 0;
        cursor: pointer;
    }
    .fil-sheet {
        max-width: 640px;
        display: flex;
        flex-direction: column;
        max-height: 84dvh;
    }
    .fil-sheet-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 14px 12px 20px;
        border-bottom: var(--border-rule);
        flex: none;
    }
    .fil-x {
        background: none;
        border: 0;
        font-size: 22px;
        line-height: 1;
        padding: 2px 8px;
        color: var(--text-muted);
        cursor: pointer;
    }
    .fil-x:hover {
        color: var(--text-strong);
    }
    .fil-sheet-body {
        padding: 0 20px 4px;
        overflow-y: auto;
    }
    .fil-sheet-foot {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        flex: none;
        padding: 14px 20px calc(14px + env(safe-area-inset-bottom, 0px));
        border-top: 1px solid var(--line);
    }
    @keyframes sheet-up {
        from {
            transform: translateY(24px);
            opacity: 0;
        }
    }

    /* ── 월별 인덱스 그리드 (sticky) ── */
    .yr-index {
        display: grid;
        grid-template-columns: repeat(12, 1fr);
        gap: 1px;
        background: var(--line);
        border: 1px solid var(--line);
        border-top: var(--border-rule);
        margin-top: 18px;
        position: sticky;
        top: 64px;
        z-index: 40;
    }
    .yr-cell {
        appearance: none;
        border: 0;
        background: var(--paper-0);
        cursor: pointer;
        font: inherit;
        padding: 13px 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background 140ms var(--ease-out);
    }
    .yr-cell:hover {
        background: var(--paper-50);
    }
    .yr-cell.off {
        cursor: default;
    }
    .yr-cell.off:hover {
        background: var(--paper-0);
    }
    .yr-cell.off .yr-num {
        color: var(--text-faint);
    }
    .yr-num {
        font-size: 17px;
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }
    .yr-suf {
        font-size: 12px;
        font-weight: 700;
        margin-left: 1px;
    }
    .yr-cell.now {
        box-shadow: inset 0 -2px 0 var(--accent);
    }
    .yr-cell.now .yr-num {
        color: var(--accent-strong);
    }

    /* ── 월 섹션 ── */
    .yr-month {
        margin-top: 36px;
    }
    .yr-month:last-of-type {
        margin-bottom: 64px;
    }
    .yr-mhead {
        display: flex;
        align-items: baseline;
        gap: 12px;
        border-top: var(--border-rule);
        padding: 12px 0;
        margin: 0;
        color: inherit;
        font: inherit;
    }
    .yr-mnum {
        font-size: 34px;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1;
    }
    .yr-thismonth {
        color: var(--text-accent);
    }
    .yr-mcount {
        margin-left: auto;
        color: var(--text-faint);
    }

    .yr-row {
        grid-template-columns: 96px 84px 1fr 100px 56px 76px 132px;
        gap: 14px;
        text-decoration: none;
        color: var(--text-strong);
    }
    .yr-badge {
        justify-self: end;
    }
    .yr-date {
        font-weight: 600;
        white-space: nowrap;
    }
    .yr-name {
        font-weight: 600;
        min-width: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .yr-dim {
        color: var(--text-muted);
        font-size: 13px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .yr-done {
        color: var(--text-faint);
    }
    .yr-row.done .yr-name {
        color: var(--text-muted);
        font-weight: 500;
    }
    .yr-row.done .yr-date {
        color: var(--text-muted);
    }

    .yr-empty {
        color: var(--text-muted);
        padding: 28px 0;
    }

    @media (max-width: 768px) {
        .hero {
            padding: 28px 0 0;
            gap: 12px;
        }
        .hero-title {
            font-size: 26px;
        }
        .hero-sub {
            font-size: 14px;
        }

        .yr-index {
            grid-template-columns: repeat(12, minmax(48px, 1fr));
            grid-auto-flow: column;
            top: 52px;
            overflow-x: auto;
            scrollbar-width: none;
        }
        .yr-index::-webkit-scrollbar {
            display: none;
        }
        .yr-cell {
            padding: 11px 2px;
        }
        .yr-num {
            font-size: 16px;
        }

        .fil-bar {
            gap: 10px;
        }
        .fil-bar .fil-sum {
            flex: 1 0 100%;
            order: 3;
        }

        /* 모달 → 바텀시트 */
        .fil-scrim {
            place-items: end stretch;
            padding: 0;
        }
        .fil-sheet {
            max-width: none;
            width: 100%;
            max-height: 86dvh;
            border-left: 0;
            border-right: 0;
            border-bottom: 0;
            animation: sheet-up 200ms var(--ease-out);
        }

        .yr-month {
            margin-top: 28px;
        }
        .yr-mnum {
            font-size: 28px;
        }
        .yr-row {
            grid-template-columns: 76px 1fr auto;
            gap: 10px;
        }
        .yr-row .hide-m {
            display: none;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .fil-sheet {
            animation: none;
        }
    }
</style>
