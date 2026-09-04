<script lang="ts">
    import type { Race } from '$lib/types';
    import { raceCourseOptions } from '$lib/race-result';
    import { StatBlock, Badge, Button, Modal } from '$lib/components/eh';
    import { clientApiFetch, isApiError } from '$lib/api.client';
    import { invalidateAll } from '$app/navigation';

    let { data } = $props();

    // ── Types ──────────────────────────────────────────────────────────────
    type SeasonStatus = 'confirmed_going' | 'maybe' | 'unknown' | 'logged';

    interface SeasonCourse {
        code: string;
        label: string;
        distKm: number;
    }

    interface SeasonResult {
        time: string;
        pace: string;
        pb?: boolean;
    }

    interface SeasonRace {
        id: string;
        slug: string;
        name: string;
        url: string;
        region: string;
        date: string;
        month: number;
        day: number;
        sport: string;
        courses: SeasonCourse[];
        deadline: { m: number; day: number } | null;
        userStatus: SeasonStatus;
        plannedCodes?: string[];
        loggedCode?: string;
        result?: SeasonResult;
        recentlyPassed?: boolean;
        mainGoal?: boolean;
        note?: string;
    }

    /**
     * Optional participation fields the backend does not return yet.
     * When the "my season" API (see notes at bottom of file) ships, the load
     * function can attach this and the strip/rows light up the richer states
     * (참가 예정 / 완주 기록 / 메인 목표 / 선택 종목). Until then we derive what
     * we honestly can from the race date + registration deadline.
     */
    type RaceWithParticipation = Race & {
        userStatus?: SeasonStatus;
        plannedCodes?: string[];
        loggedCode?: string;
        result?: SeasonResult;
        mainGoal?: boolean;
        note?: string;
    };

    // ── Date helpers ───────────────────────────────────────────────────────
    const today = new Date();
    const year = today.getFullYear();
    const todayMonth = today.getMonth() + 1;
    const todayDay = today.getDate();

    const months = [
        { m: 1, label: 'JAN', kr: '1월' },
        { m: 2, label: 'FEB', kr: '2월' },
        { m: 3, label: 'MAR', kr: '3월' },
        { m: 4, label: 'APR', kr: '4월' },
        { m: 5, label: 'MAY', kr: '5월' },
        { m: 6, label: 'JUN', kr: '6월' },
        { m: 7, label: 'JUL', kr: '7월' },
        { m: 8, label: 'AUG', kr: '8월' },
        { m: 9, label: 'SEP', kr: '9월' },
        { m: 10, label: 'OCT', kr: '10월' },
        { m: 11, label: 'NOV', kr: '11월' },
        { m: 12, label: 'DEC', kr: '12월' }
    ];

    const isLeap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
    const monthDays = [31, isLeap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    const totalDays = monthDays.reduce((a, b) => a + b, 0);
    const cumDays = (() => {
        const out = [0];
        for (const d of monthDays) out.push(out[out.length - 1] + d);
        return out;
    })();

    function dayOfYear(m: number, d: number): number {
        return cumDays[Math.max(0, m - 1)] + d;
    }
    /** horizontal position as a 0–100 percentage of the year */
    function pct(m: number, d: number): number {
        return Math.max(0, Math.min(100, (dayOfYear(m, d) / totalDays) * 100));
    }
    /** left edge / width of a month as a % of the year — proportional to its
     *  real length so the header axis matches where pins (by day-of-year) land. */
    function monthLeft(m: number): number {
        return (cumDays[m - 1] / totalDays) * 100;
    }
    function monthWidth(m: number): number {
        return (monthDays[m - 1] / totalDays) * 100;
    }

    const todayDoy = dayOfYear(todayMonth, todayDay);
    const todayPct = (todayDoy / totalDays) * 100;

    // ── Race data mapping ──────────────────────────────────────────────────
    function parseDate(d: string | null): { m: number; day: number; year: number } | null {
        if (!d) return null;
        const parts = d.split('-');
        if (parts.length < 3) return null;
        return { year: Number(parts[0]), m: Number(parts[1]), day: Number(parts[2]) };
    }

    /** Derive an honest user status from the race date when the API gives none. */
    function deriveStatus(rd: { m: number; day: number }): {
        status: SeasonStatus;
        recentlyPassed: boolean;
    } {
        const doy = dayOfYear(rd.m, rd.day);
        const diff = doy - todayDoy;
        if (diff < -14) return { status: 'unknown', recentlyPassed: false };
        if (diff < 0) return { status: 'unknown', recentlyPassed: true };
        // Favourited but no participation declared yet → 관심.
        return { status: 'maybe', recentlyPassed: false };
    }

    const seasonRaces: SeasonRace[] = $derived(
        (data.races as RaceWithParticipation[])
            .map((race): SeasonRace | null => {
                const rd = parseDate(race.raceDate);
                if (!rd || rd.year !== year) return null;
                const reg = parseDate(race.registrationEnd);
                const courses: SeasonCourse[] = raceCourseOptions(
                    (race.distances ?? []).slice(0, 4),
                    race.sport,
                    race.sportLabel,
                ).map((course) => ({
                    code: course.code,
                    label: course.label,
                    distKm: course.distanceKm,
                }));

                const derived = deriveStatus(rd);
                const userStatus = race.userStatus ?? derived.status;

                return {
                    id: race.slug,
                    slug: race.slug,
                    name: race.title,
                    url: race.url,
                    region: race.region ?? race.location ?? '',
                    date: race.raceDate ?? '',
                    month: rd.m,
                    day: rd.day,
                    sport: race.sport,
                    courses,
                    deadline: reg ? { m: reg.m, day: reg.day } : null,
                    userStatus,
                    plannedCodes: race.plannedCodes,
                    loggedCode: race.loggedCode,
                    result: race.result,
                    recentlyPassed: userStatus === 'unknown' ? derived.recentlyPassed : false,
                    mainGoal: race.mainGoal ?? false,
                    note: race.note
                };
            })
            .filter((r): r is SeasonRace => r !== null)
            .sort((a, b) => a.date.localeCompare(b.date))
    );

    // ── Derived collections ────────────────────────────────────────────────
    const upcoming = $derived(seasonRaces.filter((r) => dayOfYear(r.month, r.day) >= todayDoy));
    const past = $derived(seasonRaces.filter((r) => dayOfYear(r.month, r.day) < todayDoy));
    const pending = $derived(seasonRaces.filter((r) => r.recentlyPassed && r.userStatus === 'unknown'));

    // ── Mobile vertical timeline rail ───────────────────────────────────────
    // Chronological sequence interleaving month dividers + a single TODAY marker
    // (inserted before the first race on/after today) with the race nodes.
    type RailItem =
        | { kind: 'today' }
        | { kind: 'month'; label: string }
        | { kind: 'node'; race: SeasonRace };

    const railItems: RailItem[] = $derived.by(() => {
        const sorted = [...seasonRaces].sort(
            (a, b) => dayOfYear(a.month, a.day) - dayOfYear(b.month, b.day)
        );
        const items: RailItem[] = [];
        let lastMonth = 0;
        let todayPlaced = false;
        for (const r of sorted) {
            const doy = dayOfYear(r.month, r.day);
            if (!todayPlaced && doy >= todayDoy) {
                items.push({ kind: 'today' });
                todayPlaced = true;
            }
            if (r.month !== lastMonth) {
                items.push({ kind: 'month', label: months[r.month - 1].label });
                lastMonth = r.month;
            }
            items.push({ kind: 'node', race: r });
        }
        if (!todayPlaced) items.push({ kind: 'today' });
        return items;
    });

    const stats = $derived(
        (() => {
            const nowMs = today.getTime();
            const next = upcoming[0];
            const dday = (d: string) => Math.max(0, Math.ceil((new Date(d).getTime() - nowMs) / 86400000));
            const goal = seasonRaces.find((r) => r.mainGoal) ?? upcoming[upcoming.length - 1];
            return {
                totalRaces: seasonRaces.length,
                logged: seasonRaces.filter((r) => r.userStatus === 'logged').length,
                nextRaceDays: next ? dday(next.date) : null,
                mainGoalDays: goal ? dday(goal.date) : null,
                mainGoalName: goal?.name ?? '—'
            };
        })()
    );

    // ── UI state ───────────────────────────────────────────────────────────
    let sel = $state<string | null>(null);
    function toggle(id: string) {
        sel = sel === id ? null : id;
    }

    /** A race is "ended" once its day-of-year is before today (this season). */
    function isPast(r: SeasonRace): boolean {
        return dayOfYear(r.month, r.day) < todayDoy;
    }

    /** Human label for the logged course, derived from its code. */
    function loggedCourseLabel(r: SeasonRace): string {
        if (!r.loggedCode) return '';
        const c = r.courses.find((c) => c.code === r.loggedCode);
        return c?.label ?? r.loggedCode;
    }

    // ── Participation toggle (관심 ↔ 참가 예정) ──────────────────────────────
    let partBusy = $state<string | null>(null);

    async function setParticipation(r: SeasonRace, status: 'maybe' | 'confirmed_going') {
        if (partBusy) return;
        partBusy = r.slug;
        try {
            const res = await clientApiFetch<{ success?: boolean }>(
                `/me/races/${r.slug}/participation/`,
                { method: 'PUT', body: { status } },
            );
            if (res?.success) await invalidateAll();
        } catch {
            // 실패 시 상태 유지 — 다음 클릭에서 재시도.
        } finally {
            partBusy = null;
        }
    }

    // ── Record logging (완주 기록 입력 / 수정 / 삭제) ────────────────────────
    let logOpen = $state(false);
    let logRace = $state<SeasonRace | null>(null);
    let logCode = $state('');
    let logH = $state('');
    let logM = $state('');
    let logS = $state('');
    let logPb = $state(false);
    let logBusy = $state(false);
    let logError = $state('');
    const isEditing = $derived(logRace?.userStatus === 'logged');

    function openLog(r: SeasonRace) {
        logRace = r;
        logError = '';
        if (r.userStatus === 'logged') {
            const savedCode = r.loggedCode ?? '';
            logCode = r.courses.some((course) => course.code === savedCode)
                ? savedCode
                : r.courses[0]?.code ?? '';
            const parts = (r.result?.time ?? '').split(':').map((n) => Number(n) || 0);
            if (parts.length === 3) {
                [logH, logM, logS] = parts.map(String);
            } else if (parts.length === 2) {
                logH = '';
                [logM, logS] = parts.map(String);
            } else {
                logH = logM = logS = '';
            }
            logPb = r.result?.pb ?? false;
        } else {
            logCode = r.courses[0]?.code ?? '';
            logH = logM = logS = '';
            logPb = false;
        }
        logOpen = true;
    }

    function closeLog() {
        logOpen = false;
        logRace = null;
    }

    function firstError(res: unknown): string | null {
        if (!isApiError(res)) return null;
        const errors = res.errors as Record<string, unknown>;
        for (const v of Object.values(errors)) {
            if (Array.isArray(v) && v.length) return String(v[0]);
            if (typeof v === 'string') return v;
        }
        return null;
    }

    async function submitLog() {
        if (!logRace || logBusy) return;
        if (!logCode) {
            logError = '완주한 종목을 선택해주세요.';
            return;
        }
        const h = Number(logH) || 0;
        const m = Number(logM) || 0;
        const s = Number(logS) || 0;
        if (h * 3600 + m * 60 + s <= 0) {
            logError = '기록 시간을 입력해주세요.';
            return;
        }
        logBusy = true;
        logError = '';
        try {
            const res = await clientApiFetch<{ success?: boolean }>(
                `/me/races/${logRace.slug}/result/`,
                {
                    method: 'POST',
                    body: { course_code: logCode, hours: h, minutes: m, seconds: s, is_personal_best: logPb },
                },
            );
            if (res?.success) {
                closeLog();
                await invalidateAll();
            } else {
                logError = firstError(res) ?? '기록 저장에 실패했습니다.';
            }
        } catch {
            logError = '기록 저장에 실패했습니다.';
        } finally {
            logBusy = false;
        }
    }

    async function deleteLog() {
        if (!logRace || logBusy) return;
        logBusy = true;
        logError = '';
        try {
            const res = await clientApiFetch<{ success?: boolean }>(
                `/me/races/${logRace.slug}/result/`,
                { method: 'DELETE' },
            );
            if (res?.success) {
                closeLog();
                await invalidateAll();
            } else {
                logError = firstError(res) ?? '기록 삭제에 실패했습니다.';
            }
        } catch {
            logError = '기록 삭제에 실패했습니다.';
        } finally {
            logBusy = false;
        }
    }

    // ── Helpers ────────────────────────────────────────────────────────────
    const ST: Record<SeasonStatus, string> = {
        confirmed_going: 'going',
        maybe: 'maybe',
        unknown: 'unknown',
        logged: 'logged'
    };

    function deadlineInfo(r: SeasonRace): { text: string; warn: boolean } | null {
        if (!r.deadline) return null;
        if (r.userStatus === 'logged' || r.userStatus === 'unknown') return null;
        const left = dayOfYear(r.deadline.m, r.deadline.day) - todayDoy;
        if (left < 0) return { text: `접수 마감됨 ${r.deadline.m}.${r.deadline.day}`, warn: false };
        return { text: `접수 마감 ${r.deadline.m}.${r.deadline.day} · D-${left}`, warn: left <= 14 };
    }

    function isPlanned(r: SeasonRace, code: string): boolean {
        return (r.plannedCodes ?? []).includes(code) || r.loggedCode === code;
    }

    const userName = $derived(data.isAuthed ? (data.user?.nickname?.trim() ?? '') : '');
    const loginHref = '/auth/login?next=%2Ftimeline';
</script>

<svelte:head>
    <title>시즌 타임라인 — 엔듀로허브</title>
    <meta name="description" content="관심 대회를 한눈에 보는 연간 타임라인" />
    <meta name="robots" content="noindex" />
</svelte:head>

<main class="v-container tl">
    <!-- ── Header ─────────────────────────────────────────────────────────── -->
    <div class="hd">
        <div>
            <div class="eh-micro"><span class="acc">MY SEASON</span> · {year}{#if userName} · {userName}{/if}</div>
            <h1>시즌 타임라인</h1>
        </div>
        {#if seasonRaces.length > 0}
            <div class="hd-stats">
                <StatBlock label="올해 대회" value={stats.totalRaces} size="md" />
                <StatBlock label="다음 대회" value={stats.nextRaceDays != null ? `D-${stats.nextRaceDays}` : '—'} size="md" accent />
                <StatBlock label="메인 목표" value={stats.mainGoalDays != null ? `D-${stats.mainGoalDays}` : '—'} size="md" />
                <StatBlock label="완주 기록" value={stats.logged} size="md" />
            </div>
        {/if}
    </div>

    {#if seasonRaces.length === 0}
        <!-- ── Empty state → 로그인 유도 ──────────────────────────────────── -->
        <div class="empty-state">
            <div class="eh-micro acc">{data.isAuthed ? 'EMPTY SEASON' : 'SIGN IN'}</div>
            {#if data.isAuthed}
                <h2>아직 시즌에 담은 대회가 없어요</h2>
                <p>
                    관심 있는 대회에 ♥ 를 누르거나 참가 예정을 표시하면 이곳 타임라인에
                    한눈에 모입니다. 완주 후엔 기록도 남길 수 있어요.
                </p>
                <div class="empty-actions">
                    <Button variant="primary" size="md" href="/races?reset=1">대회 둘러보기 →</Button>
                </div>
            {:else}
                <h2>나만의 시즌 타임라인을 만들어보세요</h2>
                <p>
                    로그인하면 관심 대회·참가 예정·완주 기록을 연간 타임라인 하나로 모아
                    볼 수 있습니다. 다가오는 대회와 접수 마감일도 자동으로 챙겨드려요.
                </p>
                <div class="empty-actions">
                    <Button variant="primary" size="md" href={loginHref}>로그인하고 시작하기 →</Button>
                    <a class="empty-link" href="/races?reset=1">먼저 대회 둘러보기</a>
                </div>
            {/if}
        </div>
    {:else}

    <!-- ── Pending-log banner ─────────────────────────────────────────────── -->
    {#if pending.length > 0}
        {@const p = pending[0]}
        <div class="pending">
            <Badge status="closing">기록 대기</Badge>
            <span style="font-size: 14px;">
                <b>{p.name}</b>이(가) 끝난 지 {todayDoy - dayOfYear(p.month, p.day)}일 — 완주 기록을 남겨두면
                도구·예측에 반영됩니다.
            </span>
            <span style="margin-left: auto;">
                <Button variant="primary" size="sm" onclick={() => openLog(p)}>기록 남기기</Button>
            </span>
        </div>
    {/if}

    <!-- ── Year strip (gantt) ─────────────────────────────────────────────── -->
    <div class="strip-wrap">
        <div class="strip-head">
            <span class="eh-micro"><span class="acc">JAN — DEC</span> · 대회 {seasonRaces.length}개</span>
            <span class="eh-micro" style="color: var(--text-faint);">
                오늘 {todayMonth}.{todayDay} · 시즌 {Math.round(todayPct)}% 경과
            </span>
        </div>

        <div class="strip">
            <div class="strip-months">
                {#each months as m (m.m)}
                    <span style="left: {monthLeft(m.m)}%; width: {monthWidth(m.m)}%">{m.label}</span>
                {/each}
            </div>
            <div class="strip-body">
                {#each months.slice(1) as m (m.m)}
                    <div class="strip-gridline" style="left: {monthLeft(m.m)}%"></div>
                {/each}
                <div class="strip-today" style="left: {todayPct}%">
                    <span class="lbl">TODAY</span>
                </div>
                {#each seasonRaces as r, i (r.id)}
                    {@const lane = i % 3}
                    <button
                        class="race-pin {ST[r.userStatus]}"
                        class:goal={r.mainGoal}
                        class:sel={sel === r.id}
                        style="left: {pct(r.month, r.day)}%; top: {14 + lane * 38}px"
                        onclick={() => toggle(r.id)}
                        title={r.name}
                    >
                        <span class="mk"></span>
                        <span class="nm">{r.name}</span>
                    </button>
                {/each}
            </div>
        </div>

        <!-- Mobile vertical rail (replaces the gantt below 768px) -->
        <div class="mstrip">
            {#each railItems as item, i (i)}
                {#if item.kind === 'today'}
                    <div class="mtoday">
                        <span class="tdate eh-data">{todayMonth}.{todayDay}</span>
                        <span class="mrail"><span class="tdot"></span></span>
                        <span class="tpill">TODAY</span>
                    </div>
                {:else if item.kind === 'month'}
                    <div class="mmonth">
                        <span></span>
                        <span class="mrail"><span class="mtick"></span></span>
                        <span class="mlbl eh-micro">{item.label}</span>
                    </div>
                {:else}
                    {@render mnode(item.race)}
                {/if}
            {/each}
        </div>

        <div class="legend">
            <span><span class="mk going"></span>참가 예정</span>
            <span><span class="mk maybe"></span>관심</span>
            <span><span class="mk logged"></span>완주 기록</span>
            <span><span class="mk unknown"></span>미확인</span>
            <span style="margin-left: auto; color: var(--text-faint);">◆ 더블 사이즈 = 시즌 메인 목표</span>
        </div>
    </div>

    <!-- ── Upcoming ───────────────────────────────────────────────────────── -->
    <section class="sec">
        <div class="sechead">
            <div class="sechead-l">
                <span class="eh-micro eh-data acc">01</span>
                <h2>다가오는 대회</h2>
            </div>
            <span class="eh-micro" style="color: var(--text-faint);">{upcoming.length} RACES</span>
        </div>
        <div class="rows">
            {#each upcoming as r (r.id)}
                {@render row(r)}
            {:else}
                <p class="empty">다가오는 관심 대회가 없습니다. <a href="/races?reset=1">대회 둘러보기 →</a></p>
            {/each}
        </div>
    </section>

    <!-- ── Past ───────────────────────────────────────────────────────────── -->
    {#if past.length > 0}
        <section class="sec">
            <div class="sechead">
                <div class="sechead-l">
                    <span class="eh-micro eh-data acc">02</span>
                    <h2>지난 대회</h2>
                </div>
                <span class="eh-micro" style="color: var(--text-faint);">{past.length} RACES</span>
            </div>
            <div class="rows">
                {#each past as r (r.id)}
                    {@render row(r)}
                {/each}
            </div>
        </section>
        {/if}
    {/if}
</main>

<!-- ── Race row snippet ───────────────────────────────────────────────────── -->
{#snippet row(r: SeasonRace)}
    {@const ddl = deadlineInfo(r)}
    <div
        class="rrow"
        class:goal={r.mainGoal}
        class:sel={sel === r.id}
        onclick={() => toggle(r.id)}
        role="button"
        tabindex="0"
        onkeydown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggle(r.id);
            }
        }}
    >
        <div class="dt">
            <span class="eh-data">{months[r.month - 1].label}</span>
            <b class="eh-data">{r.month}.{String(r.day).padStart(2, '0')}</b>
        </div>
        <div style="min-width: 0;">
            <div class="nm">
                {r.name}
                <span style="color: var(--text-faint); font-weight: 500; font-size: 13px;">{r.region}</span>
            </div>
            <div class="sub">
                <span class="codes">
                    {#each r.courses as c (c.code)}
                        <span class="code eh-data" class:planned={isPlanned(r, c.code)}>{c.label}</span>
                    {/each}
                </span>
                {#if r.note}<span>· {r.note}</span>{/if}
                {#if r.result}
                    <span class="result-line eh-data">
                        {#if loggedCourseLabel(r)}<b>{loggedCourseLabel(r)}</b> · {/if}{r.result.time}{#if r.result.pace} ({r.result.pace}){/if}{r.result.pb ? ' · PB' : ''}
                    </span>
                {/if}
            </div>
        </div>
        <div class="right">
            {#if r.userStatus === 'logged'}
                <span class="logged-chip">완주 기록</span>
            {:else if r.userStatus === 'confirmed_going'}
                <Badge status="open">참가 예정</Badge>
            {:else if r.userStatus === 'maybe'}
                <Badge status="upcoming">관심</Badge>
            {:else}
                <Badge status="closed">미확인</Badge>
            {/if}

            {#if ddl}
                <span class="ddl eh-data" class:warn={ddl.warn}>{ddl.text}</span>
            {/if}
            {#if !isPast(r) && r.userStatus !== 'logged'}
                <span onclick={(e) => e.stopPropagation()}>
                    {#if r.userStatus === 'confirmed_going'}
                        <Button variant="ghost" size="sm" disabled={partBusy === r.slug} onclick={() => setParticipation(r, 'maybe')}>관심으로</Button>
                    {:else}
                        <Button variant="secondary" size="sm" disabled={partBusy === r.slug} onclick={() => setParticipation(r, 'confirmed_going')}>참가 예정으로</Button>
                    {/if}
                </span>
            {/if}
            {#if isPast(r)}
                <span onclick={(e) => e.stopPropagation()}>
                    {#if r.userStatus === 'logged'}
                        <Button variant="ghost" size="sm" onclick={() => openLog(r)}>기록 수정</Button>
                    {:else}
                        <Button variant="secondary" size="sm" onclick={() => openLog(r)}>기록 입력</Button>
                    {/if}
                </span>
            {/if}
        </div>
    </div>
{/snippet}

<!-- ── Mobile rail node snippet ────────────────────────────────────────────── -->
{#snippet mnode(r: SeasonRace)}
    {@const ddl = deadlineInfo(r)}
    <button
        class="mnode {ST[r.userStatus]}"
        class:goal={r.mainGoal}
        class:sel={sel === r.id}
        onclick={() => toggle(r.id)}
        title={r.name}
    >
        <span class="mdate eh-data">{r.month}.{String(r.day).padStart(2, '0')}</span>
        <span class="mrail"><span class="mk"></span></span>
        <span class="mbody">
            <span class="mname">{r.name}</span>
            <span class="mmeta">
                {#if r.region}<span>{r.region}</span>{/if}
                {#if r.mainGoal}<span class="goaltag">메인 목표</span>{/if}
                {#if ddl}<span class="ddl eh-data" class:warn={ddl.warn}>{ddl.text}</span>{/if}
                {#if r.result}<span class="mresult eh-data">{r.result.time}</span>{/if}
            </span>
        </span>
    </button>
{/snippet}

<!-- ── 완주 기록 입력 / 수정 모달 ──────────────────────────────────────────── -->
<Modal bind:open={logOpen} maxWidth="440px" onclose={closeLog}>
    {#if logRace}
        <div class="log">
            <div class="eh-micro acc">{isEditing ? 'EDIT RESULT' : 'LOG RESULT'}</div>
            <h2 class="log-title">{logRace.name}</h2>
            <p class="log-sub eh-data">
                {months[logRace.month - 1].label} {logRace.month}.{String(logRace.day).padStart(2, '0')}
                {#if logRace.region} · {logRace.region}{/if}
            </p>

            <!-- 종목 -->
            <div class="log-field">
                <label class="log-label" for="log-course">종목</label>
                <div class="log-courses" id="log-course">
                    {#each logRace.courses as c (c.code)}
                        <button
                            type="button"
                            class="log-chip"
                            class:on={logCode === c.code}
                            onclick={() => (logCode = c.code)}
                        >
                            {c.label}
                        </button>
                    {/each}
                </div>
            </div>

            <!-- 시간 -->
            <div class="log-field">
                <span class="log-label">기록 시간</span>
                <div class="log-time">
                    <input class="log-num eh-data" type="number" min="0" max="99" inputmode="numeric"
                        placeholder="시" aria-label="시간" bind:value={logH} />
                    <span class="log-colon">:</span>
                    <input class="log-num eh-data" type="number" min="0" max="59" inputmode="numeric"
                        placeholder="분" aria-label="분" bind:value={logM} />
                    <span class="log-colon">:</span>
                    <input class="log-num eh-data" type="number" min="0" max="59" inputmode="numeric"
                        placeholder="초" aria-label="초" bind:value={logS} />
                </div>
            </div>

            <label class="log-pb">
                <input type="checkbox" bind:checked={logPb} />
                <span>개인 최고 기록 (PB)</span>
            </label>

            {#if logError}
                <p class="log-err">{logError}</p>
            {/if}

            <div class="log-actions">
                {#if isEditing}
                    <Button variant="ghost" size="md" disabled={logBusy} onclick={deleteLog}>삭제</Button>
                {/if}
                <span class="log-spacer"></span>
                <Button variant="secondary" size="md" disabled={logBusy} onclick={closeLog}>취소</Button>
                <Button variant="primary" size="md" disabled={logBusy} onclick={submitLog}>
                    {logBusy ? '저장 중…' : isEditing ? '수정' : '저장'}
                </Button>
            </div>
        </div>
    {/if}
</Modal>

<style>
    /* ════════════════════════════════════════════════════════════════════
       Season Timeline — recreated from the v2 "Season Timeline" prototype.
       All colours come from eh-tokens.css. No hardcoded hex.
       ════════════════════════════════════════════════════════════════════ */

    .tl {
        padding-bottom: var(--sp-16);
    }
    .acc {
        color: var(--text-accent);
    }

    /* ── Empty state (로그인 유도 / 빈 시즌) ──────────────────────────────── */
    .empty-state {
        margin-top: 28px;
        border: 1px solid var(--ink-900);
        background: var(--paper-0);
        padding: 56px 40px;
        text-align: center;
    }
    .empty-state h2 {
        margin-top: 10px;
        font-size: clamp(22px, 3vw, 30px);
        font-weight: var(--w-display);
        letter-spacing: var(--track-display);
        line-height: var(--leading-heading);
        color: var(--text-strong);
    }
    .empty-state p {
        max-width: 46ch;
        margin: 12px auto 0;
        font-size: var(--text-caption);
        line-height: 1.7;
        color: var(--text-muted);
    }
    .empty-actions {
        margin-top: 26px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 18px;
        flex-wrap: wrap;
    }
    .empty-link {
        font-size: var(--text-caption);
        font-weight: 600;
        color: var(--text-muted);
        text-decoration: none;
        border-bottom: 1px solid transparent;
    }
    .empty-link:hover {
        color: var(--text-strong);
        border-bottom-color: var(--ink-900);
    }

    /* ── Header ──────────────────────────────────────────────────────────── */
    .hd {
        padding: 40px 0 0;
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 20px;
        flex-wrap: wrap;
    }
    .hd h1 {
        font-size: clamp(34px, 4.5vw, 52px);
        font-weight: var(--w-display);
        letter-spacing: var(--track-display);
        line-height: var(--leading-display);
        margin-top: 8px;
        color: var(--text-strong);
    }
    .hd-stats {
        display: flex;
        gap: 36px;
        flex-wrap: wrap;
    }

    /* ── Pending banner ──────────────────────────────────────────────────── */
    .pending {
        display: flex;
        align-items: center;
        gap: 14px;
        flex-wrap: wrap;
        border: 1px solid var(--ink-900);
        background: var(--accent-tint);
        padding: 14px 18px;
        margin-top: 26px;
    }
    .pending b {
        font-weight: 700;
    }

    /* ── Year strip (gantt) ──────────────────────────────────────────────── */
    .strip-wrap {
        margin-top: 32px;
        border-top: var(--border-rule);
        padding-top: 14px;
    }
    .strip-head {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        flex-wrap: wrap;
        gap: 8px;
    }
    .strip {
        position: relative;
        border: 1px solid var(--line);
        background: var(--paper-0);
        margin-top: 12px;
    }
    .strip-months {
        position: relative;
        height: 33px;
        border-bottom: var(--border-hair);
    }
    .strip-months span {
        position: absolute;
        top: 0;
        height: 100%;
        box-sizing: border-box;
        padding: 8px 0 0 8px;
        font-size: var(--text-micro);
        font-weight: var(--w-strong);
        letter-spacing: var(--track-micro);
        color: var(--text-muted);
        border-left: 1px solid var(--line);
        overflow: hidden;
        white-space: nowrap;
    }
    .strip-months span:first-child {
        border-left: 0;
    }
    .strip-body {
        position: relative;
        height: 132px;
    }
    .strip-gridline {
        position: absolute;
        top: 0;
        bottom: 0;
        width: 1px;
        background: var(--line);
    }
    .strip-today {
        position: absolute;
        top: -33px;
        bottom: 0;
        width: 2px;
        background: var(--accent);
        z-index: 3;
    }
    .strip-today .lbl {
        position: absolute;
        top: 0;
        left: 6px;
        font-size: 9px;
        font-weight: 800;
        letter-spacing: 0.08em;
        color: #fff;
        background: var(--accent);
        padding: 2px 6px;
        white-space: nowrap;
    }
    .race-pin {
        position: absolute;
        transform: translateX(-50%);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        background: none;
        border: 0;
        padding: 0;
        cursor: pointer;
        z-index: 2;
    }
    .race-pin .mk {
        width: 12px;
        height: 12px;
        border: 1.5px solid var(--ink-900);
        background: var(--paper-0);
        transform: rotate(45deg);
        transition: transform var(--dur-fast) var(--ease-out);
    }
    .race-pin.going .mk {
        background: var(--accent);
        border-color: var(--accent-strong);
    }
    .race-pin.logged .mk {
        background: var(--ink-900);
    }
    .race-pin.maybe .mk {
        border-style: dashed;
        border-color: var(--ink-400);
    }
    .race-pin.unknown .mk {
        border-color: var(--ink-300);
        background: var(--paper-100);
    }
    .race-pin.goal .mk {
        width: 15px;
        height: 15px;
        box-shadow: 0 0 0 3px var(--accent-tint);
    }
    .race-pin:hover .mk,
    .race-pin.sel .mk {
        transform: rotate(45deg) scale(1.25);
    }
    .race-pin .nm {
        font-size: 10px;
        font-weight: 600;
        color: var(--text-muted);
        white-space: nowrap;
        max-width: 86px;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .race-pin.sel .nm,
    .race-pin:hover .nm {
        color: var(--text-strong);
        font-weight: 700;
    }

    .legend {
        display: flex;
        gap: 18px;
        margin-top: 10px;
        flex-wrap: wrap;
    }
    .legend span {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        font-size: 12px;
        color: var(--text-muted);
    }
    .legend .mk {
        width: 9px;
        height: 9px;
        border: 1.5px solid var(--ink-900);
        background: var(--paper-0);
        transform: rotate(45deg);
        flex: none;
    }
    .legend .mk.going {
        background: var(--accent);
        border-color: var(--accent-strong);
    }
    .legend .mk.logged {
        background: var(--ink-900);
    }
    .legend .mk.maybe {
        border-style: dashed;
        border-color: var(--ink-400);
    }
    .legend .mk.unknown {
        border-color: var(--ink-300);
        background: var(--paper-100);
    }

    /* ── Sections ────────────────────────────────────────────────────────── */
    .sec {
        margin-top: 40px;
    }
    .sechead {
        border-top: var(--border-rule);
        padding-top: var(--sp-3);
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: var(--sp-4);
        flex-wrap: wrap;
    }
    .sechead-l {
        display: flex;
        align-items: baseline;
        gap: 12px;
    }
    .sechead-l .acc {
        color: var(--text-accent);
    }
    .sechead h2 {
        font-size: var(--text-h3);
        font-weight: var(--w-strong);
        letter-spacing: var(--track-heading);
        color: var(--text-strong);
    }
    .rows {
        margin-top: 4px;
    }
    .empty {
        padding: 28px 4px;
        color: var(--text-muted);
        font-size: var(--text-caption);
    }
    .empty a {
        color: var(--accent-strong);
        text-decoration: none;
        font-weight: 600;
    }

    /* ── Race rows ───────────────────────────────────────────────────────── */
    .rrow {
        display: grid;
        grid-template-columns: 86px 1fr auto;
        gap: 18px;
        align-items: center;
        padding: 16px 4px;
        border-bottom: var(--border-hair);
        cursor: pointer;
        transition: background var(--dur-fast) var(--ease-out);
    }
    .rrow:hover {
        background: var(--paper-50);
    }
    .rrow.sel {
        background: var(--accent-tint);
    }
    .rrow.goal {
        border-left: 3px solid var(--accent);
        padding-left: 12px;
    }
    .rrow .dt b {
        display: block;
        font-size: 20px;
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.05;
        color: var(--text-strong);
    }
    .rrow .dt span {
        font-size: 11px;
        color: var(--text-faint);
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    .rrow .nm {
        font-size: 16px;
        font-weight: 700;
        letter-spacing: var(--track-heading);
        color: var(--text-strong);
    }
    .rrow .sub {
        display: flex;
        gap: 10px;
        margin-top: 5px;
        font-size: 12.5px;
        color: var(--text-muted);
        flex-wrap: wrap;
        align-items: center;
    }
    .rrow .sub .codes {
        display: inline-flex;
        gap: 4px;
    }
    .rrow .sub .code {
        font-size: 10.5px;
        font-weight: 700;
        padding: 1px 6px;
        border: 1px solid var(--line);
        color: var(--text-muted);
        border-radius: var(--r-2);
    }
    .rrow .sub .code.planned {
        border-color: var(--ink-900);
        color: var(--text-strong);
    }
    .rrow .right {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 6px;
    }
    .rrow .ddl {
        font-size: 11.5px;
        color: var(--text-faint);
    }
    .rrow .ddl.warn {
        color: var(--caution);
        font-weight: 700;
    }
    .logged-chip {
        display: inline-flex;
        align-items: center;
        height: 24px;
        padding: 0 9px;
        gap: 6px;
        background: var(--ink-900);
        color: var(--paper-0);
        font-size: 12px;
        font-weight: 600;
        border-radius: var(--r-2);
    }
    .result-line {
        font-size: 12.5px;
        color: var(--text-accent);
        font-weight: 700;
    }

    /* ── Mobile vertical timeline rail ───────────────────────────────────────
       Hidden on desktop; the @media block below swaps the gantt strip for this
       continuous vertical rail with month dividers and a TODAY marker. */
    .mstrip {
        display: none;
    }
    .mnode,
    .mmonth,
    .mtoday {
        display: grid;
        grid-template-columns: 44px 22px minmax(0, 1fr);
        gap: 12px;
        width: 100%;
        text-align: left;
        background: none;
        border: 0;
        padding: 0;
        font-family: inherit;
    }
    .mnode {
        cursor: pointer;
        align-items: stretch;
        transition: background var(--dur-fast) var(--ease-out);
    }
    .mnode:hover {
        background: var(--paper-50);
    }
    .mnode.sel {
        background: var(--accent-tint);
    }
    .mrail {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .mrail::before {
        content: '';
        position: absolute;
        top: 0;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 2px;
        background: var(--line);
    }
    .mnode .mdate {
        align-self: center;
        text-align: right;
        font-size: 14px;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: var(--text-strong);
        padding: 14px 0;
    }
    .mnode .mk {
        position: relative;
        z-index: 1;
        width: 12px;
        height: 12px;
        border: 1.5px solid var(--ink-900);
        background: var(--paper-0);
        transform: rotate(45deg);
        transition: transform var(--dur-fast) var(--ease-out);
    }
    .mnode.sel .mk,
    .mnode:active .mk {
        transform: rotate(45deg) scale(1.2);
    }
    .mnode.going .mk {
        background: var(--accent);
        border-color: var(--accent-strong);
    }
    .mnode.logged .mk {
        background: var(--ink-900);
    }
    .mnode.maybe .mk {
        border-style: dashed;
        border-color: var(--ink-400);
    }
    .mnode.unknown .mk {
        border-color: var(--ink-300);
        background: var(--paper-100);
    }
    .mnode.goal .mk {
        width: 16px;
        height: 16px;
        box-shadow: 0 0 0 3px var(--accent-tint);
    }
    .mnode .mbody {
        align-self: center;
        min-width: 0;
        padding: 11px 10px 11px 0;
        display: flex;
        flex-direction: column;
        gap: 3px;
    }
    .mnode .mname {
        font-size: 15px;
        font-weight: 700;
        letter-spacing: var(--track-heading);
        line-height: 1.2;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: var(--text-strong);
    }
    .mnode .mmeta {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        font-size: 11.5px;
        color: var(--text-faint);
        font-weight: 600;
    }
    .mnode .mmeta .goaltag {
        color: var(--text-accent);
        font-weight: 700;
    }
    .mnode .mmeta .ddl.warn {
        color: var(--caution);
        font-weight: 700;
    }
    .mnode .mmeta .mresult {
        color: var(--text-accent);
        font-weight: 700;
    }
    /* month divider */
    .mmonth {
        align-items: center;
    }
    .mmonth .mtick {
        position: relative;
        z-index: 1;
        width: 12px;
        height: 2px;
        background: var(--ink-300);
    }
    .mmonth .mlbl {
        padding: 9px 0;
        color: var(--text-faint);
    }
    /* today divider */
    .mtoday {
        align-items: center;
    }
    .mtoday .tdate {
        text-align: right;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: -0.01em;
        color: var(--accent);
        align-self: center;
    }
    .mtoday .mrail::before {
        background: var(--accent);
    }
    .mtoday .tdot {
        position: relative;
        z-index: 1;
        width: 13px;
        height: 13px;
        border-radius: 50%;
        background: var(--accent);
        box-shadow: 0 0 0 3px var(--accent-tint);
    }
    .mtoday .tpill {
        align-self: center;
        justify-self: start;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.08em;
        color: #fff;
        background: var(--accent);
        padding: 3px 8px;
    }

    /* ── 기록 입력 모달 ──────────────────────────────────────────────────── */
    .log {
        padding: 26px 28px 24px;
    }
    .log .acc {
        color: var(--text-accent);
    }
    .log-title {
        margin-top: 8px;
        font-size: 20px;
        font-weight: var(--w-strong);
        letter-spacing: var(--track-heading);
        line-height: 1.25;
        color: var(--text-strong);
    }
    .log-sub {
        margin-top: 4px;
        font-size: 12px;
        color: var(--text-faint);
    }
    .log-field {
        margin-top: 20px;
    }
    .log-label {
        display: block;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: var(--track-micro);
        color: var(--text-muted);
        margin-bottom: 8px;
    }
    .log-courses {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }
    .log-chip {
        padding: 6px 12px;
        font-size: 13px;
        font-weight: 600;
        border: 1px solid var(--line);
        background: var(--paper-0);
        color: var(--text-muted);
        border-radius: var(--r-2);
        cursor: pointer;
        transition: all var(--dur-fast) var(--ease-out);
    }
    .log-chip:hover {
        border-color: var(--ink-400);
        color: var(--text-strong);
    }
    .log-chip.on {
        border-color: var(--accent-strong);
        background: var(--accent);
        color: #fff;
    }
    .log-time {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .log-num {
        width: 64px;
        padding: 9px 10px;
        font-size: 16px;
        font-weight: 700;
        text-align: center;
        border: 1px solid var(--line);
        background: var(--paper-0);
        color: var(--text-strong);
        border-radius: var(--r-2);
    }
    .log-num:focus {
        outline: none;
        border-color: var(--accent-strong);
    }
    .log-colon {
        font-weight: 700;
        color: var(--text-faint);
    }
    .log-pb {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 18px;
        font-size: 13px;
        color: var(--text-muted);
        cursor: pointer;
    }
    .log-pb input {
        width: 16px;
        height: 16px;
        accent-color: var(--accent);
    }
    .log-err {
        margin-top: 14px;
        font-size: 12.5px;
        font-weight: 600;
        color: var(--caution);
    }
    .log-actions {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 24px;
    }
    .log-spacer {
        flex: 1;
    }

    @media (max-width: 768px) {
        .hd {
            padding-top: 22px;
        }
        /* Swap the horizontal gantt for the vertical rail — far more legible
           on a narrow viewport than a squeezed 12-month strip. */
        .strip {
            display: none;
        }
        .mstrip {
            display: block;
            margin-top: 14px;
        }
        .rrow {
            grid-template-columns: 64px 1fr;
        }
        .rrow .right {
            grid-column: 2;
            flex-direction: row;
            align-items: center;
            justify-content: flex-start;
            flex-wrap: wrap;
        }
        .rrow .dt b {
            font-size: 17px;
        }
    }
</style>
