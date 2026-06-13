<script lang="ts">
    import { goto } from '$app/navigation';
    import FilterChip from '$lib/components/eh/FilterChip.svelte';
    import SportTag from '$lib/components/eh/SportTag.svelte';
    import Button from '$lib/components/eh/Button.svelte';
    import Pagination from '$lib/components/Pagination.svelte';
    import { formatDistanceToNow } from '$lib/date';
    import { dsSport } from '$lib/components/eh/meta';
    import type { Post } from '$lib/types';

    let { data } = $props();

    // ── Category definitions ────────────────────────────────────────
    type CatKey = 'all' | 'race_review' | 'question' | 'free' | 'injury' | 'gear' | 'training';
    const CATS: Record<CatKey, { label: string }> = {
        all:         { label: '전체' },
        race_review: { label: '후기' },
        question:    { label: 'Q&A' },
        free:        { label: '자유' },
        injury:      { label: '부상/재활' },
        gear:        { label: '장비' },
        training:    { label: '훈련' },
    };

    // ── State ────────────────────────────────────────────────────────
    let selectedCat = $state<CatKey>((data.category as CatKey) || 'all');
    let selectedSort = $state(data.sort || 'latest');
    let searchInput = $state(data.search || '');
    let searchDraft = $state(data.search || '');

    // Sync state when loader data changes (browser nav)
    $effect(() => {
        selectedCat = (data.category as CatKey) || 'all';
        selectedSort = data.sort || 'latest';
        searchInput = data.search || '';
        searchDraft = data.search || '';
    });

    // ── Navigation helpers ───────────────────────────────────────────
    function navigate(overrides: Record<string, string | null> = {}) {
        const params = new URLSearchParams();
        const cat = overrides.category !== undefined ? overrides.category : selectedCat;
        const sort = overrides.sort !== undefined ? overrides.sort : selectedSort;
        const search = overrides.search !== undefined ? overrides.search : searchInput;
        if (cat && cat !== 'all') params.set('category', cat);
        if (sort && sort !== 'latest') params.set('sort', sort);
        if (search && search.trim()) params.set('search', search.trim());
        const qs = params.toString();
        goto(`/community${qs ? '?' + qs : ''}`, { keepFocus: true });
    }

    function selectCat(k: CatKey) {
        navigate({ category: k === 'all' ? null : k, page: null });
    }

    function selectSort(s: string) {
        navigate({ sort: s !== 'latest' ? s : null, page: null });
    }

    function handleSearch(e: Event) {
        e.preventDefault();
        searchInput = searchDraft;
        navigate({ search: searchDraft.trim() || null, page: null });
    }

    function clearSearch() {
        searchDraft = '';
        searchInput = '';
        navigate({ search: null, page: null });
    }

    // ── Derived ──────────────────────────────────────────────────────
    const posts = $derived(data.data as Post[]);
    const meta = $derived(data.meta);
    const sidebar = $derived(data.sidebar);
    const totalCount = $derived(meta?.total ?? 0);

    // ── Helpers ──────────────────────────────────────────────────────
    const CAT_LABELS: Record<string, string> = {
        race_review: '후기',
        question:    'Q&A',
        free:        '자유',
        injury:      '부상/재활',
        gear:        '장비',
        training:    '훈련',
    };

    function catLabel(cat: string | null | undefined): string {
        if (!cat) return '자유';
        return CAT_LABELS[cat] ?? cat;
    }

    function isHot(post: Post): boolean {
        return post.likeCount >= 10 || post.commentCount >= 10;
    }

    // Primary sport from first tagged race
    function postSport(post: Post): string | null {
        return post.taggedRaces?.[0]?.sport ?? null;
    }

    // Result card data — post has a tagged race with sport + result data in title
    // We rely on taggedRaces for the race label; no dedicated result fields on Post
    function hasResultCard(post: Post): boolean {
        return (
            (post.category === 'race_review') &&
            post.taggedRaces != null &&
            post.taggedRaces.length > 0
        );
    }

    // Excerpt from contentText
    function excerpt(post: Post): string {
        const text = (post.contentText || post.content?.replace(/<[^>]*>/g, '') || '').trim();
        return text.length > 160 ? text.slice(0, 160) + '…' : text;
    }
</script>

<svelte:head>
    <title>커뮤니티 - 엔듀로허브</title>
    <meta name="description" content="대회 후기, Q&A, 자유로운 이야기를 나눠보세요." />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="커뮤니티 - 엔듀로허브" />
    <meta property="og:description" content="대회 후기, Q&A, 자유로운 이야기를 나눠보세요." />
    <meta property="og:image" content="{data.appUrl}/images/og-image.png" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta name="twitter:image" content="{data.appUrl}/images/og-image.png" />
</svelte:head>

<div class="v-container">
    <!-- ── Page header ──────────────────────────────────────── -->
    <div class="hd">
        <div>
            <div class="eh-micro"><span class="acc">COMMUNITY</span> · 후기 / Q&A / 크루</div>
            <h1 class="eh-h1" style="margin-top: var(--sp-2);">커뮤니티</h1>
        </div>
        <Button href="/posts/create" variant="primary">글쓰기</Button>
    </div>

    <!-- ── Toolbar: category chips + search + sort ─────────── -->
    <div class="toolbar">
        <div class="toolbar-chips">
            {#each Object.entries(CATS) as [k, v]}
                <FilterChip
                    selected={selectedCat === k}
                    onclick={() => selectCat(k as CatKey)}
                >
                    {v.label}
                </FilterChip>
            {/each}
        </div>

        <div class="toolbar-right">
            <form class="search-form" onsubmit={handleSearch}>
                <input
                    class="search-input"
                    type="search"
                    placeholder="검색"
                    bind:value={searchDraft}
                    aria-label="게시글 검색"
                />
                {#if searchDraft}
                    <button type="button" class="search-clear" onclick={clearSearch} aria-label="검색 지우기">×</button>
                {/if}
                <button type="submit" class="search-btn" aria-label="검색 실행">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                </button>
            </form>

            <div class="sort-group">
                <button
                    type="button"
                    class="sort-btn"
                    class:sort-btn--on={selectedSort === 'latest'}
                    onclick={() => selectSort('latest')}
                >최신순</button>
                <button
                    type="button"
                    class="sort-btn"
                    class:sort-btn--on={selectedSort === 'popular'}
                    onclick={() => selectSort('popular')}
                >인기순</button>
            </div>

            <span class="eh-micro eh-data post-count">{totalCount.toLocaleString()} POSTS</span>
        </div>
    </div>

    <!-- ── Active search banner ────────────────────────────── -->
    {#if searchInput}
        <div class="search-banner">
            <span class="eh-micro">검색: <strong>"{searchInput}"</strong></span>
            <button type="button" class="search-clear-btn" onclick={clearSearch}>지우기 ×</button>
        </div>
    {/if}

    <!-- ── Two-column layout ───────────────────────────────── -->
    <div class="layout">
        <!-- Feed -->
        <div class="feed">
            {#if posts.length === 0}
                <div class="empty">
                    <span class="eh-micro">NO RESULTS</span>
                    <p>{searchInput ? '검색 결과가 없습니다.' : '아직 작성된 글이 없습니다.'}</p>
                    <a href="/posts/create" class="eh-btn eh-btn--sm eh-btn--secondary" style="margin-top: var(--sp-3);">첫 글 작성하기</a>
                </div>
            {:else}
                {#each posts as post (post.id)}
                    <a href="/posts/{post.id}" class="post-row">
                        <div class="post-top">
                            {#if isHot(post)}
                                <span class="mark mark--hot eh-micro">HOT</span>
                            {/if}
                            <span class="cat-chip eh-micro">{catLabel(post.category)}</span>
                            {#if postSport(post)}
                                <SportTag sport={dsSport(postSport(post) as any)} muted />
                            {/if}
                        </div>

                        <h3 class="post-title">{post.title}</h3>

                        {#if post.contentText || post.content}
                            <p class="post-snip">{excerpt(post)}</p>
                        {/if}

                        {#if hasResultCard(post)}
                            <div class="result-strip eh-data">
                                {#each (post.taggedRaces ?? []).slice(0, 1) as race}
                                    <span class="result-race">{race.title}</span>
                                {/each}
                            </div>
                        {/if}

                        <div class="post-meta eh-data">
                            <span><strong>{post.nickname}</strong> · {formatDistanceToNow(post.createdAt)}</span>
                            <span>조회 {post.viewCount.toLocaleString()}</span>
                            <span>댓글 {post.commentCount}</span>
                            <span>추천 {post.likeCount}</span>
                        </div>
                    </a>
                {/each}

                {#if meta && meta.lastPage > 1}
                    <div class="pag-wrap">
                        <Pagination {meta} showInfo scrollToTop />
                    </div>
                {/if}
            {/if}
        </div>

        <!-- Right rail -->
        <aside class="rail">
            <!-- Hot posts -->
            {#if sidebar?.popularPosts && sidebar.popularPosts.length > 0}
                <div class="rail-box">
                    <div class="rail-head eh-micro"><span class="acc">HOT</span> · 지금 뜨는 글</div>
                    {#each sidebar.popularPosts.slice(0, 5) as p, i}
                        <a href="/posts/{p.id}" class="rail-row">
                            <span class="rail-rank eh-data" class:rail-rank--top={i < 3}>{i + 1}</span>
                            <span class="rail-nm">{p.title}</span>
                            <span class="rail-n eh-data">{p.commentCount}</span>
                        </a>
                    {/each}
                </div>
            {/if}

            <!-- Upcoming races (events this week) -->
            {#if sidebar?.upcomingRaces && sidebar.upcomingRaces.length > 0}
                <div class="rail-box">
                    <div class="rail-head eh-micro">다가오는 대회</div>
                    {#each sidebar.upcomingRaces.slice(0, 4) as r}
                        <a href="/races/{r.id}" class="rail-row rail-row--event">
                            <span class="rail-date eh-data">{r.raceDate?.slice(5).replace('-', '·') ?? '—'}</span>
                            <span class="rail-nm">{r.title}</span>
                        </a>
                    {/each}
                </div>
            {/if}

            <!-- Write CTA -->
            <div class="rail-cta">
                <div class="eh-micro" style="margin-bottom: var(--sp-3);">이야기를 나눠보세요</div>
                <Button href="/posts/create" variant="secondary" size="sm" fullWidth>글쓰기</Button>
            </div>
        </aside>
    </div>
</div>

<style>
    /* ── Layout ────────────────────────────────── */
    .v-container {
        padding-top: 0;
        padding-bottom: var(--sp-20);
    }

    .hd {
        padding: var(--sp-10) 0 0;
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: var(--sp-4);
        flex-wrap: wrap;
    }
    .acc { color: var(--accent-strong); }

    /* ── Toolbar ───────────────────────────────── */
    .toolbar {
        display: flex;
        align-items: center;
        gap: var(--sp-4);
        margin-top: 22px;
        padding: 14px 0;
        border-top: var(--border-rule);
        border-bottom: var(--border-hair);
        flex-wrap: wrap;
    }
    .toolbar-chips {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
    }
    .toolbar-right {
        display: flex;
        align-items: center;
        gap: var(--sp-3);
        margin-left: auto;
        flex-wrap: wrap;
    }
    .post-count {
        white-space: nowrap;
    }

    /* Search input */
    .search-form {
        position: relative;
        display: flex;
        align-items: center;
    }
    .search-input {
        height: 34px;
        padding: 0 32px 0 12px;
        font-family: var(--font-sans);
        font-size: 13px;
        color: var(--text-strong);
        background: var(--paper-0);
        border: 1px solid var(--line);
        border-radius: 0;
        appearance: none;
        width: 160px;
        transition: border-color var(--dur-fast) var(--ease-out), width var(--dur-base) var(--ease-out);
    }
    .search-input:focus {
        outline: none;
        border-color: var(--ink-900);
        width: 200px;
    }
    .search-input::placeholder { color: var(--text-faint); }
    .search-btn {
        position: absolute;
        right: 8px;
        background: none;
        border: none;
        cursor: pointer;
        color: var(--text-muted);
        padding: 0;
        display: flex;
        align-items: center;
    }
    .search-clear {
        position: absolute;
        right: 28px;
        background: none;
        border: none;
        cursor: pointer;
        color: var(--text-faint);
        font-size: 14px;
        line-height: 1;
        padding: 0 2px;
    }
    .search-clear:hover { color: var(--text-strong); }

    /* Sort buttons */
    .sort-group {
        display: flex;
        border: 1px solid var(--line);
    }
    .sort-btn {
        height: 34px;
        padding: 0 12px;
        font-family: var(--font-sans);
        font-size: 12px;
        font-weight: 600;
        color: var(--text-muted);
        background: var(--paper-0);
        border: none;
        border-right: 1px solid var(--line);
        cursor: pointer;
        letter-spacing: -0.01em;
        transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
        white-space: nowrap;
    }
    .sort-btn:last-child { border-right: none; }
    .sort-btn:hover { color: var(--text-strong); background: var(--paper-50); }
    .sort-btn--on { background: var(--ink-900); color: var(--paper-0); border-color: var(--ink-900); }
    .sort-btn--on + .sort-btn { border-left: none; }

    /* Active search banner */
    .search-banner {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 14px;
        background: var(--paper-50);
        border: var(--border-hair);
        border-top: none;
        font-size: 13px;
        color: var(--text-muted);
    }
    .search-banner strong { color: var(--text-strong); font-weight: 600; }
    .search-clear-btn {
        background: none;
        border: none;
        cursor: pointer;
        font-family: var(--font-sans);
        font-size: 11px;
        font-weight: 600;
        color: var(--text-faint);
        letter-spacing: 0.04em;
        padding: 0;
    }
    .search-clear-btn:hover { color: var(--danger); }

    /* ── Two-column layout ─────────────────────── */
    .layout {
        display: grid;
        grid-template-columns: minmax(0, 1fr) 300px;
        gap: var(--sp-10);
        align-items: start;
        margin-top: var(--sp-2);
    }

    /* ── Post rows ─────────────────────────────── */
    .feed {
        min-width: 0;
    }
    .post-row {
        display: block;
        padding: 18px 4px;
        border-bottom: var(--border-hair);
        text-decoration: none;
        color: inherit;
        cursor: pointer;
        transition: background var(--dur-fast) var(--ease-out);
    }
    .post-row:hover { background: var(--paper-50); }

    .post-top {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }
    .mark {
        padding: 2px 6px;
        border-radius: var(--r-2);
        letter-spacing: var(--track-micro);
    }
    .mark--hot {
        color: var(--danger);
        background: var(--danger-bg);
        font-weight: 800;
    }
    /* category chip */
    .cat-chip {
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        padding: 2px 7px;
        border: 1px solid var(--line);
        border-radius: var(--r-2);
        color: var(--text-muted);
        white-space: nowrap;
    }

    .post-title {
        font-size: 16.5px;
        font-weight: 700;
        letter-spacing: var(--track-heading);
        line-height: var(--leading-tight);
        margin: 8px 0 0;
        color: var(--text-strong);
    }
    .post-row:hover .post-title {
        text-decoration: underline;
        text-underline-offset: 3px;
    }

    .post-snip {
        font-size: 13.5px;
        color: var(--text-muted);
        line-height: 1.55;
        margin: 6px 0 0;
        max-width: 640px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    /* result strip (대회 후기) */
    .result-strip {
        display: inline-flex;
        gap: 0;
        border: 1px solid var(--line);
        margin-top: 10px;
    }
    .result-race {
        padding: 5px 12px;
        font-size: 12px;
        color: var(--text-muted);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 280px;
    }

    .post-meta {
        display: flex;
        gap: 14px;
        margin-top: 10px;
        font-size: 12px;
        color: var(--text-faint);
        flex-wrap: wrap;
    }
    .post-meta strong {
        color: var(--text-muted);
        font-weight: 600;
    }

    .empty {
        padding: 64px 24px;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        border-bottom: var(--border-hair);
    }
    .empty p {
        margin: 0;
        font-size: 14px;
        color: var(--text-muted);
    }

    .pag-wrap {
        margin-top: var(--sp-8);
        display: flex;
        justify-content: center;
    }

    /* ── Right rail ────────────────────────────── */
    .rail {
        position: sticky;
        top: 80px;
        display: flex;
        flex-direction: column;
        gap: var(--sp-5);
    }
    .rail-box {
        border-top: var(--border-rule);
        padding-top: 12px;
    }
    .rail-head {
        margin-bottom: 4px;
    }
    .rail-row {
        display: grid;
        grid-template-columns: 18px 1fr auto;
        gap: 10px;
        align-items: baseline;
        padding: 9px 0;
        border-bottom: var(--border-hair);
        font-size: 13.5px;
        text-decoration: none;
        color: inherit;
        transition: background var(--dur-fast) var(--ease-out);
    }
    .rail-row:hover { background: var(--paper-50); }
    .rail-row:last-child { border-bottom: 0; }
    .rail-row--event {
        grid-template-columns: 44px 1fr;
    }
    .rail-rank {
        font-weight: 800;
        color: var(--text-faint);
        font-size: 12px;
    }
    .rail-rank--top { color: var(--text-strong); }
    .rail-nm {
        font-weight: 600;
        color: var(--text-strong);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        min-width: 0;
    }
    .rail-n {
        color: var(--text-faint);
        font-size: 12px;
        white-space: nowrap;
    }
    .rail-date {
        font-weight: 700;
        font-size: 12px;
        color: var(--text-muted);
    }

    .rail-cta {
        border-top: var(--border-rule);
        padding-top: 12px;
    }

    /* ── Responsive ────────────────────────────── */
    @media (max-width: 960px) {
        .layout {
            grid-template-columns: 1fr;
        }
        .rail {
            position: static;
        }
    }
    @media (max-width: 768px) {
        .hd {
            padding-top: 22px;
        }
        .toolbar-right {
            width: 100%;
            margin-left: 0;
            justify-content: space-between;
        }
        .search-input {
            width: 120px;
        }
        .search-input:focus {
            width: 160px;
        }
    }
</style>
