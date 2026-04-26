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
        goto(`/posts${qs ? '?' + qs : ''}`).then(() => {
            isSearching = false;
        });
    }

    function handleSearch(e: Event) {
        e.preventDefault();
        applyFilters();
    }

    function clearAll() {
        searchInput = '';
        selectedCategory = '';
        selectedSort = 'latest';
        goto('/posts');
    }

    function selectCategory(value: string) {
        selectedCategory = selectedCategory === value ? '' : value;
        applyFilters();
    }

    function selectSort(value: string) {
        selectedSort = value;
        applyFilters();
    }

    const categoryOptions = [
        { value: 'free', label: '자유' },
        { value: 'race_review', label: '대회 후기' },
        { value: 'injury', label: '부상/재활' },
        { value: 'gear', label: '장비' },
        { value: 'training', label: '훈련' },
        { value: 'question', label: '질문' },
    ];

    const hasActiveFilter = $derived(!!(data.search || data.category));
</script>

<svelte:head>
    <title>커뮤니티 - 엔듀로허브</title>
    <meta name="description" content="대회 후기, 훈련 이야기, 자유로운 이야기를 나눠보세요." />
    <meta property="og:title" content="커뮤니티 - 엔듀로허브" />
    <meta property="og:description" content="대회 후기, 훈련 이야기, 자유로운 이야기를 나눠보세요." />
</svelte:head>

<div class="posts-wrap">
    <div class="filter-card">
        <form onsubmit={handleSearch}>
            <header class="filter-head">
                <div class="kicker">자유게시판</div>
                <h1 class="title">
                    커뮤니티
                    <span class="count">총 {data.meta.total.toLocaleString()}개</span>
                </h1>
            </header>

            <div class="search-row">
                <input
                    type="text"
                    bind:value={searchInput}
                    placeholder="제목 또는 내용으로 검색..."
                    class="search-input"
                />
                <button type="submit" class="submit-btn" disabled={isSearching}>
                    {isSearching ? '...' : '검색 →'}
                </button>
                <a href="/posts/create" class="write-btn">글쓰기 +</a>
            </div>

            <div class="quick-row">
                <span class="label">카테고리</span>
                <div class="chips">
                    {#each categoryOptions as opt}
                        <button
                            type="button"
                            class="chip"
                            class:active={selectedCategory === opt.value}
                            onclick={() => selectCategory(opt.value)}
                        >
                            {opt.label}
                        </button>
                    {/each}
                </div>
                <div class="sort-group">
                    <span class="label">정렬</span>
                    <div class="chips">
                        <button
                            type="button"
                            class="chip"
                            class:active={selectedSort === 'latest'}
                            onclick={() => selectSort('latest')}
                        >
                            최신순
                        </button>
                        <button
                            type="button"
                            class="chip"
                            class:active={selectedSort === 'popular'}
                            onclick={() => selectSort('popular')}
                        >
                            인기순
                        </button>
                    </div>
                </div>
            </div>

            {#if hasActiveFilter}
                <div class="active-row">
                    {#if data.search}
                        <span class="active-chip">
                            "{data.search}"
                            <button type="button" class="x" onclick={() => { searchInput = ''; applyFilters(); }} aria-label="검색어 제거">×</button>
                        </span>
                    {/if}
                    {#if data.category}
                        <span class="active-chip">
                            {categoryOptions.find((o) => o.value === data.category)?.label ?? data.category}
                            <button type="button" class="x" onclick={() => { selectedCategory = ''; applyFilters(); }} aria-label="카테고리 제거">×</button>
                        </span>
                    {/if}
                    <button type="button" class="clear-all" onclick={clearAll}>모두 지우기 ↺</button>
                </div>
            {/if}
        </form>
    </div>

    {#if data.data.length === 0}
        <div class="empty">
            <span class="kicker">NO RESULTS</span>
            <p>{data.search ? '검색 결과가 없습니다.' : '아직 작성된 글이 없습니다. 첫 번째 글을 작성해보세요.'}</p>
        </div>
    {:else}
        <div class="post-list">
            {#each data.data as post (post.id)}
                <PostCard {post} showExcerpt />
            {/each}
        </div>

        <div class="pagination-wrap">
            <Pagination meta={data.meta} showInfo scrollToTop />
        </div>
    {/if}
</div>

<style>
    .posts-wrap {
        max-width: 960px;
        margin: 0 auto;
        padding: 32px 24px;
    }
    @media (min-width: 1024px) {
        .posts-wrap {
            padding: 40px 32px;
        }
    }

    /* Filter card */
    .filter-card {
        background: var(--arena-paper);
        border: 1px solid var(--arena-line);
        margin-bottom: 24px;
        font-family: var(--arena-f-body);
        color: var(--arena-ink);
    }
    .filter-head {
        padding: 18px 22px 14px;
        border-bottom: 1px solid var(--arena-line-soft);
    }
    .kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: var(--arena-ink-soft);
        margin-bottom: 8px;
    }
    .title {
        font-family: var(--arena-f-display);
        font-size: clamp(22px, 3vw, 30px);
        font-weight: 700;
        letter-spacing: -0.5px;
        margin: 0;
        display: flex;
        align-items: baseline;
        gap: 12px;
        flex-wrap: wrap;
    }
    .count {
        font-family: var(--arena-f-mono);
        font-size: 12px;
        font-weight: 400;
        letter-spacing: 1px;
        color: var(--arena-ink-soft);
    }

    .search-row {
        display: flex;
        gap: 0;
        padding: 14px 22px;
        border-bottom: 1px solid var(--arena-line-soft);
    }
    .search-input {
        flex: 1;
        min-width: 0;
        border: 1px solid var(--arena-line);
        border-radius: 0;
        background: var(--arena-paper);
        padding: 10px 14px;
        font-family: var(--arena-f-body);
        font-size: 14px;
        color: var(--arena-ink);
        border-right: none;
        appearance: none;
        -webkit-appearance: none;
    }
    .search-input:focus {
        outline: none;
        border-color: var(--arena-ink);
        background: var(--arena-paper-alt);
    }
    .search-input::placeholder {
        color: var(--arena-ink-mute);
    }
    .submit-btn {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border: 1px solid var(--arena-ink);
        padding: 10px 18px;
        font-family: var(--arena-f-mono);
        font-size: 12px;
        letter-spacing: 1px;
        cursor: pointer;
        text-transform: uppercase;
        white-space: nowrap;
    }
    .submit-btn:hover {
        background: var(--arena-ink-soft);
    }
    .write-btn {
        background: var(--arena-accent);
        color: var(--arena-ink);
        border: 1px solid var(--arena-accent);
        padding: 10px 16px;
        margin-left: 8px;
        font-family: var(--arena-f-mono);
        font-size: 12px;
        letter-spacing: 1px;
        text-transform: uppercase;
        text-decoration: none;
        white-space: nowrap;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
    }
    .write-btn:hover {
        background: var(--arena-accent-deep);
        color: var(--arena-paper);
        border-color: var(--arena-accent-deep);
    }

    .quick-row {
        padding: 12px 22px;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 10px 16px;
    }
    .label {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
    }
    .chips {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }
    .chip {
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
        color: var(--arena-ink);
        padding: 6px 12px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.5px;
        cursor: pointer;
        transition: background 0.1s, border-color 0.1s;
        line-height: 1.4;
    }
    .chip:hover {
        border-color: var(--arena-ink);
    }
    .chip.active {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border-color: var(--arena-ink);
    }
    .sort-group {
        margin-left: auto;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .active-row {
        padding: 12px 22px;
        border-top: 1px solid var(--arena-line-soft);
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: center;
    }
    .active-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: var(--arena-ink);
        color: var(--arena-paper);
        padding: 4px 6px 4px 10px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.5px;
        line-height: 1.4;
        border: 1px solid var(--arena-ink);
    }
    .active-chip .x {
        background: transparent;
        border: none;
        color: inherit;
        cursor: pointer;
        font-size: 14px;
        line-height: 1;
        padding: 0 2px;
        opacity: 0.7;
        transform: translateY(-1px);
    }
    .active-chip .x:hover {
        opacity: 1;
    }
    .clear-all {
        margin-left: auto;
        background: transparent;
        border: none;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1px;
        color: var(--arena-ink-soft);
        cursor: pointer;
        text-transform: uppercase;
    }
    .clear-all:hover {
        color: var(--arena-urgent);
    }

    @media (max-width: 640px) {
        .filter-head,
        .search-row,
        .quick-row,
        .active-row {
            padding-left: 16px;
            padding-right: 16px;
        }
        .sort-group {
            margin-left: 0;
            width: 100%;
            padding-top: 4px;
            border-top: 1px dashed var(--arena-line-soft);
        }
        .clear-all {
            margin-left: 0;
        }
    }

    /* Empty */
    .empty {
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
        padding: 48px 24px;
        text-align: center;
        font-family: var(--arena-f-body);
        color: var(--arena-ink-soft);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
    }
    .empty .kicker {
        margin-bottom: 0;
    }
    .empty p {
        margin: 0;
        font-size: 14px;
    }

    /* Post list */
    .post-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    .pagination-wrap {
        margin-top: 32px;
        display: flex;
        justify-content: center;
    }
</style>
