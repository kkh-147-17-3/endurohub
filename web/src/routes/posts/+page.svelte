<script lang="ts">
    import { goto } from '$app/navigation';
    import PostCard from '$lib/components/PostCard.svelte';
    import Pagination from '$lib/components/Pagination.svelte';

    let { data } = $props();

    let searchInput = $state(data.search || '');
    let isSearching = $state(false);

    function handleSearch(e: Event) {
        e.preventDefault();
        isSearching = true;
        const params = new URLSearchParams();
        if (searchInput.trim()) params.set('search', searchInput.trim());
        goto(`/posts?${params.toString()}`).then(() => { isSearching = false; });
    }

    function clearSearch() {
        searchInput = '';
        goto('/posts');
    }
</script>

<svelte:head>
    <title>자유게시판 - 엔듀로허브</title>
    <meta name="description" content="대회 후기, 훈련 이야기, 자유로운 이야기를 나눠보세요." />
    <meta property="og:title" content="자유게시판 - 엔듀로허브" />
    <meta property="og:description" content="대회 후기, 훈련 이야기, 자유로운 이야기를 나눠보세요." />
</svelte:head>

<div class="container mx-auto px-4 py-8">
    <div class="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
            <h1 class="text-3xl font-bold">자유게시판</h1>
            <p class="text-base-content/60 mt-1">대회 후기, 훈련 이야기, 자유로운 이야기를 나눠보세요.</p>
        </div>
        <a href="/posts/create" class="btn btn-primary shrink-0">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
            글쓰기
        </a>
    </div>

    <form onsubmit={handleSearch} class="mb-6">
        <div class="join w-full">
            <input type="text" bind:value={searchInput} placeholder="제목 또는 내용으로 검색..." class="input input-bordered join-item flex-1" />
            {#if data.search}
                <button type="button" onclick={clearSearch} class="btn btn-ghost join-item">
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
    </form>

    {#if data.search}
        <div class="mb-4 flex items-center gap-2 text-sm text-base-content/60">
            <span>"{data.search}" 검색 결과: {data.meta.total}개</span>
        </div>
    {/if}

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
