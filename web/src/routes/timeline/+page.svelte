<script lang="ts">
    import type { Race, Distance } from '$lib/types';
    import { arenaSportCode } from '$lib/arena';

    let { data } = $props();

    type SeasonStatus = 'confirmed_going' | 'maybe' | 'unknown' | 'logged';

    interface SeasonCourse {
        code: string;
        label: string;
        distKm: number;
    }

    interface SeasonRace {
        id: string;
        slug: string;
        name: string;
        url: string;
        region: string;
        date: string; // YYYY-MM-DD
        month: number;
        day: number;
        sport: string;
        courses: SeasonCourse[];
        deadline: { m: number; day: number } | null;
        userStatus: SeasonStatus;
        plannedCodes?: string[];
        recentlyPassed?: boolean;
        mainGoal?: boolean;
        note?: string;
    }

    const today = new Date();
    const year = today.getFullYear();
    const todayMonth = today.getMonth() + 1;
    const todayDay = today.getDate();

    const months = [
        { m: 1, label: 'JAN', kr: '1월', days: 31 },
        { m: 2, label: 'FEB', kr: '2월', days: 28 + (year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0) ? 1 : 0) },
        { m: 3, label: 'MAR', kr: '3월', days: 31 },
        { m: 4, label: 'APR', kr: '4월', days: 30 },
        { m: 5, label: 'MAY', kr: '5월', days: 31 },
        { m: 6, label: 'JUN', kr: '6월', days: 30 },
        { m: 7, label: 'JUL', kr: '7월', days: 31 },
        { m: 8, label: 'AUG', kr: '8월', days: 31 },
        { m: 9, label: 'SEP', kr: '9월', days: 30 },
        { m: 10, label: 'OCT', kr: '10월', days: 31 },
        { m: 11, label: 'NOV', kr: '11월', days: 30 },
        { m: 12, label: 'DEC', kr: '12월', days: 31 },
    ];

    const totalDays = months.reduce((acc, m) => acc + m.days, 0);
    const cumDays = (() => {
        const out: number[] = [0];
        for (const m of months) out.push(out[out.length - 1] + m.days);
        return out;
    })();

    function dayOfYear(m: number, d: number): number {
        return cumDays[Math.max(0, m - 1)] + d;
    }
    function yearProgress(m: number, d: number): number {
        return Math.max(0, Math.min(1, dayOfYear(m, d) / totalDays));
    }

    function distanceCode(d: Distance): string {
        if (d.distance_meter && d.distance_meter > 0) {
            const km = d.distance_meter / 1000;
            if (Number.isInteger(km)) return `${km}K`;
            return `${km.toFixed(1)}K`;
        }
        return d.name.slice(0, 4).toUpperCase();
    }

    function distanceKm(d: Distance): number {
        if (d.distance_meter && d.distance_meter > 0) return d.distance_meter / 1000;
        const m = d.name.match(/(\d+(?:\.\d+)?)/);
        return m ? Number(m[1]) : 0;
    }

    function parseDate(d: string | null): { m: number; day: number; year: number } | null {
        if (!d) return null;
        const parts = d.split('-');
        if (parts.length < 3) return null;
        return { year: Number(parts[0]), m: Number(parts[1]), day: Number(parts[2]) };
    }

    function deriveStatus(race: Race): {
        status: SeasonStatus;
        recentlyPassed: boolean;
    } {
        const raceDate = parseDate(race.raceDate);
        if (!raceDate) return { status: 'maybe', recentlyPassed: false };
        const raceDt = new Date(raceDate.year, raceDate.m - 1, raceDate.day);
        const diffDays = Math.floor((raceDt.getTime() - today.getTime()) / 86400000);
        if (diffDays < -14) return { status: 'unknown', recentlyPassed: false };
        if (diffDays < 0) return { status: 'unknown', recentlyPassed: true };
        return { status: 'maybe', recentlyPassed: false };
    }

    const seasonRaces: SeasonRace[] = $derived(
        (data.races as Race[])
            .map((race): SeasonRace | null => {
                const rd = parseDate(race.raceDate);
                if (!rd || rd.year !== year) return null;
                const reg = parseDate(race.registrationEnd);
                const courses: SeasonCourse[] = (race.distances ?? []).slice(0, 4).map((d) => ({
                    code: distanceCode(d),
                    label: d.name,
                    distKm: distanceKm(d),
                }));
                if (courses.length === 0) {
                    courses.push({ code: arenaSportCode[race.sport], label: race.sportLabel, distKm: 0 });
                }
                const { status, recentlyPassed } = deriveStatus(race);
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
                    userStatus: status,
                    recentlyPassed,
                };
            })
            .filter((r): r is SeasonRace => r !== null)
            .sort((a, b) => a.date.localeCompare(b.date)),
    );

    const stats = $derived(() => {
        const now = today.getTime();
        const upcoming = seasonRaces.filter((r) => {
            const dt = new Date(r.date).getTime();
            return dt >= now;
        });
        const next = upcoming[0];
        const nextDays = next
            ? Math.max(0, Math.ceil((new Date(next.date).getTime() - now) / 86400000))
            : null;
        const goingCount = seasonRaces.filter((r) => r.userStatus === 'confirmed_going').length;
        const maybeCount = seasonRaces.filter((r) => r.userStatus === 'maybe').length;
        const loggedCount = seasonRaces.filter((r) => r.userStatus === 'logged').length;
        const pendingCount = seasonRaces.filter((r) => r.recentlyPassed).length;
        const main = seasonRaces.find((r) => r.mainGoal) ?? upcoming[upcoming.length - 1];
        const mainDays = main
            ? Math.max(0, Math.ceil((new Date(main.date).getTime() - now) / 86400000))
            : null;
        return {
            totalRaces: seasonRaces.length,
            confirmedGoing: goingCount,
            maybe: maybeCount,
            logged: loggedCount,
            pendingLogs: pendingCount,
            nextRaceDays: nextDays,
            nextRaceName: next?.name ?? '—',
            mainGoal: main?.name ?? '—',
            mainGoalDays: mainDays,
        };
    });

    const pendingLogs = $derived(seasonRaces.filter((r) => r.recentlyPassed));

    let openId = $state<string | null>(null);
    let bannerDismissed = $state(false);

    function toggleOpen(id: string) {
        openId = openId === id ? null : id;
    }

    // Layout constants
    const LEFT_W = 240;
    const RIGHT_W = 200;
    const CHART_W = 1180;
    const TOTAL_W = LEFT_W + CHART_W + RIGHT_W;

    const xOf = (m: number, d: number) => yearProgress(m, d) * CHART_W;
    const nowX = $derived(xOf(todayMonth, todayDay));

    function statusBadgeClass(s: SeasonStatus): string {
        return `badge-${s}`;
    }

    function statusBadgeLabel(s: SeasonStatus): string {
        switch (s) {
            case 'confirmed_going':
                return 'GO';
            case 'logged':
                return '✓';
            case 'maybe':
                return '?';
            case 'unknown':
                return '—';
        }
    }

    function rowHeight(courses: SeasonCourse[]): number {
        const COURSE_H = 11;
        const COURSE_GAP = 3;
        const block = courses.length * COURSE_H + (courses.length - 1) * COURSE_GAP;
        return Math.max(76, block + 36);
    }

    function isHighlight(race: SeasonRace, code: string): boolean {
        if (race.userStatus === 'confirmed_going' && race.plannedCodes?.includes(code)) return true;
        if (race.userStatus === 'logged' && code === race.plannedCodes?.[0]) return true;
        return false;
    }

    const sourceLabel = $derived(data.source === 'favorites' ? '관심 대회' : '추천 대회');
</script>

<svelte:head>
    <title>내 시즌 타임라인 — 엔듀로허브</title>
    <meta name="description" content="관심 대회를 한눈에 보는 연간 타임라인" />
    <meta name="robots" content="noindex" />
</svelte:head>

<div class="page">
    <div class="head">
        <div class="arena-kicker">My Season · {year}</div>
        <h1 class="title">내 대회 달력 · {stats().totalRaces}개 이벤트</h1>
        <p class="sub">
            {#if data.source === 'favorites'}
                관심 표시한 대회들 · 참가 여부와 기록은 직접 남겨주세요
            {:else if data.isAuthed}
                아직 관심 대회가 없습니다 · 다가오는 대회 샘플로 보여드려요
            {:else}
                <a href="/auth/login?next=%2Ftimeline" class="login-link">로그인</a>해서 내 관심
                대회로 채워보세요 · 지금은 다가오는 대회 샘플
            {/if}
        </p>

        <div class="stat-row">
            <div class="stat-cell">
                <div class="stat-label">참가 예정</div>
                <div class="stat-val">{stats().confirmedGoing}</div>
                <div class="stat-sub">종목까지 확정</div>
            </div>
            <div class="stat-cell">
                <div class="stat-label">관심</div>
                <div class="stat-val">{stats().maybe}</div>
                <div class="stat-sub">종목 미정</div>
            </div>
            <div class="stat-cell">
                <div class="stat-label">다음 레이스</div>
                <div class="stat-val">{stats().nextRaceDays != null ? `D-${stats().nextRaceDays}` : '—'}</div>
                <div class="stat-sub" title={stats().nextRaceName}>
                    {stats().nextRaceName.length > 16
                        ? stats().nextRaceName.slice(0, 16) + '…'
                        : stats().nextRaceName}
                </div>
            </div>
            <div class="stat-cell">
                <div class="stat-label">메인 목표</div>
                <div class="stat-val small" title={stats().mainGoal}>
                    {stats().mainGoal.length > 14
                        ? stats().mainGoal.slice(0, 14) + '…'
                        : stats().mainGoal}
                </div>
                <div class="stat-sub">{stats().mainGoalDays != null ? `D-${stats().mainGoalDays}` : '—'}</div>
            </div>
            <div class="stat-cell stat-cell-pending" class:active={pendingLogs.length > 0}>
                <div class="stat-label">기록 미입력</div>
                <div class="stat-val">{stats().pendingLogs}</div>
                <div class="stat-sub">지난 대회</div>
            </div>
        </div>

        {#if pendingLogs.length > 0 && !bannerDismissed}
            <div class="banner">
                <span class="banner-bang">!</span>
                <div>
                    <div class="banner-kicker">Log your race · 최근 대회</div>
                    <div class="banner-title">
                        '{pendingLogs[0].name}' 참가하셨나요? 기록을 남겨두면 내년 계획에 활용할 수
                        있어요
                    </div>
                </div>
                <a href={pendingLogs[0].url} class="banner-cta">대회 상세 →</a>
                <button class="banner-dismiss" onclick={() => (bannerDismissed = true)}>나중에</button>
            </div>
        {/if}
    </div>

    {#if seasonRaces.length === 0}
        <div class="empty-frame">
            <div class="empty-inner">
                <div class="arena-kicker">No Events</div>
                <h2 class="empty-title">{year}년에 등록한 관심 대회가 없습니다</h2>
                <p class="empty-desc">관심 있는 대회의 ♥ 버튼을 눌러 시즌을 채워보세요.</p>
                <a href="/races?reset=1" class="arena-btn arena-btn-primary">대회 둘러보기 →</a>
            </div>
        </div>
    {:else}
        <div class="chart-wrap">
            <div class="chart-frame">
                <div class="chart-inner" style="width: {TOTAL_W}px">
                    <!-- Month axis -->
                    <div class="month-axis" style="grid-template-columns: {LEFT_W}px 1fr {RIGHT_W}px">
                        <div class="axis-side">RACE</div>
                        <div class="axis-center">
                            {#each months as m (m.m)}
                                <div
                                    class="axis-month"
                                    class:current={m.m === todayMonth}
                                    style="left: {xOf(m.m, 1)}px; width: {(m.days / totalDays) *
                                        CHART_W}px"
                                >
                                    {m.label}
                                </div>
                            {/each}
                            <div class="axis-now-label" style="left: {nowX}px">
                                NOW · {todayMonth}/{todayDay}
                            </div>
                        </div>
                        <div class="axis-side right">STATUS · COURSES</div>
                    </div>

                    <!-- Rows -->
                    <div class="rows">
                        <div class="now-line" style="left: {LEFT_W + nowX}px"></div>

                        {#each seasonRaces as race, idx (race.id)}
                            {@const isOpen = openId === race.id}
                            {@const status = race.userStatus}
                            {@const isUnknown = status === 'unknown'}
                            {@const isMaybe = status === 'maybe'}
                            {@const isConfirmed = status === 'confirmed_going'}
                            {@const isLogged = status === 'logged'}
                            {@const raceX = xOf(race.month, race.day)}
                            {@const deadlineX = race.deadline ? xOf(race.deadline.m, race.deadline.day) : raceX - 30}
                            {@const rh = rowHeight(race.courses)}
                            {@const altRow = idx % 2 === 1}
                            <div
                                class="race-row"
                                class:open={isOpen}
                                class:unknown={isUnknown}
                                class:alt={altRow && !isUnknown && !isOpen}
                                style="grid-template-columns: {LEFT_W}px 1fr {RIGHT_W}px"
                            >
                                <button
                                    class="row-toggle"
                                    onclick={() => toggleOpen(race.id)}
                                    aria-expanded={isOpen}
                                    aria-label={`${race.name} 상세 ${isOpen ? '닫기' : '열기'}`}
                                ></button>

                                <!-- LEFT -->
                                <div class="cell-left">
                                    <span class="status-badge {statusBadgeClass(status)}"
                                        >{statusBadgeLabel(status)}</span
                                    >
                                    <div class="row-name">
                                        <div class="row-title" class:dim={isUnknown}>
                                            {#if race.mainGoal}<span class="star">★</span>{/if}
                                            <span class="ellipsis">{race.name}</span>
                                        </div>
                                        <div class="row-meta">
                                            {race.region} · {race.month}/{race.day}
                                        </div>
                                    </div>
                                </div>

                                <!-- CENTER -->
                                <div class="cell-center" style="min-height: {rh}px">
                                    <!-- Month grid -->
                                    {#each months as m (m.m)}
                                        <div
                                            class="month-grid-line"
                                            style="left: {xOf(m.m, 1)}px"
                                        ></div>
                                    {/each}

                                    <!-- Registration window -->
                                    {#if deadlineX < raceX && !isUnknown}
                                        <div
                                            class="reg-window"
                                            style="left: {deadlineX}px; width: {Math.max(
                                                raceX - deadlineX,
                                                2,
                                            )}px"
                                        ></div>
                                    {/if}

                                    <!-- Deadline marker -->
                                    {#if race.deadline}
                                        <div class="deadline-line" style="left: {deadlineX}px"></div>
                                    {/if}

                                    <!-- Course bars stacked -->
                                    <div
                                        class="course-stack"
                                        style="top: {(rh - (race.courses.length * 11 + (race.courses.length - 1) * 3)) /
                                            2}px"
                                    >
                                        {#each race.courses as c, j (j)}
                                            {@const hl = isHighlight(race, c.code)}
                                            <div class="course-bar-wrap" style="margin-top: {j === 0 ? 0 : 3}px">
                                                <div
                                                    class="course-bar"
                                                    class:highlight={hl}
                                                    class:unknown-bar={isUnknown && !hl}
                                                    class:maybe-bar={isMaybe && !hl}
                                                    style="left: {deadlineX}px; width: {raceX -
                                                        deadlineX}px"
                                                ></div>
                                                <div
                                                    class="course-label"
                                                    class:hl
                                                    style="left: {deadlineX - 6}px"
                                                >
                                                    {c.code}
                                                </div>
                                            </div>
                                        {/each}
                                    </div>

                                    <!-- Race day diamond -->
                                    <div
                                        class="race-diamond"
                                        class:logged={isLogged}
                                        class:going={isConfirmed}
                                        class:unknown-diamond={isUnknown}
                                        class:maybe-diamond={isMaybe}
                                        style="left: {raceX - 9}px; top: {rh / 2 - 9}px"
                                        title={race.date}
                                    ></div>

                                    <!-- Date label -->
                                    <div
                                        class="date-label"
                                        class:dim={isUnknown}
                                        style="left: {raceX + 16}px; top: {rh / 2 - 8}px"
                                    >
                                        {race.month}/{race.day}
                                        {#if race.recentlyPassed}
                                            <span class="date-tail accent">· 기록 남기기 →</span>
                                        {:else if !isUnknown && race.note}
                                            <span class="date-tail muted">· {race.note}</span>
                                        {/if}
                                    </div>
                                </div>

                                <!-- RIGHT -->
                                <div class="cell-right" class:dim={isUnknown}>
                                    {#if isLogged}
                                        <div class="right-time">
                                            {race.note ?? '—'}
                                        </div>
                                        <div class="right-sub">{race.plannedCodes?.[0] ?? ''}</div>
                                    {:else if isConfirmed && race.plannedCodes}
                                        <div class="right-tag accent">
                                            ● {race.plannedCodes.join(' · ')}
                                        </div>
                                        <div class="right-sub">
                                            {race.courses.length}개 종목 중 {race.plannedCodes.length}개 선택
                                        </div>
                                    {:else if isMaybe}
                                        <div class="right-tag soft">○ 관심 등록</div>
                                        <div class="right-sub">
                                            {race.courses.length}개 종목 · 종목 미정
                                        </div>
                                    {:else}
                                        <div class="right-tag muted">? 참여 미확인</div>
                                        <div class="right-sub">
                                            {race.recentlyPassed ? '기록 남기기 버튼 →' : '지난 대회 · 기록 없음'}
                                        </div>
                                    {/if}
                                </div>

                                {#if isOpen}
                                    <div class="expanded">
                                        <div class="ex-grid">
                                            <div>
                                                <div class="ex-kicker">
                                                    이 대회 제공 종목 ({race.courses.length})
                                                </div>
                                                <div class="ex-courses">
                                                    {#each race.courses as c, j (j)}
                                                        {@const hl = isHighlight(race, c.code)}
                                                        <div class="ex-course" class:hl>
                                                            <span class="ex-code">{c.code}</span>
                                                            <span class="ex-label">{c.label}</span>
                                                            <span class="ex-dist"
                                                                >{c.distKm > 0 ? `${c.distKm}K` : '—'}</span
                                                            >
                                                            <span class="ex-tag" class:hl
                                                                >{hl
                                                                    ? isLogged
                                                                        ? 'LOGGED'
                                                                        : 'PLANNED'
                                                                    : '—'}</span
                                                            >
                                                        </div>
                                                    {/each}
                                                </div>
                                                <div class="ex-note">
                                                    {#if isConfirmed}※ 선택한 종목만 강조 표시됩니다.{/if}
                                                    {#if isMaybe}※ 아직 종목을 정하지 않으셨습니다.{/if}
                                                    {#if isUnknown}※ 저희 사이트는 접수를 받지 않아 어느 종목을 뛰셨는지 알 수 없습니다.{/if}
                                                    {#if isLogged}※ 직접 입력하신 기록입니다.{/if}
                                                </div>
                                            </div>

                                            <div>
                                                <div class="ex-kicker">일정</div>
                                                <div class="ex-card">
                                                    {#if race.deadline}
                                                        <div class="ex-row">
                                                            <span>접수 마감</span>
                                                            <span class="bold"
                                                                >{race.deadline.m}/{race.deadline.day}</span
                                                            >
                                                        </div>
                                                    {/if}
                                                    <div class="ex-row">
                                                        <span>대회일</span>
                                                        <span class="big">{race.month}/{race.day}</span>
                                                    </div>
                                                    <div class="ex-row">
                                                        <span>지역</span>
                                                        <span>{race.region}</span>
                                                    </div>
                                                    {#if race.note}
                                                        <div class="ex-divider"></div>
                                                        <div class="ex-memo">
                                                            <div class="ex-memo-kicker">메모</div>
                                                            <div>{race.note}</div>
                                                        </div>
                                                    {/if}
                                                </div>
                                            </div>

                                            <div>
                                                <div class="ex-kicker">액션</div>
                                                <div class="ex-actions">
                                                    {#if race.recentlyPassed}
                                                        <a href={race.url} class="ex-btn primary">
                                                            <span>기록 남기기</span><span>→</span>
                                                        </a>
                                                    {/if}
                                                    <a href={race.url} class="ex-btn">
                                                        <span>대회 상세</span><span>→</span>
                                                    </a>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                {/if}
                            </div>
                        {/each}
                    </div>

                    <!-- Legend -->
                    <div
                        class="legend"
                        style="grid-template-columns: {LEFT_W}px 1fr {RIGHT_W}px"
                    >
                        <div class="legend-side">LEGEND</div>
                        <div class="legend-items">
                            <span class="legend-item"
                                ><span class="lg-bar solid"></span>참가 예정 (종목 확정)</span
                            >
                            <span class="legend-item"
                                ><span class="lg-bar dashed"></span>다른 종목 (대회 제공)</span
                            >
                            <span class="legend-item"
                                ><span class="lg-bar dashed-soft"></span>관심 (종목 미정)</span
                            >
                            <span class="legend-item"
                                ><span class="lg-diamond solid"></span>완주 기록</span
                            >
                            <span class="legend-item"
                                ><span class="lg-diamond hollow"></span>미확인 (지난 대회)</span
                            >
                        </div>
                        <div class="legend-now">● NOW · {todayMonth}/{todayDay}</div>
                    </div>
                </div>
            </div>

            <div class="chart-foot">
                <span>↑ 행 클릭 → 종목 상세 · 차트는 가로 스크롤</span>
                <span>SEASON {year} · {stats().totalRaces} EVENTS</span>
            </div>
        </div>
    {/if}
</div>

<style>
    .page {
        background: var(--arena-paper-alt);
        color: var(--arena-ink);
        font-family: var(--arena-f-body);
        min-height: 100vh;
        padding-bottom: 60px;
    }

    /* ── Head ── */
    .head {
        max-width: 1700px;
        margin: 0 auto;
        padding: 32px 24px 20px;
    }
    @media (min-width: 1024px) {
        .head {
            padding: 32px 32px 20px;
        }
    }
    .title {
        font-family: var(--arena-f-display);
        font-size: clamp(28px, 4vw, 44px);
        font-weight: 700;
        letter-spacing: -1.5px;
        line-height: 1;
        margin: 8px 0 8px;
        color: var(--arena-ink);
    }
    .sub {
        font-family: var(--arena-f-mono);
        font-size: 12px;
        color: var(--arena-ink-soft);
        margin: 0;
    }
    .login-link {
        color: var(--arena-accent-deep);
        text-decoration: underline;
    }

    .stat-row {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        margin-top: 24px;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
    }
    @media (min-width: 768px) {
        .stat-row {
            grid-template-columns: repeat(5, 1fr);
        }
    }
    .stat-cell {
        padding: 14px 18px;
        border-right: 1px solid var(--arena-line-soft);
        border-bottom: 1px solid var(--arena-line-soft);
    }
    @media (min-width: 768px) {
        .stat-cell {
            border-bottom: none;
        }
        .stat-cell:last-child {
            border-right: none;
        }
    }
    .stat-cell-pending.active {
        background: var(--arena-ink);
        color: var(--arena-paper);
    }
    .stat-cell-pending.active .stat-label,
    .stat-cell-pending.active .stat-sub {
        color: rgba(255, 255, 255, 0.5);
    }
    .stat-cell-pending.active .stat-val {
        color: var(--arena-accent);
    }
    .stat-label {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .stat-val {
        font-family: var(--arena-f-display);
        font-size: 26px;
        font-weight: 700;
        letter-spacing: -0.6px;
    }
    .stat-val.small {
        font-size: 16px;
        line-height: 1.2;
    }
    .stat-sub {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
        margin-top: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .banner {
        margin-top: 16px;
        background: var(--arena-ink);
        color: var(--arena-paper);
        padding: 14px 20px;
        display: grid;
        grid-template-columns: auto 1fr;
        gap: 12px 20px;
        align-items: center;
        border: 1px solid var(--arena-ink);
    }
    @media (min-width: 768px) {
        .banner {
            grid-template-columns: auto 1fr auto auto;
        }
    }
    .banner-bang {
        width: 32px;
        height: 32px;
        background: var(--arena-accent);
        color: var(--arena-ink);
        display: grid;
        place-items: center;
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: 14px;
    }
    .banner-kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-accent);
        font-weight: 700;
        text-transform: uppercase;
    }
    .banner-title {
        font-family: var(--arena-f-display);
        font-size: 15px;
        font-weight: 600;
        letter-spacing: -0.3px;
        margin-top: 3px;
    }
    .banner-cta {
        padding: 10px 16px;
        background: var(--arena-accent);
        color: var(--arena-ink);
        font-family: var(--arena-f-display);
        font-weight: 600;
        font-size: 13px;
        letter-spacing: -0.2px;
        text-decoration: none;
        grid-column: 1 / -1;
        text-align: center;
    }
    @media (min-width: 768px) {
        .banner-cta {
            grid-column: auto;
            text-align: left;
        }
    }
    .banner-dismiss {
        padding: 10px 14px;
        background: transparent;
        color: rgba(255, 255, 255, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.2);
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1px;
        cursor: pointer;
        grid-column: 1 / -1;
    }
    @media (min-width: 768px) {
        .banner-dismiss {
            grid-column: auto;
        }
    }

    /* ── Empty ── */
    .empty-frame {
        max-width: 1700px;
        margin: 0 auto;
        padding: 0 24px 60px;
    }
    .empty-inner {
        background: var(--arena-paper);
        border: 1px solid var(--arena-line);
        padding: 80px 40px;
        text-align: center;
    }
    .empty-title {
        font-family: var(--arena-f-display);
        font-size: 22px;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin: 12px 0 4px;
    }
    .empty-desc {
        color: var(--arena-ink-soft);
        font-size: 13px;
        margin: 0 0 20px;
    }

    /* ── Chart ── */
    .chart-wrap {
        max-width: 1700px;
        margin: 0 auto;
        padding: 0 24px 40px;
    }
    @media (min-width: 1024px) {
        .chart-wrap {
            padding: 0 32px 40px;
        }
    }
    .chart-frame {
        background: var(--arena-paper);
        border: 1px solid var(--arena-line);
        overflow-x: auto;
    }
    .chart-inner {
        position: relative;
    }

    /* Month axis */
    .month-axis {
        display: grid;
        border-bottom: 1px solid var(--arena-line);
    }
    .axis-side {
        padding: 10px 16px;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        border-right: 1px solid var(--arena-line);
    }
    .axis-side.right {
        border-right: none;
        border-left: 1px solid var(--arena-line);
        text-align: right;
    }
    .axis-center {
        position: relative;
        height: 32px;
    }
    .axis-month {
        position: absolute;
        top: 0;
        height: 32px;
        padding: 8px 10px;
        border-left: 1px solid var(--arena-line-soft);
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
        letter-spacing: 1.5px;
        font-weight: 500;
    }
    .axis-month.current {
        color: var(--arena-ink);
        background: oklch(96% 0.04 145);
        font-weight: 700;
    }
    .axis-now-label {
        position: absolute;
        top: 8px;
        transform: translateX(-50%);
        font-family: var(--arena-f-mono);
        font-size: 9px;
        letter-spacing: 1.5px;
        color: var(--arena-accent-deep);
        font-weight: 700;
        background: var(--arena-paper);
        padding: 0 4px;
        white-space: nowrap;
    }

    /* Rows */
    .rows {
        position: relative;
    }
    .now-line {
        position: absolute;
        top: 0;
        bottom: 0;
        width: 1.5px;
        background: var(--arena-accent-deep);
        pointer-events: none;
        z-index: 5;
    }

    .race-row {
        display: grid;
        border-bottom: 1px solid var(--arena-line-soft);
        position: relative;
        background: var(--arena-paper);
    }
    .race-row.alt {
        background: oklch(98.5% 0.005 110);
    }
    .race-row.unknown {
        background: oklch(97% 0.003 110);
    }
    .race-row.open {
        background: oklch(96% 0.04 145);
    }
    .row-toggle {
        position: absolute;
        inset: 0;
        background: transparent;
        border: none;
        padding: 0;
        cursor: pointer;
        z-index: 1;
    }
    .race-row > *:not(.row-toggle):not(.expanded) {
        z-index: 2;
        position: relative;
        pointer-events: none;
    }

    .cell-left {
        padding: 12px 16px;
        border-right: 1px solid var(--arena-line-soft);
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .race-row.unknown .cell-left {
        opacity: 0.7;
    }
    .status-badge {
        width: 26px;
        height: 26px;
        display: grid;
        place-items: center;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.5px;
        flex-shrink: 0;
        border: 1px solid var(--arena-ink-mute);
    }
    .badge-confirmed_going {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border-color: var(--arena-ink);
    }
    .badge-logged {
        background: var(--arena-accent);
        color: var(--arena-ink);
        border-color: var(--arena-accent);
    }
    .badge-maybe {
        background: var(--arena-paper);
        color: var(--arena-ink-soft);
        border-color: var(--arena-ink-soft);
    }
    .badge-unknown {
        background: var(--arena-paper-alt);
        color: var(--arena-ink-mute);
        border-color: var(--arena-ink-mute);
    }
    .row-name {
        flex: 1;
        min-width: 0;
    }
    .row-title {
        font-weight: 700;
        font-size: 14px;
        letter-spacing: -0.2px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .row-title.dim {
        color: var(--arena-ink-soft);
    }
    .star {
        font-size: 10px;
        color: var(--arena-accent-deep);
    }
    .ellipsis {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .row-meta {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        color: var(--arena-ink-soft);
        margin-top: 2px;
        letter-spacing: 0.5px;
    }

    .cell-center {
        position: relative;
    }
    .month-grid-line {
        position: absolute;
        top: 0;
        bottom: 0;
        width: 1px;
        background: var(--arena-line-soft);
        opacity: 0.4;
    }
    .reg-window {
        position: absolute;
        top: 8px;
        bottom: 8px;
        background: oklch(94% 0.01 145);
        opacity: 0.5;
    }
    .deadline-line {
        position: absolute;
        top: 10px;
        bottom: 10px;
        width: 1px;
        border-left: 1px dashed var(--arena-ink-mute);
        opacity: 0.5;
    }
    .course-stack {
        position: absolute;
        left: 0;
        right: 0;
    }
    .course-bar-wrap {
        position: relative;
        height: 11px;
    }
    .course-bar {
        position: absolute;
        top: 0;
        height: 11px;
        background: transparent;
        border: 1.5px dashed var(--arena-ink-mute);
        opacity: 0.55;
    }
    .course-bar.highlight {
        background: var(--arena-ink);
        border: none;
        opacity: 1;
    }
    .course-bar.unknown-bar {
        border-color: oklch(78% 0.01 110);
        opacity: 0.5;
    }
    .course-bar.maybe-bar {
        border-color: var(--arena-ink-soft);
    }
    .course-label {
        position: absolute;
        top: -1px;
        transform: translateX(-100%);
        font-family: var(--arena-f-mono);
        font-size: 9px;
        letter-spacing: 0.5px;
        color: var(--arena-ink-soft);
        font-weight: 500;
        white-space: nowrap;
    }
    .course-label.hl {
        color: var(--arena-ink);
        font-weight: 700;
    }
    .race-diamond {
        position: absolute;
        width: 18px;
        height: 18px;
        background: var(--arena-paper);
        transform: rotate(45deg);
        z-index: 3;
        border: 1.5px dashed var(--arena-ink-mute);
    }
    .race-diamond.going,
    .race-diamond.logged {
        background: var(--arena-ink);
        border: 2px solid var(--arena-ink);
    }
    .race-diamond.maybe-diamond {
        border: 1.5px dashed var(--arena-ink-soft);
    }
    .race-diamond.unknown-diamond {
        border: 1.5px dashed var(--arena-ink-mute);
    }
    .date-label {
        position: absolute;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        color: var(--arena-ink);
        letter-spacing: 0.3px;
        white-space: nowrap;
        font-weight: 600;
    }
    .date-label.dim {
        color: var(--arena-ink-mute);
    }
    .date-tail {
        margin-left: 8px;
        font-weight: 400;
    }
    .date-tail.muted {
        color: var(--arena-ink-soft);
    }
    .date-tail.accent {
        color: var(--arena-accent-deep);
        font-weight: 700;
    }

    .cell-right {
        padding: 12px 16px;
        border-left: 1px solid var(--arena-line-soft);
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .cell-right.dim {
        opacity: 0.7;
    }
    .right-time {
        font-family: var(--arena-f-display);
        font-size: 16px;
        font-weight: 700;
        letter-spacing: -0.3px;
    }
    .right-tag {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        font-weight: 700;
        margin-bottom: 2px;
    }
    .right-tag.accent {
        color: var(--arena-accent-deep);
    }
    .right-tag.soft {
        color: var(--arena-ink-soft);
    }
    .right-tag.muted {
        color: var(--arena-ink-mute);
    }
    .right-sub {
        font-size: 12px;
        color: var(--arena-ink-soft);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* ── Expanded row ── */
    .expanded {
        grid-column: 1 / -1;
        border-top: 1px solid var(--arena-line);
        background: var(--arena-paper);
        padding: 20px 24px;
        z-index: 2;
        position: relative;
        pointer-events: auto;
    }
    .ex-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 24px;
    }
    @media (min-width: 1024px) {
        .ex-grid {
            grid-template-columns: 1.2fr 1fr 1fr;
            gap: 28px;
        }
    }
    .ex-kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .ex-courses {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .ex-course {
        display: grid;
        grid-template-columns: 60px 1fr 80px auto;
        gap: 12px;
        align-items: center;
        padding: 8px 10px;
        background: var(--arena-paper-alt);
        border: 1px solid var(--arena-line-soft);
        font-family: var(--arena-f-mono);
        font-size: 11px;
    }
    .ex-course.hl {
        background: oklch(95% 0.02 145);
        border-color: var(--arena-ink);
    }
    .ex-code {
        font-weight: 700;
        letter-spacing: 1px;
    }
    .ex-label {
        font-family: var(--arena-f-body);
        font-size: 13px;
    }
    .ex-course.hl .ex-label {
        font-weight: 600;
    }
    .ex-dist {
        color: var(--arena-ink-soft);
    }
    .ex-tag {
        font-size: 9px;
        letter-spacing: 1px;
        padding: 2px 7px;
        background: transparent;
        color: var(--arena-ink-mute);
        border: 1px solid var(--arena-line-soft);
        font-weight: 700;
    }
    .ex-tag.hl {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border: none;
    }
    .ex-note {
        margin-top: 10px;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        color: var(--arena-ink-soft);
        letter-spacing: 0.5px;
        line-height: 1.6;
    }
    .ex-card {
        border: 1px solid var(--arena-line-soft);
        padding: 14px;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .ex-row {
        display: flex;
        justify-content: space-between;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
    }
    .ex-row > *:last-child {
        color: var(--arena-ink);
    }
    .ex-row .bold {
        font-weight: 600;
    }
    .ex-row .big {
        font-weight: 700;
        font-family: var(--arena-f-display);
        font-size: 14px;
    }
    .ex-divider {
        border-top: 1px dashed var(--arena-line-soft);
        margin: 4px 0;
    }
    .ex-memo-kicker {
        font-family: var(--arena-f-mono);
        font-size: 9px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .ex-memo > div:last-child {
        font-size: 13px;
    }

    .ex-actions {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .ex-btn {
        padding: 10px 14px;
        background: transparent;
        color: var(--arena-ink);
        border: 1px solid var(--arena-line);
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1px;
        cursor: pointer;
        text-decoration: none;
        text-align: left;
        display: flex;
        justify-content: space-between;
    }
    .ex-btn:hover {
        background: var(--arena-paper-alt);
    }
    .ex-btn.primary {
        padding: 12px 14px;
        background: var(--arena-accent);
        color: var(--arena-ink);
        border: none;
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: 13px;
        letter-spacing: -0.2px;
    }
    .ex-btn.primary:hover {
        opacity: 0.9;
    }

    /* ── Legend ── */
    .legend {
        display: grid;
        border-top: 1px solid var(--arena-line);
    }
    .legend-side {
        padding: 12px 16px;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        border-right: 1px solid var(--arena-line-soft);
    }
    .legend-items {
        padding: 12px 16px;
        display: flex;
        gap: 22px;
        align-items: center;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
        flex-wrap: wrap;
    }
    .legend-item {
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    .lg-bar {
        width: 28px;
        height: 10px;
    }
    .lg-bar.solid {
        background: var(--arena-ink);
    }
    .lg-bar.dashed {
        border: 1.5px dashed var(--arena-ink-mute);
    }
    .lg-bar.dashed-soft {
        border: 1.5px dashed var(--arena-ink-soft);
    }
    .lg-diamond {
        width: 14px;
        height: 14px;
        transform: rotate(45deg);
    }
    .lg-diamond.solid {
        background: var(--arena-ink);
        border: 2px solid var(--arena-ink);
    }
    .lg-diamond.hollow {
        background: var(--arena-paper);
        border: 1.5px dashed var(--arena-ink-mute);
    }
    .legend-now {
        padding: 12px 16px;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        color: var(--arena-accent-deep);
        letter-spacing: 1.5px;
        text-align: right;
        border-left: 1px solid var(--arena-line-soft);
    }

    .chart-foot {
        margin-top: 14px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 8px;
    }
</style>
