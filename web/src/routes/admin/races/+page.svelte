<script lang="ts">
    import { goto } from '$app/navigation';

    let { data } = $props();

    let q = $state(data.q);

    function submitSearch(e: Event) {
        e.preventDefault();
        const params = new URLSearchParams();
        if (q) params.set('q', q);
        goto(`/admin/races${params.size ? '?' + params : ''}`);
    }

    function gotoPage(p: number) {
        const params = new URLSearchParams();
        if (data.q) params.set('q', data.q);
        if (p > 1) params.set('page', String(p));
        goto(`/admin/races${params.size ? '?' + params : ''}`);
    }

    let lastPage = $derived(Math.max(1, Math.ceil(data.total / data.perPage)));
</script>

<svelte:head>
    <title>대회 관리 · Admin</title>
</svelte:head>

<div class="page">
    <div class="page-head">
        <h1>대회 관리</h1>
        <span class="count">{data.total.toLocaleString()}개</span>
    </div>

    <form class="search" onsubmit={submitSearch}>
        <input
            type="search"
            placeholder="대회 이름 검색"
            bind:value={q}
        />
        <button type="submit">검색</button>
    </form>

    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th class="thumb-col"></th>
                    <th>제목</th>
                    <th class="date-col">대회일</th>
                    <th>지역</th>
                    <th class="sport-col">종목</th>
                    <th class="status-col">검수</th>
                </tr>
            </thead>
            <tbody>
                {#each data.races as r (r.id)}
                    <tr onclick={() => goto(`/admin/races/${r.slug}`)}>
                        <td class="thumb-col">
                            {#if r.imageSrcThumb}
                                <img src={r.imageSrcThumb} alt="" />
                            {:else}
                                <div class="thumb-empty"></div>
                            {/if}
                        </td>
                        <td>
                            <div class="title">{r.title}</div>
                            {#if r.location}<div class="loc">{r.location}</div>{/if}
                        </td>
                        <td class="date-col mono">{r.raceDate ?? '—'}</td>
                        <td>{r.region ?? '—'}</td>
                        <td class="sport-col"><span class="badge">{r.sportLabel}</span></td>
                        <td class="status-col">
                            {#if r.isVerified}
                                <span class="verified">✓</span>
                            {:else}
                                <span class="unverified">·</span>
                            {/if}
                        </td>
                    </tr>
                {/each}
                {#if data.races.length === 0}
                    <tr><td colspan="6" class="empty">결과 없음</td></tr>
                {/if}
            </tbody>
        </table>
    </div>

    {#if lastPage > 1}
        <div class="pagination">
            <button onclick={() => gotoPage(data.page - 1)} disabled={data.page <= 1}>‹ 이전</button>
            <span class="mono">{data.page} / {lastPage}</span>
            <button onclick={() => gotoPage(data.page + 1)} disabled={data.page >= lastPage}>다음 ›</button>
        </div>
    {/if}
</div>

<style>
    .page-head {
        display: flex;
        align-items: baseline;
        gap: 12px;
        margin-bottom: 16px;
    }
    h1 {
        font-family: var(--arena-f-display, system-ui);
        font-size: 24px;
        font-weight: 700;
        margin: 0;
    }
    .count {
        font-family: var(--arena-f-mono, ui-monospace);
        font-size: 12px;
        color: var(--arena-ink-mute, #888);
    }
    .search {
        display: flex;
        gap: 8px;
        margin-bottom: 16px;
    }
    .search input {
        flex: 1;
        max-width: 360px;
        padding: 8px 12px;
        border: 1px solid var(--arena-line, #ddd);
        background: #fff;
        font-size: 13px;
    }
    .search button {
        padding: 8px 16px;
        background: var(--arena-ink, #111);
        color: #fff;
        border: 0;
        cursor: pointer;
        font-size: 12px;
        font-family: var(--arena-f-mono, ui-monospace);
        letter-spacing: 0.5px;
    }
    .table-wrap {
        background: #fff;
        border: 1px solid var(--arena-line, #ddd);
        overflow-x: auto;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }
    th {
        text-align: left;
        padding: 10px 12px;
        background: var(--arena-paper-alt, #f4f4f0);
        border-bottom: 1px solid var(--arena-line, #ddd);
        font-family: var(--arena-f-mono, ui-monospace);
        font-size: 10px;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: var(--arena-ink-soft, #555);
        font-weight: 600;
    }
    td {
        padding: 10px 12px;
        border-bottom: 1px solid var(--arena-line-soft, #eee);
        vertical-align: middle;
    }
    tbody tr {
        cursor: pointer;
    }
    tbody tr:hover {
        background: var(--arena-paper-alt, #f4f4f0);
    }
    .thumb-col { width: 60px; }
    .date-col { width: 110px; }
    .sport-col { width: 100px; }
    .status-col { width: 60px; text-align: center; }
    .thumb-col img {
        width: 44px;
        height: 44px;
        object-fit: cover;
        border-radius: 4px;
    }
    .thumb-empty {
        width: 44px;
        height: 44px;
        background: var(--arena-paper-alt, #f4f4f0);
        border-radius: 4px;
    }
    .title { font-weight: 600; }
    .loc { font-size: 11px; color: var(--arena-ink-mute, #888); margin-top: 2px; }
    .mono { font-family: var(--arena-f-mono, ui-monospace); font-size: 11px; }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        background: var(--arena-paper-alt, #f4f4f0);
        border: 1px solid var(--arena-line, #ddd);
        font-size: 10px;
        font-family: var(--arena-f-mono, ui-monospace);
        letter-spacing: 0.5px;
    }
    .verified {
        display: inline-block;
        width: 22px; height: 22px;
        line-height: 20px;
        text-align: center;
        background: var(--arena-accent, #22c55e);
        color: #fff;
        font-size: 12px;
        font-weight: 700;
        border-radius: 50%;
    }
    .unverified { color: var(--arena-ink-mute, #ccc); }
    .empty { text-align: center; color: var(--arena-ink-mute, #888); padding: 40px; }
    .pagination {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 16px;
        margin-top: 16px;
    }
    .pagination button {
        padding: 6px 12px;
        background: #fff;
        border: 1px solid var(--arena-line, #ddd);
        cursor: pointer;
        font-size: 12px;
    }
    .pagination button:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }
</style>
