<script lang="ts">
    import { page } from '$app/stores';
    import RaceFilterBar from '$lib/components/races/RaceFilterBar.svelte';
    import RaceResultList from '$lib/components/eh/RaceResultList.svelte';
    import { sportLabels } from '$lib/race';
    import { track } from '$lib/analytics';

    let { data } = $props();

    // Fire a GA4/PostHog `search` event whenever the user lands on a filtered
    // result set. Deduped by query string so re-renders don't double-count.
    let lastSearchKey = $state('');
    $effect(() => {
        const a = (data.applied ?? {}) as Record<string, unknown>;
        const norm = (v: unknown) => (Array.isArray(v) ? v.join(',') : (v ?? '')) as string;
        const term = String(norm(a.name));
        const sport = String(norm(a.sport));
        const region = String(norm(a.region));
        const statusF = String(norm(a.status));
        const distance = String(norm(a.distanceCategory));
        const hasFilters = !!(term || sport || region || statusF || distance);
        const key = $page.url.search;
        if (hasFilters && key !== lastSearchKey) {
            lastSearchKey = key;
            track('search', {
                search_term: term,
                sport,
                region,
                status: statusF,
                distance_category: distance,
            });
        }
    });

    let closingSoon = $derived(Array.isArray(data.applied.status) && data.applied.status.includes('closing_soon'));

    let sportTitle = $derived(() => {
        const sportArray = Array.isArray(data.applied.sport) ? data.applied.sport : data.applied.sport ? [data.applied.sport] : [];
        if (sportArray.length === 0) return '';
        if (sportArray.length === 1) return sportLabels[sportArray[0] as keyof typeof sportLabels] || '';
        return '';
    });

    let title = $derived(closingSoon ? '마감 임박 대회' : sportTitle() ? `${sportTitle()} 대회 목록` : '전체 대회');
    let metaDescription = $derived(`국내 ${sportTitle() || '엔듀어런스'} 대회 일정을 확인하세요.`);

    let ogImagePath = $derived.by(() => {
        const sportArray = Array.isArray(data.applied.sport)
            ? data.applied.sport
            : data.applied.sport ? [data.applied.sport] : [];
        if (sportArray.length === 1) {
            const slug = String(sportArray[0]).replace('_', '-');
            if (['running', 'swimming', 'cycling', 'triathlon', 'trail-running'].includes(slug)) {
                return `/images/og-${slug}.png`;
            }
        }
        return '/images/og-image.png';
    });
    let ogImage = $derived(`${data.appUrl}${ogImagePath}`);

    // ── Pagination (DS) ───────────────────────────────────────────────────────
    let meta = $derived(data.meta);
    function pageHref(n: number): string {
        const sp = new URLSearchParams($page.url.search);
        if (n <= 1) sp.delete('page');
        else sp.set('page', String(n));
        const qs = sp.toString();
        return qs ? `?${qs}` : '/races';
    }
    let pageItems = $derived.by((): (number | 'gap')[] => {
        const cur = meta.currentPage;
        const last = meta.lastPage;
        const out: (number | 'gap')[] = [];
        const push = (n: number) => out.push(n);
        push(1);
        const start = Math.max(2, cur - 2);
        const end = Math.min(last - 1, cur + 2);
        if (start > 2) out.push('gap');
        for (let i = start; i <= end; i++) push(i);
        if (end < last - 1) out.push('gap');
        if (last > 1) push(last);
        return out;
    });
</script>

<svelte:head>
    <title>{title} - 엔듀로허브</title>
    <meta name="description" content={metaDescription} />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="{title} - 엔듀로허브" />
    <meta property="og:description" content={metaDescription} />
    <meta property="og:image" content={ogImage} />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta name="twitter:image" content={ogImage} />
</svelte:head>

<main class="v-container races-page">
    <h1 class="sr-only">{title}</h1>

    <RaceFilterBar filters={data.filters} applied={data.applied} total={data.meta.total} {title} />

    {#if data.data.length === 0}
        <div class="empty">
            <span class="eh-micro">NO RESULTS</span>
            <p>검색 조건에 맞는 대회가 없습니다. 조건을 바꿔보세요.</p>
        </div>
    {:else}
        <RaceResultList races={data.data} />

        {#if meta.lastPage > 1}
            <nav class="pager" aria-label="페이지 이동">
                <a class="pager__edge" class:disabled={meta.currentPage <= 1} href={pageHref(meta.currentPage - 1)} aria-disabled={meta.currentPage <= 1} tabindex={meta.currentPage <= 1 ? -1 : undefined}>← 이전</a>
                <div class="pager__nums">
                    {#each pageItems as item, i (item === 'gap' ? `gap-${i}` : item)}
                        {#if item === 'gap'}
                            <span class="pager__gap">…</span>
                        {:else}
                            <a class="pager__num eh-data" class:on={item === meta.currentPage} href={pageHref(item)} aria-current={item === meta.currentPage ? 'page' : undefined}>{item}</a>
                        {/if}
                    {/each}
                </div>
                <a class="pager__edge" class:disabled={meta.currentPage >= meta.lastPage} href={pageHref(meta.currentPage + 1)} aria-disabled={meta.currentPage >= meta.lastPage} tabindex={meta.currentPage >= meta.lastPage ? -1 : undefined}>다음 →</a>
            </nav>
            <p class="pager__info eh-micro eh-data">{meta.from}–{meta.to} / {meta.total.toLocaleString()}</p>
        {/if}
    {/if}
</main>

<style>
    .races-page {
        padding-top: var(--sp-6);
        padding-bottom: var(--sp-16);
    }

    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }

    /* ── Empty ────────────────────────────────────────────────────────────── */
    .empty {
        border: var(--border-hair);
        background: var(--surface-card);
        padding: 56px 24px;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
    }
    .empty .eh-micro {
        color: var(--text-faint);
    }
    .empty p {
        margin: 0;
        font-size: 14px;
        color: var(--text-muted);
    }

    /* ── Pager ────────────────────────────────────────────────────────────── */
    .pager {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        margin-top: var(--sp-6);
        flex-wrap: wrap;
    }
    .pager__nums {
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .pager__edge,
    .pager__num {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 34px;
        height: 34px;
        padding: 0 10px;
        border: 1px solid var(--line);
        background: var(--paper-0);
        color: var(--text-body);
        font-family: var(--font-sans);
        font-size: 13px;
        font-weight: 600;
        text-decoration: none;
        transition: border-color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out);
    }
    .pager__num {
        padding: 0;
    }
    .pager__edge:hover,
    .pager__num:hover {
        border-color: var(--ink-900);
    }
    .pager__num.on {
        background: var(--ink-900);
        border-color: var(--ink-900);
        color: var(--paper-0);
    }
    .pager__edge.disabled {
        opacity: 0.35;
        pointer-events: none;
    }
    .pager__gap {
        padding: 0 4px;
        color: var(--text-faint);
    }
    .pager__info {
        text-align: center;
        color: var(--text-faint);
        margin: 10px 0 0;
    }
</style>
