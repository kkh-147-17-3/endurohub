<script lang="ts">
    import { page } from '$app/stores';
    import { clientApiFetch } from '$lib/api.client';
    import type { OAuthLoginResponse } from '$lib/types';
    import ProgressBar from '$lib/components/ProgressBar.svelte';

    let isLoading = $state<string | null>(null);
    let error = $state('');

    const appUrl = $derived($page.data.appUrl || 'https://www.endurohub.kr');

    async function handleLogin(provider: string) {
        if (isLoading) return;
        isLoading = provider;
        error = '';

        try {
            const redirectUri = `${appUrl}/auth/${provider}/callback`;
            const result = await clientApiFetch<OAuthLoginResponse>(
                `/auth/${provider}/login/`,
                {
                    method: 'POST',
                    body: { redirect_uri: redirectUri },
                }
            );

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
    <title>로그인 - 엔듀로허브</title>
    <meta name="description" content="소셜 계정으로 엔듀로허브에 로그인하세요." />
    <meta name="robots" content="noindex" />
</svelte:head>

<ProgressBar active={!!isLoading} />

<div class="auth-wrap">
    <div class="auth-shell">
        <header class="auth-head">
            <a class="auth-brand" href="/">
                <span class="brand-mark"></span>
                <span class="brand-name">EnduroHub</span>
            </a>
            <div class="kicker">SIGN IN · OAUTH</div>
            <h1 class="auth-title">로그인</h1>
            <p class="auth-sub">소셜 계정으로 간편 로그인</p>
        </header>

        <div class="auth-panel">
            <div class="oauth-list">
                <button
                    type="button"
                    class="oauth-btn oauth-kakao"
                    onclick={() => handleLogin('kakao')}
                    disabled={!!isLoading}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" class="oauth-icon" viewBox="0 0 24 24" fill="#191919">
                        <path d="M12 3C6.48 3 2 6.48 2 10.5c0 2.55 1.7 4.8 4.25 6.08-.13.47-.85 3.02-.88 3.24 0 0-.02.17.08.24.1.07.22.03.22.03.3-.04 3.44-2.27 3.98-2.66.77.1 1.56.17 2.35.17 5.52 0 10-3.48 10-7.78C22 6.48 17.52 3 12 3z" />
                    </svg>
                    <span class="oauth-label">카카오로 시작하기</span>
                    <span class="oauth-arrow">→</span>
                </button>

                <button
                    type="button"
                    class="oauth-btn oauth-naver"
                    onclick={() => handleLogin('naver')}
                    disabled={!!isLoading}
                >
                    <span class="oauth-icon naver-mark">N</span>
                    <span class="oauth-label">네이버로 시작하기</span>
                    <span class="oauth-arrow">→</span>
                </button>

                <button
                    type="button"
                    class="oauth-btn oauth-google"
                    onclick={() => handleLogin('google')}
                    disabled={!!isLoading}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" class="oauth-icon" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                    </svg>
                    <span class="oauth-label">Google로 시작하기</span>
                    <span class="oauth-arrow">→</span>
                </button>
            </div>

            {#if error}
                <div class="auth-error">
                    <span class="auth-error-mark">!</span>
                    <span class="auth-error-msg">{error}</span>
                </div>
            {/if}
        </div>

        <p class="auth-foot">로그인 없이도 글쓰기와 댓글 작성이 가능합니다.</p>
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
    .auth-brand {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 24px;
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: 18px;
        letter-spacing: -0.5px;
        color: var(--arena-ink);
        text-decoration: none;
    }
    .brand-mark {
        width: 8px;
        height: 8px;
        background: var(--arena-accent);
    }
    .brand-name :global(.accent) {
        color: var(--arena-accent-deep);
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
        display: flex;
        flex-direction: column;
        gap: 16px;
    }

    .oauth-list { display: flex; flex-direction: column; gap: 8px; }
    .oauth-btn {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        border: 1px solid var(--arena-line-soft);
        background: var(--arena-paper);
        font-family: var(--arena-f-display);
        font-weight: 600;
        font-size: 14px;
        letter-spacing: -0.2px;
        color: var(--arena-ink);
        cursor: pointer;
        transition: transform 0.1s, border-color 0.1s;
        text-align: left;
    }
    .oauth-btn:active:not(:disabled) { transform: translateY(1px); }
    .oauth-btn:disabled { cursor: not-allowed; opacity: 0.6; }
    .oauth-btn:hover:not(:disabled) { border-color: var(--arena-ink); }
    .oauth-icon {
        width: 18px;
        height: 18px;
        flex-shrink: 0;
    }
    .oauth-label { flex: 1; }
    .oauth-arrow {
        font-family: var(--arena-f-mono);
        font-size: 13px;
        color: var(--arena-ink-soft);
    }

    .oauth-kakao {
        background: #FEE500;
        border-color: #FEE500;
        color: #191919;
    }
    .oauth-kakao:hover:not(:disabled) { border-color: #191919; }
    .oauth-kakao .oauth-arrow { color: rgba(25, 25, 25, 0.6); }

    .oauth-naver {
        background: #03C75A;
        border-color: #03C75A;
        color: #fff;
    }
    .oauth-naver:hover:not(:disabled) { border-color: #fff; box-shadow: inset 0 0 0 1px #03C75A; }
    .oauth-naver .oauth-arrow { color: rgba(255, 255, 255, 0.7); }
    .naver-mark {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: 13px;
        color: #fff;
    }

    .oauth-google {
        background: var(--arena-paper);
        border-color: var(--arena-line-soft);
        color: var(--arena-ink);
    }

    .auth-error {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        background: var(--arena-paper-alt);
        border: 1px solid var(--arena-urgent);
        font-family: var(--arena-f-mono);
        font-size: 12px;
        color: var(--arena-urgent);
    }
    .auth-error-mark {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        background: var(--arena-urgent);
        color: var(--arena-paper);
        font-weight: 700;
        flex-shrink: 0;
    }
    .auth-error-msg { flex: 1; }

    .auth-foot {
        text-align: center;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.3px;
        color: var(--arena-ink-mute);
        margin: 0;
    }

</style>
