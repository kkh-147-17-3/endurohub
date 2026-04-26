<script lang="ts">
    import { page } from '$app/stores';
    import ToolsShell from '$lib/components/arena/ToolsShell.svelte';
    import {
        STD_DISTANCES,
        ZONE_INK,
        type ZoneKey,
        buildPlan,
        fmtPace,
        parseTime,
        vdot,
    } from '$lib/tools';

    let weeks = $state(12);
    let openWeek = $state(3);
    let baseDistKm = $state(21.0975);
    let baseTimeStr = $state('1:42:15');

    const baseTimeSec = $derived(parseTime(baseTimeStr));
    const v = $derived(vdot(baseDistKm, baseTimeSec));
    const built = $derived(buildPlan(weeks, v));
    const focusedWeek = $derived(built.plan[openWeek] ?? built.plan[0]);

    const phaseLabelKr: Record<string, string> = {
        BASE: '베이스',
        BUILD: '빌드',
        PEAK: '피크',
        TAPER: '테이퍼',
    };

    const dayLabelKr = ['월', '화', '수', '목', '금', '토', '일'];

    function workoutDescription(zone: string, weekKm: number, paces: ReturnType<typeof buildPlan>['paces']): string {
        if (zone === 'REST') return '';
        if (zone === 'LONG E') return `~${Math.round(weekKm * 0.35)}K @ ${fmtPace(paces.E.sec)}`;
        if (zone === 'RACE/E') return `대회/E @ ${fmtPace(paces.E.sec)}`;
        const z = zone[0] as ZoneKey;
        if (z === 'E') return `~${Math.round(weekKm * 0.15)}K @ ${fmtPace(paces.E.sec)}`;
        if (z === 'T') return `~8K @ ${fmtPace(paces.T.sec)}`;
        if (z === 'I') return `5×1K @ ${fmtPace(paces.I.sec)}`;
        if (z === 'M') return `~6K @ ${fmtPace(paces.M.sec)}`;
        if (z === 'R') return `8×400m @ ${fmtPace(paces.R.sec)}`;
        return '';
    }

    function zoneText(zone: string): string {
        if (zone === 'REST') return '휴식';
        if (zone === 'LONG E') return '롱 E';
        if (zone === 'RACE/E') return '대회';
        return zone;
    }

    function cellBg(zone: string): string {
        if (zone === 'REST') return 'var(--arena-paper-alt)';
        if (zone === 'LONG E') return 'oklch(92% 0.04 145)';
        if (zone[0] === 'E') return 'var(--arena-paper)';
        return 'oklch(94% 0.05 80)';
    }

    function cellInk(zone: string): string {
        if (zone === 'REST') return 'var(--arena-ink-mute)';
        const k = zone[0] === 'L' ? 'E' : (zone[0] as ZoneKey);
        return ZONE_INK[k] ?? 'var(--arena-ink)';
    }
</script>

<svelte:head>
    <title>훈련 플랜 — endurohub</title>
</svelte:head>

<ToolsShell currentPath={$page.url.pathname}>
    <div class="page">
        <header class="head">
            <div class="head-left">
                <div class="arena-kicker">02 · TRAINING</div>
                <h2>훈련 플랜</h2>
                <p>
                    최근 기록 ({baseDistKm}K · {baseTimeStr}) · VDOT
                    <strong>{v.toFixed(1)}</strong> 기준
                </p>
            </div>
            <div class="weeks-toggle">
                {#each [8, 12, 16] as w}
                    <button
                        type="button"
                        class:active={weeks === w}
                        onclick={() => {
                            weeks = w;
                            openWeek = Math.min(openWeek, w - 1);
                        }}>{w}주</button
                    >
                {/each}
            </div>
        </header>

        <!-- Base inputs -->
        <div class="base-row">
            <div class="base-cell">
                <div class="base-lbl">최근 기록 거리</div>
                <div class="dist-buttons">
                    {#each STD_DISTANCES as d}
                        <button
                            type="button"
                            class="dist-btn"
                            class:active={Math.abs(baseDistKm - d.km) < 0.01}
                            onclick={() => (baseDistKm = d.km)}>{d.label}</button
                        >
                    {/each}
                </div>
            </div>
            <div class="base-cell">
                <div class="base-lbl">완주 시간</div>
                <input
                    class="base-input"
                    value={baseTimeStr}
                    oninput={(e) => (baseTimeStr = (e.currentTarget as HTMLInputElement).value)}
                />
                <div class="hint">시:분:초</div>
            </div>
        </div>

        <!-- Phase bar -->
        <div class="phase-bar">
            {#each built.plan as w, i}
                <button
                    type="button"
                    class="phase-cell"
                    class:active={openWeek === i}
                    style="background: {w.phaseColor}; opacity: {openWeek === i ? 1 : 0.55}"
                    onclick={() => (openWeek = i)}
                    title={`${phaseLabelKr[w.phase]} · ${w.weekNum}주차 · ${w.weekKm}km`}
                >
                    {w.weekNum}
                </button>
            {/each}
        </div>

        <!-- Calendar -->
        <section class="block">
            <div class="block-title">
                <span class="title-rule"></span>
                {weeks}주 캘린더
            </div>
            <div class="cal">
                <div class="cal-head">
                    {#each dayLabelKr as d}
                        <div class="cal-head-cell">{d}</div>
                    {/each}
                </div>
                <div class="cal-grid">
                    {#each built.plan as w, wi}
                        {#each w.days as day, di (`${wi}-${di}`)}
                            <button
                                type="button"
                                class="cal-cell"
                                class:current={openWeek === wi}
                                style="background: {cellBg(day.zone)}"
                                onclick={() => (openWeek = wi)}
                            >
                                <div class="cal-w">W{w.weekNum}</div>
                                <div class="cal-zone" style="color: {cellInk(day.zone)}">
                                    {zoneText(day.zone)}
                                </div>
                            </button>
                        {/each}
                    {/each}
                </div>
            </div>
        </section>

        <!-- Focused week detail -->
        {#if focusedWeek}
            <section class="focus-card">
                <div class="focus-head">
                    <div>
                        <div class="focus-phase" style="color: {focusedWeek.phaseColor}">
                            {phaseLabelKr[focusedWeek.phase]} · {focusedWeek.weekNum}주차
                        </div>
                        <div class="focus-km">{focusedWeek.weekKm} km / 주</div>
                    </div>
                    <div class="focus-meta">
                        포커스: <span class="hl" style="color: {ZONE_INK[focusedWeek.focus]}"
                            >{focusedWeek.focus}</span
                        > 존
                    </div>
                </div>
                <div class="focus-grid">
                    {#each focusedWeek.days as day, di}
                        <div class="focus-day">
                            <div class="focus-day-name">{dayLabelKr[di]}</div>
                            <div class="focus-day-zone" style="color: {cellInk(day.zone)}">
                                {zoneText(day.zone)}
                            </div>
                            {#if day.zone !== 'REST'}
                                <div class="focus-day-desc">
                                    {workoutDescription(day.zone, focusedWeek.weekKm, built.paces)}
                                </div>
                            {/if}
                        </div>
                    {/each}
                </div>
            </section>
        {/if}

        <!-- Pace reference -->
        <section class="block">
            <div class="block-title">
                <span class="title-rule"></span>
                트레이닝 페이스 기준 (VDOT {v.toFixed(1)})
            </div>
            <div class="pace-table">
                {#each Object.entries(built.paces) as [k, p] (k)}
                    <div class="pace-row">
                        <span class="pace-zone" style="color: {ZONE_INK[k as ZoneKey]}">{k}</span>
                        <span class="pace-name">{p.label}</span>
                        <span class="pace-val">{fmtPace(p.sec)}/km</span>
                        <span class="pace-hr">심박 {p.hr}</span>
                    </div>
                {/each}
            </div>
        </section>
    </div>
</ToolsShell>

<style>
    .page {
        max-width: 1100px;
        margin: 0 auto;
        padding: 32px 24px 60px;
    }
    @media (min-width: 1024px) {
        .page {
            padding: 40px 32px 80px;
        }
    }
    .head {
        display: grid;
        grid-template-columns: 1fr;
        gap: 16px;
        align-items: flex-end;
        margin-bottom: 24px;
    }
    @media (min-width: 768px) {
        .head {
            grid-template-columns: 1fr auto;
        }
    }
    .head h2 {
        font-family: var(--arena-f-display);
        font-size: clamp(24px, 3vw, 32px);
        font-weight: 700;
        letter-spacing: -0.8px;
        margin: 8px 0 6px;
        color: var(--arena-ink);
    }
    .head p {
        margin: 0;
        font-size: 13px;
        color: var(--arena-ink-soft);
    }
    .head p strong {
        color: var(--arena-ink);
    }
    .weeks-toggle {
        display: flex;
        border: 1px solid var(--arena-line);
    }
    .weeks-toggle button {
        padding: 8px 14px;
        background: transparent;
        color: var(--arena-ink);
        border: none;
        border-right: 1px solid var(--arena-line);
        font-family: var(--arena-f-mono);
        font-size: 12px;
        cursor: pointer;
    }
    .weeks-toggle button:last-child {
        border-right: none;
    }
    .weeks-toggle button.active {
        background: var(--arena-ink);
        color: var(--arena-paper);
    }

    .base-row {
        display: grid;
        grid-template-columns: 1fr;
        gap: 12px;
        margin-bottom: 22px;
    }
    @media (min-width: 768px) {
        .base-row {
            grid-template-columns: 1fr 1fr;
        }
    }
    .base-cell {
        border: 1px solid var(--arena-line);
        padding: 14px 16px;
    }
    .base-lbl {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .dist-buttons {
        display: flex;
        gap: 6px;
    }
    .dist-btn {
        flex: 1;
        padding: 8px 12px;
        background: transparent;
        color: var(--arena-ink);
        border: 1px solid var(--arena-line);
        font-family: var(--arena-f-mono);
        font-size: 12px;
        cursor: pointer;
    }
    .dist-btn.active {
        background: var(--arena-ink);
        color: var(--arena-paper);
    }
    .base-input {
        width: 100%;
        background: transparent;
        border: none;
        outline: none;
        font-family: var(--arena-f-display);
        font-size: 24px;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: var(--arena-ink);
        padding: 0;
    }
    .hint {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        color: var(--arena-ink-mute);
        margin-top: 2px;
    }

    .phase-bar {
        display: flex;
        height: 36px;
        margin-bottom: 20px;
        border: 1px solid var(--arena-line);
    }
    .phase-cell {
        flex: 1;
        border: none;
        border-right: 1px solid var(--arena-paper);
        cursor: pointer;
        color: var(--arena-paper);
        font-family: var(--arena-f-mono);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.5px;
        display: grid;
        place-items: center;
    }
    .phase-cell:last-child {
        border-right: none;
    }
    .phase-cell.active {
        outline: 2px solid var(--arena-ink);
        outline-offset: -2px;
    }

    .block {
        margin-bottom: 24px;
    }
    .block-title {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .title-rule {
        width: 14px;
        height: 1px;
        background: var(--arena-ink);
    }

    .cal {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .cal-head {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 4px;
    }
    .cal-head-cell {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        padding: 4px 6px;
    }
    .cal-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 4px;
    }
    .cal-cell {
        padding: 8px;
        border: 1px solid var(--arena-line-soft);
        cursor: pointer;
        min-height: 56px;
        text-align: left;
    }
    .cal-cell.current {
        border: 1.5px solid var(--arena-ink);
    }
    .cal-w {
        font-family: var(--arena-f-mono);
        font-size: 9px;
        color: var(--arena-ink-soft);
    }
    .cal-zone {
        font-family: var(--arena-f-display);
        font-size: 13px;
        font-weight: 700;
        margin-top: 2px;
    }

    .focus-card {
        border: 1px solid var(--arena-line);
        padding: 22px;
        margin-bottom: 24px;
    }
    .focus-head {
        display: flex;
        justify-content: space-between;
        margin-bottom: 14px;
        flex-wrap: wrap;
        gap: 12px;
    }
    .focus-phase {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .focus-km {
        font-family: var(--arena-f-display);
        font-size: 22px;
        font-weight: 700;
        letter-spacing: -0.4px;
    }
    .focus-meta {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
        align-self: flex-end;
    }
    .focus-meta .hl {
        font-weight: 700;
    }
    .focus-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 6px;
    }
    @media (min-width: 768px) {
        .focus-grid {
            grid-template-columns: repeat(7, 1fr);
        }
    }
    .focus-day {
        border: 1px solid var(--arena-line-soft);
        padding: 10px;
        min-height: 84px;
    }
    .focus-day-name {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        color: var(--arena-ink-soft);
        margin-bottom: 4px;
    }
    .focus-day-zone {
        font-family: var(--arena-f-display);
        font-size: 14px;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .focus-day-desc {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        color: var(--arena-ink-soft);
    }

    .pace-table {
        border: 1px solid var(--arena-line);
    }
    .pace-row {
        display: grid;
        grid-template-columns: 50px 1fr 110px 110px;
        gap: 16px;
        padding: 12px 16px;
        border-top: 1px solid var(--arena-line-soft);
        align-items: center;
    }
    .pace-row:first-child {
        border-top: none;
    }
    .pace-zone {
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: 18px;
    }
    .pace-name {
        font-weight: 600;
        font-size: 14px;
    }
    .pace-val {
        font-family: var(--arena-f-mono);
        font-weight: 700;
        font-size: 14px;
    }
    .pace-hr {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
    }
</style>
