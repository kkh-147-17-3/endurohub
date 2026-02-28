<script lang="ts">
    import { goto } from '$app/navigation';
    import PostCard from '$lib/components/PostCard.svelte';
    import Pagination from '$lib/components/Pagination.svelte';

    let { data } = $props();

    let searchInput = $state('');
    let selectedCategory = $state('');
    let selectedSort = $state('latest');
    let isSearching = $state(false);

    $effect(() => {
        searchInput = data.search || '';
        selectedCategory = data.category || '';
        selectedSort = data.sort || 'latest';
    });

    function applyFilters() {
        isSearching = true;
        const params = new URLSearchParams();
        if (searchInput.trim()) params.set('search', searchInput.trim());
        if (selectedCategory) params.set('category', selectedCategory);
        if (selectedSort && selectedSort !== 'latest') params.set('sort', selectedSort);
        const qs = params.toString();
        goto(`/posts${qs ? '?' + qs : ''}`).then(() => { isSearching = false; });
    }

    function handleSearch(e: Event) {
        e.preventDefault();
        applyFilters();
    }

    function clearSearch() {
        searchInput = '';
        selectedCategory = '';
        selectedSort = 'latest';
        goto('/posts');
    }

    const categoryOptions = [
        { value: '', label: '전체' },
        { value: 'free', label: '자유' },
        { value: 'race_review', label: '대회 후기' },
        { value: 'injury', label: '부상/재활' },
        { value: 'gear', label: '장비 추천' },
        { value: 'training', label: '훈련 팁' },
        { value: 'question', label: '질문' },
    ];

    const sidebar = $derived(data.sidebar);
</script>

<svelte:head>
    <title>자유게시판 - 엔듀로허브</title>
    <meta name="description" content="대회 후기, 훈련 이야기, 자유로운 이야기를 나눠보세요." />
    <meta property="og:title" content="자유게시판 - 엔듀로허브" />
    <meta property="og:description" content="대회 후기, 훈련 이야기, 자유로운 이야기를 나눠보세요." />
</svelte:head>

<div class="container mx-auto px-4 py-8">
    <div class="mb-6">
        <h1 class="text-3xl font-bold">자유게시판</h1>
        <p class="text-base-content/60 mt-1">대회 후기, 훈련 이야기, 자유로운 이야기를 나눠보세요.</p>
    </div>

    <!-- Filters bar -->
    <form onsubmit={handleSearch} class="mb-6">
        <div class="flex flex-col sm:flex-row gap-3">
            <div class="join flex-1">
                <input type="text" bind:value={searchInput} placeholder="제목 또는 내용으로 검색..." class="input input-bordered join-item flex-1" />
                {#if data.search}
                    <button type="button" onclick={clearSearch} class="btn btn-ghost join-item" aria-label="검색 초기화">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                {/if}
                <button type="submit" class="btn btn-primary join-item" disabled={isSearching}>
                    {#if isSearching}
                        <span class="loading loading-spinner loading-sm"></span>
                    {:else}
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                    {/if}
                </button>
            </div>
            <div class="flex gap-2 shrink-0">
                <select class="select select-bordered select-sm sm:select-md" bind:value={selectedCategory} onchange={applyFilters}>
                    {#each categoryOptions as opt}
                        <option value={opt.value}>{opt.label}</option>
                    {/each}
                </select>
                <select class="select select-bordered select-sm sm:select-md" bind:value={selectedSort} onchange={applyFilters}>
                    <option value="latest">최신순</option>
                    <option value="popular">인기순</option>
                </select>
                <a href="/posts/create" class="btn btn-primary btn-sm sm:btn-md shrink-0">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
                    <span class="hidden sm:inline">글쓰기</span>
                </a>
            </div>
        </div>
    </form>

    {#if data.search || data.category}
        <div class="mb-4 flex items-center gap-2 text-sm text-base-content/60">
            {#if data.search}
                <span>"{data.search}" 검색 결과: {data.meta.total}개</span>
            {:else}
                <span>총 {data.meta.total}개</span>
            {/if}
        </div>
    {/if}

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Main content -->
        <div class="lg:col-span-2">
            {#if data.data.length === 0}
                <div class="alert">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-info shrink-0 w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    {#if data.search}
                        <span>검색 결과가 없습니다.</span>
                    {:else}
                        <span>아직 작성된 글이 없습니다. 첫 번째 글을 작성해보세요!</span>
                    {/if}
                </div>
            {:else}
                <div class="space-y-4">
                    {#each data.data as post (post.id)}
                        <PostCard {post} showExcerpt />
                    {/each}
                </div>

                <div class="mt-8 flex justify-center">
                    <Pagination meta={data.meta} showInfo scrollToTop />
                </div>
            {/if}
        </div>

        <!-- Sidebar -->
        {#if sidebar}
            <aside class="hidden lg:block space-y-6">
                {#if sidebar.popularPosts && sidebar.popularPosts.length > 0}
                    <div class="card bg-base-100 shadow-lg">
                        <div class="card-body">
                            <h3 class="card-title text-base">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" /></svg>
                                이번 주 인기 글
                            </h3>
                            <ul class="space-y-3 mt-2">
                                {#each sidebar.popularPosts as post, i}
                                    <li>
                                        <a href="/posts/{post.id}" class="flex items-start gap-2 group">
                                            <span class="text-sm font-bold text-base-content/40 mt-0.5">{i + 1}</span>
                                            <div class="min-w-0">
                                                <p class="text-sm font-medium line-clamp-1 group-hover:text-primary transition-colors">{post.title}</p>
                                                <p class="text-xs text-base-content/50">조회 {post.viewCount} · 추천 {post.likeCount}</p>
                                            </div>
                                        </a>
                                    </li>
                                {/each}
                            </ul>
                        </div>
                    </div>
                {/if}

                {#if sidebar.upcomingRaces && sidebar.upcomingRaces.length > 0}
                    <div class="card bg-base-100 shadow-lg">
                        <div class="card-body">
                            <h3 class="card-title text-base">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                다가오는 대회
                            </h3>
                            <ul class="space-y-3 mt-2">
                                {#each sidebar.upcomingRaces as race}
                                    <li>
                                        <a href="/races/{race.id}" class="flex items-center justify-between group">
                                            <span class="text-sm font-medium line-clamp-1 group-hover:text-primary transition-colors">{race.title}</span>
                                            <span class="text-xs text-base-content/50 shrink-0 ml-2">{race.raceDate}</span>
                                        </a>
                                    </li>
                                {/each}
                            </ul>
                            <a href="/races" class="text-sm text-primary hover:underline mt-2">전체 대회 보기 →</a>
                        </div>
                    </div>
                {/if}
            </aside>
        {/if}
    </div>
</div>

<style>
    .line-clamp-1 {
        display: -webkit-box;
        -webkit-line-clamp: 1;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
</style>
