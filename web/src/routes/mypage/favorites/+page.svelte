<script lang="ts">
    import RaceRow from '$lib/components/arena/RaceRow.svelte';
    import Pagination from '$lib/components/Pagination.svelte';

    let { data } = $props();

    let races = $derived(data.data);
    let total = $derived(data.meta.total);
</script>

<svelte:head>
    <title>관심 대회 - 엔듀로허브</title>
    <meta name="robots" content="noindex" />
</svelte:head>

<div class="page-wrap">
    <article class="page-shell">

        <header class="page-head">
            <div class="head-top">
                <div class="arena-kicker">계정</div>
                <a href="/mypage" class="back-link">← 마이페이지</a>
            </div>
            <h1 class="page-title">관심 대회</h1>
            <div class="head-meta">
                <span class="count-num">{total}</span>
                <span class="count-label">저장한 대회</span>
            </div>
        </header>

        {#if races.length === 0}
            <section class="empty">
                <h2 class="empty-title">저장한 대회가 없습니다</h2>
                <p class="empty-desc">
                    대회 카드의 하트 아이콘을 눌러 관심 있는 대회를 저장해보세요.<br />
                    저장한 대회는 이 페이지에서 한눈에 모아볼 수 있습니다.
                </p>
                <a href="/races" class="empty-cta">
                    대회 둘러보기 <span class="arrow">→</span>
                </a>
            </section>
        {:else}
            <div class="race-table">
                <div class="race-thead">
                    <span>접수마감</span>
                    <span>대회명</span>
                    <span>일정</span>
                    <span>종목</span>
                    <span>거리</span>
                    <span>지역</span>
                    <span>참가비</span>
                </div>
                {#each races as race (race.id)}
                    <RaceRow {race} />
                {/each}
            </div>

            {#if data.meta.lastPage > 1}
                <div class="pagination-wrap">
                    <Pagination meta={data.meta} showInfo scrollToTop />
                </div>
            {/if}
        {/if}

    </article>
</div>

<style>
    .page-wrap {
        background: var(--arena-paper);
        padding: 56px 24px 80px;
    }
    .page-shell {
        max-width: 1200px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        gap: 40px;
    }

    .page-head {
        display: flex;
        flex-direction: column;
        gap: 14px;
        padding-bottom: 24px;
        border-bottom: 1px solid var(--arena-line);
    }
    .head-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
    }
    .back-link {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.5px;
        color: var(--arena-ink-soft);
        text-decoration: none;
        padding: 4px 10px;
        border: 1px solid var(--arena-line-soft);
    }
    .back-link:hover {
        color: var(--arena-ink);
        background: var(--arena-paper-alt);
        border-color: var(--arena-line);
    }
    .page-title {
        font-family: var(--arena-f-display);
        font-size: 56px;
        font-weight: 700;
        letter-spacing: -2px;
        line-height: 1;
        margin: 0;
        color: var(--arena-ink);
    }
    .head-meta {
        display: flex;
        align-items: baseline;
        gap: 10px;
    }
    .count-num {
        font-family: var(--arena-f-mono);
        font-size: 22px;
        font-weight: 600;
        color: var(--arena-accent-deep);
        letter-spacing: -0.5px;
    }
    .count-label {
        font-family: var(--arena-f-body);
        font-size: 13px;
        color: var(--arena-ink-soft);
    }

    /* Race table — same structure as /races */
    .race-table {
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
    }
    .race-thead {
        display: grid;
        grid-template-columns: 56px 1fr 90px 60px 100px 110px 90px;
        gap: 16px;
        padding: 10px 20px;
        background: var(--arena-paper-alt);
        border-bottom: 1px solid var(--arena-line);
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.3px;
        color: var(--arena-ink-soft);
    }
    @media (max-width: 879px) {
        .race-thead {
            display: none;
        }
    }

    /* Empty state */
    .empty {
        padding: 60px 24px;
        background: var(--arena-paper);
        border: 1px dashed var(--arena-line);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 14px;
        text-align: center;
    }
    .empty-title {
        font-family: var(--arena-f-display);
        font-size: 22px;
        font-weight: 600;
        letter-spacing: -0.5px;
        color: var(--arena-ink);
        margin: 0;
    }
    .empty-desc {
        font-family: var(--arena-f-body);
        font-size: 13px;
        line-height: 1.7;
        color: var(--arena-ink-soft);
        margin: 0;
        max-width: 44ch;
        word-break: keep-all;
    }
    .empty-cta {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 12px 18px;
        background: var(--arena-ink);
        color: var(--arena-paper);
        font-family: var(--arena-f-display);
        font-weight: 600;
        font-size: 13px;
        letter-spacing: -0.2px;
        text-decoration: none;
        margin-top: 8px;
    }
    .empty-cta .arrow {
        font-family: var(--arena-f-mono);
        color: var(--arena-accent);
    }

    .pagination-wrap {
        display: flex;
        justify-content: center;
        padding-top: 16px;
        border-top: 1px solid var(--arena-line-soft);
    }

    @media (max-width: 640px) {
        .page-title {
            font-size: 40px;
            letter-spacing: -1.5px;
        }
        .count-num {
            font-size: 18px;
        }
    }
</style>
