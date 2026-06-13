<script lang="ts">
    import { SearchBar, FilterChip } from '$lib/components/eh';
    import {
        glossaryCats,
        glossaryGroups,
        glossaryTerms,
        type GlossaryCategory
    } from '$lib/tools/glossary-data';

    let { data } = $props();

    const TOTAL = glossaryTerms.length;
    const ALPHA = glossaryGroups.map((g) => g.key);

    const OTHER_TOOLS = [
        { no: '01', t: '페이스 계산기', d: '거리·목표 시간으로 구간 페이스 산출', href: '/tools/pace-calculator' },
        { no: '02', t: '훈련 플랜', d: '목표 대회까지 주차별 단계 구성', href: '/tools/training-plan' },
        { no: '03', t: 'VO₂max 계산기', d: '최근 기록으로 유산소 능력 추정', href: '/tools/vo2max' },
        { no: '04', t: '기록 예측기', d: 'Riegel 공식 기반 거리별 예상 기록', href: '/tools/race-predictor' }
    ];

    let q = $state('');
    let activeCat = $state<GlossaryCategory | 'all'>('all');
    let open = $state<Record<string, boolean>>({});
    let jump = $state<string | null>(null);

    let groupRefs: Record<string, HTMLElement | null> = {};

    function catKo(id: GlossaryCategory | 'all'): string {
        return glossaryCats.find((c) => c.id === id)?.ko ?? id;
    }

    function matches(t: { ko: string; en: string; short: string; def: string }, ql: string): boolean {
        return !ql || (t.ko + ' ' + t.en + ' ' + t.short + ' ' + t.def).toLowerCase().includes(ql);
    }

    // Category counts respect the search, ignore the active category.
    let counts = $derived.by(() => {
        const ql = q.trim().toLowerCase();
        const c: Record<string, number> = { all: 0 };
        for (const cc of glossaryCats) if (cc.id !== 'all') c[cc.id] = 0;
        for (const t of glossaryTerms) {
            if (matches(t, ql)) {
                c.all++;
                c[t.cat]++;
            }
        }
        return c;
    });

    let groups = $derived.by(() => {
        const ql = q.trim().toLowerCase();
        return glossaryGroups
            .map((g) => ({
                key: g.key,
                terms: g.terms.filter((t) => {
                    if (activeCat !== 'all' && t.cat !== activeCat) return false;
                    return matches(t, ql);
                })
            }))
            .filter((g) => g.terms.length > 0);
    });

    let shown = $derived(groups.reduce((n, g) => n + g.terms.length, 0));
    let availKeys = $derived(new Set(groups.map((g) => g.key)));
    let allOpen = $derived(shown > 0 && groups.every((g) => g.terms.every((t) => open[t.ko])));

    function toggle(ko: string) {
        open = { ...open, [ko]: !open[ko] };
    }

    function toggleAll() {
        if (allOpen) {
            open = {};
        } else {
            const o: Record<string, boolean> = {};
            for (const g of groups) for (const t of g.terms) o[t.ko] = true;
            open = o;
        }
    }

    function jumpTo(key: string) {
        if (!availKeys.has(key)) return;
        jump = key;
        const el = groupRefs[key];
        if (el) {
            const y = el.getBoundingClientRect().top + window.scrollY - 116;
            window.scrollTo({ top: y, behavior: 'smooth' });
        }
    }

    // SEO: FAQ structured data from the first 20 terms.
    let faqSchema = $derived({
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        mainEntity: glossaryTerms.slice(0, 20).map((t) => ({
            '@type': 'Question',
            name: `${t.ko}이란?`,
            acceptedAnswer: { '@type': 'Answer', text: t.def }
        }))
    });
</script>

<svelte:head>
    <title>러닝 용어 사전 — 엔듀로허브</title>
    <meta
        name="description"
        content="마라톤 러닝 용어 사전 - LSD, 인터벌, 템포런, VO2max, 네거티브 스플릿, 카보로딩 등 러닝 용어를 초보자도 이해하기 쉽게 설명합니다."
    />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="러닝 용어 사전 — 엔듀로허브" />
    <meta
        property="og:description"
        content="LSD, 인터벌, 템포런, VO2max, 네거티브 스플릿 등 러닝 용어를 쉽게 알아보세요."
    />
    <meta property="og:image" content="{data.appUrl}/images/og-image.png" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta name="twitter:image" content="{data.appUrl}/images/og-image.png" />
    {@html `<script type="application/ld+json">${JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebPage',
        name: '러닝 용어 사전 — 엔듀로허브',
        description:
            '마라톤, 러닝 용어 사전 - LSD, 인터벌, 템포런, VO2max, 네거티브 스플릿 등 러닝 용어를 쉽게 알아보세요.'
    })}</script>`}
    {@html `<script type="application/ld+json">${JSON.stringify(faqSchema)}</script>`}
    {@html `<script type="application/ld+json">${JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        itemListElement: [
            { '@type': 'ListItem', position: 1, name: '홈', item: 'https://www.endurohub.kr' },
            { '@type': 'ListItem', position: 2, name: '도구', item: 'https://www.endurohub.kr/tools' },
            { '@type': 'ListItem', position: 3, name: '러닝 용어 사전' }
        ]
    })}</script>`}
</svelte:head>

<main class="v-container glossary">
    <nav class="crumb" aria-label="breadcrumb">
        <a href="/">홈</a>
        <span>›</span>
        <a href="/tools">도구</a>
        <span>›</span>
        <span class="here">러닝 용어 사전</span>
    </nav>

    <header class="hd">
        <div class="eh-micro"><span class="acc">GLOSSARY</span> · 용어 {TOTAL}</div>
        <h1>러닝 용어 사전</h1>
        <p class="lede">
            마라톤과 러닝에서 자주 쓰이는 용어를 카테고리·초성별로 정리했습니다. 항목을 누르면 자세한
            설명이 열립니다.
        </p>
        <div class="searchwrap">
            <SearchBar
                bind:value={q}
                placeholder="용어 검색 — LSD, 테이퍼, 젖산역치…"
                shortcutHint="/"
            />
        </div>
    </header>

    <div class="catrow">
        {#each glossaryCats as c (c.id)}
            <FilterChip
                selected={activeCat === c.id}
                count={counts[c.id]}
                onclick={() => (activeCat = c.id)}
            >
                {c.ko}
            </FilterChip>
        {/each}
    </div>

    <nav class="alpha" aria-label="초성 색인">
        {#each ALPHA as k (k)}
            <button
                class="ai eh-data {jump === k ? 'on' : ''}"
                disabled={!availKeys.has(k)}
                onclick={() => jumpTo(k)}
            >
                {k}
            </button>
        {/each}
    </nav>

    <div class="resmeta">
        <span class="n"
            >결과 <b class="eh-data">{shown}</b>{#if activeCat !== 'all'}<span>
                    · {catKo(activeCat)}</span
                >{/if}{#if q}<span> · “{q}”</span>{/if}</span
        >
        {#if shown > 0}
            <button class="expand" onclick={toggleAll}>{allOpen ? '모두 접기' : '모두 펼치기'}</button>
        {/if}
    </div>

    {#if shown === 0}
        <div class="empty">일치하는 용어가 없습니다. 다른 검색어나 카테고리를 시도하세요.</div>
    {:else}
        <div class="grouplist">
            {#each groups as g (g.key)}
                <section class="grp" bind:this={groupRefs[g.key]}>
                    <div class="grp-hd">
                        <span class="gl eh-data">{g.key}</span>
                        <span class="gc">{g.terms.length}개</span>
                    </div>
                    <div>
                        {#each g.terms as term (term.ko)}
                            {@const isOpen = !!open[term.ko]}
                            <div class="term {isOpen ? 'open' : ''}">
                                <button class="term-row" onclick={() => toggle(term.ko)} aria-expanded={isOpen}>
                                    <span class="cat">{catKo(term.cat)}</span>
                                    <span class="name">
                                        <span class="ko">{term.ko}</span>
                                        {#if term.en}<span class="en">{term.en}</span>{/if}
                                    </span>
                                    <span class="short">{term.short}</span>
                                    <span class="tog" aria-hidden="true">
                                        <svg
                                            width="14"
                                            height="14"
                                            viewBox="0 0 24 24"
                                            fill="none"
                                            stroke="currentColor"
                                            stroke-width="2"
                                            stroke-linecap="round"
                                        >
                                            <path d="M12 5v14M5 12h14" />
                                        </svg>
                                    </span>
                                </button>
                                <div class="def">
                                    <div class="def-clip">
                                        <div class="def-inner">
                                            <p>{term.def}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        {/each}
                    </div>
                </section>
            {/each}
        </div>
    {/if}

    <section class="other">
        <div class="sec-head">
            <h2>다른 도구</h2>
            <span class="eh-micro">TOOLS · 4</span>
        </div>
        <div class="other-grid">
            {#each OTHER_TOOLS as o (o.no)}
                <a href={o.href}>
                    <span class="num eh-data">{o.no}</span>
                    <span class="ot">{o.t} <span class="arr">→</span></span>
                    <span class="od">{o.d}</span>
                </a>
            {/each}
        </div>
    </section>
</main>

<style>
    .glossary {
        padding-bottom: var(--sp-20);
    }

    /* ---- breadcrumb ---- */
    .crumb {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 14px 0 0;
        font-size: 12.5px;
        color: var(--text-faint);
        flex-wrap: wrap;
    }
    .crumb a {
        color: var(--text-muted);
        text-decoration: none;
    }
    .crumb a:hover {
        color: var(--text-strong);
        text-decoration: underline;
        text-underline-offset: 3px;
    }
    .crumb .here {
        color: var(--text-strong);
        font-weight: 600;
    }

    /* ---- header ---- */
    .hd {
        padding: 26px 0 0;
    }
    .hd .acc {
        color: var(--accent);
    }
    .hd h1 {
        font-size: var(--text-h1);
        font-weight: var(--w-display);
        letter-spacing: var(--track-display);
        line-height: var(--leading-heading);
        margin-top: 8px;
        color: var(--text-strong);
    }
    .hd .lede {
        color: var(--text-muted);
        font-size: 15px;
        margin-top: 12px;
        max-width: 560px;
        line-height: var(--leading-body);
    }
    .hd .searchwrap {
        margin-top: 22px;
        max-width: 560px;
    }

    /* ---- category filter row ---- */
    .catrow {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 24px;
        padding-bottom: 18px;
        border-bottom: var(--border-rule);
    }

    /* ---- 초성 index bar (sticky under the 64px nav) ---- */
    .alpha {
        position: sticky;
        top: 64px;
        z-index: 40;
        display: flex;
        align-items: center;
        gap: 2px;
        flex-wrap: wrap;
        padding: 12px 0;
        margin: 0 0 8px;
        background: var(--surface-glass);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-bottom: var(--border-hair);
    }
    .alpha .ai {
        min-width: 30px;
        height: 30px;
        padding: 0 6px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: var(--text-strong);
        background: none;
        border: 1px solid transparent;
        border-radius: var(--r-2);
        font-variant-numeric: tabular-nums;
        transition:
            background var(--dur-fast) var(--ease-out),
            color var(--dur-fast) var(--ease-out),
            border-color var(--dur-fast) var(--ease-out);
    }
    .alpha .ai:hover:not(:disabled) {
        background: var(--paper-100);
    }
    .alpha .ai:disabled {
        color: var(--text-faint);
        opacity: 0.4;
        cursor: default;
    }
    .alpha .ai.on {
        background: var(--ink-900);
        color: var(--paper-0);
    }

    /* ---- result meta ---- */
    .resmeta {
        display: flex;
        align-items: baseline;
        gap: 12px;
        padding: 4px 0 0;
    }
    .resmeta .n {
        font-size: 13px;
        color: var(--text-faint);
    }
    .resmeta .n b {
        color: var(--text-strong);
        font-weight: 700;
    }
    .resmeta .expand {
        margin-left: auto;
        background: none;
        border: 0;
        padding: 0;
        font-size: 12.5px;
        font-weight: 600;
        color: var(--text-accent);
        border-bottom: 1px solid transparent;
    }
    .resmeta .expand:hover {
        border-bottom-color: var(--text-accent);
    }

    /* ---- group ---- */
    .grouplist {
        margin-top: 4px;
    }
    .grp {
        scroll-margin-top: 120px;
    }
    .grp + .grp {
        margin-top: 8px;
    }
    .grp-hd {
        display: flex;
        align-items: baseline;
        gap: 16px;
        border-top: var(--border-rule);
        padding: 18px 0 12px;
        margin-top: 18px;
    }
    .grp-hd .gl {
        font-size: 30px;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1;
        min-width: 56px;
        color: var(--text-strong);
    }
    .grp-hd .gc {
        font-size: var(--text-micro);
        font-weight: var(--w-strong);
        letter-spacing: var(--track-micro);
        text-transform: uppercase;
        color: var(--text-faint);
    }

    /* ---- term row ---- */
    .term {
        border-bottom: var(--border-hair);
    }
    .term-row {
        display: grid;
        grid-template-columns: 88px minmax(220px, 1.1fr) minmax(0, 1.3fr) 32px;
        gap: 18px;
        align-items: baseline;
        padding: 16px 6px;
        width: 100%;
        text-align: left;
        background: none;
        border: 0;
        cursor: pointer;
        transition: background var(--dur-fast) var(--ease-out);
    }
    .term-row:hover {
        background: var(--paper-50);
    }
    .term .cat {
        justify-self: start;
        align-self: center;
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--text-muted);
        padding: 3px 8px;
        border: 1px solid var(--line);
        border-radius: var(--r-2);
        white-space: nowrap;
    }
    .term .name {
        min-width: 0;
    }
    .term .name .ko {
        font-size: 16px;
        font-weight: 700;
        letter-spacing: var(--track-heading);
        color: var(--text-strong);
    }
    .term .name .en {
        display: block;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--text-faint);
        margin-top: 3px;
    }
    .term .short {
        font-size: 13.5px;
        color: var(--text-muted);
        line-height: 1.5;
        align-self: center;
    }
    .term .tog {
        justify-self: end;
        align-self: center;
        width: 26px;
        height: 26px;
        flex: none;
        display: grid;
        place-items: center;
        border: 1px solid var(--line);
        border-radius: var(--r-2);
        color: var(--text-muted);
        transition:
            transform var(--dur-base) var(--ease-out),
            border-color var(--dur-fast) var(--ease-out),
            background var(--dur-fast) var(--ease-out);
    }
    .term-row:hover .tog {
        border-color: var(--ink-900);
        color: var(--text-strong);
    }
    .term.open .tog {
        transform: rotate(45deg);
        background: var(--ink-900);
        color: var(--paper-0);
        border-color: var(--ink-900);
    }

    /* ---- expanded definition (animated height via grid-rows) ---- */
    .def {
        display: grid;
        grid-template-rows: 0fr;
        transition: grid-template-rows var(--dur-base) var(--ease-out);
    }
    .term.open .def {
        grid-template-rows: 1fr;
    }
    .def-clip {
        overflow: hidden;
        min-height: 0;
    }
    .def-inner {
        padding: 0 0 18px;
        margin-left: 106px;
        border-left: 2px solid var(--ink-900);
        padding-left: 18px;
        max-width: 640px;
    }
    .def-inner p {
        font-size: 14.5px;
        line-height: 1.72;
        color: var(--text-body);
        margin: 0;
    }

    /* ---- empty ---- */
    .empty {
        padding: 60px 0;
        text-align: center;
        color: var(--text-faint);
        font-size: 14px;
    }

    /* ---- other tools ---- */
    .other {
        margin-top: var(--sp-16);
    }
    .sec-head {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 16px;
        border-bottom: var(--border-rule);
        padding-bottom: 12px;
    }
    .sec-head h2 {
        font-size: var(--text-h3);
        font-weight: var(--w-heading);
        letter-spacing: var(--track-heading);
        color: var(--text-strong);
        margin: 0;
    }
    .other-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1px;
        background: var(--line);
        border: 1px solid var(--line);
        border-top: none;
        margin-top: 16px;
    }
    .other-grid a {
        background: var(--paper-0);
        padding: 20px;
        min-height: 116px;
        display: flex;
        flex-direction: column;
        text-decoration: none;
        color: inherit;
        transition: background var(--dur-fast) var(--ease-out);
    }
    .other-grid a:hover {
        background: var(--paper-50);
    }
    .other-grid .num {
        font-size: var(--text-micro);
        font-weight: 700;
        letter-spacing: var(--track-micro);
        color: var(--text-faint);
    }
    .other-grid .ot {
        font-size: 16px;
        font-weight: 700;
        letter-spacing: var(--track-heading);
        margin-top: auto;
        color: var(--text-strong);
    }
    .other-grid .od {
        font-size: 12px;
        color: var(--text-muted);
        margin-top: 5px;
        line-height: 1.45;
    }
    .other-grid a .arr {
        color: var(--text-accent);
        transition: transform var(--dur-base) var(--ease-out);
        display: inline-block;
    }
    .other-grid a:hover .arr {
        transform: translateX(3px);
    }

    @media (max-width: 768px) {
        .alpha {
            top: 52px;
        }
        .term-row {
            grid-template-columns: 1fr 28px;
            gap: 10px 12px;
            padding: 14px 4px;
        }
        .term .cat {
            grid-row: 1;
            grid-column: 1;
        }
        .term .name {
            grid-row: 2;
            grid-column: 1;
        }
        .term .short {
            grid-row: 3;
            grid-column: 1;
            font-size: 13px;
        }
        .term .tog {
            grid-row: 1;
            grid-column: 2;
        }
        .def-inner {
            margin-left: 0;
        }
        .other-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        .grp-hd .gl {
            font-size: 26px;
            min-width: 44px;
        }
    }
</style>
