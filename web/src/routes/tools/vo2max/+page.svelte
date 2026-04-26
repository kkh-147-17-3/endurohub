<script lang="ts">
    import { page } from '$app/stores';
    import ToolsShell from '$lib/components/arena/ToolsShell.svelte';
    import {
        STD_DISTANCES,
        ZONE_INK,
        type ZoneKey,
        fmtPace,
        parseTime,
        trainingPaces,
        vdot,
    } from '$lib/tools';

    let distKm = $state(21.0975);
    let timeStr = $state('1:42:15');

    const timeSec = $derived(parseTime(timeStr));
    const v = $derived(vdot(distKm, timeSec));
    const paces = $derived(trainingPaces(v));

    const grade = $derived(
        v >= 60 ? '엘리트' : v >= 50 ? '상급' : v >= 40 ? '중급' : '초급',
    );

    const gradePct = $derived(Math.max(0, Math.min(100, (v / 70) * 100)));
</script>

<svelte:head>
    <title>VO₂max 계산기 — endurohub</title>
</svelte:head>

<ToolsShell currentPath={$page.url.pathname}>
    <div class="page">
        <header class="head">
            <div class="arena-kicker">03 · VDOT</div>
            <h2>VO₂max 계산기</h2>
            <p>최근 레이스 기록으로 VDOT(Daniels)를 추정하고, 트레이닝 페이스를 자동 산출합니다.</p>
        </header>

        <!-- Inputs -->
        <div class="inputs">
            <div class="input-cell">
                <div class="cell-lbl">거리</div>
                <div class="dist-buttons">
                    {#each STD_DISTANCES as d}
                        <button
                            type="button"
                            class="dist-btn"
                            class:active={Math.abs(distKm - d.km) < 0.01}
                            onclick={() => (distKm = d.km)}>{d.label}</button
                        >
                    {/each}
                </div>
            </div>
            <div class="input-cell">
                <div class="cell-lbl">완주 시간</div>
                <input
                    class="time-input"
                    value={timeStr}
                    oninput={(e) => (timeStr = (e.currentTarget as HTMLInputElement).value)}
                />
                <div class="hint">시:분:초</div>
            </div>
        </div>

        <!-- Result card -->
        <div class="result">
            <div class="result-half">
                <div class="result-kicker">VDOT</div>
                <div class="vdot-num">{v.toFixed(1)}</div>
                <div class="vdot-sub">ml/kg/min 환산</div>
            </div>
            <div class="result-half">
                <div class="result-kicker">등급</div>
                <div class="grade-name">{grade}</div>
                <div class="grade-bar">
                    <div class="grade-fill" style="width: {gradePct}%"></div>
                    <div class="grade-tick" style="left: 57%"></div>
                    <div class="grade-tick" style="left: 71%"></div>
                    <div class="grade-tick" style="left: 86%"></div>
                </div>
                <div class="grade-axis">
                    <span>30</span>
                    <span>40</span>
                    <span>50</span>
                    <span>60</span>
                    <span>70</span>
                </div>
            </div>
        </div>

        <!-- Training paces -->
        <section class="block">
            <div class="block-title">
                <span class="title-rule"></span>
                트레이닝 페이스 (Daniels)
            </div>
            <div class="paces">
                {#each Object.entries(paces) as [k, p] (k)}
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
        margin-bottom: 28px;
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

    .inputs {
        display: grid;
        grid-template-columns: 1fr;
        gap: 12px;
        margin-bottom: 24px;
    }
    @media (min-width: 768px) {
        .inputs {
            grid-template-columns: 1fr 1fr;
        }
    }
    .input-cell {
        border: 1px solid var(--arena-line);
        padding: 14px 16px;
    }
    .cell-lbl {
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
    .time-input {
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

    .result {
        background: var(--arena-ink);
        color: var(--arena-paper);
        padding: 28px;
        margin-bottom: 24px;
        display: grid;
        grid-template-columns: 1fr;
        gap: 24px;
    }
    @media (min-width: 768px) {
        .result {
            grid-template-columns: 1fr 1fr;
        }
    }
    .result-kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        opacity: 0.6;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .vdot-num {
        font-family: var(--arena-f-display);
        font-size: 72px;
        font-weight: 700;
        letter-spacing: -2px;
        line-height: 0.95;
    }
    .vdot-sub {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        opacity: 0.6;
        margin-top: 4px;
    }
    .grade-name {
        font-family: var(--arena-f-display);
        font-size: 32px;
        font-weight: 700;
        letter-spacing: -0.6px;
    }
    .grade-bar {
        margin-top: 14px;
        height: 6px;
        background: oklch(40% 0.03 145);
        position: relative;
    }
    .grade-fill {
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        background: var(--arena-accent);
    }
    .grade-tick {
        position: absolute;
        top: -2px;
        bottom: -2px;
        width: 1px;
        background: oklch(70% 0.03 145);
    }
    .grade-axis {
        display: flex;
        justify-content: space-between;
        font-family: var(--arena-f-mono);
        font-size: 9px;
        color: oklch(70% 0.03 145);
        margin-top: 4px;
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

    .paces {
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

    .save {
        margin-top: 8px;
        padding: 16px 20px;
        background: var(--arena-paper-alt);
        border: 1px dashed var(--arena-line);
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 16px;
        align-items: center;
    }
    .save-desc {
        font-size: 13px;
        color: var(--arena-ink);
        margin-top: 2px;
    }
    .save-cta {
        padding: 10px 14px;
        border: 1px solid var(--arena-ink);
        background: var(--arena-paper);
        font-family: var(--arena-f-mono);
        font-size: 12px;
        color: var(--arena-ink);
        text-decoration: none;
    }
    .save-cta:hover {
        background: var(--arena-ink);
        color: var(--arena-paper);
    }
</style>
