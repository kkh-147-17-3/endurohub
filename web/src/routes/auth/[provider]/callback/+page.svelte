<script lang="ts">
    import ProgressBar from '$lib/components/ProgressBar.svelte';

    let { data } = $props();
</script>

<svelte:head>
    <title>로그인 중... - 엔듀로허브</title>
    <meta name="robots" content="noindex" />
</svelte:head>

<div class="auth-wrap">
    <div class="auth-shell">
        {#if data.error}
            <header class="auth-head">
                <div class="kicker error-kicker">SIGN IN · FAILED</div>
                <h1 class="auth-title">로그인 실패</h1>
                <p class="auth-sub">{data.error}</p>
            </header>

            <div class="auth-actions">
                <a href="/auth/login" class="arena-submit">
                    <span>다시 시도</span>
                    <span class="arena-arrow">→</span>
                </a>
            </div>
        {:else}
            <ProgressBar active={true} />
            <header class="auth-head">
                <div class="kicker">SIGN IN · PROCESSING</div>
                <h1 class="auth-title">로그인 처리 중</h1>
                <p class="auth-sub">잠시만 기다려주세요...</p>
            </header>
        {/if}
    </div>
</div>

<style>
    .auth-wrap {
        min-height: calc(100vh - 4rem);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 56px 24px 80px;
        background: var(--arena-paper);
    }
    .auth-shell {
        width: 100%;
        max-width: 380px;
        display: flex;
        flex-direction: column;
        gap: 24px;
        text-align: center;
        align-items: center;
    }

    .auth-head {
        display: flex;
        flex-direction: column;
        gap: 4px;
        align-items: center;
    }
    .kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: var(--arena-ink-soft);
    }
    .error-kicker { color: var(--arena-urgent); }
    .auth-title {
        font-family: var(--arena-f-display);
        font-size: 32px;
        font-weight: 700;
        letter-spacing: -1px;
        line-height: 1;
        margin: 4px 0 6px;
        color: var(--arena-ink);
    }
    .auth-sub {
        font-family: var(--arena-f-mono);
        font-size: 12px;
        color: var(--arena-ink-soft);
        margin: 0;
        line-height: 1.5;
    }

    .auth-actions { width: 100%; }
    .arena-submit {
        width: 100%;
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
        text-decoration: none;
        transition: transform 0.1s;
    }
    .arena-submit:active { transform: translateY(1px); }
    .arena-arrow {
        font-family: var(--arena-f-mono);
        font-size: 14px;
        color: var(--arena-accent);
    }

</style>
