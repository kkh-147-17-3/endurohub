<script lang="ts">
    import RaceRow from '$lib/components/arena/RaceRow.svelte';
    import FilterBar from '$lib/components/FilterBar.svelte';
    import Pagination from '$lib/components/Pagination.svelte';
    import { sportLabels } from '$lib/race';

    let { data } = $props();

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

<div class="races-wrap">
    <FilterBar
        sports={data.filters.sports}
        regions={data.filters.regions}
        distanceCategories={data.filters.distanceCategories}
        selectedSport={data.applied.sport}
        selectedRegion={data.applied.region}
        selectedStatus={data.applied.status}
        selectedName={data.applied.name}
        selectedDistanceCategory={data.applied.distanceCategory}
        selectedMonthFrom={data.applied.monthFrom}
        selectedMonthTo={data.applied.monthTo}
        title={closingSoon ? '마감 임박 대회' : sportTitle() ? `${sportTitle()} 대회` : '전체 대회'}
        totalCount={data.meta.total}
    />

    {#if data.data.length === 0}
        <div class="empty-card">
            <span class="empty-kicker">NO RESULTS</span>
            <p>검색 조건에 맞는 대회가 없습니다.</p>
        </div>
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
            {#each data.data as race (race.id)}
                <RaceRow {race} />
            {/each}
        </div>

        <div class="mt-8 flex justify-center">
            <Pagination meta={data.meta} scrollToTop showInfo />
        </div>
    {/if}
</div>

<style>
    .races-wrap {
        max-width: 1400px;
        margin: 0 auto;
        padding: 32px 24px;
    }
    @media (min-width: 1024px) {
        .races-wrap {
            padding: 40px 32px;
        }
    }

    .empty-card {
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
    .empty-kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        color: var(--arena-ink-mute);
    }
    .empty-card p {
        margin: 0;
        font-size: 14px;
    }

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
    /* Mobile: hide thead — RaceRow reflows into a 2-line self-describing layout */
    @media (max-width: 879px) {
        .race-thead {
            display: none;
        }
    }
</style>
