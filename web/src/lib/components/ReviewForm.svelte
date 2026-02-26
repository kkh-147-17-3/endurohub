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
    let isSubmitting = $state(false);

    let commentLength = $derived(comment.length);
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
                action="?/createReview"
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
                    <label class="label">
                        <span class="label-text">별점 <span class="text-error">*</span></span>
                    </label>
                    <StarRating bind:rating onchange={(value) => rating = value} size="lg" />
                    <input type="hidden" name="rating" value={rating} />
                    {#if errors.rating}
                        <label class="label" role="alert">
                            <span class="label-text-alt text-error">{errors.rating[0]}</span>
                        </label>
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
                        <label class="label" role="alert">
                            <span class="label-text-alt text-error">{errors.comment[0]}</span>
                        </label>
                    {/if}
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
