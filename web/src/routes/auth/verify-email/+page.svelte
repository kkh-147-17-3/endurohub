<script lang="ts">
    import { enhance } from '$app/forms';
    import ProgressBar from '$lib/components/ProgressBar.svelte';

    let { data, form } = $props();

    let user = $derived(data.user);
    let hasPendingSocialLogin = $derived(!!data.hasPendingSocialLogin);
    let email = $state('');
    let code = $state('');
    let emailUpdatesOptIn = $state(false);
    let isSubmitting = $state(false);
    let isSending = $state(false);

    let errors = $derived(flattenErrors(form?.errors));
    let sendErrors = $derived(flattenErrors(form?.sendErrors));
    let sendMessage = $derived(form?.sendMessage || '');

    function flattenErrors(errs: Record<string, string[]> | undefined): Record<string, string> {
        if (!errs) return {};
        const flat: Record<string, string> = {};
        for (const [key, msgs] of Object.entries(errs)) {
            flat[key] = Array.isArray(msgs) ? msgs[0] : msgs;
        }
        return flat;
    }

    function normalizeOtpDigits(raw: string): string {
        const ascii = raw.replace(/[０-９]/g, (c) =>
            String.fromCharCode(c.charCodeAt(0) - 0xff10 + 0x30)
        );
        return ascii.replace(/\D/g, '').slice(0, 6);
    }

    $effect(() => {
        if (!email) {
            email = form?.email || data.user?.email || '';
        }

        if (form?.emailUpdatesOptIn !== undefined) {
            emailUpdatesOptIn = !!form.emailUpdatesOptIn;
        } else if (user?.emailUpdatesOptIn !== undefined) {
            emailUpdatesOptIn = !!user.emailUpdatesOptIn;
        }
    });
</script>

<svelte:head>
    <title>이메일 인증 - 엔듀로허브</title>
    <meta name="robots" content="noindex" />
</svelte:head>

<ProgressBar active={isSending || isSubmitting} />

<div class="auth-wrap">
    <div class="auth-shell">
        <header class="auth-head">
            <h1 class="auth-title">이메일 인증</h1>
            <p class="auth-sub">
                {#if hasPendingSocialLogin}
                    소셜 로그인 가입을 완료하려면 이메일 인증이 필요합니다.
                {:else if user?.email}
                    가입한 이메일로 전송된 인증 코드를 입력해주세요.
                {:else}
                    인증 코드를 받을 이메일을 먼저 입력해주세요.
                {/if}
            </p>
        </header>

        <div class="auth-panel">
            <!-- 1단계: 코드 발송 -->
            <section class="verify-step">
                <div class="step-marker">
                    <span class="step-num">1</span>
                    <span class="step-name">이메일 입력</span>
                </div>

                <form
                    method="POST"
                    action="?/send"
                    use:enhance={() => {
                        isSending = true;
                        return async ({ update }) => {
                            isSending = false;
                            await update();
                        };
                    }}
                >
                    <div class="field">
                        <label class="field-label" for="email">이메일</label>
                        <input
                            type="email"
                            id="email"
                            name="email"
                            class="arena-input"
                            class:error={sendErrors.email}
                            placeholder="you@example.com"
                            autocomplete="email"
                            bind:value={email}
                        />
                        {#if sendErrors.email}
                            <p class="field-error">{sendErrors.email}</p>
                        {:else}
                            <p class="field-hint">인증 코드는 이 주소로 발송됩니다.</p>
                        {/if}
                    </div>

                    <label class="optin">
                        <input
                            type="checkbox"
                            name="email_updates_opt_in"
                            class="optin-check"
                            bind:checked={emailUpdatesOptIn}
                        />
                        <span class="optin-box" class:checked={emailUpdatesOptIn} aria-hidden="true">
                            {emailUpdatesOptIn ? '✓' : ''}
                        </span>
                        <span class="optin-text">
                            <span class="optin-tag">선택</span>
                            대회 소식, 업데이트, 이벤트 등 이메일 알림 수신에 동의합니다.
                            <span class="optin-note">계정 관련 중요 안내는 동의 여부와 관계없이 발송됩니다.</span>
                        </span>
                    </label>

                    <button type="submit" class="arena-ghost" disabled={isSending || !email.trim()}>
                        <span>인증 코드 발송</span>
                        <span class="arena-arrow">→</span>
                    </button>
                    {#if sendMessage}
                        <p class="send-success">
                            <span class="send-success-mark"></span>
                            {sendMessage}
                        </p>
                    {/if}
                </form>
            </section>

            <div class="step-divider"></div>

            <!-- 2단계: 인증 코드 입력 -->
            <section class="verify-step">
                <div class="step-marker">
                    <span class="step-num">2</span>
                    <span class="step-name">인증 코드 입력</span>
                </div>

                <form
                    method="POST"
                    action="?/verify"
                    use:enhance={() => {
                        isSubmitting = true;
                        return async ({ update }) => {
                            isSubmitting = false;
                            await update();
                        };
                    }}
                >
                    <input type="hidden" name="email" value={email} />
                    <input type="hidden" name="email_updates_opt_in" value={emailUpdatesOptIn ? 'true' : 'false'} />

                    <div class="field">
                        <label class="field-label" for="code">인증 코드 <span class="field-label-meta">6자리 숫자</span></label>
                        <input
                            type="text"
                            id="code"
                            name="code"
                            class="arena-input otp-input"
                            class:error={errors.code}
                            placeholder="000000"
                            maxlength="6"
                            inputmode="numeric"
                            autocomplete="one-time-code"
                            required
                            value={code}
                            oninput={(e) => {
                                code = normalizeOtpDigits(e.currentTarget.value);
                            }}
                        />
                        {#if errors.code}
                            <p class="field-error">{errors.code}</p>
                        {/if}
                    </div>

                    <button
                        type="submit"
                        class="arena-submit"
                        disabled={isSubmitting || code.length !== 6}
                    >
                        <span>인증 확인</span>
                        <span class="arena-arrow">→</span>
                    </button>
                </form>
            </section>
        </div>

        <div class="auth-foot">
            <a href={hasPendingSocialLogin ? '/auth/login' : '/'} class="foot-link">
                {hasPendingSocialLogin ? '← 로그인 다시 하기' : '나중에 하기'}
            </a>
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
        max-width: 440px;
        display: flex;
        flex-direction: column;
        gap: 28px;
    }

    .auth-head {
        display: flex;
        flex-direction: column;
        gap: 8px;
        align-items: flex-start;
    }
    .auth-title {
        font-family: var(--arena-f-display);
        font-size: 36px;
        font-weight: 700;
        letter-spacing: -1px;
        line-height: 1;
        margin: 0;
        color: var(--arena-ink);
    }
    .auth-sub {
        font-family: var(--arena-f-body);
        font-size: 15px;
        color: var(--arena-ink);
        margin: 0;
        line-height: 1.55;
    }

    .auth-panel {
        background: var(--arena-paper);
        border: 1px solid var(--arena-line);
        padding: 4px 24px;
    }

    .verify-step { padding: 22px 0; }
    .step-marker {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 18px;
    }
    .step-num {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 26px;
        height: 26px;
        background: var(--arena-ink);
        color: var(--arena-paper);
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: 15px;
        flex-shrink: 0;
    }
    .step-name {
        font-family: var(--arena-f-body);
        font-weight: 700;
        font-size: 16px;
        letter-spacing: -0.2px;
        color: var(--arena-ink);
    }
    .step-divider {
        height: 1px;
        background: var(--arena-line-soft);
    }

    .field { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
    .field-label {
        font-family: var(--arena-f-body);
        font-size: 14px;
        font-weight: 600;
        color: var(--arena-ink);
        display: flex;
        align-items: baseline;
        gap: 8px;
    }
    .field-label-meta {
        font-weight: 500;
        font-size: 12px;
        color: var(--arena-ink-soft);
    }
    .field-hint {
        font-family: var(--arena-f-body);
        font-size: 13px;
        color: var(--arena-ink-soft);
        margin: 0;
    }
    .field-error {
        font-family: var(--arena-f-body);
        font-size: 13px;
        font-weight: 500;
        color: var(--arena-urgent);
        margin: 0;
    }

    .arena-input {
        width: 100%;
        padding: 12px 14px;
        background: var(--arena-paper);
        border: 1px solid var(--arena-line);
        font-family: var(--arena-f-body);
        font-size: 15px;
        color: var(--arena-ink);
        outline: none;
        transition: border-color 0.1s;
    }
    .arena-input::placeholder { color: var(--arena-ink-mute); }
    .arena-input:focus { border-color: var(--arena-ink); box-shadow: inset 0 0 0 1px var(--arena-ink); }
    .arena-input.error { border-color: var(--arena-urgent); }

    .otp-input {
        text-align: center;
        font-family: var(--arena-f-mono);
        font-size: 28px;
        letter-spacing: 0.5em;
        font-weight: 600;
        padding: 16px;
    }

    /* 알림 수신 동의 체크박스 */
    .optin {
        display: flex;
        gap: 12px;
        align-items: flex-start;
        padding: 14px;
        border: 1px solid var(--arena-line-soft);
        background: var(--arena-paper-alt);
        margin-bottom: 14px;
        cursor: pointer;
    }
    .optin-check {
        position: absolute;
        opacity: 0;
        pointer-events: none;
    }
    .optin-box {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
        font-family: var(--arena-f-mono);
        font-size: 12px;
        color: var(--arena-paper);
        flex-shrink: 0;
        margin-top: 2px;
        transition: background 0.1s, border-color 0.1s;
    }
    .optin-box.checked {
        background: var(--arena-ink);
        border-color: var(--arena-ink);
        color: var(--arena-accent);
    }
    .optin-text {
        font-family: var(--arena-f-body);
        font-size: 14px;
        line-height: 1.55;
        color: var(--arena-ink);
        flex: 1;
    }
    .optin-tag {
        display: inline-block;
        font-family: var(--arena-f-body);
        font-size: 12px;
        font-weight: 700;
        padding: 1px 6px;
        margin-right: 6px;
        background: var(--arena-ink);
        color: var(--arena-paper);
        vertical-align: 1px;
    }
    .optin-note {
        display: block;
        margin-top: 6px;
        font-size: 13px;
        color: var(--arena-ink-soft);
    }

    .send-success {
        margin: 12px 0 0;
        display: flex;
        align-items: center;
        gap: 8px;
        font-family: var(--arena-f-body);
        font-size: 13px;
        font-weight: 500;
        color: var(--arena-accent-deep);
    }
    .send-success-mark {
        width: 8px;
        height: 8px;
        background: var(--arena-accent);
        flex-shrink: 0;
    }

    /* 버튼 */
    .arena-ghost {
        width: 100%;
        padding: 13px 16px;
        background: var(--arena-paper);
        color: var(--arena-ink);
        border: 1px solid var(--arena-line);
        font-family: var(--arena-f-body);
        font-weight: 600;
        font-size: 14px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        transition: background 0.1s;
    }
    .arena-ghost:hover:not(:disabled) { background: var(--arena-paper-alt); }
    .arena-ghost:disabled { opacity: 0.5; cursor: not-allowed; }

    .arena-submit {
        width: 100%;
        padding: 14px 16px;
        background: var(--arena-ink);
        color: var(--arena-paper);
        border: none;
        font-family: var(--arena-f-display);
        font-weight: 600;
        font-size: 15px;
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

    .arena-arrow {
        font-family: var(--arena-f-mono);
        font-size: 15px;
        color: var(--arena-accent);
    }
    .arena-ghost .arena-arrow { color: var(--arena-ink-soft); }

    .auth-foot {
        text-align: center;
    }
    .foot-link {
        font-family: var(--arena-f-body);
        font-size: 13px;
        color: var(--arena-ink-soft);
        text-decoration: underline;
        text-decoration-color: var(--arena-line-soft);
        text-underline-offset: 4px;
    }
    .foot-link:hover { color: var(--arena-ink); }
</style>
