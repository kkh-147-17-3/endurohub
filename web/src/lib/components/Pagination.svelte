<script lang="ts">
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import type { PaginationMeta } from '$lib/types';

    interface Props {
        meta: PaginationMeta;
        showInfo?: boolean;
        scrollToTop?: boolean;
    }

    let { meta, showInfo = false, scrollToTop = false }: Props = $props();

    let visiblePages = $derived(() => {
        const current = meta.currentPage;
        const last = meta.lastPage;
        const delta = 2;
        const pages: (number | 'ellipsis')[] = [];

        pages.push(1);

        const start = Math.max(2, current - delta);
        const end = Math.min(last - 1, current + delta);

        if (start > 2) {
            pages.push('ellipsis');
        }

        for (let i = start; i <= end; i++) {
            pages.push(i);
        }

        if (end < last - 1) {
            pages.push('ellipsis');
        }

        if (last > 1) {
            pages.push(last);
        }

        return pages;
    });

    function goToPage(pageNum: number) {
        const url = new URL($page.url);
        url.searchParams.set('page', pageNum.toString());

        goto(url.toString(), {
            noScroll: !scrollToTop,
            keepFocus: true,
        });
    }
</script>

{#if meta.lastPage > 1}
    <nav aria-label="페이지 네비게이션" class="arena-pagination">
        {#if showInfo}
            <div class="pag-info">
                {#if meta.from && meta.to}
                    총 <strong>{meta.total.toLocaleString()}</strong>개 중
                    <strong>{meta.from.toLocaleString()}</strong>–<strong>{meta.to.toLocaleString()}</strong>
                {:else}
                    총 <strong>{meta.total.toLocaleString()}</strong>개
                {/if}
            </div>
        {/if}

        <div class="pag-controls">
            <button
                type="button"
                onclick={() => goToPage(meta.currentPage - 1)}
                disabled={meta.currentPage <= 1}
                class="pag-btn pag-btn-nav"
                aria-label="이전 페이지"
            >
                <svg xmlns="http://www.w3.org/2000/svg" class="pag-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
                <span>이전</span>
            </button>

            <div class="pag-pages">
                {#each visiblePages() as p}
                    {#if p === 'ellipsis'}
                        <span class="pag-ellipsis" aria-hidden="true">···</span>
                    {:else}
                        <button
                            type="button"
                            onclick={() => goToPage(p)}
                            class="pag-btn pag-btn-page"
                            class:is-active={p === meta.currentPage}
                            aria-label="{p} 페이지"
                            aria-current={p === meta.currentPage ? 'page' : undefined}
                        >
                            {p}
                        </button>
                    {/if}
                {/each}
            </div>

            <div class="pag-mobile">
                <strong>{meta.currentPage}</strong>
                <span class="pag-mobile-sep">/</span>
                <span>{meta.lastPage}</span>
            </div>

            <button
                type="button"
                onclick={() => goToPage(meta.currentPage + 1)}
                disabled={meta.currentPage >= meta.lastPage}
                class="pag-btn pag-btn-nav"
                aria-label="다음 페이지"
            >
                <span>다음</span>
                <svg xmlns="http://www.w3.org/2000/svg" class="pag-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
            </button>
        </div>
    </nav>
{/if}

<style>
    .arena-pagination {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 14px;
        font-family: var(--arena-f-body);
    }
    .pag-info {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.5px;
        color: var(--arena-ink-soft);
    }
    .pag-info strong {
        color: var(--arena-ink);
        font-weight: 500;
    }
    .pag-controls {
        display: flex;
        align-items: stretch;
        gap: 4px;
    }
    .pag-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        min-width: 36px;
        height: 36px;
        padding: 0 10px;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
        color: var(--arena-ink);
        font-family: var(--arena-f-mono);
        font-size: 12px;
        letter-spacing: 0.3px;
        cursor: pointer;
        transition: background 0.1s, border-color 0.1s, color 0.1s;
    }
    .pag-btn:hover:not(:disabled) {
        border-color: var(--arena-ink);
    }
    .pag-btn:disabled {
        opacity: 0.35;
        cursor: not-allowed;
    }
    .pag-btn.is-active {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border-color: var(--arena-ink);
    }
    .pag-btn-page {
        min-width: 36px;
        padding: 0;
    }
    .pag-icon {
        width: 12px;
        height: 12px;
    }
    .pag-btn-nav span {
        display: none;
    }
    .pag-pages {
        display: none;
        gap: 4px;
    }
    .pag-mobile {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 0 14px;
        font-family: var(--arena-f-mono);
        font-size: 12px;
        letter-spacing: 0.5px;
        color: var(--arena-ink-soft);
    }
    .pag-mobile strong {
        color: var(--arena-ink);
        font-weight: 500;
    }
    .pag-mobile-sep {
        color: var(--arena-ink-mute);
    }
    .pag-ellipsis {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 24px;
        height: 36px;
        font-family: var(--arena-f-mono);
        font-size: 12px;
        color: var(--arena-ink-mute);
        letter-spacing: 1px;
    }

    @media (min-width: 640px) {
        .pag-btn-nav span {
            display: inline;
        }
        .pag-pages {
            display: flex;
        }
        .pag-mobile {
            display: none;
        }
    }
</style>
