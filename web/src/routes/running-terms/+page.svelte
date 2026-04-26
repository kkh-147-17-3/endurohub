<script lang="ts">
    import ToolsSidebar from '$lib/components/Tools/ToolsSidebar.svelte';
    import { glossaryTerms, categoryLabels, type GlossaryCategory } from '$lib/tools/glossary-data';

    let selectedCategory = $state<GlossaryCategory | 'all'>('all');
    let searchQuery = $state('');

    let filteredTerms = $derived.by(() => {
        let terms = glossaryTerms;
        if (selectedCategory !== 'all') {
            terms = terms.filter((t) => t.category === selectedCategory);
        }
        if (searchQuery.trim()) {
            const q = searchQuery.trim().toLowerCase();
            terms = terms.filter(
                (t) =>
                    t.term.toLowerCase().includes(q) ||
                    t.shortDesc.includes(q) ||
                    t.fullDesc.includes(q)
            );
        }
        return terms;
    });

    let categories = $derived.by(() => {
        const counts = new Map<string, number>();
        for (const t of glossaryTerms) {
            counts.set(t.category, (counts.get(t.category) || 0) + 1);
        }
        return Object.entries(categoryLabels).map(([key, label]) => ({
            key: key as GlossaryCategory,
            label,
            count: counts.get(key) || 0,
        }));
    });

    let expandedId = $state<string | null>(null);

    function toggle(id: string) {
        expandedId = expandedId === id ? null : id;
    }

    function getRelatedTerms(ids: string[] | undefined) {
        if (!ids) return [];
        return ids.map((id) => glossaryTerms.find((t) => t.id === id)).filter(Boolean);
    }

    const KOREAN_INITIALS = ['ㄱ','ㄲ','ㄴ','ㄷ','ㄸ','ㄹ','ㅁ','ㅂ','ㅃ','ㅅ','ㅆ','ㅇ','ㅈ','ㅉ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ'];
    const DISPLAY_INITIALS = ['ㄱ','ㄴ','ㄷ','ㄹ','ㅁ','ㅂ','ㅅ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ','A-Z','0-9'];
    const DOUBLE_TO_SINGLE: Record<string, string> = { 'ㄲ':'ㄱ', 'ㄸ':'ㄷ', 'ㅃ':'ㅂ', 'ㅆ':'ㅅ', 'ㅉ':'ㅈ' };

    function getInitial(str: string): string {
        const ch = str.charAt(0);
        const code = ch.charCodeAt(0);
        if (code >= 0xac00 && code <= 0xd7a3) {
            const idx = Math.floor((code - 0xac00) / (21 * 28));
            const initial = KOREAN_INITIALS[idx];
            return DOUBLE_TO_SINGLE[initial] || initial;
        }
        if (/[a-zA-Z]/.test(ch)) return 'A-Z';
        if (/[0-9]/.test(ch)) return '0-9';
        return 'ㅇ';
    }

    let groupedTerms = $derived.by(() => {
        const groups = new Map<string, typeof filteredTerms>();
        for (const term of filteredTerms) {
            const initial = getInitial(term.term);
            if (!groups.has(initial)) groups.set(initial, []);
            groups.get(initial)!.push(term);
        }
        const ordered: { initial: string; terms: typeof filteredTerms }[] = [];
        for (const ini of DISPLAY_INITIALS) {
            if (groups.has(ini)) {
                ordered.push({ initial: ini, terms: groups.get(ini)! });
            }
        }
        return ordered;
    });

    let availableInitials = $derived(new Set(groupedTerms.map((g) => g.initial)));

    function scrollToGroup(initial: string) {
        document.getElementById(`group-${initial}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function clearSearch() {
        searchQuery = '';
    }

    function resetAll() {
        searchQuery = '';
        selectedCategory = 'all';
    }

    let faqSchema = $derived({
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        mainEntity: glossaryTerms.slice(0, 20).map((t) => ({
            '@type': 'Question',
            name: `${t.term}이란?`,
            acceptedAnswer: { '@type': 'Answer', text: t.fullDesc },
        })),
    });
</script>

<svelte:head>
    <title>러닝 용어 사전 - 엔듀로허브</title>
    <meta
        name="description"
        content="마라톤 러닝 용어 사전 - LSD, 인터벌, 템포런, VO2max, 네거티브 스플릿, 카보로딩 등 러닝 용어를 초보자도 이해하기 쉽게 설명합니다."
    />
    <meta property="og:title" content="러닝 용어 사전 - 엔듀로허브" />
    <meta
        property="og:description"
        content="LSD, 인터벌, 템포런, VO2max, 네거티브 스플릿 등 러닝 용어를 쉽게 알아보세요."
    />
    {@html `<script type="application/ld+json">${JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebPage',
        name: '러닝 용어 사전 - 엔듀로허브',
        description:
            '마라톤, 러닝 용어 사전 - LSD, 인터벌, 템포런, VO2max, 네거티브 스플릿 등 러닝 용어를 쉽게 알아보세요.',
    })}</script>`}
    {@html `<script type="application/ld+json">${JSON.stringify(faqSchema)}</script>`}
    {@html `<script type="application/ld+json">${JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        itemListElement: [
            { '@type': 'ListItem', position: 1, name: '홈', item: 'https://www.endurohub.kr' },
            { '@type': 'ListItem', position: 2, name: '러닝 용어 사전' },
        ],
    })}</script>`}
</svelte:head>

<div class="page-wrap">
    <article class="page-shell">
        <nav class="crumbs" aria-label="breadcrumb">
            <a href="/" class="crumb-link">홈</a>
            <span class="crumb-sep">/</span>
            <span class="crumb-current">러닝 용어 사전</span>
        </nav>

        <header class="page-head">
            <div class="head-row">
                <div class="arena-kicker">용어 · {glossaryTerms.length}</div>
                <div class="head-meta">
                    <span class="meta-key">결과</span>
                    <span class="meta-val">{filteredTerms.length}</span>
                </div>
            </div>
            <h1 class="page-title">러닝 용어 사전</h1>
            <p class="page-lead">
                마라톤과 러닝에서 자주 쓰이는 용어를 카테고리·초성별로 정리했습니다.
            </p>
        </header>

        <div class="filter-bar">
            <div class="search-wrap">
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="search-icon"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    stroke-width="2"
                    aria-hidden="true"
                >
                    <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                    type="text"
                    bind:value={searchQuery}
                    placeholder="용어 검색"
                    class="search-input"
                    aria-label="용어 검색"
                />
                {#if searchQuery}
                    <button type="button" class="search-clear" onclick={clearSearch} aria-label="검색어 지우기">
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            class="clear-icon"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            stroke-width="2"
                        >
                            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                {/if}
            </div>

            <div class="cat-row" role="tablist" aria-label="카테고리">
                <button
                    type="button"
                    class="cat-chip"
                    class:active={selectedCategory === 'all'}
                    role="tab"
                    aria-selected={selectedCategory === 'all'}
                    onclick={() => (selectedCategory = 'all')}
                >
                    <span class="cat-label">전체</span>
                    <span class="cat-count">{glossaryTerms.length}</span>
                </button>
                {#each categories as cat (cat.key)}
                    <button
                        type="button"
                        class="cat-chip"
                        class:active={selectedCategory === cat.key}
                        data-cat={cat.key}
                        role="tab"
                        aria-selected={selectedCategory === cat.key}
                        onclick={() => (selectedCategory = cat.key)}
                    >
                        <span class="cat-label">{cat.label}</span>
                        <span class="cat-count">{cat.count}</span>
                    </button>
                {/each}
            </div>
        </div>

        {#if !searchQuery.trim()}
            <div class="initials-row" aria-label="초성으로 이동">
                {#each DISPLAY_INITIALS as ini}
                    {@const has = availableInitials.has(ini)}
                    <button
                        type="button"
                        class="initial-btn"
                        class:has
                        disabled={!has}
                        onclick={() => scrollToGroup(ini)}
                        aria-label={`${ini}으로 이동`}
                    >
                        {ini}
                    </button>
                {/each}
            </div>
        {/if}

        <div class="groups">
            {#each groupedTerms as group (group.initial)}
                <section id={`group-${group.initial}`} class="group">
                    <div class="group-head">
                        <span class="group-initial">{group.initial}</span>
                        <span class="group-rule"></span>
                        <span class="group-count">{group.terms.length}개</span>
                    </div>

                    <div class="term-list">
                        {#each group.terms as term (term.id)}
                            {@const open = expandedId === term.id}
                            <div id={term.id} class="term" class:open>
                                <button
                                    type="button"
                                    class="term-head"
                                    onclick={() => toggle(term.id)}
                                    aria-expanded={open}
                                >
                                    <div class="term-meta">
                                        <span class="term-cat" data-cat={term.category}>
                                            {categoryLabels[term.category]}
                                        </span>
                                    </div>
                                    <div class="term-body">
                                        <h2 class="term-title">{term.term}</h2>
                                        <p class="term-short">{term.shortDesc}</p>
                                    </div>
                                    <span class="term-toggle" aria-hidden="true">
                                        {open ? '−' : '+'}
                                    </span>
                                </button>

                                {#if open}
                                    <div class="term-detail">
                                        <p class="detail-text">{term.fullDesc}</p>
                                        {#if term.related && term.related.length > 0}
                                            <div class="related">
                                                <div class="arena-kicker related-kicker">관련 용어</div>
                                                <div class="related-list">
                                                    {#each getRelatedTerms(term.related) as related}
                                                        {#if related}
                                                            <button
                                                                type="button"
                                                                class="related-chip"
                                                                onclick={() => {
                                                                    expandedId = related.id;
                                                                    document
                                                                        .getElementById(related.id)
                                                                        ?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                                                }}
                                                            >
                                                                {related.term}
                                                                <span class="related-arrow">→</span>
                                                            </button>
                                                        {/if}
                                                    {/each}
                                                </div>
                                            </div>
                                        {/if}
                                    </div>
                                {/if}
                            </div>
                        {/each}
                    </div>
                </section>
            {/each}
        </div>

        {#if filteredTerms.length === 0}
            <div class="empty">
                <div class="arena-kicker">결과 없음</div>
                <p class="empty-msg">조건에 맞는 용어가 없습니다.</p>
                <button type="button" class="empty-reset" onclick={resetAll}>
                    필터 초기화 <span class="empty-arrow">→</span>
                </button>
            </div>
        {/if}

        <div class="sidebar-wrap">
            <ToolsSidebar current="glossary" />
        </div>
    </article>
</div>

<style>
    .page-wrap {
        background: var(--arena-paper);
        padding: 40px 24px 80px;
    }
    .page-shell {
        max-width: 880px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        gap: 24px;
    }

    /* Breadcrumbs */
    .crumbs {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
    }
    .crumb-link {
        color: var(--arena-ink-soft);
        text-decoration: none;
    }
    .crumb-link:hover {
        color: var(--arena-ink);
    }
    .crumb-sep {
        color: var(--arena-ink-mute);
    }
    .crumb-current {
        color: var(--arena-ink);
        font-weight: 600;
    }

    /* Header */
    .page-head {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding-bottom: 24px;
        border-bottom: 1px solid var(--arena-line);
    }
    .head-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
    }
    .head-meta {
        display: inline-flex;
        align-items: baseline;
        gap: 6px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
    }
    .meta-key {
        color: var(--arena-ink-mute);
        letter-spacing: 1.5px;
    }
    .meta-val {
        color: var(--arena-ink);
        font-weight: 700;
    }
    .page-title {
        font-family: var(--arena-f-display);
        font-size: 44px;
        font-weight: 700;
        letter-spacing: -1.5px;
        line-height: 1;
        margin: 0;
        color: var(--arena-ink);
    }
    .page-lead {
        font-family: var(--arena-f-body);
        font-size: 14px;
        line-height: 1.6;
        color: var(--arena-ink-soft);
        margin: 0;
        max-width: 56ch;
        word-break: keep-all;
    }

    /* Filter bar */
    .filter-bar {
        position: sticky;
        top: 64px;
        z-index: 10;
        background: var(--arena-paper);
        padding: 12px 0;
        margin: 0 -4px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        border-top: 1px solid transparent;
        border-bottom: 1px solid var(--arena-line);
    }
    .search-wrap {
        position: relative;
        display: flex;
        align-items: center;
    }
    .search-icon {
        position: absolute;
        left: 12px;
        top: 50%;
        transform: translateY(-50%);
        width: 16px;
        height: 16px;
        color: var(--arena-ink-soft);
        pointer-events: none;
    }
    .search-input {
        width: 100%;
        padding: 11px 36px 11px 36px;
        background: var(--arena-paper);
        border: 1px solid var(--arena-line);
        font-family: var(--arena-f-body);
        font-size: 14px;
        color: var(--arena-ink);
        outline: none;
        transition: border-color 0.1s, box-shadow 0.1s;
    }
    .search-input::placeholder {
        color: var(--arena-ink-mute);
    }
    .search-input:focus {
        border-color: var(--arena-ink);
        box-shadow: inset 0 0 0 1px var(--arena-ink);
    }
    .search-clear {
        position: absolute;
        right: 6px;
        top: 50%;
        transform: translateY(-50%);
        background: transparent;
        border: none;
        cursor: pointer;
        padding: 6px;
        color: var(--arena-ink-soft);
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
    .search-clear:hover {
        color: var(--arena-ink);
    }
    .clear-icon {
        width: 14px;
        height: 14px;
    }

    .cat-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }
    .cat-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 7px 12px;
        background: var(--arena-paper);
        border: 1px solid var(--arena-line-soft);
        font-family: var(--arena-f-mono);
        font-size: 12px;
        color: var(--arena-ink-soft);
        cursor: pointer;
        transition: border-color 0.1s, color 0.1s, background 0.1s;
    }
    .cat-chip:hover {
        border-color: var(--arena-ink);
        color: var(--arena-ink);
    }
    .cat-chip.active {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border-color: var(--arena-ink);
    }
    .cat-label {
        letter-spacing: 0.3px;
    }
    .cat-count {
        font-size: 10px;
        letter-spacing: 1px;
        opacity: 0.7;
    }
    .cat-chip.active .cat-count {
        color: var(--arena-accent);
        opacity: 1;
    }

    /* Initials row */
    .initials-row {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
    }
    .initial-btn {
        min-width: 36px;
        padding: 6px 10px;
        background: var(--arena-paper);
        border: 1px solid var(--arena-line-soft);
        font-family: var(--arena-f-mono);
        font-size: 13px;
        font-weight: 600;
        color: var(--arena-ink-mute);
        cursor: pointer;
        transition: border-color 0.1s, color 0.1s, background 0.1s;
    }
    .initial-btn.has {
        color: var(--arena-ink);
    }
    .initial-btn:hover:not(:disabled) {
        border-color: var(--arena-ink);
        background: var(--arena-paper-alt);
    }
    .initial-btn:disabled {
        cursor: not-allowed;
        opacity: 0.4;
    }

    /* Groups */
    .groups {
        display: flex;
        flex-direction: column;
        gap: 32px;
    }
    .group {
        scroll-margin-top: 160px;
    }
    .group-head {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
    }
    .group-initial {
        font-family: var(--arena-f-display);
        font-size: 22px;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: var(--arena-ink);
    }
    .group-rule {
        flex: 1;
        height: 1px;
        background: var(--arena-line);
    }
    .group-count {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1px;
        color: var(--arena-ink-soft);
    }

    /* Term list */
    .term-list {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .term {
        background: var(--arena-paper);
        border: 1px solid var(--arena-line-soft);
        transition: border-color 0.1s;
    }
    .term:hover {
        border-color: var(--arena-line);
    }
    .term.open {
        border-color: var(--arena-ink);
    }

    .term-head {
        width: 100%;
        display: grid;
        grid-template-columns: 84px 1fr 28px;
        gap: 14px;
        padding: 14px 16px;
        background: transparent;
        border: none;
        cursor: pointer;
        text-align: left;
        align-items: start;
    }
    @media (max-width: 540px) {
        .term-head {
            grid-template-columns: 1fr 28px;
            grid-template-rows: auto auto;
        }
        .term-meta {
            grid-row: 1;
            grid-column: 1 / -1;
        }
        .term-body {
            grid-row: 2;
            grid-column: 1;
        }
        .term-toggle {
            grid-row: 2;
            grid-column: 2;
        }
    }
    .term-meta {
        display: flex;
        align-items: center;
        padding-top: 2px;
    }
    .term-cat {
        display: inline-flex;
        align-items: center;
        padding: 2px 8px;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1px;
        color: var(--arena-ink-soft);
        border: 1px solid var(--arena-line-soft);
        background: var(--arena-paper-alt);
        white-space: nowrap;
    }
    .term-cat[data-cat='training'] {
        color: var(--arena-zone-e);
        border-color: var(--arena-zone-e);
    }
    .term-cat[data-cat='race'] {
        color: var(--arena-zone-t);
        border-color: var(--arena-zone-t);
    }
    .term-cat[data-cat='body'] {
        color: var(--arena-zone-r);
        border-color: var(--arena-zone-r);
    }
    .term-cat[data-cat='gear'] {
        color: var(--arena-zone-m);
        border-color: var(--arena-zone-m);
    }
    .term-cat[data-cat='nutrition'] {
        color: var(--arena-zone-i);
        border-color: var(--arena-zone-i);
    }

    .term-body {
        display: flex;
        flex-direction: column;
        gap: 4px;
        min-width: 0;
    }
    .term-title {
        font-family: var(--arena-f-display);
        font-size: 16px;
        font-weight: 700;
        letter-spacing: -0.3px;
        line-height: 1.3;
        color: var(--arena-ink);
        margin: 0;
        word-break: keep-all;
    }
    .term-short {
        font-family: var(--arena-f-body);
        font-size: 13px;
        color: var(--arena-ink-soft);
        margin: 0;
        line-height: 1.5;
        word-break: keep-all;
    }
    .term-toggle {
        font-family: var(--arena-f-mono);
        font-size: 18px;
        font-weight: 600;
        color: var(--arena-ink-soft);
        text-align: center;
        line-height: 1;
        padding-top: 4px;
    }
    .term.open .term-toggle {
        color: var(--arena-accent-deep);
    }

    .term-detail {
        padding: 16px 16px 18px;
        border-top: 1px solid var(--arena-line-soft);
        background: var(--arena-paper-alt);
        display: flex;
        flex-direction: column;
        gap: 14px;
    }
    .detail-text {
        margin: 0;
        font-family: var(--arena-f-body);
        font-size: 14px;
        line-height: 1.75;
        color: var(--arena-ink);
        word-break: keep-all;
    }

    .related {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .related-kicker {
        font-size: 10px;
    }
    .related-list {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
    }
    .related-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        background: var(--arena-paper);
        border: 1px solid var(--arena-line-soft);
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink);
        cursor: pointer;
        transition: border-color 0.1s, color 0.1s;
    }
    .related-chip:hover {
        border-color: var(--arena-ink);
        color: var(--arena-accent-deep);
    }
    .related-arrow {
        color: var(--arena-ink-soft);
        font-size: 10px;
    }

    /* Empty */
    .empty {
        padding: 48px 24px;
        border: 1px dashed var(--arena-line);
        background: var(--arena-paper-alt);
        text-align: center;
        display: flex;
        flex-direction: column;
        gap: 10px;
        align-items: center;
    }
    .empty-msg {
        font-family: var(--arena-f-body);
        font-size: 14px;
        color: var(--arena-ink-soft);
        margin: 0;
    }
    .empty-reset {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 14px;
        background: var(--arena-ink);
        color: var(--arena-paper);
        border: 1px solid var(--arena-ink);
        font-family: var(--arena-f-display);
        font-weight: 600;
        font-size: 13px;
        cursor: pointer;
    }
    .empty-arrow {
        font-family: var(--arena-f-mono);
        color: var(--arena-accent);
    }

    .sidebar-wrap {
        margin-top: 32px;
    }

    @media (max-width: 719px) {
        .page-title {
            font-size: 32px;
            letter-spacing: -1px;
        }
        .filter-bar {
            top: 56px;
        }
    }
</style>
