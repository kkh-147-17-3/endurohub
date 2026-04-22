<script lang="ts">
    import RaceCard from '$lib/components/RaceCard.svelte';
    import Pagination from '$lib/components/Pagination.svelte';
    import type { Race } from '$lib/types';

    let { data } = $props();

    let races = $state<Race[]>(data.data as Race[]);

    $effect(() => {
        races = data.data as Race[];
    });

    function handleFavoriteChange(slug: string, favorited: boolean) {
        if (!favorited) {
            races = races.filter((r) => r.slug !== slug);
        }
    }
</script>

<svelte:head>
    <title>관심 대회 - 엔듀로허브</title>
    <meta name="robots" content="noindex" />
</svelte:head>

<div class="container mx-auto px-4 py-10">
    <div class="max-w-5xl mx-auto">
        <div class="flex items-center justify-between mb-6">
            <div>
                <h1 class="text-2xl font-bold">관심 대회</h1>
                <p class="text-sm text-base-content/50 mt-1">
                    저장한 대회 {data.meta.total}개
                </p>
            </div>
            <a href="/mypage" class="btn btn-ghost btn-sm">← 마이페이지</a>
        </div>

        {#if races.length === 0}
            <div class="text-center py-16 border border-dashed border-base-300 rounded-xl">
                <div class="text-5xl mb-4">🤍</div>
                <h2 class="text-lg font-semibold mb-2">저장한 대회가 없어요</h2>
                <p class="text-sm text-base-content/50 mb-6">
                    관심 있는 대회의 하트 버튼을 눌러 저장해보세요.
                </p>
                <a href="/races" class="btn btn-primary btn-sm">대회 둘러보기</a>
            </div>
        {:else}
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {#each races as race (race.id)}
                    <RaceCard {race} onFavoriteChange={handleFavoriteChange} />
                {/each}
            </div>

            {#if data.meta.lastPage > 1}
                <div class="mt-8 flex justify-center">
                    <Pagination meta={data.meta} showInfo scrollToTop />
                </div>
            {/if}
        {/if}
    </div>
</div>
