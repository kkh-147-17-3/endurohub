<script lang="ts">
    import { page } from '$app/stores';
    import ToolsShell from '$lib/components/arena/ToolsShell.svelte';
    import { STD_DISTANCES, fmtPace, fmtTime, parsePace, parseTime } from '$lib/tools';

    type Mode = 'time-from-dist-pace' | 'pace-from-dist-time' | 'dist-from-time-pace';

    let { data } = $props();
    const pf = data.prefill;

    // When prefilled from a real record, show its pace (distance + time → pace).
    let mode = $state<Mode>(pf ? 'pace-from-dist-time' : 'time-from-dist-pace');
    let distKm = $state(pf?.distKm ?? 21.0975);
    let timeSec = $state(pf?.timeSec ?? parseTime('1:42:15'));
    let paceSec = $state(
        Math.round((pf?.timeSec ?? parseTime('1:42:15')) / (pf?.distKm ?? 21.0975))
    );

    const computed = $derived.by(() => {
        if (mode === 'time-from-dist-pace') return { distKm, paceSec, timeSec: distKm * paceSec };
        if (mode === 'pace-from-dist-time')
            return { distKm, timeSec, paceSec: distKm > 0 ? timeSec / distKm : 0 };
        return { paceSec, timeSec, distKm: paceSec > 0 ? timeSec / paceSec : 0 };
    });

    function fmtDistInput(km: number): string {
        if (!Number.isFinite(km)) return '0';
        if (km % 1 === 0) return String(km);
        return km.toFixed(km < 10 ? 2 : 4).replace(/\.?0+$/, '');
    }

    function paceInputStr(sec: number): string {
        if (!Number.isFinite(sec) || sec < 0) return '0:00';
        const m = Math.floor(sec / 60);
        const s = Math.round(sec % 60);
        return `${m}:${String(s).padStart(2, '0')}`;
    }

    const splits = $derived.by(() => {
        const out: { km: number; time: number; label: string }[] = [];
        const nWhole = Math.floor(computed.distKm);
        for (let kkm = 1; kkm <= nWhole; kkm++) {
            out.push({ km: kkm, time: kkm * computed.paceSec, label: `${kkm}K` });
        }
        if (computed.distKm - nWhole > 0.01) {
            out.push({
                km: computed.distKm,
                time: computed.distKm * computed.paceSec,
                label: `완주 (${computed.distKm.toFixed(2)}K)`,
            });
        }
        return out;
    });

    const modeOptions: { k: Mode; label: string; sub: string }[] = [
        { k: 'time-from-dist-pace', label: '완주 시간 계산', sub: '거리 + 페이스' },
        { k: 'pace-from-dist-time', label: '평균 페이스 계산', sub: '거리 + 시간' },
        { k: 'dist-from-time-pace', label: '거리 계산', sub: '시간 + 페이스' },
    ];

    function setDist(v: string) {
        const n = parseFloat(v);
        if (Number.isFinite(n)) distKm = n;
    }
    function setTime(v: string) {
        timeSec = parseTime(v);
    }
    function setPace(v: string) {
        paceSec = parsePace(v);
    }
</script>

<svelte:head>
    <title>페이스 계산기 — endurohub</title>
</svelte:head>

<ToolsShell currentPath={$page.url.pathname}>
    <div class="page">
        <header class="head">
            <div class="arena-kicker">01 · PACE</div>
            <h2>페이스 계산기</h2>
            <p>거리 · 시간 · 페이스 — 셋 중 둘을 입력하면 나머지를 계산합니다.</p>
        </header>

        {#if pf}
            <div class="prefill-note">최근 기록 <b>{pf.label}</b> 을(를) 불러왔어요</div>
        {/if}

        <!-- Mode tabs -->
        <div class="modes">
            {#each modeOptions as opt (opt.k)}
                <button
                    type="button"
                    class="mode"
                    class:active={mode === opt.k}
                    onclick={() => (mode = opt.k)}
                >
                    <div class="mode-label">{opt.label}</div>
                    <div class="mode-sub">{opt.sub}</div>
                </button>
            {/each}
        </div>

        <!-- Inputs -->
        <div class="fields">
            <div class="field" class:dim={mode === 'dist-from-time-pace'}>
                <div class="field-head">
                    <span>거리 (km)</span>
                    {#if mode === 'dist-from-time-pace'}<span class="auto">계산됨</span>{/if}
                </div>
                <input
                    class="field-input"
                    readOnly={mode === 'dist-from-time-pace'}
                    value={fmtDistInput(computed.distKm)}
                    oninput={(e) => setDist((e.currentTarget as HTMLInputElement).value)}
                />
                {#if mode !== 'dist-from-time-pace'}
                    <div class="presets">
                        {#each STD_DISTANCES as d}
                            <button class="preset" onclick={() => (distKm = d.km)}
                                >{d.label}</button
                            >
                        {/each}
                    </div>
                {/if}
            </div>
            <div class="field" class:dim={mode === 'time-from-dist-pace'}>
                <div class="field-head">
                    <span>시간</span>
                    {#if mode === 'time-from-dist-pace'}<span class="auto">계산됨</span>{/if}
                </div>
                <input
                    class="field-input"
                    readOnly={mode === 'time-from-dist-pace'}
                    value={fmtTime(computed.timeSec)}
                    oninput={(e) => setTime((e.currentTarget as HTMLInputElement).value)}
                />
                <div class="hint">시:분:초</div>
            </div>
            <div class="field" class:dim={mode === 'pace-from-dist-time'}>
                <div class="field-head">
                    <span>페이스 (/km)</span>
                    {#if mode === 'pace-from-dist-time'}<span class="auto">계산됨</span>{/if}
                </div>
                <input
                    class="field-input"
                    readOnly={mode === 'pace-from-dist-time'}
                    value={paceInputStr(computed.paceSec)}
                    oninput={(e) => setPace((e.currentTarget as HTMLInputElement).value)}
                />
                <div class="hint">분:초</div>
            </div>
        </div>

        <!-- Result card -->
        <div class="result">
            <div class="result-kicker">결과</div>
            <div class="result-grid">
                <div class="result-cell" class:active={mode === 'dist-from-time-pace'}>
                    <div class="cell-lbl">
                        {#if mode === 'dist-from-time-pace'}<span class="dot"></span>{/if}거리
                    </div>
                    <div class="cell-val">
                        {fmtDistInput(computed.distKm)}<span class="unit">km</span>
                    </div>
                </div>
                <div class="result-cell" class:active={mode === 'time-from-dist-pace'}>
                    <div class="cell-lbl">
                        {#if mode === 'time-from-dist-pace'}<span class="dot"></span>{/if}시간
                    </div>
                    <div class="cell-val">{fmtTime(computed.timeSec)}</div>
                </div>
                <div class="result-cell" class:active={mode === 'pace-from-dist-time'}>
                    <div class="cell-lbl">
                        {#if mode === 'pace-from-dist-time'}<span class="dot"></span>{/if}페이스
                    </div>
                    <div class="cell-val">
                        {fmtPace(computed.paceSec)}<span class="unit">/km</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Pace conversions -->
        <section class="block">
            <div class="block-title">
                <span class="title-rule"></span>
                페이스 변환
            </div>
            <div class="conv-grid">
                {#each [['/ km', fmtPace(computed.paceSec)], ['/ mile', fmtPace(computed.paceSec * 1.60934)], ['/ 400m', fmtPace(computed.paceSec * 0.4)], ['km/h', (3600 / Math.max(computed.paceSec, 1)).toFixed(2)]] as [lbl, val]}
                    <div class="conv-cell">
                        <div class="conv-lbl">{lbl}</div>
                        <div class="conv-val">{val}</div>
                    </div>
                {/each}
            </div>
        </section>

        <!-- Splits -->
        <section class="block">
            <div class="block-title">
                <span class="title-rule"></span>
                1km 스플릿 ({splits.length}개)
            </div>
            <div class="splits">
                <div class="splits-head">
                    <span>지점</span>
                    <span>누적 시간</span>
                    <span class="right">구간 페이스</span>
                </div>
                <div class="splits-body">
                    {#each splits as s, i (i)}
                        <div class="split-row" class:final={i === splits.length - 1}>
                            <span class="split-lbl">{s.label}</span>
                            <span>{fmtTime(s.time)}</span>
                            <span class="right muted">{fmtPace(computed.paceSec)}</span>
                        </div>
                    {/each}
                </div>
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

    .modes {
        display: grid;
        grid-template-columns: 1fr;
        border: 1px solid var(--arena-line);
        margin-bottom: 20px;
    }
    @media (min-width: 768px) {
        .modes {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    .mode {
        padding: 12px 14px;
        background: var(--arena-paper);
        color: var(--arena-ink);
        border: none;
        border-bottom: 1px solid var(--arena-line);
        cursor: pointer;
        text-align: left;
    }
    @media (min-width: 768px) {
        .mode {
            border-bottom: none;
            border-right: 1px solid var(--arena-line);
        }
        .mode:last-child {
            border-right: none;
        }
    }
    .mode:last-child {
        border-bottom: none;
    }
    .mode.active {
        background: var(--arena-ink);
        color: var(--arena-paper);
    }
    .mode-label {
        font-family: var(--arena-f-display);
        font-weight: 600;
        font-size: 13px;
        letter-spacing: -0.2px;
    }
    .mode-sub {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        opacity: 0.7;
        margin-top: 2px;
    }

    .fields {
        display: grid;
        grid-template-columns: 1fr;
        gap: 12px;
        margin-bottom: 24px;
    }
    @media (min-width: 768px) {
        .fields {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    .field {
        border: 1px solid var(--arena-line);
        padding: 12px 14px;
        background: var(--arena-paper);
    }
    .field.dim {
        background: var(--arena-paper-alt);
        opacity: 0.7;
    }
    .field-head {
        display: flex;
        justify-content: space-between;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .auto {
        color: var(--arena-ink-mute);
    }
    .field-input {
        width: 100%;
        border: none;
        outline: none;
        background: transparent;
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
    .presets {
        display: flex;
        gap: 4px;
        margin-top: 8px;
        flex-wrap: wrap;
    }
    .preset {
        padding: 3px 8px;
        border: 1px solid var(--arena-line-soft);
        background: transparent;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        cursor: pointer;
    }
    .preset:hover {
        background: var(--arena-paper-alt);
    }

    .result {
        background: var(--arena-ink);
        color: var(--arena-paper);
        padding: 28px;
        margin-bottom: 24px;
    }
    .result-kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        opacity: 0.6;
        text-transform: uppercase;
        margin-bottom: 14px;
    }
    .result-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 28px;
    }
    @media (max-width: 640px) {
        .result-grid {
            grid-template-columns: 1fr;
            gap: 16px;
        }
    }
    .result-cell .cell-lbl {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        opacity: 0.5;
        text-transform: uppercase;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .result-cell.active .cell-lbl {
        opacity: 0.9;
    }
    .dot {
        width: 6px;
        height: 6px;
        background: var(--arena-accent);
        display: inline-block;
    }
    .cell-val {
        font-family: var(--arena-f-display);
        font-size: 36px;
        font-weight: 700;
        letter-spacing: -1px;
    }
    .unit {
        font-size: 16px;
        font-weight: 500;
        opacity: 0.6;
        margin-left: 4px;
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

    .conv-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
    }
    @media (min-width: 768px) {
        .conv-grid {
            grid-template-columns: repeat(4, 1fr);
        }
    }
    .conv-cell {
        border: 1px solid var(--arena-line-soft);
        padding: 10px 12px;
    }
    .conv-lbl {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .conv-val {
        font-family: var(--arena-f-mono);
        font-size: 18px;
        font-weight: 700;
        letter-spacing: -0.3px;
        color: var(--arena-ink);
    }

    .splits {
        border: 1px solid var(--arena-line);
    }
    .splits-head {
        display: grid;
        grid-template-columns: 110px 1fr 130px;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        padding: 8px 14px;
        background: var(--arena-paper-alt);
        border-bottom: 1px solid var(--arena-line);
    }
    .splits-body {
        max-height: 320px;
        overflow: auto;
    }
    .split-row {
        display: grid;
        grid-template-columns: 110px 1fr 130px;
        font-family: var(--arena-f-mono);
        font-size: 12px;
        padding: 7px 14px;
        border-bottom: 1px solid var(--arena-line-soft);
    }
    .split-row.final {
        background: oklch(95% 0.04 145);
    }
    .split-lbl {
        font-weight: 700;
    }
    .right {
        text-align: right;
    }
    .muted {
        color: var(--arena-ink-soft);
    }

    .save {
        margin-top: 24px;
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
