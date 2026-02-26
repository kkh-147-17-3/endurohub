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
    <nav aria-label="페이지 네비게이션" class="flex flex-col items-center gap-4">
        {#if showInfo}
            <div class="text-sm text-base-content/60">
                {#if meta.from && meta.to}
                    총 <span class="font-medium">{meta.total.toLocaleString()}</span>개 중
                    <span class="font-medium">{meta.from.toLocaleString()}</span> -
                    <span class="font-medium">{meta.to.toLocaleString()}</span>
                {:else}
                    총 <span class="font-medium">{meta.total.toLocaleString()}</span>개
                {/if}
            </div>
        {/if}

        <div class="flex items-center gap-1">
            <button
                onclick={() => goToPage(meta.currentPage - 1)}
                disabled={meta.currentPage <= 1}
                class="btn btn-sm btn-ghost cursor-pointer"
                class:btn-disabled={meta.currentPage <= 1}
                aria-label="이전 페이지"
            >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
                <span class="hidden sm:inline">이전</span>
            </button>

            <div class="hidden sm:flex join">
                {#each visiblePages() as p}
                    {#if p === 'ellipsis'}
                        <span class="join-item btn btn-sm btn-ghost btn-disabled" aria-hidden="true">
                            ...
                        </span>
                    {:else}
                        <button
                            onclick={() => goToPage(p)}
                            class="join-item btn btn-sm cursor-pointer"
                            class:btn-active={p === meta.currentPage}
                            aria-label="{p} 페이지"
                            aria-current={p === meta.currentPage ? 'page' : undefined}
                        >
                            {p}
                        </button>
                    {/if}
                {/each}
            </div>

            <div class="flex sm:hidden items-center gap-2">
                <span class="text-sm">
                    <span class="font-medium">{meta.currentPage}</span>
                    <span class="text-base-content/50"> / </span>
                    <span class="text-base-content/70">{meta.lastPage}</span>
                </span>
            </div>

            <button
                onclick={() => goToPage(meta.currentPage + 1)}
                disabled={meta.currentPage >= meta.lastPage}
                class="btn btn-sm btn-ghost cursor-pointer"
                class:btn-disabled={meta.currentPage >= meta.lastPage}
                aria-label="다음 페이지"
            >
                <span class="hidden sm:inline">다음</span>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
            </button>
        </div>
    </nav>
{/if}
