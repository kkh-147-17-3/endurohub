<script lang="ts">
    import { page } from '$app/stores';
    import ToolsShell from '$lib/components/arena/ToolsShell.svelte';
    import { STD_DISTANCES, fmtPace, fmtTime, parseTime, riegel } from '$lib/tools';

    let { data } = $props();
    const pf = data.prefill;

    let distKm = $state(pf?.distKm ?? 21.0975);
    let timeStr = $state(pf?.timeStr ?? '1:42:15');

    const baseTimeSec = $derived(parseTime(timeStr));

    const targets = [
        { code: '5K', km: 5, label: '5K' },
        { code: '10K', km: 10, label: '10K' },
        { code: 'HM', km: 21.0975, label: '하프' },
        { code: 'FM', km: 42.195, label: '풀코스' },
        { code: '50K', km: 50, label: '50K' },
    ];

    const predictions = $derived(
        targets.map((t) => ({
            ...t,
            timeSec: riegel(baseTimeSec, distKm, t.km),
            paceSec:
                t.km > 0 && baseTimeSec > 0 ? riegel(baseTimeSec, distKm, t.km) / t.km : 0,
            isBase: Math.abs(t.km - distKm) < 0.5,
        })),
    );
</script>

<svelte:head>
    <title>대회 기록 예측 — endurohub</title>
</svelte:head>

<ToolsShell currentPath={$page.url.pathname}>
    <div class="page">
        <header class="head">
            <div class="arena-kicker">04 · PREDICT</div>
            <h2>대회 기록 예측</h2>
            <p>최근 기록을 입력하면 다른 거리의 예상 완주 시간을 산출합니다 (Riegel 모델, k=1.06).</p>
        </header>

        {#if pf}
            <div class="prefill-note">최근 기록 <b>{pf.label}</b> 을(를) 불러왔어요</div>
        {/if}

        <!-- Inputs -->
        <div class="inputs">
            <div class="input-cell">
                <div class="cell-lbl">최근 기록 거리</div>
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

        <!-- Predictions table -->
        <section class="block">
            <div class="block-title">
                <span class="title-rule"></span>
                거리별 예상 기록
            </div>
            <div class="pred-table">
                <div class="pred-head">
                    <span>거리</span>
                    <span></span>
                    <span>예상 시간</span>
                    <span>예상 페이스</span>
                </div>
                {#each predictions as p (p.code)}
                    <div class="pred-row" class:base={p.isBase}>
                        <span class="p-label" class:hl={p.isBase}>{p.label}</span>
                        <span class="p-note">
                            {p.isBase ? '입력 기준' : `${p.km < 10 ? p.km.toFixed(1) : Math.round(p.km)} km`}
                        </span>
                        <span class="p-time">{fmtTime(p.timeSec)}</span>
                        <span class="p-pace">{fmtPace(p.paceSec)}/km</span>
                    </div>
                {/each}
            </div>
        </section>

        <p class="footnote">
            ※ Riegel 모델은 일반적으로 단거리(5K~10K)에서 장거리(하프·풀)로 외삽할 때 잘 맞으며,
            울트라(50K+) 구간에서는 컨디션·코스·기온에 따라 오차가 커질 수 있습니다.
        </p>
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

    .prefill-note {
        margin: 0 0 20px;
        padding: 8px 12px;
        border: 1px solid var(--arena-line-soft);
        background: var(--arena-paper-alt);
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.3px;
        color: var(--arena-ink-soft);
    }
    .prefill-note b {
        color: var(--arena-ink);
        font-weight: 700;
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

    .pred-table {
        border: 1px solid var(--arena-line);
    }
    .pred-head {
        display: grid;
        grid-template-columns: 80px 1fr 130px 130px;
        padding: 10px 16px;
        background: var(--arena-paper-alt);
        border-bottom: 1px solid var(--arena-line);
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
    }
    .pred-row {
        display: grid;
        grid-template-columns: 80px 1fr 130px 130px;
        padding: 14px 16px;
        border-top: 1px solid var(--arena-line-soft);
        align-items: center;
    }
    .pred-row:first-of-type {
        border-top: none;
    }
    .pred-row.base {
        background: oklch(95% 0.04 145);
    }
    .p-label {
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: 18px;
    }
    .p-label.hl {
        color: var(--arena-accent-deep);
    }
    .p-note {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
    }
    .p-time {
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: 20px;
        letter-spacing: -0.4px;
    }
    .p-pace {
        font-family: var(--arena-f-mono);
        font-size: 12px;
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

    .footnote {
        margin-top: 16px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
        line-height: 1.6;
    }
</style>
