<script lang="ts" module>
    declare const Kakao: any;
</script>

<script lang="ts">
    import '../app.css';
    import { page, navigating, updated } from '$app/stores';
    import { afterNavigate, beforeNavigate } from '$app/navigation';
    import { onMount } from 'svelte';
    import { capturePostHogPageView, initPostHog, syncPostHogUser } from '$lib/posthog';
    import { track } from '$lib/analytics';
    import { getTheme, toggleTheme, type Theme } from '$lib/theme';
    import ProgressBar from '$lib/components/ProgressBar.svelte';
    import EventPopup from '$lib/components/EventPopup.svelte';
    import { isDismissed } from '$lib/popup';

    let { data, children } = $props();

    let currentYear = $derived(data.currentYear);
    let feedbackFormUrl = $derived(data.feedbackFormUrl);
    let googleAnalyticsId = $derived(data.googleAnalyticsId);
    let kakaoJsKey = $derived(data.kakaoJsKey);
    let user = $derived(data.user);
    let currentPath = $derived($page.url.pathname);

    // Canonical URL must include indexing-significant query params (e.g. calendar
    // year/month) — otherwise every /calendar?year=&month= page canonicalizes to
    // bare /calendar and Google drops them as "alternate page with proper canonical".
    // Tracking params (utm_*, fbclid, …) are intentionally excluded. Keys are emitted
    // in a fixed (alphabetical) order so the canonical matches the sitemap exactly.
    const INDEXABLE_PARAMS = ['month', 'year'];
    const TRACKING_PARAM = /^(utm_|fbclid$|gclid$|msclkid$|igshid$|ref$)/;

    // `page` is deliberately NOT a facet: /races?page=2 lists *different* races than
    // /races, so folding it into the bare path would deindex pages 2..N — and those
    // pages are the only internal-link path to most race detail pages. It therefore
    // self-canonicalizes, but only on an otherwise-unfiltered URL: once a facet
    // (sport/region/status/…) is active the facet policy wins and the whole thing
    // folds to the bare path, so filtered views can't explode into crawlable
    // filter×page combinations.
    const PAGE_PARAM = 'page';
    let canonicalPath = $derived(buildCanonicalPath($page.url));

    // Facet URLs (/races?sport=…, ?region=…, ?reset=1) get `noindex, follow`.
    // They used to canonicalize to the bare path instead, but Search Console shows
    // that consolidation never happened — none landed in "alternate page with proper
    // canonical"; they sat in "crawled – currently not indexed" and kept a fix
    // validation failing. noindex states the intent outright, and `follow` keeps the
    // race detail links on those pages working as a discovery path. The canonical tag
    // is dropped alongside it: pairing noindex with a canonical pointing at a
    // *different* URL is a contradiction (remove this page vs. merge it into that one).
    // Sport keywords are served by the real landing pages (/running, /swimming, …).
    let facetFiltered = $derived(hasFacetParam($page.url));

    function hasFacetParam(url: URL): boolean {
        for (const key of url.searchParams.keys()) {
            if (key === PAGE_PARAM || INDEXABLE_PARAMS.includes(key)) continue;
            if (TRACKING_PARAM.test(key)) continue;
            return true;
        }
        return false;
    }

    function buildCanonicalPath(url: URL): string {
        const params = new URLSearchParams();
        for (const key of INDEXABLE_PARAMS) {
            const value = url.searchParams.get(key);
            if (value) params.set(key, value);
        }
        // page=1 is never emitted as a link (see pageHref in /races), so canonicalize
        // it away to keep /races and /races?page=1 from splitting into two URLs.
        const pageValue = url.searchParams.get(PAGE_PARAM);
        if (pageValue && pageValue !== '1' && !hasFacetParam(url)) {
            params.set(PAGE_PARAM, pageValue);
        }
        params.sort();
        const qs = params.toString();
        return qs ? `${url.pathname}?${qs}` : url.pathname;
    }

    // Full-bleed routes render their own chrome (e.g. the split-screen login).
    const BARE_ROUTES = new Set(['/auth/login']);
    let bare = $derived(BARE_ROUTES.has(currentPath));

    // The 404 error page is a full-bleed photo hero with its own bottom rule —
    // drop the footer's top margin so it sits flush against it.
    let errorHero = $derived(!!$page.error && $page.status === 404);

    // Race detail pages (/races/{slug}) carry their own sticky bottom CTA
    // (참가비 + 접수하기), so the global mobile tab bar steps aside there.
    // Excludes /races and /races/year/{year}.
    let isRaceDetail = $derived(/^\/races\/(?!year(?:\/|$))[^/]+\/?$/.test(currentPath));

    let userLabel = $derived(
        user ? (user.nickname?.trim() || user.email.split('@')[0] || '계정') : ''
    );

    let theme = $state<Theme>('light');
    let lastTrackedPath = $state('');
    let mobileMenuOpen = $state(false);
    let userMenuOpen = $state(false);

    // ── 이벤트 팝업 ───────────────────────────────────────────
    // 내용·게시기간은 django admin 의 "팝업 배너"에서 관리한다. 여기서는
    // "언제 띄울지"만 정한다: 마운트 이후(=localStorage 를 읽을 수 있을 때),
    // 노출 위치가 맞고, 다시 보지 않기 기간이 아닐 때.
    let mounted = $state(false);
    let popupOpen = $state(false);
    // 일반 닫기는 현재 경로에서만 유지한다. 다른 페이지로 이동하면 다시
    // 노출하며, 기간 숨김은 EventPopup에서 명시적으로 선택했을 때만 저장된다.
    let popupClosedContext = $state('');
    let popupBanner = $derived(data.popup);

    $effect(() => {
        if (!mounted || popupOpen) return;
        const banner = popupBanner;
        if (!banner || bare) return;
        if (banner.placement === 'home' && currentPath !== '/') return;
        const context = `${banner.id}:${banner.version}:${currentPath}`;
        if (popupClosedContext === context || isDismissed(banner)) return;
        popupOpen = true;
    });

    function closePopup() {
        const banner = popupBanner;
        if (banner) popupClosedContext = `${banner.id}:${banner.version}:${currentPath}`;
        popupOpen = false;
    }


    beforeNavigate((nav) => {
        if ($updated && !nav.willUnload && nav.to?.url) {
            nav.cancel();
            location.href = nav.to.url.href;
        }
    });

    $effect(() => {
        if (typeof document === 'undefined') return;
        if (mobileMenuOpen) {
            const prev = document.body.style.overflow;
            document.body.style.overflow = 'hidden';
            return () => {
                document.body.style.overflow = prev;
            };
        }
    });

    onMount(() => {
        mounted = true;
        theme = getTheme();
        initPostHog();
        syncPostHogUser(user);

        const initialPath = $page.url.pathname + $page.url.search;
        capturePostHogPageView($page.url.pathname, $page.url.search, document.referrer);
        lastTrackedPath = initialPath;

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

    // Auth conversions complete via server-side redirects, so the server sets a
    // one-shot `eh_evt` cookie that we read here, fire to GA/PostHog, then clear.
    function fireAuthEvent() {
        if (typeof document === 'undefined') return;
        const match = document.cookie.match(/(?:^|;\s*)eh_evt=([^;]+)/);
        if (!match) return;
        const value = decodeURIComponent(match[1]);
        document.cookie = 'eh_evt=; Max-Age=0; path=/';
        if (value.startsWith('login')) {
            track('login', { method: value.split(':')[1] || '' });
        } else if (value.startsWith('signup')) {
            track('sign_up', { method: value.split(':')[1] || '' });
        }
    }

    afterNavigate(() => {
        // 일반 닫기는 해당 방문에서만 유지한다. 다른 경로를 거쳐 홈으로
        // 돌아오면 팝업을 다시 평가한다.
        popupClosedContext = '';
        const pathWithSearch = `${$page.url.pathname}${$page.url.search}`;
        if (lastTrackedPath !== pathWithSearch) {
            capturePostHogPageView($page.url.pathname, $page.url.search, document.referrer);
            lastTrackedPath = pathWithSearch;
        }
        if (googleAnalyticsId && typeof gtag === 'function') {
            gtag('config', googleAnalyticsId, { page_path: $page.url.pathname });
        }
        fireAuthEvent();
        mobileMenuOpen = false;
        userMenuOpen = false;
    });

    // Primary nav — mirrors the DS shell (대회 / 검색 / 시즌 / 커뮤니티 / 공지 / 도구).
    type NavItem = { id: string; href: string; label: string; match: (p: string) => boolean };
    const navItems: NavItem[] = $derived([
        { id: 'home', href: '/', label: '대회', match: (p) => p === '/' || p.startsWith('/calendar') },
        { id: 'search', href: '/races', label: '검색', match: (p) => p.startsWith('/races') && !p.startsWith('/races/year') },
        { id: 'year', href: `/races/year/${currentYear}`, label: `${currentYear} 대회`, match: (p) => p.startsWith('/races/year') },
        { id: 'season', href: '/timeline', label: '시즌', match: (p) => p.startsWith('/timeline') },
        { id: 'community', href: '/community', label: '커뮤니티', match: (p) => p.startsWith('/community') || p.startsWith('/posts') },
        { id: 'notice', href: '/notice', label: '공지', match: (p) => p.startsWith('/notice') },
        { id: 'tools', href: '/tools', label: '도구', match: (p) => p.startsWith('/tools') || p === '/running-terms' }
    ]);

    const activeNavId = $derived(navItems.find((n) => n.match(currentPath))?.id ?? '');

    const sportLinks = [
        { href: '/running', label: '마라톤', code: 'RUN' },
        { href: '/swimming', label: '수영', code: 'SWIM' },
        { href: '/cycling', label: '자전거', code: 'CYCLE' },
        { href: '/triathlon', label: '철인3종', code: 'TRI' },
        { href: '/trail-running', label: '트레일러닝', code: 'TRL' }
    ];

    // Bottom tab bar (mobile) — primary destinations + a "메뉴" sheet trigger.
    const tabItems = [
        { id: 'home', href: '/', label: '대회' },
        { id: 'search', href: '/races', label: '검색' },
        { id: 'season', href: '/timeline', label: '시즌' },
        { id: 'community', href: '/community', label: '커뮤니티' }
    ];
</script>

<svelte:head>
    <meta property="og:site_name" content="endurohub" />
    <meta property="og:url" content="{data.appUrl}{canonicalPath}" />
    <meta property="og:locale" content="ko_KR" />
    <meta name="twitter:card" content="summary_large_image" />
    {#if facetFiltered}
        <meta name="robots" content="noindex, follow" />
    {:else}
        <link rel="canonical" href="{data.appUrl}{canonicalPath}" />
    {/if}
    {#if googleAnalyticsId}
        <script async src="https://www.googletagmanager.com/gtag/js?id={googleAnalyticsId}"></script>
        {@html `<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${googleAnalyticsId}');</script>`}
    {/if}
</svelte:head>

<!-- ── Top navbar (DS .eh-nav) ───────────────────────────── -->
{#if !bare}
<header class="eh-nav">
    <a class="eh-nav__wordmark" href="/">ENDURO<span class="slash">/</span>HUB</a>

    <nav class="eh-nav__links">
        {#each navItems as it (it.id)}
            <a
                href={it.href}
                class="eh-nav__link {it.id === activeNavId ? 'eh-nav__link--on' : ''}"
            >
                {it.label}
            </a>
        {/each}
    </nav>

    <div class="eh-nav__right">
        <a class="eh-iconbtn eh-nav__searchbtn" href="/races" aria-label="검색" title="검색">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg>
        </a>

        <button
            class="eh-iconbtn"
            onclick={handleToggleTheme}
            aria-label={theme === 'dark' ? '라이트 모드로 전환' : '다크 모드로 전환'}
            title="테마 전환"
        >
            {#if theme === 'dark'}
                <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
            {:else}
                <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
            {/if}
        </button>

        {#if user}
            <div class="eh-user">
                <button
                    class="v-avatar"
                    class:open={userMenuOpen}
                    onclick={() => (userMenuOpen = !userMenuOpen)}
                    aria-expanded={userMenuOpen}
                    aria-label="계정 메뉴"
                >
                    {#if user.profileImage}
                        <img src={user.profileImage} alt={userLabel} />
                    {:else}
                        {userLabel.charAt(0).toUpperCase()}
                    {/if}
                </button>
                {#if userMenuOpen}
                    <div class="eh-user__menu" role="menu">
                        <div class="eh-user__head">
                            <div class="eh-user__name">{userLabel}</div>
                            <div class="eh-user__email" title={user.email}>{user.email}</div>
                        </div>
                        <a href="/mypage" role="menuitem" onclick={() => (userMenuOpen = false)}>마이페이지</a>
                        <a href="/mypage/favorites" role="menuitem" onclick={() => (userMenuOpen = false)}>관심 대회</a>
                        <form method="POST" action="/auth/logout">
                            <button type="submit" role="menuitem">로그아웃</button>
                        </form>
                    </div>
                {/if}
            </div>
        {:else}
            <a href="/auth/login" class="eh-btn eh-btn--secondary eh-btn--sm">로그인</a>
        {/if}
    </div>
</header>
{/if}

<ProgressBar active={!!$navigating} />

{#if popupOpen && popupBanner}
    <EventPopup banner={popupBanner} onClose={closePopup} />
{/if}

<main class="eh-main">
    {@render children()}
</main>

{#if !bare}
<!-- ── Footer (2px ink rule — DS signature) ──────────────── -->
<footer class="v-footer" class:flush={errorHero}>
    <div class="eh-footer-grid">
        <div class="eh-footer-brand">
            <a href="/" class="v-wordmark">ENDURO<span class="slash">/</span>HUB</a>
            <p>국내 마라톤 · 트레일 · 사이클 · 수영 · 철인3종 대회를 한곳에서.</p>
        </div>
        <div class="eh-footer-cols">
            <div class="eh-footer-col">
                <div class="eh-micro">RACES</div>
                <!-- ?reset=1 은 서버에서도 필터바에서도 읽지 않는 잉여 파라미터였다.
                     facet 으로 분류돼 noindex 가 붙는데, 전 페이지 푸터에 걸린 링크라
                     대회 목록으로 가야 할 내부 링크가 통째로 noindex 로 새고 있었다. -->
                <a href="/races">전체 대회</a>
                <a href={`/races/year/${currentYear}`}>{currentYear}년 대회</a>
                <a href="/calendar">캘린더</a>
                <a href="/timeline">시즌 타임라인</a>
            </div>
            <div class="eh-footer-col">
                <div class="eh-micro">SPORTS</div>
                {#each sportLinks as s (s.href)}<a href={s.href}>{s.label}</a>{/each}
            </div>
            <div class="eh-footer-col">
                <div class="eh-micro">TOOLS</div>
                <a href="/tools/pace-calculator">페이스 계산기</a>
                <a href="/tools/training-plan">훈련 플랜</a>
                <a href="/tools/vo2max">VO2max</a>
                <a href="/tools/race-predictor">기록 예측</a>
                <a href="/running-terms">러닝 용어</a>
            </div>
            <div class="eh-footer-col">
                <div class="eh-micro">SUPPORT</div>
                <a href="/about">서비스 소개</a>
                <a href="/terms">서비스 이용약관</a>
                <a href="/privacy">개인정보처리방침</a>
                {#if feedbackFormUrl}
                    <a href={feedbackFormUrl} target="_blank" rel="noopener">문의하기 ↗</a>
                {:else}
                    <a href="mailto:contact@endurohub.kr">문의하기</a>
                {/if}
            </div>
        </div>
    </div>
    <div class="eh-footer-base eh-micro">© {currentYear} ENDUROHUB · 지구력 스포츠 대회 큐레이션</div>
</footer>

<!-- ── Mobile bottom tab bar ─────────────────────────────── -->
<!-- Race detail pages render their own sticky CTA bar instead. -->
{#if !isRaceDetail}
<div class="v-tabbar-wrap">
    <nav class="eh-tabbar">
        {#each tabItems as it (it.id)}
            <a class="eh-tabbar__item {it.id === activeNavId ? 'eh-tabbar__item--on' : ''}" href={it.href}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    {#if it.id === 'home'}<path d="M3 9.5 12 3l9 6.5V21H3z"/>
                    {:else if it.id === 'search'}<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
                    {:else if it.id === 'season'}<path d="M8 2v4M16 2v4M3 10h18M5 6h14a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z"/>
                    {:else}<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>{/if}
                </svg>
                <span>{it.label}</span>
                <span class="eh-tabbar__ind"></span>
            </a>
        {/each}
        <button class="eh-tabbar__item" onclick={() => (mobileMenuOpen = !mobileMenuOpen)}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h16M4 12h16M4 18h16"/></svg>
            <span>메뉴</span>
            <span class="eh-tabbar__ind"></span>
        </button>
    </nav>
</div>
{/if}

{#if mobileMenuOpen}
    <div class="eh-sheet" role="presentation" onclick={(e) => { if (e.target === e.currentTarget) mobileMenuOpen = false; }}>
        <div class="eh-sheet__panel">
            <div class="eh-sheet__sec">
                <div class="eh-micro">대회</div>
                <a href={`/races/year/${currentYear}`} class="eh-sheet__link"><span>{currentYear} 대회</span><span class="eh-sheet__code">YEAR</span></a>
                <a href="/calendar" class="eh-sheet__link"><span>캘린더</span><span class="eh-sheet__code">CAL</span></a>
            </div>
            <div class="eh-sheet__sec">
                <div class="eh-micro">종목</div>
                {#each sportLinks as s (s.href)}
                    <a href={s.href} class="eh-sheet__link"><span>{s.label}</span><span class="eh-sheet__code">{s.code}</span></a>
                {/each}
            </div>
            <div class="eh-sheet__sec">
                <div class="eh-micro">도구</div>
                <a href="/tools" class="eh-sheet__link">전체 도구</a>
                <a href="/notice" class="eh-sheet__link">공지사항</a>
                <a href="/about" class="eh-sheet__link">서비스 소개</a>
            </div>
            <div class="eh-sheet__sec">
                {#if user}
                    <div class="eh-micro">계정 · {userLabel}</div>
                    <a href="/mypage" class="eh-sheet__link">마이페이지</a>
                    <a href="/mypage/favorites" class="eh-sheet__link">관심 대회</a>
                    <form method="POST" action="/auth/logout"><button type="submit" class="eh-sheet__link">로그아웃</button></form>
                {:else}
                    <a href="/auth/login" class="eh-sheet__link">로그인</a>
                {/if}
            </div>
        </div>
    </div>
{/if}
{/if}

<style>
    :global(.eh-main) { flex: 1; }

    /* 404 hero ends in its own rule — footer sits flush, no top gap. */
    .v-footer.flush { margin-top: 0; }

    .eh-nav__searchbtn { display: none; }

    /* User menu */
    .eh-user { position: relative; }
    .v-avatar.open { background: var(--paper-50); }
    .v-avatar img { width: 100%; height: 100%; object-fit: cover; }
    .eh-user__menu {
        position: absolute; top: calc(100% + 10px); right: 0;
        min-width: 240px; background: var(--paper-0);
        border: 1px solid var(--ink-900); box-shadow: var(--shadow-pop);
        z-index: 100; display: flex; flex-direction: column;
        animation: v-rise var(--dur-base) var(--ease-out);
    }
    .eh-user__head { padding: 12px 14px; border-bottom: 1px solid var(--line); background: var(--paper-50); }
    .eh-user__name { font-size: 14px; font-weight: 700; color: var(--text-strong); }
    .eh-user__email { font-size: 11px; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .eh-user__menu a,
    .eh-user__menu button {
        padding: 11px 14px; font-size: 13px; font-weight: 600; text-align: left;
        color: var(--text-body); text-decoration: none; background: none; border: none;
        border-top: 1px solid var(--line); cursor: pointer; width: 100%; font-family: var(--font-sans);
    }
    .eh-user__menu a:first-of-type { border-top: none; }
    .eh-user__menu a:hover { background: var(--paper-50); color: var(--text-strong); }
    .eh-user__menu button:hover { background: var(--danger-bg); color: var(--danger); }

    /* Footer */
    .eh-footer-grid {
        max-width: var(--container-max); margin: 0 auto;
        padding: var(--sp-12) var(--container-pad) var(--sp-6);
        display: grid; grid-template-columns: 1fr; gap: var(--sp-10);
    }
    @media (min-width: 768px) { .eh-footer-grid { grid-template-columns: 280px 1fr; } }
    .eh-footer-brand p { margin-top: 12px; font-size: 13px; color: var(--text-muted); line-height: 1.6; max-width: 32ch; }
    .eh-footer-cols { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--sp-6); }
    @media (min-width: 768px) { .eh-footer-cols { grid-template-columns: repeat(4, 1fr); } }
    .eh-footer-col { display: flex; flex-direction: column; gap: 9px; }
    .eh-footer-col .eh-micro { margin-bottom: 3px; }
    .eh-footer-col a { font-size: 13px; color: var(--text-muted); text-decoration: none; }
    .eh-footer-col a:hover { color: var(--text-strong); }
    .eh-footer-base {
        max-width: var(--container-max); margin: 0 auto;
        padding: var(--sp-4) var(--container-pad) var(--sp-8);
    }

    /* Mobile sheet */
    .eh-sheet {
        position: fixed; inset: 0; z-index: 95; background: rgba(16,19,18,0.45);
        display: flex; align-items: flex-end;
    }
    .eh-sheet__panel {
        width: 100%; background: var(--paper-0); border-top: var(--border-rule);
        padding: var(--sp-5) var(--container-pad-mobile) calc(var(--sp-5) + 76px);
        display: flex; flex-direction: column; gap: var(--sp-5);
        max-height: 70vh; overflow-y: auto;
        animation: v-rise var(--dur-base) var(--ease-out);
    }
    .eh-sheet__sec { display: flex; flex-direction: column; gap: 2px; }
    .eh-sheet__sec .eh-micro { margin-bottom: 6px; }
    .eh-sheet__link {
        display: flex; justify-content: space-between; align-items: center;
        padding: 11px 0; font-size: 15px; font-weight: 600; color: var(--text-strong);
        text-decoration: none; border: none; background: none; width: 100%; cursor: pointer;
        font-family: var(--font-sans); text-align: left;
    }
    .eh-sheet__code { font-size: 10px; font-weight: 700; letter-spacing: 0.09em; color: var(--text-faint); }

    @media (max-width: 768px) {
        .eh-nav__searchbtn { display: inline-flex; }
    }
    @keyframes v-rise { from { opacity: 0; transform: translateY(8px); } }
</style>
