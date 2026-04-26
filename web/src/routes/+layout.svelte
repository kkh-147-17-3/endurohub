<script lang="ts" module>
    declare const Kakao: any;
</script>

<script lang="ts">
    import '../app.css';
    import { page } from '$app/stores';
    import { navigating } from '$app/stores';
    import { afterNavigate } from '$app/navigation';
    import { onMount } from 'svelte';
    import { capturePostHogPageView, initPostHog, syncPostHogUser } from '$lib/posthog';
    import { getTheme, toggleTheme, type Theme } from '$lib/theme';
    import ProgressBar from '$lib/components/ProgressBar.svelte';

    let { data, children } = $props();

    let currentYear = $derived(data.currentYear);
    let feedbackFormUrl = $derived(data.feedbackFormUrl);
    let googleAnalyticsId = $derived(data.googleAnalyticsId);
    let kakaoJsKey = $derived(data.kakaoJsKey);
    let user = $derived(data.user);
    let currentPath = $derived($page.url.pathname);

    let userLabel = $derived(
        user ? (user.nickname?.trim() || user.email.split('@')[0] || '계정') : ''
    );

    let theme = $state<Theme>('light');
    let lastTrackedPath = $state('');
    let mobileMenuOpen = $state(false);
    let userMenuOpen = $state(false);

    onMount(() => {
        theme = getTheme();
        initPostHog();
        syncPostHogUser(user);

        const initialPath = $page.url.pathname + $page.url.search;
        capturePostHogPageView($page.url.pathname, $page.url.search, document.referrer);
        lastTrackedPath = initialPath;

        if (googleAnalyticsId && !document.querySelector('script[src*="googletagmanager"]')) {
            window.dataLayer = window.dataLayer || [];
            window.gtag = function () {
                window.dataLayer.push(arguments);
            };
            window.gtag('js', new Date());
            window.gtag('config', googleAnalyticsId);
            const gaScript = document.createElement('script');
            gaScript.src = `https://www.googletagmanager.com/gtag/js?id=${googleAnalyticsId}`;
            gaScript.async = true;
            document.head.appendChild(gaScript);
        }

        if (kakaoJsKey && !document.querySelector('script[src*="kakao_js_sdk"]')) {
            const script = document.createElement('script');
            script.src = 'https://t1.kakaocdn.net/kakao_js_sdk/2.7.4/kakao.min.js';
            script.crossOrigin = 'anonymous';
            script.defer = true;
            script.onload = () => {
                if (typeof Kakao !== 'undefined' && !Kakao.isInitialized()) {
                    Kakao.init(kakaoJsKey);
                }
            };
            document.head.appendChild(script);
        }
    });

    $effect(() => {
        syncPostHogUser(user);
    });

    function handleToggleTheme() {
        theme = toggleTheme();
    }

    afterNavigate(() => {
        const pathWithSearch = `${$page.url.pathname}${$page.url.search}`;
        if (lastTrackedPath !== pathWithSearch) {
            capturePostHogPageView($page.url.pathname, $page.url.search, document.referrer);
            lastTrackedPath = pathWithSearch;
        }
        if (googleAnalyticsId && typeof gtag === 'function') {
            gtag('config', googleAnalyticsId, { page_path: $page.url.pathname });
        }
        mobileMenuOpen = false;
        userMenuOpen = false;
    });

    const links = [
        { href: '/', label: '홈', match: (p: string) => p === '/' },
        { href: '/races?reset=1', label: '전체 대회', match: (p: string) => p === '/races' },
        { href: '/races/year/2026', label: '2026년 대회', match: (p: string) => p === '/races/year/2026' },
        { href: '/calendar', label: '캘린더', match: (p: string) => p === '/calendar' },
        { href: '/posts', label: '커뮤니티', match: (p: string) => p.startsWith('/posts') },
        { href: '/tools', label: '도구', match: (p: string) => p.startsWith('/tools') || p === '/running-terms' },
    ];

    const sportLinks = [
        { href: '/running', label: '마라톤', code: 'RUN' },
        { href: '/swimming', label: '수영', code: 'SWIM' },
        { href: '/cycling', label: '자전거', code: 'CYCLE' },
        { href: '/triathlon', label: '철인3종', code: 'TRI' },
        { href: '/trail-running', label: '트레일러닝', code: 'TRL' },
    ];
</script>

<svelte:head>
    <meta property="og:site_name" content="EnduroHub" />
    <meta property="og:url" content="{data.appUrl}{currentPath}" />
    <meta property="og:locale" content="ko_KR" />
    <meta name="twitter:card" content="summary_large_image" />
    <link rel="canonical" href="{data.appUrl}{currentPath}" />
</svelte:head>

<nav class="arena-nav">
    <div class="nav-inner">
        <a href="/" class="nav-logo">
            <span class="logo-dot"></span>
            endurohub
        </a>

        <div class="nav-links desktop">
            {#each links as l (l.href)}
                <a
                    href={l.href}
                    class="nav-link"
                    class:active={l.match(currentPath)}
                >
                    {l.label}
                </a>
            {/each}
        </div>

        <div class="nav-spacer"></div>

        <button
            class="theme-toggle"
            onclick={handleToggleTheme}
            aria-label={theme === 'dark' ? '라이트 모드로 전환' : '다크 모드로 전환'}
            title="테마 전환"
        >
            {#if theme === 'dark'}
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
            {:else}
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
            {/if}
        </button>

        {#if user}
            <a
                href="/mypage/favorites"
                class="user-icon"
                class:active={currentPath === '/mypage/favorites'}
                aria-label="관심 대회"
                title="관심 대회"
            >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 21s-7.5-4.35-10-9.5C.5 7 3 3 7 3c2.1 0 3.6 1 5 2.5C13.4 4 14.9 3 17 3c4 0 6.5 4 5 8.5-2.5 5.15-10 9.5-10 9.5z" />
                </svg>
            </a>
            <div class="user-dropdown">
                <button
                    class="avatar-btn"
                    onclick={() => (userMenuOpen = !userMenuOpen)}
                    aria-expanded={userMenuOpen}
                    aria-label="계정 메뉴"
                >
                    {#if user.profileImage}
                        <img src={user.profileImage} alt={userLabel} />
                    {:else}
                        <span class="avatar-fallback">{userLabel.charAt(0).toUpperCase()}</span>
                    {/if}
                </button>
                {#if userMenuOpen}
                    <ul class="user-menu">
                        <li class="user-menu-label" title={user.email}>{userLabel}</li>
                        <li><a href="/mypage" onclick={() => (userMenuOpen = false)}>마이페이지</a></li>
                        <li><a href="/mypage/favorites" onclick={() => (userMenuOpen = false)}>관심 대회</a></li>
                        <li>
                            <form method="POST" action="/auth/logout">
                                <button type="submit">로그아웃</button>
                            </form>
                        </li>
                    </ul>
                {/if}
            </div>
        {:else}
            <a href="/auth/login" class="arena-btn arena-btn-ghost login-btn">로그인</a>
        {/if}

        <button
            class="hamburger"
            onclick={() => (mobileMenuOpen = !mobileMenuOpen)}
            aria-label="메뉴 열기"
            aria-expanded={mobileMenuOpen}
        >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                {#if mobileMenuOpen}
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                {:else}
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                {/if}
            </svg>
        </button>
    </div>

    {#if mobileMenuOpen}
        <div class="mobile-panel">
            <div class="mobile-section">
                {#each links as l (l.href)}
                    <a href={l.href} class="mobile-link" class:active={l.match(currentPath)}>{l.label}</a>
                {/each}
                <a href={`/races/year/${currentYear}`} class="mobile-link">{currentYear}년 대회</a>
            </div>
            <div class="mobile-section">
                <div class="arena-kicker mobile-kicker">By Sport</div>
                {#each sportLinks as s (s.href)}
                    <a href={s.href} class="mobile-link mobile-link-row">
                        <span>{s.label}</span>
                        <span class="mono-mini">{s.code}</span>
                    </a>
                {/each}
            </div>
            <div class="mobile-section">
                <div class="arena-kicker mobile-kicker">Tools</div>
                <a href="/tools/pace-calculator" class="mobile-link">페이스 계산기</a>
                <a href="/tools/training-plan" class="mobile-link">훈련 플랜</a>
                <a href="/tools/vo2max" class="mobile-link">VO2max</a>
                <a href="/tools/race-predictor" class="mobile-link">기록 예측</a>
                <a href="/running-terms" class="mobile-link">러닝 용어</a>
            </div>
            {#if user}
                <div class="mobile-section">
                    <div class="arena-kicker mobile-kicker">Account · {userLabel}</div>
                    <a href="/mypage" class="mobile-link">마이페이지</a>
                    <a href="/mypage/favorites" class="mobile-link">관심 대회</a>
                    <form method="POST" action="/auth/logout">
                        <button type="submit" class="mobile-link mobile-logout">로그아웃</button>
                    </form>
                </div>
            {:else}
                <div class="mobile-section">
                    <a href="/auth/login" class="mobile-link mobile-login">로그인</a>
                </div>
            {/if}
        </div>
    {/if}
</nav>

<ProgressBar active={!!$navigating} />

<main class="arena-main">
    {@render children()}
</main>

<footer class="arena-footer">
    <div class="footer-inner">
        <div class="footer-top">
            <div class="footer-brand">
                <a href="/" class="footer-logo">
                    <span class="logo-dot"></span>
                    endurohub
                </a>
                <p class="footer-desc">국내 마라톤 · 수영 · 자전거 · 철인3종 · 트레일러닝 대회 정보를 한곳에서.</p>
            </div>
            <div class="footer-cols">
                <div class="footer-col">
                    <div class="arena-kicker footer-kicker">Race</div>
                    <a href="/races?reset=1">전체 대회</a>
                    <a href={`/races/year/${currentYear}`}>{currentYear}년 대회</a>
                    <a href="/calendar">캘린더</a>
                </div>
                <div class="footer-col">
                    <div class="arena-kicker footer-kicker">Sport</div>
                    <a href="/running">마라톤</a>
                    <a href="/swimming">수영</a>
                    <a href="/cycling">자전거</a>
                    <a href="/triathlon">철인3종</a>
                    <a href="/trail-running">트레일러닝</a>
                </div>
                <div class="footer-col">
                    <div class="arena-kicker footer-kicker">Tools</div>
                    <a href="/tools/pace-calculator">페이스 계산기</a>
                    <a href="/tools/training-plan">훈련 플랜</a>
                    <a href="/tools/vo2max">VO2max</a>
                    <a href="/tools/race-predictor">기록 예측</a>
                    <a href="/running-terms">러닝 용어</a>
                </div>
                <div class="footer-col">
                    <div class="arena-kicker footer-kicker">Support</div>
                    <a href="/about">서비스 소개</a>
                    <a href="/privacy">개인정보처리방침</a>
                    <a href="mailto:contact@endurohub.kr">문의하기</a>
                    {#if feedbackFormUrl}
                        <a href={feedbackFormUrl} target="_blank" rel="noopener">피드백 보내기 ↗</a>
                    {/if}
                </div>
            </div>
        </div>
        <div class="footer-bottom">
            <span>© {currentYear} endurohub · 지구력 스포츠 대회 플랫폼</span>
            <span class="footer-meta">KR · {currentYear}</span>
        </div>
    </div>
</footer>

<style>
    /* ── Nav ─────────────────────────── */
    .arena-nav {
        position: sticky;
        top: 0;
        z-index: 50;
        background: var(--arena-paper);
        border-bottom: 1px solid var(--arena-line);
    }
    .nav-inner {
        max-width: 1400px;
        margin: 0 auto;
        padding: 14px 24px;
        display: flex;
        align-items: center;
        gap: 24px;
    }
    @media (min-width: 1024px) {
        .nav-inner {
            padding: 14px 32px;
            gap: 32px;
        }
    }
    .nav-logo {
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: 18px;
        letter-spacing: -0.5px;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        color: var(--arena-ink);
        text-decoration: none;
    }
    .logo-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        background: var(--arena-accent);
    }
    .nav-links {
        display: flex;
        gap: 4px;
    }
    .nav-link {
        padding: 6px 12px;
        font-size: 13px;
        font-weight: 500;
        font-family: var(--arena-f-body);
        color: var(--arena-ink-soft);
        white-space: nowrap;
        text-decoration: none;
    }
    .nav-link:hover {
        color: var(--arena-ink);
        background: var(--arena-paper-alt);
    }
    .nav-link.active {
        color: var(--arena-ink);
        background: var(--arena-paper-alt);
        box-shadow: inset 0 -2px 0 var(--arena-ink);
    }
    .nav-spacer {
        flex: 1;
    }
    .theme-toggle,
    .user-icon,
    .avatar-btn,
    .hamburger {
        background: transparent;
        border: 1px solid transparent;
        padding: 6px;
        cursor: pointer;
        color: var(--arena-ink-soft);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
    }
    .theme-toggle:hover,
    .user-icon:hover {
        color: var(--arena-ink);
        background: var(--arena-paper-alt);
    }
    .user-icon.active {
        color: var(--arena-urgent);
    }
    .avatar-btn {
        padding: 0;
        width: 32px;
        height: 32px;
        overflow: hidden;
    }
    .avatar-btn img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .avatar-fallback {
        width: 32px;
        height: 32px;
        display: grid;
        place-items: center;
        background: var(--arena-paper-alt);
        color: var(--arena-ink);
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: 13px;
        border: 1px solid var(--arena-line);
    }
    .user-dropdown {
        position: relative;
    }
    .user-menu {
        position: absolute;
        top: calc(100% + 8px);
        right: 0;
        margin: 0;
        padding: 6px 0;
        list-style: none;
        background: var(--arena-paper);
        border: 1px solid var(--arena-line);
        min-width: 200px;
        z-index: 100;
        box-shadow: 4px 4px 0 var(--arena-ink);
    }
    .user-menu li {
        padding: 0;
    }
    .user-menu-label {
        padding: 8px 14px;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        border-bottom: 1px solid var(--arena-line-soft);
    }
    .user-menu a,
    .user-menu button {
        display: block;
        width: 100%;
        padding: 10px 14px;
        background: transparent;
        border: none;
        cursor: pointer;
        text-align: left;
        font-family: var(--arena-f-body);
        font-size: 13px;
        color: var(--arena-ink);
        text-decoration: none;
    }
    .user-menu a:hover,
    .user-menu button:hover {
        background: var(--arena-paper-alt);
    }
    .login-btn {
        font-size: 12px !important;
        padding: 6px 12px !important;
    }
    .hamburger {
        display: none;
    }
    .desktop {
        display: none;
    }
    @media (min-width: 1024px) {
        .desktop {
            display: inline-flex;
        }
        .nav-links.desktop {
            display: flex;
        }
    }
    @media (max-width: 1023px) {
        .hamburger {
            display: inline-flex;
        }
        .login-btn {
            display: none;
        }
    }

    .mobile-panel {
        border-top: 1px solid var(--arena-line);
        background: var(--arena-paper);
        padding: 12px 24px 20px;
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    .mobile-section {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--arena-line-soft);
    }
    .mobile-section:last-child {
        border-bottom: none;
    }
    .mobile-kicker {
        margin-bottom: 4px;
    }
    .mobile-link {
        padding: 8px 0;
        font-size: 14px;
        font-family: var(--arena-f-body);
        color: var(--arena-ink);
        text-decoration: none;
        background: transparent;
        border: none;
        cursor: pointer;
        text-align: left;
        width: 100%;
    }
    .mobile-link:hover {
        color: var(--arena-accent-deep);
    }
    .mobile-link.active {
        color: var(--arena-accent-deep);
        font-weight: 600;
    }
    .mobile-link-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .mono-mini {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        color: var(--arena-ink-soft);
        letter-spacing: 1.5px;
    }
    .mobile-login,
    .mobile-logout {
        font-weight: 600;
        color: var(--arena-accent-deep);
    }

    /* ── Main ─────────────────────────── */
    :global(.arena-main) {
        flex: 1;
    }

    /* ── Footer ─────────────────────────── */
    .arena-footer {
        margin-top: 60px;
        border-top: 1px solid var(--arena-line);
        background: var(--arena-paper);
    }
    .footer-inner {
        max-width: 1400px;
        margin: 0 auto;
        padding: 40px 32px 24px;
    }
    .footer-top {
        display: grid;
        grid-template-columns: 1fr;
        gap: 32px;
    }
    @media (min-width: 768px) {
        .footer-top {
            grid-template-columns: 280px 1fr;
        }
    }
    .footer-brand {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    .footer-logo {
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: 18px;
        letter-spacing: -0.5px;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        color: var(--arena-ink);
        text-decoration: none;
    }
    .footer-desc {
        font-size: 12px;
        color: var(--arena-ink-soft);
        line-height: 1.6;
        margin: 0;
        text-wrap: balance;
    }
    .footer-cols {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 24px;
    }
    @media (min-width: 768px) {
        .footer-cols {
            grid-template-columns: repeat(4, 1fr);
        }
    }
    .footer-col {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .footer-kicker {
        margin-bottom: 4px;
    }
    .footer-col a {
        font-family: var(--arena-f-body);
        font-size: 12px;
        color: var(--arena-ink-soft);
        text-decoration: none;
    }
    .footer-col a:hover {
        color: var(--arena-ink);
    }
    .footer-bottom {
        margin-top: 40px;
        padding-top: 16px;
        border-top: 1px solid var(--arena-line-soft);
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.2px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
    }
    .footer-meta {
        opacity: 0.6;
    }
</style>
