<script lang="ts">
    import ToolsSidebar from '$lib/components/Tools/ToolsSidebar.svelte';
    import { glossaryTerms, categoryLabels, categoryColors, type GlossaryCategory } from '$lib/tools/glossary-data';

    let selectedCategory = $state<GlossaryCategory | 'all'>('all');
    let searchQuery = $state('');

    let filteredTerms = $derived.by(() => {
        let terms = glossaryTerms;
        if (selectedCategory !== 'all') {
            terms = terms.filter(t => t.category === selectedCategory);
        }
        if (searchQuery.trim()) {
            const q = searchQuery.trim().toLowerCase();
            terms = terms.filter(t =>
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

    const categoryActiveColors: Record<string, string> = {
        training: 'btn-primary',
        race: 'btn-secondary',
        body: 'btn-error',
        gear: 'btn-warning',
        nutrition: 'btn-success',
    };

    let expandedId = $state<string | null>(null);

    function toggle(id: string) {
        expandedId = expandedId === id ? null : id;
    }

    function getRelatedTerms(ids: string[] | undefined) {
        if (!ids) return [];
        return ids.map(id => glossaryTerms.find(t => t.id === id)).filter(Boolean);
    }

    const KOREAN_INITIALS = ['ㄱ','ㄲ','ㄴ','ㄷ','ㄸ','ㄹ','ㅁ','ㅂ','ㅃ','ㅅ','ㅆ','ㅇ','ㅈ','ㅉ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ'];
    const DISPLAY_INITIALS = ['ㄱ','ㄴ','ㄷ','ㄹ','ㅁ','ㅂ','ㅅ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ','A-Z','0-9'];
    const DOUBLE_TO_SINGLE: Record<string, string> = { 'ㄲ':'ㄱ', 'ㄸ':'ㄷ', 'ㅃ':'ㅂ', 'ㅆ':'ㅅ', 'ㅉ':'ㅈ' };

    function getInitial(str: string): string {
        const ch = str.charAt(0);
        const code = ch.charCodeAt(0);
        if (code >= 0xAC00 && code <= 0xD7A3) {
            const idx = Math.floor((code - 0xAC00) / (21 * 28));
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

    let availableInitials = $derived(new Set(groupedTerms.map(g => g.initial)));

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
        'mainEntity': glossaryTerms.slice(0, 20).map(t => ({
            '@type': 'Question',
            'name': `${t.term}이란?`,
            'acceptedAnswer': {
                '@type': 'Answer',
                'text': t.fullDesc,
            },
        })),
    });
</script>

<svelte:head>
    <title>러닝 용어 사전 - 엔듀로허브</title>
    <meta name="description" content="마라톤 러닝 용어 사전 - LSD, 인터벌, 템포런, VO2max, 네거티브 스플릿, 카보로딩 등 러닝 용어를 초보자도 이해하기 쉽게 설명합니다." />
    <meta property="og:title" content="러닝 용어 사전 - 엔듀로허브" />
    <meta property="og:description" content="LSD, 인터벌, 템포런, VO2max, 네거티브 스플릿 등 러닝 용어를 쉽게 알아보세요." />
    {@html `<script type="application/ld+json">${JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebPage',
        'name': '러닝 용어 사전 - 엔듀로허브',
        'description': '마라톤, 러닝 용어 사전 - LSD, 인터벌, 템포런, VO2max, 네거티브 스플릿 등 러닝 용어를 쉽게 알아보세요.',
    })}</script>`}
    {@html `<script type="application/ld+json">${JSON.stringify(faqSchema)}</script>`}
    {@html `<script type="application/ld+json">${JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            { '@type': 'ListItem', 'position': 1, 'name': '홈', 'item': 'https://www.endurohub.kr' },
            { '@type': 'ListItem', 'position': 2, 'name': '러닝 용어 사전' },
        ],
    })}</script>`}
</svelte:head>

<div class="container mx-auto px-4 py-8">
    <div class="breadcrumbs text-sm mb-6">
        <ul>
            <li><a href="/">홈</a></li>
            <li>러닝 용어 사전</li>
        </ul>
    </div>

    <div class="mb-8">
        <h1 class="text-2xl md:text-3xl font-bold">러닝 용어 사전</h1>
        <p class="text-base-content/60 mt-1">마라톤과 러닝에서 자주 사용되는 용어를 쉽게 알아보세요</p>
    </div>

    <div class="sticky top-16 z-10 bg-base-100/95 backdrop-blur-sm -mx-4 px-4 py-3 border-b border-base-200 mb-6">
        <div class="flex flex-col sm:flex-row gap-3">
            <div class="form-control flex-1">
                <div class="relative">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 absolute left-3 top-1/2 -translate-y-1/2 text-base-content/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                    <input type="text" bind:value={searchQuery} placeholder="용어 검색..." class="input input-bordered w-full pl-10 pr-10" aria-label="용어 검색" />
                    {#if searchQuery}
                        <button type="button" class="absolute right-2 top-1/2 -translate-y-1/2 btn btn-ghost btn-xs btn-circle cursor-pointer" onclick={clearSearch} aria-label="검색어 지우기">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                        </button>
                    {/if}
                </div>
            </div>
            <div class="flex flex-wrap gap-2 items-center">
                <button type="button" class="btn cursor-pointer transition-colors duration-200 {selectedCategory === 'all' ? 'btn-neutral' : 'btn-outline'}" onclick={() => selectedCategory = 'all'}>
                    전체 <span class="badge badge-xs ml-1">{glossaryTerms.length}</span>
                </button>
                {#each categories as cat (cat.key)}
                    <button type="button" class="btn cursor-pointer transition-colors duration-200 {selectedCategory === cat.key ? categoryActiveColors[cat.key] || 'btn-neutral' : 'btn-outline'}" onclick={() => selectedCategory = cat.key}>
                        {cat.label} <span class="badge badge-xs ml-1">{cat.count}</span>
                    </button>
                {/each}
            </div>
        </div>
    </div>

    {#if !searchQuery.trim()}
        <div class="flex flex-wrap gap-1.5 mb-4">
            {#each DISPLAY_INITIALS as ini}
                <button type="button" class="btn btn-sm min-w-[2.5rem] cursor-pointer transition-colors duration-200 {availableInitials.has(ini) ? 'btn-outline hover:btn-primary' : 'btn-ghost btn-disabled opacity-30'}" onclick={() => scrollToGroup(ini)} disabled={!availableInitials.has(ini)}>
                    {ini}
                </button>
            {/each}
        </div>
    {/if}

    <p class="text-sm text-base-content/50 mb-4">{filteredTerms.length}개 용어</p>

    {#each groupedTerms as group (group.initial)}
        <div id="group-{group.initial}" class="mb-6 scroll-mt-36">
            <div class="flex items-center gap-3 mb-3">
                <span class="text-lg font-bold text-primary">{group.initial}</span>
                <div class="flex-1 border-t border-base-300"></div>
                <span class="text-xs text-base-content/50">{group.terms.length}개</span>
            </div>

            <div class="space-y-2">
                {#each group.terms as term (term.id)}
                    <div id={term.id} class="card bg-base-100 border border-base-300 overflow-hidden transition-colors duration-200 hover:border-base-content/20">
                        <button type="button" class="w-full flex items-start justify-between p-4 cursor-pointer text-left" onclick={() => toggle(term.id)} aria-expanded={expandedId === term.id}>
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center gap-2 flex-wrap mb-1">
                                    <h2 class="font-bold text-base">{term.term}</h2>
                                    <span class="badge badge-sm {categoryColors[term.category]}">{categoryLabels[term.category]}</span>
                                </div>
                                <p class="text-sm text-base-content/50">{term.shortDesc}</p>
                            </div>
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-base-content/50 transition-transform duration-200 shrink-0 ml-3 mt-1 {expandedId === term.id ? 'rotate-180' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                            </svg>
                        </button>

                        {#if expandedId === term.id}
                            <div class="border-t border-base-300 px-4 py-4">
                                <p class="text-sm text-base-content/80 leading-relaxed">{term.fullDesc}</p>
                                {#if term.related && term.related.length > 0}
                                    <div class="mt-4">
                                        <p class="text-xs text-base-content/50 mb-2">관련 용어</p>
                                        <div class="flex flex-wrap gap-2">
                                            {#each getRelatedTerms(term.related) as related}
                                                {#if related}
                                                    <button type="button" class="badge badge-outline badge-sm cursor-pointer hover:badge-primary transition-colors duration-200" onclick={() => { expandedId = related.id; document.getElementById(related.id)?.scrollIntoView({ behavior: 'smooth', block: 'center' }); }}>{related.term}</button>
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
        </div>
    {/each}

    {#if filteredTerms.length === 0}
        <div class="text-center py-12">
            <p class="text-sm text-base-content/50 mb-3">검색 결과 없음</p>
            <button type="button" class="btn btn-ghost btn-sm cursor-pointer" onclick={resetAll}>필터 초기화</button>
        </div>
    {/if}

    <div class="mt-12 max-w-sm mx-auto">
        <ToolsSidebar current="glossary" />
    </div>
</div>
