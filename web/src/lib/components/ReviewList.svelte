<script lang="ts">
    import type { Review, ReviewStats, Post } from '$lib/types';
    import Avatar from './Avatar.svelte';
    import StarRating from './StarRating.svelte';

    interface Props {
        reviews: Review[];
        stats: ReviewStats;
        relatedPosts?: Post[];
        canReview?: boolean;
        onwriteReview?: () => void;
    }

    let { reviews, stats, relatedPosts = [], canReview = true, onwriteReview }: Props = $props();

    const difficultyLabels: Record<string, { label: string; badge: string }> = {
        easy: { label: '쉬움', badge: 'badge-success' },
        normal: { label: '보통', badge: 'badge-warning' },
        hard: { label: '어려움', badge: 'badge-error' },
    };
</script>

<div class="card bg-base-100 shadow-xl">
    <div class="card-body">
        <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
                <h3 class="card-title text-lg">참가자 리뷰</h3>
                {#if stats.count > 0}
                    <div class="flex items-center gap-1.5">
                        <StarRating rating={Math.round(stats.average)} readonly size="sm" />
                        <span class="text-sm text-base-content/70">
                            {stats.average.toFixed(1)} ({stats.count}개)
                        </span>
                    </div>
                {/if}
            </div>
            {#if canReview && onwriteReview}
                <button onclick={onwriteReview} class="btn btn-primary btn-sm cursor-pointer">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                    리뷰 작성
                </button>
            {/if}
        </div>

        {#if reviews.length === 0}
            <div class="text-center py-8 text-base-content/50">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <p>아직 리뷰가 없습니다.</p>
                <p class="text-sm mt-1">첫 번째 리뷰를 남겨보세요!</p>
                {#if canReview && onwriteReview}
                    <button onclick={onwriteReview} class="btn btn-primary btn-sm mt-4 cursor-pointer">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                        리뷰 작성하기
                    </button>
                {/if}

                {#if relatedPosts && relatedPosts.length > 0}
                    <div class="mt-4 text-left">
                        <p class="text-sm font-medium text-base-content/70 mb-2">커뮤니티 관련 글 {relatedPosts.length}개</p>
                        <ul class="space-y-1">
                            {#each relatedPosts as post}
                                <li>
                                    <a href="/posts/{post.id}" class="text-sm text-primary hover:underline">{post.title}</a>
                                </li>
                            {/each}
                        </ul>
                    </div>
                {/if}
            </div>
        {:else}
            <div class="space-y-4">
                {#each reviews as review (review.id)}
                    <div class="border-b border-base-200 pb-4 last:border-b-0 last:pb-0">
                        <div class="flex items-start justify-between mb-2">
                            <div class="flex items-center gap-2">
                                <Avatar nickname={review.nickname} size="sm" />
                                <span class="font-medium">{review.nickname}</span>
                                <StarRating rating={review.rating} readonly size="sm" />
                            </div>
                            <span class="text-xs text-base-content/50">{review.createdAtFormatted}</span>
                        </div>
                        <p class="text-base-content/80">{review.comment}</p>

                        {#if review.completionTime || review.courseDifficulty || review.operationSatisfaction || (review.recommendationTags && review.recommendationTags.length > 0)}
                            <div class="flex flex-wrap items-center gap-2 mt-2">
                                {#if review.courseDifficulty && difficultyLabels[review.courseDifficulty]}
                                    <span class="badge badge-sm {difficultyLabels[review.courseDifficulty].badge}">
                                        {difficultyLabels[review.courseDifficulty].label}
                                    </span>
                                {/if}
                                {#if review.completionTime}
                                    <span class="badge badge-sm badge-outline">
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                        {review.completionTime}
                                    </span>
                                {/if}
                                {#if review.operationSatisfaction}
                                    <span class="text-xs text-base-content/60 inline-flex items-center gap-1">운영 <StarRating rating={review.operationSatisfaction} readonly size="sm" /></span>
                                {/if}
                            </div>
                            {#if review.recommendationTags && review.recommendationTags.length > 0}
                                <div class="flex flex-wrap gap-1 mt-1.5">
                                    {#each review.recommendationTags as tag}
                                        <span class="badge badge-xs badge-primary badge-outline">{tag}</span>
                                    {/each}
                                </div>
                            {/if}
                        {/if}
                    </div>
                {/each}
            </div>
        {/if}
    </div>
</div>
