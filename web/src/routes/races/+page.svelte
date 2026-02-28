<script lang="ts">
    import RaceCard from '$lib/components/RaceCard.svelte';
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
</script>

<svelte:head>
    <title>{title} - 엔듀로허브</title>
    <meta name="description" content={metaDescription} />
    <meta property="og:title" content="{title} - 엔듀로허브" />
    <meta property="og:description" content={metaDescription} />
</svelte:head>

<div class="container mx-auto px-4 py-8">
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
        <div class="alert">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-info shrink-0 w-6 h-6">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span>검색 조건에 맞는 대회가 없습니다.</span>
        </div>
    {:else}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {#each data.data as race (race.id)}
                <RaceCard {race} />
            {/each}
        </div>

        <div class="mt-8 flex justify-center">
            <Pagination meta={data.meta} scrollToTop showInfo />
        </div>
    {/if}
</div>
