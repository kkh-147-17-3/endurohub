<script lang="ts">
    import { page } from '$app/stores';
    import { clientApiFetch } from '$lib/api.client';
    import type { OAuthLoginResponse } from '$lib/types';
    import ProgressBar from '$lib/components/ProgressBar.svelte';

    let isLoading = $state<string | null>(null);
    let error = $state('');

    const appUrl = $derived($page.data.appUrl || 'https://www.endurohub.kr');

    // Official provider buttons — brand colours, logos, and wording per each
    // service's sign-in button guidelines (Kakao / Naver / Google).
    const SOCIALS = [
        {
            id: 'kakao',
            label: '카카오 로그인',
            svg: '<svg viewBox="0 0 18 18" width="18" height="18" aria-hidden="true"><path fill="#000000" d="M9 1.2C4.58 1.2 1 3.98 1 7.41c0 2.2 1.47 4.12 3.68 5.2-.16.57-.59 2.13-.67 2.46-.1.41.15.4.32.29.13-.09 2.07-1.4 2.91-1.97.57.08 1.16.13 1.76.13 4.42 0 8-2.78 8-6.21C17 3.98 13.42 1.2 9 1.2z"/></svg>'
        },
        {
            id: 'naver',
            label: '네이버 로그인',
            svg: '<svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true"><path fill="#ffffff" d="M16.273 12.845 7.376 0H0v24h7.726V11.156L16.624 24H24V0h-7.727z"/></svg>'
        },
        {
            id: 'google',
            label: 'Google 계정으로 로그인',
            svg: '<svg viewBox="0 0 18 18" width="18" height="18" aria-hidden="true"><path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"/><path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"/><path fill="#FBBC05" d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"/><path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"/></svg>'
        }
    ];

    async function handleLogin(provider: string) {
        if (isLoading) return;
        isLoading = provider;
        error = '';

        try {
            const redirectUri = `${appUrl}/auth/${provider}/callback`;
            const result = await clientApiFetch<OAuthLoginResponse>(`/auth/${provider}/login/`, {
                method: 'POST',
                body: { redirect_uri: redirectUri }
            });

            if ('error' in result || 'detail' in result) {
                error = (result as any).error || (result as any).detail || '로그인 요청에 실패했습니다.';
                isLoading = null;
                return;
            }

            if (!result.authorizeUrl) {
                error = '로그인 요청에 실패했습니다. 다시 시도해주세요.';
                isLoading = null;
                return;
            }

            if (result.state) {
                sessionStorage.setItem('oauth_state', result.state);
            }

            window.location.href = result.authorizeUrl;
        } catch {
            error = '로그인 요청에 실패했습니다. 다시 시도해주세요.';
            isLoading = null;
        }
    }
</script>

<svelte:head>
    <title>ENDUROHUB — 로그인</title>
    <meta name="description" content="소셜 계정으로 엔듀로허브에 로그인하세요." />
    <meta name="robots" content="noindex" />
</svelte:head>

<ProgressBar active={!!isLoading} />

<div class="auth">
    <!-- ── Left ink hero panel ── -->
    <aside class="auth-hero">
        <a class="hero-wordmark" href="/">ENDURO<span class="slash">/</span>HUB</a>

        <h1 class="hero-display">출발선까지,<br />가장 빠른 길.</h1>
    </aside>

    <!-- ── Right form panel ── -->
    <div class="auth-pane">
        <span class="pane-url eh-data">WWW.ENDUROHUB.KR/AUTH/LOGIN</span>

        <div class="auth-form">
            <a class="form-brand" href="/">ENDURO<span class="slash">/</span>HUB</a>

            <div class="eh-micro sign-eyebrow"><span class="acc">SIGN IN</span></div>
            <h2 class="auth-title">로그인</h2>
            <p class="auth-sub">대회 일정, 시즌 플랜, 기록이 계정에 저장됩니다.</p>

            <div class="social-col">
                {#each SOCIALS as s (s.id)}
                    <button
                        type="button"
                        class="social-btn {s.id}"
                        onclick={() => handleLogin(s.id)}
                        disabled={!!isLoading}
                    >
                        <span class="logo">{@html s.svg}</span>
                        <span>{isLoading === s.id ? '연결 중…' : s.label}</span>
                        <span></span>
                    </button>
                {/each}
            </div>

            {#if error}
                <div class="auth-error" role="alert">
                    <span class="auth-error-mark">!</span>
                    <span>{error}</span>
                </div>
            {/if}

            <p class="terms-note">
                계속하면 <a href="/terms" class="terms-link">서비스 이용약관</a> 및
                <a href="/privacy" class="terms-link">개인정보 처리방침</a>을 확인할 수 있습니다. 필수 동의는 이메일 인증 단계에서 받습니다.
            </p>
        </div>
    </div>
</div>

<style>
    .auth {
        min-height: 100vh;
        display: grid;
        grid-template-columns: minmax(380px, 44%) 1fr;
        background: var(--bg-page);
    }

    /* ── Left ink panel — pinned dark in both themes (editorial intent) ── */
    .auth-hero {
        position: relative;
        background-color: #101312;
        background-image:
            linear-gradient(180deg, rgba(16, 19, 18, 0.55) 0%, rgba(16, 19, 18, 0.35) 38%, rgba(16, 19, 18, 0.88) 100%),
            url('/images/login-hero.webp');
        background-size: cover;
        background-position: center 30%;
        background-repeat: no-repeat;
        color: #fff;
        padding: 36px 44px 40px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 100vh;
    }
    .hero-wordmark {
        font-weight: 900;
        font-size: 18px;
        letter-spacing: -0.02em;
        color: #fff;
        text-decoration: none;
        white-space: nowrap;
    }
    .hero-wordmark .slash,
    .form-brand .slash { color: var(--accent); }

    .hero-display {
        font-size: clamp(40px, 4.6vw, 64px);
        font-weight: var(--w-display);
        letter-spacing: var(--track-display);
        line-height: 0.98;
        text-wrap: balance;
        margin: 0 0 30vh;
    }

    /* ── Right form panel ── */
    .auth-pane {
        display: grid;
        place-items: center;
        padding: 48px var(--container-pad-mobile);
        position: relative;
    }
    .pane-url {
        position: absolute;
        top: 22px;
        right: 28px;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.08em;
        color: var(--text-faint);
    }
    .auth-form {
        width: 100%;
        max-width: 380px;
        display: flex;
        flex-direction: column;
    }
    .form-brand {
        display: none;
        margin-bottom: 40px;
        font-weight: 900;
        font-size: 17px;
        letter-spacing: -0.02em;
        color: var(--text-strong);
        text-decoration: none;
    }

    .sign-eyebrow { margin-bottom: 10px; }
    .auth-title {
        font-size: clamp(30px, 4vw, 38px);
        font-weight: var(--w-display);
        letter-spacing: var(--track-display);
        line-height: 1.05;
        margin: 0;
        color: var(--text-strong);
    }
    .auth-sub {
        color: var(--text-muted);
        font-size: 14.5px;
        line-height: var(--leading-body);
        margin: 12px 0 0;
        word-break: keep-all;
    }

    /* ── Social buttons — official provider styling ── */
    .social-col {
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-top: 28px;
    }
    .social-btn {
        height: 48px;
        display: grid;
        grid-template-columns: 48px 1fr 48px;
        align-items: center;
        border: 1px solid transparent;
        border-radius: var(--r-1);
        font-family: var(--font-sans);
        font-size: 14.5px;
        font-weight: 600;
        cursor: pointer;
        transition: filter var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out), box-shadow var(--dur-fast) var(--ease-out);
    }
    .social-btn:active:not(:disabled) { transform: translateY(1px); }
    .social-btn:disabled { cursor: not-allowed; opacity: 0.55; }
    .social-btn .logo {
        width: 18px;
        height: 18px;
        margin-left: 16px;
        display: grid;
        place-items: center;
    }
    .social-btn .logo :global(svg) { display: block; }

    /* Kakao — yellow #FEE500, black symbol, label 85% black */
    .social-btn.kakao {
        background: #fee500;
        color: rgba(0, 0, 0, 0.85);
    }
    .social-btn.kakao:hover:not(:disabled) { filter: brightness(0.96); }

    /* Naver — green #03C75A, white logo + label */
    .social-btn.naver {
        background: #03c75a;
        color: #ffffff;
    }
    .social-btn.naver:hover:not(:disabled) { filter: brightness(0.96); }

    /* Google — white, neutral border, 4-colour G, #1f1f1f label */
    .social-btn.google {
        background: #ffffff;
        color: #1f1f1f;
        border-color: #747775;
    }
    .social-btn.google:hover:not(:disabled) {
        background: #f7f8f8;
        box-shadow: 0 1px 2px rgba(60, 64, 67, 0.16);
    }

    /* ── Error ── */
    .auth-error {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 16px;
        padding: 10px 12px;
        border: 1px solid var(--danger);
        font-size: 12.5px;
        color: var(--danger);
        line-height: 1.5;
    }
    .auth-error-mark {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        flex-shrink: 0;
        background: var(--danger);
        color: var(--paper-0);
        font-weight: 700;
    }

    .terms-note {
        margin-top: 24px;
        padding-top: 14px;
        border-top: var(--border-hair);
        font-size: 12.5px;
        color: var(--text-faint);
        line-height: 1.6;
        text-wrap: pretty;
    }
    .terms-link { color: var(--text-muted); text-decoration: underline; text-underline-offset: 2px; }
    .terms-link:hover { color: var(--text-strong); }

    @media (max-width: 880px) {
        .auth {
            grid-template-columns: 1fr;
            grid-template-rows: auto 1fr;
        }

        /* Hero collapses into a top band instead of disappearing */
        .auth-hero {
            min-height: 0;
            height: 40vh;
            max-height: 340px;
            padding: 22px 24px 26px;
        }
        .hero-display {
            font-size: clamp(32px, 9.5vw, 46px);
            margin-bottom: 0;
        }

        /* Wordmark lives in the hero band, so keep the form brand hidden */
        .form-brand { display: none; }
        .pane-url { display: none; }
        .auth-pane { padding-top: 36px; align-items: start; }
    }
</style>
