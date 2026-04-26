<script lang="ts">
    import { enhance } from '$app/forms';
    import ProgressBar from '$lib/components/ProgressBar.svelte';

    let { form } = $props();

    let nickname = $state('');
    let isSubmitting = $state(false);

    let errors = $derived(flattenErrors(form?.errors));

    function flattenErrors(errs: Record<string, string[]> | undefined): Record<string, string> {
        if (!errs) return {};
        const flat: Record<string, string> = {};
        for (const [key, msgs] of Object.entries(errs)) {
            flat[key] = Array.isArray(msgs) ? msgs[0] : msgs;
        }
        return flat;
    }
</script>

<svelte:head>
    <title>닉네임 설정 - 엔듀로허브</title>
    <meta name="robots" content="noindex" />
</svelte:head>

<ProgressBar active={isSubmitting} />

<div class="auth-wrap">
    <div class="auth-shell">
        <header class="auth-head">
            <div class="kicker">PROFILE · NICKNAME</div>
            <h1 class="auth-title">닉네임 설정</h1>
            <p class="auth-sub">커뮤니티에서 사용할 닉네임을 정해주세요.</p>
        </header>

        <div class="auth-panel">
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
                <div class="field">
                    <label class="field-label" for="nickname">
                        <span>NICKNAME</span>
                        <span class="field-required">*</span>
                    </label>
                    <input
                        type="text"
                        id="nickname"
                        name="nickname"
                        class="arena-input"
                        class:error={errors.nickname}
                        placeholder="2~50자, 한글/영문/숫자"
                        minlength="2"
                        maxlength="50"
                        required
                        bind:value={nickname}
                    />
                    {#if errors.nickname}
                        <p class="field-error">{errors.nickname}</p>
                    {:else}
                        <p class="field-hint">한글, 영문, 숫자, 밑줄(_), 하이픈(-) 사용 가능</p>
                    {/if}
                </div>

                <button
                    type="submit"
                    class="arena-submit"
                    disabled={isSubmitting || !nickname.trim()}
                >
                    <span>설정 완료</span>
                    <span class="arena-submit-arrow">→</span>
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
        padding: 56px 24px 80px;
        background: var(--arena-paper);
    }
    .auth-shell {
        width: 100%;
        max-width: 380px;
        display: flex;
        flex-direction: column;
        gap: 24px;
    }
    .auth-head {
        display: flex;
        flex-direction: column;
        gap: 4px;
        align-items: flex-start;
    }
    .kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: var(--arena-ink-soft);
    }
    .auth-title {
        font-family: var(--arena-f-display);
        font-size: 36px;
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
    }

    .auth-panel {
        background: var(--arena-paper);
        border: 1px solid var(--arena-line);
        padding: 20px;
    }

    .field { display: flex; flex-direction: column; gap: 6px; }
    .field-label {
        display: flex;
        align-items: center;
        gap: 4px;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
    }
    .field-required { color: var(--arena-urgent); }
    .field-hint {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-mute);
        margin: 0;
    }
    .field-error {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-urgent);
        margin: 0;
    }

    .arena-input {
        width: 100%;
        padding: 11px 14px;
        background: var(--arena-paper);
        border: 1px solid var(--arena-line);
        font-family: var(--arena-f-body);
        font-size: 14px;
        color: var(--arena-ink);
        outline: none;
        transition: border-color 0.1s;
    }
    .arena-input::placeholder { color: var(--arena-ink-mute); }
    .arena-input:focus { border-color: var(--arena-ink); box-shadow: inset 0 0 0 1px var(--arena-ink); }
    .arena-input.error { border-color: var(--arena-urgent); }

    .arena-submit {
        margin-top: 18px;
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
        transition: transform 0.1s;
    }
    .arena-submit:active:not(:disabled) { transform: translateY(1px); }
    .arena-submit:disabled { opacity: 0.5; cursor: not-allowed; }
    .arena-submit-arrow {
        font-family: var(--arena-f-mono);
        font-size: 14px;
        color: var(--arena-accent);
    }

</style>
