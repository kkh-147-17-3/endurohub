<script lang="ts">
    import RaceCard from '$lib/components/RaceCard.svelte';
    import PostCard from '$lib/components/PostCard.svelte';
    import type { Race, Post } from '$lib/types';

    let { data } = $props();

    const closingSoon: Race[] = data.closingSoon;
    const upcomingRaces: Race[] = data.upcomingRaces;
    const recentlyAdded: Race[] = data.recentlyAdded;
    const recentPosts: Post[] = data.recentPosts;
    const sportCounts = data.sportCounts;
    const totalUpcoming: number = data.totalUpcoming;

    const appUrl = data.appUrl || 'https://www.endurohub.kr';

    const websiteSchema = {
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        'name': 'EnduroHub',
        'url': appUrl,
        'description': '국내 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정과 접수 정보를 한곳에서 확인하세요.',
        'potentialAction': {
            '@type': 'SearchAction',
            'target': `${appUrl}/races?search={search_term_string}`,
            'query-input': 'required name=search_term_string',
        },
    };

    let itemListSchema = $derived({
        '@context': 'https://schema.org',
        '@type': 'ItemList',
        'name': '다가오는 대회',
        'numberOfItems': upcomingRaces.length,
        'itemListElement': upcomingRaces.map((race, index) => ({
            '@type': 'ListItem',
            'position': index + 1,
            'name': race.title,
            'url': race.url,
        })),
    });
</script>

<svelte:head>
    <title>엔듀로허브 - 국내 지구력 스포츠 대회 정보 플랫폼</title>
    <meta name="description" content="엔듀로허브에서 국내 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정과 접수 정보를 한곳에서 확인하세요." />
    <meta property="og:title" content="엔듀로허브 - 국내 지구력 스포츠 대회 정보 플랫폼" />
    <meta property="og:description" content="엔듀로허브에서 국내 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정과 접수 정보를 한곳에서 확인하세요." />
    {@html `<script type="application/ld+json">${JSON.stringify(websiteSchema)}</script>`}
    {@html `<script type="application/ld+json">${JSON.stringify(itemListSchema)}</script>`}
</svelte:head>

<!-- Hero Section -->
<section class="relative bg-slate-900">
    <div class="container mx-auto px-4 py-3 md:py-4">
        <div class="flex items-center justify-center md:justify-start md:relative">
            <h1 class="hidden md:block text-xl font-bold text-white">
                지구력 스포츠 대회 모음
            </h1>
            <div class="flex items-center gap-2 md:absolute md:left-1/2 md:-translate-x-1/2">
                <a href="/calendar" class="btn btn-primary btn-xs md:btn-sm gap-1.5 cursor-pointer">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    캘린더
                </a>
                <a href="/races" class="btn btn-ghost btn-xs md:btn-sm text-white hover:bg-white/10 cursor-pointer">
                    전체 대회
                </a>
                <a href="/posts" class="btn btn-ghost btn-xs md:btn-sm text-white hover:bg-white/10 cursor-pointer">
                    자유게시판
                </a>
            </div>
        </div>
    </div>
    <div class="absolute left-1/2 -translate-x-1/2 top-[120%] z-10 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border border-base-300 text-base-content/50 text-xs">
        <span class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
        {totalUpcoming}개 접수중
    </div>
</section>

<!-- Closing Soon Section -->
<section class="py-8">
    <div class="container mx-auto px-4">
        <div class="flex items-center justify-between mb-6">
            <div>
                <h2 class="text-xl md:text-2xl font-bold">마감 임박</h2>
                <p class="text-base-content/50 text-base">접수 마감 7일 이내</p>
            </div>
        </div>

        {#if closingSoon.length === 0}
            <div class="border border-base-300 rounded-lg p-8 text-center">
                <p class="text-base-content/50">현재 마감 임박한 대회가 없습니다</p>
            </div>
        {:else}
            <div class="flex items-center gap-3">
                <div class="flex-1 min-w-0 flex items-stretch gap-3 overflow-x-auto snap-x snap-mandatory pb-2 scrollbar-hide">
                    {#each closingSoon as race (race.id)}
                        <div class="w-[280px] snap-start shrink-0 flex">
                            <div class="flex-1">
                                <RaceCard {race} />
                            </div>
                        </div>
                    {/each}
                </div>
                <a href="/races?status=closing_soon" class="shrink-0 flex flex-col items-center gap-1.5 cursor-pointer group/more">
                    <div class="w-10 h-10 rounded-full border border-base-300 group-hover/more:border-primary group-hover/more:bg-primary/10 flex items-center justify-center transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-base-content/50 group-hover/more:text-primary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                        </svg>
                    </div>
                    <span class="text-xs text-base-content/50 group-hover/more:text-primary transition-colors">전체보기</span>
                </a>
            </div>
        {/if}
    </div>
</section>

<!-- Sports Categories Section -->
<section class="py-10 bg-base-200/50">
    <div class="container mx-auto px-4">
        <div class="mb-6">
            <h2 class="text-xl md:text-2xl font-bold">종목별 대회</h2>
            <p class="text-base-content/50 text-base">관심있는 종목을 선택하세요</p>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            <a href="/running" class="block p-4 bg-base-100 border border-base-300 rounded-lg hover:border-primary transition-colors cursor-pointer">
                <div class="flex items-center justify-between mb-3">
                    <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                    </div>
                    <span class="text-sm text-base-content/50">{sportCounts.running}개</span>
                </div>
                <h3 class="font-semibold text-base">마라톤</h3>
                <p class="text-sm text-base-content/50 mt-0.5">풀코스, 하프, 10K</p>
            </a>

            <a href="/swimming" class="block p-4 bg-base-100 border border-base-300 rounded-lg hover:border-info transition-colors cursor-pointer">
                <div class="flex items-center justify-between mb-3">
                    <div class="w-10 h-10 rounded-lg bg-info/10 flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-info" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                        </svg>
                    </div>
                    <span class="text-sm text-base-content/50">{sportCounts.swimming}개</span>
                </div>
                <h3 class="font-semibold text-base">수영</h3>
                <p class="text-sm text-base-content/50 mt-0.5">오픈워터, 마스터즈</p>
            </a>

            <a href="/cycling" class="block p-4 bg-base-100 border border-base-300 rounded-lg hover:border-warning transition-colors cursor-pointer">
                <div class="flex items-center justify-between mb-3">
                    <div class="w-10 h-10 rounded-lg bg-warning/10 flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <span class="text-sm text-base-content/50">{sportCounts.cycling}개</span>
                </div>
                <h3 class="font-semibold text-base">자전거</h3>
                <p class="text-sm text-base-content/50 mt-0.5">로드, MTB, 그란폰도</p>
            </a>

            <a href="/triathlon" class="block p-4 bg-base-100 border border-base-300 rounded-lg hover:border-secondary transition-colors cursor-pointer">
                <div class="flex items-center justify-between mb-3">
                    <div class="w-10 h-10 rounded-lg bg-secondary/10 flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                        </svg>
                    </div>
                    <span class="text-sm text-base-content/50">{sportCounts.triathlon}개</span>
                </div>
                <h3 class="font-semibold text-base">철인3종</h3>
                <p class="text-sm text-base-content/50 mt-0.5">스프린트, 올림픽, 풀</p>
            </a>

            <a href="/trail-running" class="block p-4 bg-base-100 border border-base-300 rounded-lg hover:border-success transition-colors cursor-pointer">
                <div class="flex items-center justify-between mb-3">
                    <div class="w-10 h-10 rounded-lg bg-success/10 flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
                        </svg>
                    </div>
                    <span class="text-sm text-base-content/50">{sportCounts.trailRunning}개</span>
                </div>
                <h3 class="font-semibold text-base">트레일러닝</h3>
                <p class="text-sm text-base-content/50 mt-0.5">산악, 오름, 숲길</p>
            </a>
        </div>
    </div>
</section>

<!-- Recently Added Section -->
<section class="py-8">
    <div class="container mx-auto px-4">
        <div class="flex items-center justify-between mb-6">
            <div>
                <h2 class="text-xl md:text-2xl font-bold">방금 추가된 대회</h2>
                <p class="text-base-content/50 text-base">새로 등록된 대회를 확인하세요</p>
            </div>
        </div>

        {#if recentlyAdded.length === 0}
            <div class="border border-base-300 rounded-lg p-8 text-center">
                <p class="text-base-content/50">최근 추가된 대회가 없습니다</p>
            </div>
        {:else}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {#each recentlyAdded as race (race.id)}
                    <RaceCard {race} />
                {/each}
            </div>
        {/if}
    </div>
</section>

<!-- CTA Banner -->
<section class="bg-slate-900">
    <div class="container mx-auto px-4 py-12 text-center">
        <h2 class="text-xl md:text-2xl font-bold text-white mb-2">다음 도전을 시작하세요</h2>
        <p class="text-white/50 text-base mb-6">
            캘린더에서 대회 일정을 확인하고 계획을 세워보세요
        </p>
        <div class="flex flex-wrap gap-3 justify-center">
            <a href="/calendar" class="btn btn-primary btn-sm gap-2 cursor-pointer">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                캘린더 보기
            </a>
            <a href="/races" class="btn btn-ghost btn-sm text-white hover:bg-white/10 gap-2 cursor-pointer">
                전체 대회 목록
            </a>
        </div>
    </div>
</section>

<!-- Upcoming Races Section -->
<section class="py-8">
    <div class="container mx-auto px-4">
        <div class="flex items-center justify-between mb-6">
            <div>
                <h2 class="text-xl md:text-2xl font-bold">다가오는 대회</h2>
                <p class="text-base-content/50 text-base">곧 열리는 대회를 확인하세요</p>
            </div>
            <a href="/races" class="text-base text-base-content/60 hover:text-primary cursor-pointer">
                전체보기 →
            </a>
        </div>

        {#if upcomingRaces.length === 0}
            <div class="border border-base-300 rounded-lg p-8 text-center">
                <p class="text-base-content/50">등록된 대회가 없습니다</p>
            </div>
        {:else}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {#each upcomingRaces as race (race.id)}
                    <RaceCard {race} />
                {/each}
            </div>
        {/if}
    </div>
</section>

<!-- Recent Posts Section -->
<section class="py-8 bg-base-200/50">
    <div class="container mx-auto px-4">
        <div class="flex items-center justify-between mb-6">
            <div>
                <h2 class="text-xl md:text-2xl font-bold">자유게시판</h2>
                <p class="text-base-content/50 text-base">대회 후기와 정보를 나눠보세요</p>
            </div>
            {#if recentPosts.length > 0}
                <a href="/posts" class="text-base text-base-content/60 hover:text-primary cursor-pointer">
                    전체보기 →
                </a>
            {/if}
        </div>

        {#if recentPosts.length === 0}
            <div class="border border-base-300 rounded-lg p-8 text-center">
                <p class="text-base-content/50 mb-4">아직 작성된 글이 없습니다</p>
                <a href="/posts/create" class="btn btn-primary btn-sm">
                    첫 글 작성하기
                </a>
            </div>
        {:else}
            <div class="space-y-3">
                {#each recentPosts as post (post.id)}
                    <PostCard {post} showExcerpt />
                {/each}
            </div>
        {/if}
    </div>
</section>

<style>
    .scrollbar-hide::-webkit-scrollbar { display: none; }
    .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
</style>
