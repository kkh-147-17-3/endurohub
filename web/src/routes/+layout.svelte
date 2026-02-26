<script lang="ts">
    import '../app.css';
    import { page } from '$app/stores';
    import { navigating } from '$app/stores';

    let { data, children } = $props();

    let currentYear = $derived(data.currentYear);
    let feedbackFormUrl = $derived(data.feedbackFormUrl);
    let googleAnalyticsId = $derived(data.googleAnalyticsId);
    let kakaoJsKey = $derived(data.kakaoJsKey);
    let currentPath = $derived($page.url.pathname);
</script>

<svelte:head>
    <meta property="og:site_name" content="EnduroHub" />
    <meta property="og:url" content="{data.appUrl}{currentPath}" />
    <meta property="og:locale" content="ko_KR" />
    <meta name="twitter:card" content="summary_large_image" />
    <link rel="canonical" href="{data.appUrl}{currentPath}" />
    {#if googleAnalyticsId}
        <script async src="https://www.googletagmanager.com/gtag/js?id={googleAnalyticsId}"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '{googleAnalyticsId}');
        </script>
    {/if}
    {#if kakaoJsKey}
        <script src="https://t1.kakaocdn.net/kakao_js_sdk/2.7.4/kakao.min.js" crossorigin="anonymous"></script>
        <script>
            if (typeof Kakao !== 'undefined' && !Kakao.isInitialized()) {
                Kakao.init('{kakaoJsKey}');
            }
        </script>
    {/if}
</svelte:head>

<header class="sticky top-0 z-50 bg-base-100 border-b border-base-200">
    <div class="navbar container mx-auto px-4 h-16">
        <div class="navbar-start">
            <!-- Mobile Menu -->
            <div class="dropdown">
                <div tabindex="0" role="button" class="btn btn-ghost btn-sm lg:hidden cursor-pointer" aria-label="메뉴 열기">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h8m-8 6h16" />
                    </svg>
                </div>
                <ul class="menu menu-sm dropdown-content mt-2 z-[1] p-2 bg-base-100 rounded-lg w-52 border border-base-200">
                    <li><a href="/" class:active={currentPath === '/'}>홈</a></li>
                    <li><a href="/races" class:active={currentPath === '/races'}>전체 대회</a></li>
                    <li><a href={`/races/year/${currentYear}`} class:active={currentPath.startsWith('/races/year/')}>{currentYear}년 대회보기</a></li>
                    <li class="menu-title pt-2">
                        <span class="text-xs">종목별</span>
                    </li>
                    <li><a href="/running">마라톤</a></li>
                    <li><a href="/swimming">수영</a></li>
                    <li><a href="/cycling">자전거</a></li>
                    <li><a href="/triathlon">철인3종</a></li>
                    <li><a href="/trail-running">트레일러닝</a></li>
                    <div class="divider my-1"></div>
                    <li><a href="/calendar" class:active={currentPath === '/calendar'}>캘린더</a></li>
                    <li class="menu-title pt-2">
                        <span class="text-xs">도구</span>
                    </li>
                    <li><a href="/tools/pace-calculator" class:active={currentPath === '/tools/pace-calculator'}>페이스 계산기</a></li>
                    <li><a href="/tools/training-plan" class:active={currentPath === '/tools/training-plan'}>훈련 플랜</a></li>
                    <li><a href="/tools/vo2max" class:active={currentPath === '/tools/vo2max'}>VO2max</a></li>
                    <li><a href="/tools/race-predictor" class:active={currentPath === '/tools/race-predictor'}>기록 예측</a></li>
                    <li><a href="/running-terms" class:active={currentPath === '/running-terms'}>러닝 용어</a></li>
                    <div class="divider my-1"></div>
                    <li><a href="/posts" class:active={currentPath === '/posts'}>자유게시판</a></li>
                </ul>
            </div>
            <!-- Logo -->
            <a href="/" class="text-xl font-bold cursor-pointer flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span><span class="text-primary">Enduro</span><span class="text-base-content">Hub</span></span>
            </a>
        </div>

        <!-- Desktop Menu -->
        <div class="navbar-center hidden lg:flex">
            <ul class="menu menu-horizontal gap-1 text-base">
                <li>
                    <a href="/" class:active={currentPath === '/'}>홈</a>
                </li>
                <li>
                    <a href="/races" class:active={currentPath === '/races'}>전체 대회</a>
                </li>
                <li>
                    <a href={`/races/year/${currentYear}`} class:active={currentPath.startsWith('/races/year/')}>{currentYear}년 대회</a>
                </li>
                <li>
                    <details>
                        <summary>종목별</summary>
                        <ul class="p-2 bg-base-100 rounded-lg w-40 border border-base-200">
                            <li><a href="/running" class="flex items-center gap-2">
                                <span class="w-1.5 h-1.5 rounded-full bg-primary"></span>마라톤
                            </a></li>
                            <li><a href="/swimming" class="flex items-center gap-2">
                                <span class="w-1.5 h-1.5 rounded-full bg-info"></span>수영
                            </a></li>
                            <li><a href="/cycling" class="flex items-center gap-2">
                                <span class="w-1.5 h-1.5 rounded-full bg-warning"></span>자전거
                            </a></li>
                            <li><a href="/triathlon" class="flex items-center gap-2">
                                <span class="w-1.5 h-1.5 rounded-full bg-secondary"></span>철인3종
                            </a></li>
                            <li><a href="/trail-running" class="flex items-center gap-2">
                                <span class="w-1.5 h-1.5 rounded-full bg-success"></span>트레일러닝
                            </a></li>
                        </ul>
                    </details>
                </li>
                <li>
                    <a href="/calendar" class:active={currentPath === '/calendar'}>캘린더</a>
                </li>
                <li>
                    <details>
                        <summary>도구</summary>
                        <ul class="p-2 bg-base-100 rounded-lg w-44 border border-base-200">
                            <li><a href="/tools/pace-calculator" class="flex items-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                페이스 계산기
                            </a></li>
                            <li><a href="/tools/training-plan" class="flex items-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" /></svg>
                                훈련 플랜
                            </a></li>
                            <li><a href="/tools/vo2max" class="flex items-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>
                                VO2max
                            </a></li>
                            <li><a href="/tools/race-predictor" class="flex items-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                                기록 예측
                            </a></li>
                            <li><a href="/running-terms" class="flex items-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
                                러닝 용어
                            </a></li>
                        </ul>
                    </details>
                </li>
                <li>
                    <a href="/posts" class:active={currentPath === '/posts'}>자유게시판</a>
                </li>
            </ul>
        </div>

        <!-- CTA -->
        <div class="navbar-end">
            <a href="/races" class="btn btn-primary cursor-pointer">
                대회 찾기
            </a>
        </div>
    </div>
</header>

{#if $navigating}
    <div class="fixed top-16 left-0 right-0 z-50 h-0.5 bg-base-200">
        <div class="h-full bg-primary animate-progress rounded-r-full"></div>
    </div>
{/if}

<main class="flex-1">
    {@render children()}
</main>

<!-- Footer -->
<footer class="bg-slate-900 text-white">
    <div class="container mx-auto px-4">
        <div class="py-10 grid grid-cols-1 md:grid-cols-4 gap-8">
            <!-- Brand -->
            <div class="md:col-span-2">
                <a href="/" class="text-xl font-bold cursor-pointer flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <span><span class="text-primary">Enduro</span>Hub</span>
                </a>
                <p class="mt-3 text-slate-400 text-sm max-w-md">
                    국내 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 정보를 한곳에서 확인하세요.
                </p>
            </div>

            <!-- Quick Links -->
            <div>
                <h3 class="font-semibold text-sm mb-3">바로가기</h3>
                <ul class="space-y-2 text-sm">
                    <li><a href="/races" class="text-slate-400 hover:text-white cursor-pointer">전체 대회</a></li>
                    <li><a href="/calendar" class="text-slate-400 hover:text-white cursor-pointer">캘린더</a></li>
                    <li><a href="/running" class="text-slate-400 hover:text-white cursor-pointer">마라톤</a></li>
                    <li><a href="/swimming" class="text-slate-400 hover:text-white cursor-pointer">수영</a></li>
                    <li><a href="/cycling" class="text-slate-400 hover:text-white cursor-pointer">자전거</a></li>
                    <li><a href="/triathlon" class="text-slate-400 hover:text-white cursor-pointer">철인3종</a></li>
                    <li><a href="/trail-running" class="text-slate-400 hover:text-white cursor-pointer">트레일러닝</a></li>
                    <li><a href="/tools/pace-calculator" class="text-slate-400 hover:text-white cursor-pointer">페이스 계산기</a></li>
                    <li><a href="/tools/training-plan" class="text-slate-400 hover:text-white cursor-pointer">훈련 플랜</a></li>
                    <li><a href="/tools/vo2max" class="text-slate-400 hover:text-white cursor-pointer">VO2max</a></li>
                    <li><a href="/tools/race-predictor" class="text-slate-400 hover:text-white cursor-pointer">기록 예측</a></li>
                    <li><a href="/running-terms" class="text-slate-400 hover:text-white cursor-pointer">러닝 용어</a></li>
                </ul>
            </div>

            <!-- Support -->
            <div>
                <h3 class="font-semibold text-sm mb-3">지원</h3>
                <ul class="space-y-2 text-sm">
                    <li><a href="/about" class="text-slate-400 hover:text-white cursor-pointer">서비스 소개</a></li>
                    <li><a href="/privacy" class="text-slate-400 hover:text-white cursor-pointer">개인정보처리방침</a></li>
                    <li><a href="mailto:contact@endurohub.kr" class="text-slate-400 hover:text-white cursor-pointer">문의하기</a></li>
                    {#if feedbackFormUrl}
                    <li>
                        <a href={feedbackFormUrl} target="_blank" rel="noopener" class="text-slate-400 hover:text-white cursor-pointer inline-flex items-center gap-1">
                            피드백 보내기
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                        </a>
                    </li>
                    {/if}
                </ul>
            </div>
        </div>

        <!-- Bottom Bar -->
        <div class="py-4 border-t border-slate-800 flex flex-col sm:flex-row justify-between items-center gap-2 text-xs text-slate-500">
            <p>&copy; {currentYear} EnduroHub</p>
            <div class="flex items-center gap-4">
                <a href="/privacy" class="hover:text-white cursor-pointer">개인정보처리방침</a>
                <a href="/about" class="hover:text-white cursor-pointer">이용약관</a>
            </div>
        </div>
    </div>
</footer>
