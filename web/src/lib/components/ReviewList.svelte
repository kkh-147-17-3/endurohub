<script lang="ts">
    import type { Review, ReviewStats } from '$lib/types';
    import StarRating from './StarRating.svelte';

    interface Props {
        reviews: Review[];
        stats: ReviewStats;
    }

    let { reviews, stats }: Props = $props();
</script>

<div class="card bg-base-100 shadow-xl">
    <div class="card-body">
        <div class="flex items-center justify-between mb-4">
            <h3 class="card-title text-lg">참가자 리뷰</h3>
            <div class="flex items-center gap-2">
                <StarRating rating={Math.round(stats.average)} readonly size="sm" />
                <span class="text-sm text-base-content/70">
                    {stats.average > 0 ? stats.average.toFixed(1) : '-'} ({stats.count}개)
                </span>
            </div>
        </div>

        {#if reviews.length === 0}
            <div class="text-center py-8 text-base-content/50">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <p>아직 리뷰가 없습니다.</p>
                <p class="text-sm">첫 번째 리뷰를 남겨보세요!</p>
            </div>
        {:else}
            <div class="space-y-4">
                {#each reviews as review (review.id)}
                    <div class="border-b border-base-200 pb-4 last:border-b-0 last:pb-0">
                        <div class="flex items-start justify-between mb-2">
                            <div class="flex items-center gap-2">
                                <span class="font-medium">{review.nickname}</span>
                                <StarRating rating={review.rating} readonly size="sm" />
                            </div>
                            <span class="text-xs text-base-content/50">{review.createdAtFormatted}</span>
                        </div>
                        <p class="text-base-content/80">{review.comment}</p>
                    </div>
                {/each}
            </div>
        {/if}
    </div>
</div>
