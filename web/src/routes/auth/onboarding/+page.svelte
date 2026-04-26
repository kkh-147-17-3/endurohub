<script lang="ts">
    import { enhance } from '$app/forms';
    import type { Sport } from '$lib/types';
    import ProgressBar from '$lib/components/ProgressBar.svelte';

    let { data, form } = $props();

    let selectedSports = $state<string[]>([]);
    let selectedRegions = $state<string[]>([]);
    let isSubmitting = $state(false);

    const sports: { value: Sport; label: string; code: string }[] = [
        { value: 'running', label: '러닝', code: 'RUN' },
        { value: 'trail_running', label: '트레일', code: 'TRL' },
        { value: 'cycling', label: '자전거', code: 'CYCLE' },
        { value: 'swimming', label: '수영', code: 'SWIM' },
        { value: 'triathlon', label: '철인3종', code: 'TRI' },
    ];

    const regions = [
        '서울', '경기', '인천', '부산', '대구', '광주', '대전', '울산', '세종',
        '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주',
    ];

    function toggleSport(sport: string) {
        if (selectedSports.includes(sport)) {
            selectedSports = selectedSports.filter((s) => s !== sport);
        } else {
            selectedSports = [...selectedSports, sport];
        }
    }

    function toggleRegion(region: string) {
        if (selectedRegions.includes(region)) {
            selectedRegions = selectedRegions.filter((r) => r !== region);
        } else {
            selectedRegions = [...selectedRegions, region];
        }
    }

    let step = $state(1);
    let totalSteps = 2;

    function nextStep() {
        if (step < totalSteps) step++;
    }

    function prevStep() {
        if (step > 1) step--;
    }
</script>

<svelte:head>
    <title>관심사 설정 - 엔듀로허브</title>
    <meta name="robots" content="noindex" />
</svelte:head>

<ProgressBar active={isSubmitting} />

<div class="auth-wrap">
    <div class="auth-shell">
        <div class="progress-row">
            <div class="progress-bar">
                <div class="progress-fill" style="width: {(step / totalSteps) * 100}%"></div>
            </div>
            <span class="progress-num">{step}/{totalSteps}</span>
        </div>

        <form
            method="POST"
            use:enhance={() => {
                isSubmitting = true;
                return async ({ update }) => {
                    isSubmitting = false;
                    await update();
                };
            }}
        >
            <input type="hidden" name="preferred_sports" value={selectedSports.join(',')} />
            <input type="hidden" name="preferred_regions" value={selectedRegions.join(',')} />

            {#if step === 1}
                <header class="step-head">
                    <div class="kicker">STEP 01 · SPORT</div>
                    <h1 class="step-title">어떤 종목에<br />관심 있으세요?</h1>
                    <p class="step-sub">관심 종목을 선택하면 맞춤 대회 정보를 받을 수 있어요</p>
                </header>

                <div class="sport-list">
                    {#each sports as sport}
                        {@const isSelected = selectedSports.includes(sport.value)}
                        <button
                            type="button"
                            class="sport-tile"
                            class:active={isSelected}
                            data-sport={sport.value}
                            onclick={() => toggleSport(sport.value)}
                        >
                            <span class="sport-code">{sport.code}</span>
                            <span class="sport-label">{sport.label}</span>
                            <span class="sport-mark" class:checked={isSelected}>
                                {isSelected ? '✓' : ''}
                            </span>
                        </button>
                    {/each}
                </div>

                <div class="step-actions">
                    <button type="button" class="arena-submit" onclick={nextStep}>
                        <span>{selectedSports.length > 0 ? '다음' : '건너뛰기'}</span>
                        <span class="arena-submit-arrow">→</span>
                    </button>
                </div>
            {/if}

            {#if step === 2}
                <header class="step-head">
                    <div class="kicker">STEP 02 · REGION</div>
                    <h1 class="step-title">주로 어디서<br />뛰세요?</h1>
                    <p class="step-sub">관심 지역의 대회를 우선 추천해드릴게요</p>
                </header>

                <div class="region-list">
                    {#each regions as region}
                        {@const isSelected = selectedRegions.includes(region)}
                        <button
                            type="button"
                            class="region-chip"
                            class:active={isSelected}
                            onclick={() => toggleRegion(region)}
                        >
                            {region}
                        </button>
                    {/each}
                </div>

                {#if selectedRegions.length > 0}
                    <div class="region-summary">
                        <span class="summary-label">SELECTED</span>
                        <span class="summary-value">{selectedRegions.join(' · ')}</span>
                    </div>
                {/if}

                <div class="step-actions">
                    <button type="button" class="arena-back" onclick={prevStep}>
                        <span class="arena-submit-arrow">←</span>
                        <span>이전</span>
                    </button>
                    <button type="submit" class="arena-submit" disabled={isSubmitting}>
                        <span>시작하기</span>
                        <span class="arena-submit-arrow">→</span>
                    </button>
                </div>
            {/if}
        </form>

        <div class="skip-row">
            <form
                method="POST"
                use:enhance={() => {
                    isSubmitting = true;
                    return async ({ update }) => {
                        isSubmitting = false;
                        await update();
                    };
                }}
            >
                <input type="hidden" name="preferred_sports" value="" />
                <input type="hidden" name="preferred_regions" value="" />
                <button type="submit" class="skip-btn" disabled={isSubmitting}>
                    나중에 설정할게요
                </button>
            </form>
        </div>
    </div>
</div>

<style>
    .auth-wrap {
        min-height: calc(100vh - 4rem);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 48px 24px 80px;
        background: var(--arena-paper);
    }
    .auth-shell {
        width: 100%;
        max-width: 480px;
        display: flex;
        flex-direction: column;
        gap: 24px;
    }

    .progress-row {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .progress-bar {
        flex: 1;
        height: 2px;
        background: var(--arena-line-soft);
        position: relative;
    }
    .progress-fill {
        position: absolute;
        inset: 0 auto 0 0;
        background: var(--arena-ink);
        transition: width 0.4s ease-out;
    }
    .progress-num {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
    }

    .step-head { margin-bottom: 28px; }
    .kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        color: var(--arena-ink-soft);
        margin-bottom: 8px;
    }
    .step-title {
        font-family: var(--arena-f-display);
        font-size: 32px;
        font-weight: 700;
        letter-spacing: -1px;
        line-height: 1.05;
        margin: 0 0 8px;
        color: var(--arena-ink);
    }
    .step-sub {
        font-family: var(--arena-f-mono);
        font-size: 12px;
        color: var(--arena-ink-soft);
        margin: 0;
    }

    /* Sport tiles */
    .sport-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .sport-tile {
        display: grid;
        grid-template-columns: 60px 1fr 24px;
        align-items: center;
        gap: 14px;
        padding: 14px 16px;
        background: var(--arena-paper);
        border: 1px solid var(--arena-line-soft);
        cursor: pointer;
        text-align: left;
        transition: border-color 0.1s, background 0.1s;
    }
    .sport-tile:hover { border-color: var(--arena-ink); }
    .sport-tile.active {
        background: var(--arena-ink);
        border-color: var(--arena-ink);
        color: var(--arena-paper);
    }
    .sport-tile.active .sport-code { color: var(--arena-accent); }
    .sport-code {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
    }
    .sport-label {
        font-family: var(--arena-f-display);
        font-weight: 600;
        font-size: 16px;
        letter-spacing: -0.2px;
    }
    .sport-mark {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 22px;
        height: 22px;
        border: 1px solid var(--arena-line);
        font-family: var(--arena-f-mono);
        font-size: 12px;
        color: var(--arena-paper);
    }
    .sport-mark.checked {
        background: var(--arena-accent);
        border-color: var(--arena-accent);
        color: var(--arena-ink);
    }

    /* Region chips */
    .region-list {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }
    .region-chip {
        padding: 7px 12px;
        border: 1px solid var(--arena-line-soft);
        background: var(--arena-paper);
        font-family: var(--arena-f-mono);
        font-size: 12px;
        letter-spacing: 0.3px;
        color: var(--arena-ink-soft);
        cursor: pointer;
        transition: border-color 0.1s, background 0.1s, color 0.1s;
    }
    .region-chip:hover { border-color: var(--arena-ink); color: var(--arena-ink); }
    .region-chip.active {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border-color: var(--arena-ink);
    }

    .region-summary {
        margin-top: 14px;
        padding: 10px 12px;
        border: 1px solid var(--arena-line-soft);
        background: var(--arena-paper-alt);
        display: flex;
        align-items: baseline;
        gap: 10px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
    }
    .summary-label {
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
    }
    .summary-value {
        color: var(--arena-ink);
        flex: 1;
        word-break: keep-all;
    }

    /* Action buttons */
    .step-actions {
        display: flex;
        gap: 8px;
        margin-top: 24px;
    }
    .arena-submit {
        flex: 1;
        padding: 12px 16px;
        background: var(--arena-ink);
        color: var(--arena-paper);
        border: none;
        font-family: var(--arena-f-display);
        font-weight: 600;
        font-size: 14px;
        letter-spacing: -0.2px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        transition: transform 0.1s;
    }
    .arena-submit:active:not(:disabled) { transform: translateY(1px); }
    .arena-submit:disabled { opacity: 0.5; cursor: not-allowed; }
    .arena-submit-arrow {
        font-family: var(--arena-f-mono);
        font-size: 14px;
        color: var(--arena-accent);
    }
    .arena-back {
        padding: 12px 16px;
        background: transparent;
        color: var(--arena-ink);
        border: 1px solid var(--arena-line);
        font-family: var(--arena-f-mono);
        font-size: 12px;
        letter-spacing: 1px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .arena-back:hover { background: var(--arena-paper-alt); }
    .arena-back .arena-submit-arrow { color: var(--arena-ink-soft); }

    .skip-row { text-align: center; }
    .skip-btn {
        background: transparent;
        border: none;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.5px;
        color: var(--arena-ink-mute);
        cursor: pointer;
        padding: 4px 8px;
        text-decoration: underline;
        text-decoration-color: var(--arena-line-soft);
        text-underline-offset: 4px;
    }
    .skip-btn:hover { color: var(--arena-ink-soft); }
    .skip-btn:disabled { opacity: 0.5; cursor: not-allowed; }

</style>
