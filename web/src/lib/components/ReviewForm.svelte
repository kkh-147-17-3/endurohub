<script lang="ts">
    import { enhance } from '$app/forms';
    import StarRating from './StarRating.svelte';

    interface Props {
        raceSlug: string;
        hasReviewed: boolean;
        raceStatus: string;
        errors?: Record<string, string[]>;
    }

    let { raceSlug, hasReviewed, raceStatus, errors = {} }: Props = $props();

    const isFinished = $derived(raceStatus === 'finished');

    let rating = $state(0);
    let comment = $state('');
    let completionTime = $state('');
    let courseDifficulty = $state('');
    let operationSatisfaction = $state(0);
    let selectedTags = $state<string[]>([]);
    let isSubmitting = $state(false);

    let commentLength = $derived(comment.length);

    const RECOMMENDATION_TAGS = [
        '초보자 추천', '경치 좋은', '잘 운영된', '기념품 좋은',
        '코스 좋은', '접근성 좋은', '다시 참가하고 싶은',
    ];

    function toggleTag(tag: string) {
        if (selectedTags.includes(tag)) {
            selectedTags = selectedTags.filter(t => t !== tag);
        } else {
            selectedTags = [...selectedTags, tag];
        }
    }
</script>

<div class="card bg-base-100 shadow-xl">
    <div class="card-body">
        <h3 class="card-title text-lg">리뷰 작성</h3>

        {#if !isFinished}
            <div class="alert alert-warning">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>대회 종료 후 리뷰를 작성할 수 있습니다.</span>
            </div>
        {:else if hasReviewed}
            <div class="alert alert-info">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>이미 이 대회에 리뷰를 작성하셨습니다.</span>
            </div>
        {:else}
            <form
                method="POST"
                action="?/review"
                use:enhance={() => {
                    isSubmitting = true;
                    return async ({ update }) => {
                        isSubmitting = false;
                        await update();
                    };
                }}
                class="space-y-4"
            >
                <div class="form-control">
                    <label class="label" for="nickname">
                        <span class="label-text">닉네임 (선택)</span>
                    </label>
                    <input
                        type="text"
                        id="nickname"
                        name="nickname"
                        placeholder="미입력 시 익명으로 표시됩니다"
                        maxlength="50"
                        class="input input-bordered w-full"
                    />
                </div>

                <div class="form-control">
                    <div class="label">
                        <span class="label-text">별점 <span class="text-error">*</span></span>
                    </div>
                    <StarRating bind:rating onchange={(value) => rating = value} size="lg" />
                    <input type="hidden" name="rating" value={rating} />
                    {#if errors.rating}
                        <div class="label" role="alert">
                            <span class="label-text-alt text-error">{errors.rating[0]}</span>
                        </div>
                    {/if}
                </div>

                <div class="form-control">
                    <label class="label" for="comment">
                        <span class="label-text">한줄평 <span class="text-error">*</span></span>
                        <span class="label-text-alt">{commentLength}/200</span>
                    </label>
                    <textarea
                        id="comment"
                        name="comment"
                        bind:value={comment}
                        placeholder="대회에 대한 솔직한 후기를 남겨주세요 (5-200자)"
                        maxlength="200"
                        rows="3"
                        class="textarea textarea-bordered w-full"
                    ></textarea>
                    {#if errors.comment}
                        <div class="label" role="alert">
                            <span class="label-text-alt text-error">{errors.comment[0]}</span>
                        </div>
                    {/if}
                </div>

                <!-- Completion Time -->
                <div class="form-control">
                    <label class="label" for="completion_time">
                        <span class="label-text">완주 기록 (선택)</span>
                    </label>
                    <input
                        type="text"
                        id="completion_time"
                        name="completion_time"
                        bind:value={completionTime}
                        placeholder="예: 4:30:00"
                        maxlength="20"
                        class="input input-bordered w-full"
                    />
                </div>

                <!-- Course Difficulty -->
                <div class="form-control">
                    <div class="label">
                        <span class="label-text">코스 난이도 (선택)</span>
                    </div>
                    <div class="flex gap-2">
                        <button type="button" class="btn btn-sm flex-1 {courseDifficulty === 'easy' ? 'btn-success' : 'btn-outline'}" onclick={() => courseDifficulty = courseDifficulty === 'easy' ? '' : 'easy'}>쉬움</button>
                        <button type="button" class="btn btn-sm flex-1 {courseDifficulty === 'normal' ? 'btn-warning' : 'btn-outline'}" onclick={() => courseDifficulty = courseDifficulty === 'normal' ? '' : 'normal'}>보통</button>
                        <button type="button" class="btn btn-sm flex-1 {courseDifficulty === 'hard' ? 'btn-error' : 'btn-outline'}" onclick={() => courseDifficulty = courseDifficulty === 'hard' ? '' : 'hard'}>어려움</button>
                    </div>
                    <input type="hidden" name="course_difficulty" value={courseDifficulty} />
                </div>

                <!-- Operation Satisfaction -->
                <div class="form-control">
                    <div class="label">
                        <span class="label-text">운영 만족도 (선택)</span>
                    </div>
                    <StarRating bind:rating={operationSatisfaction} onchange={(value) => operationSatisfaction = value} size="md" />
                    <input type="hidden" name="operation_satisfaction" value={operationSatisfaction || ''} />
                </div>

                <!-- Recommendation Tags -->
                <div class="form-control">
                    <div class="label">
                        <span class="label-text">추천 태그 (선택)</span>
                    </div>
                    <div class="flex flex-wrap gap-2">
                        {#each RECOMMENDATION_TAGS as tag}
                            <button
                                type="button"
                                class="badge badge-lg cursor-pointer {selectedTags.includes(tag) ? 'badge-primary' : 'badge-outline'}"
                                onclick={() => toggleTag(tag)}
                            >
                                {tag}
                            </button>
                        {/each}
                    </div>
                    {#each selectedTags as tag}
                        <input type="hidden" name="recommendation_tags" value={tag} />
                    {/each}
                </div>

                {#if errors.review}
                    <div class="alert alert-error" role="alert">
                        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>{errors.review[0]}</span>
                    </div>
                {/if}

                <button
                    type="submit"
                    disabled={isSubmitting}
                    class="btn btn-primary w-full"
                >
                    {#if isSubmitting}
                        <span class="loading loading-spinner loading-sm"></span>
                        등록 중...
                    {:else}
                        리뷰 등록
                    {/if}
                </button>
            </form>
        {/if}
    </div>
</div>
