<script lang="ts">
    import { page } from '$app/stores';
    import { clientApiFetch } from '$lib/api.client';
    import type { OAuthLoginResponse } from '$lib/types';

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

            // Save state for naver CSRF check
            if (result.state) {
                sessionStorage.setItem('oauth_state', result.state);
            }

            // Redirect to provider
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

<div class="container mx-auto px-4 py-16">
    <div class="max-w-sm mx-auto">
        <div class="text-center mb-8">
            <a href="/" class="text-3xl font-bold inline-flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span><span class="text-primary">Enduro</span><span class="text-base-content">Hub</span></span>
            </a>
            <p class="mt-4 text-base-content/60">소셜 계정으로 간편 로그인</p>
        </div>

        <div class="card bg-base-100 border border-base-300">
            <div class="card-body space-y-3">
                <!-- Kakao -->
                <button
                    class="btn btn-block justify-start gap-3 border-none"
                    style="background:#FEE500;color:#191919;"
                    onclick={() => handleLogin('kakao')}
                    disabled={!!isLoading}
                >
                    {#if isLoading === 'kakao'}
                        <span class="loading loading-spinner loading-sm"></span>
                    {:else}
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" fill="#191919"><path d="M12 3C6.48 3 2 6.48 2 10.5c0 2.55 1.7 4.8 4.25 6.08-.13.47-.85 3.02-.88 3.24 0 0-.02.17.08.24.1.07.22.03.22.03.3-.04 3.44-2.27 3.98-2.66.77.1 1.56.17 2.35.17 5.52 0 10-3.48 10-7.78C22 6.48 17.52 3 12 3z"/></svg>
                    {/if}
                    카카오로 시작하기
                </button>

                <!-- Naver -->
                <button
                    class="btn btn-block justify-start gap-3 border-none text-white"
                    style="background:#03C75A;"
                    onclick={() => handleLogin('naver')}
                    disabled={!!isLoading}
                >
                    {#if isLoading === 'naver'}
                        <span class="loading loading-spinner loading-sm"></span>
                    {:else}
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" fill="white"><path d="M16.273 12.845L7.376 0H0v24h7.727V11.155L16.624 24H24V0h-7.727z" transform="scale(0.6) translate(8,8)"/></svg>
                    {/if}
                    네이버로 시작하기
                </button>

                <!-- Google -->
                <button
                    class="btn btn-block justify-start gap-3 bg-white hover:bg-gray-50 border border-gray-300 text-gray-700"
                    onclick={() => handleLogin('google')}
                    disabled={!!isLoading}
                >
                    {#if isLoading === 'google'}
                        <span class="loading loading-spinner loading-sm"></span>
                    {:else}
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24">
                            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
                            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                        </svg>
                    {/if}
                    Google로 시작하기
                </button>

                {#if error}
                    <div class="alert alert-error mt-4">
                        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        <span class="text-sm">{error}</span>
                    </div>
                {/if}
            </div>
        </div>

        <p class="text-center text-sm text-base-content/50 mt-6">
            로그인 없이도 글쓰기와 댓글 작성이 가능합니다.
        </p>
    </div>
</div>
