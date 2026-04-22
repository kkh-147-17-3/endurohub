<script lang="ts">
    import { enhance } from '$app/forms';
    import StarRating from './StarRating.svelte';

    interface Props {
        raceSlug: string;
        hasReviewed: boolean;
        raceDate: string | null;
        raceEndDate?: string | null;
        open: boolean;
        onclose: () => void;
        errors?: Record<string, string[]>;
    }

    let { raceSlug, hasReviewed, raceDate, raceEndDate, open = $bindable(false), onclose, errors = {} }: Props = $props();

    const isFinished = $derived.by(() => {
        const endDate = raceEndDate || raceDate;
        if (!endDate) return false;
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return new Date(endDate + 'T00:00:00') <= today;
    });
    const canReview = $derived(isFinished && !hasReviewed);

    let rating = $state(0);
    let comment = $state('');
    let completionTime = $state('');
    let courseDifficulty = $state('');
    let operationSatisfaction = $state(0);
    let selectedTags = $state<string[]>([]);
    let isSubmitting = $state(false);
    let showOptional = $state(false);

    let commentLength = $derived(comment.length);

    const RATING_LABELS: Record<number, string> = {
        1: '별로예요',
        2: '그저 그래요',
        3: '보통이에요',
        4: '좋아요',
        5: '최고예요',
    };

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

    function close() {
        open = false;
        onclose?.();
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Escape') close();
    }

    function resetForm() {
        rating = 0;
        comment = '';
        completionTime = '';
        courseDifficulty = '';
        operationSatisfaction = 0;
        selectedTags = [];
        showOptional = false;
    }
</script>

{#if open}
    <div
        class="modal modal-open modal-bottom sm:modal-middle"
        role="dialog"
        aria-modal="true"
        aria-label="리뷰 작성"
        onkeydown={handleKeydown}
    >
        <div class="modal-box sm:max-w-lg p-0 flex flex-col max-h-[90vh] sm:max-h-[85vh]">
            <!-- Header -->
            <div class="flex items-center justify-between px-5 py-4 border-b border-base-200 shrink-0">
                <h3 class="font-bold text-lg">리뷰 작성</h3>
                <button onclick={close} class="btn btn-sm btn-circle btn-ghost" aria-label="닫기">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
            </div>

            <!-- Body -->
            <div class="overflow-y-auto flex-1 overscroll-contain">
                {#if !isFinished}
                    <div class="p-5">
                        <div class="flex flex-col items-center py-8 text-center">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-warning mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                            <p class="font-medium text-base-content/80">대회 종료 후 리뷰를 작성할 수 있습니다.</p>
                            <p class="text-sm text-base-content/50 mt-1">대회가 끝나면 다시 방문해주세요!</p>
                        </div>
                    </div>
                {:else if hasReviewed}
                    <div class="p-5">
                        <div class="flex flex-col items-center py-8 text-center">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-success mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <p class="font-medium text-base-content/80">이미 이 대회에 리뷰를 작성하셨습니다.</p>
                            <p class="text-sm text-base-content/50 mt-1">소중한 후기 감사합니다!</p>
                        </div>
                    </div>
                {:else}
                    <form
                        method="POST"
                        action="?/review"
                        use:enhance={() => {
                            isSubmitting = true;
                            return async ({ result, update }) => {
                                isSubmitting = false;
                                if (result.type === 'success') {
                                    resetForm();
                                    close();
                                }
                                await update();
                            };
                        }}
                        class="p-5 space-y-5"
                    >
                        <!-- Rating (Required) -->
                        <div class="form-control">
                            <div class="label pb-1">
                                <span class="label-text font-medium">별점 <span class="text-error">*</span></span>
                            </div>
                            <div class="flex items-center gap-3">
                                <StarRating bind:rating onchange={(value) => rating = value} size="lg" />
                                {#if rating > 0}
                                    <span class="text-sm font-medium text-warning">{RATING_LABELS[rating]}</span>
                                {/if}
                            </div>
                            <input type="hidden" name="rating" value={rating} />
                            {#if errors.rating}
                                <p class="text-error text-sm mt-1" role="alert">{errors.rating[0]}</p>
                            {/if}
                        </div>

                        <!-- Comment (Required) -->
                        <div class="form-control">
                            <label class="label pb-1" for="review-comment">
                                <span class="label-text font-medium">한줄평 <span class="text-error">*</span></span>
                                <span class="label-text-alt {commentLength > 180 ? 'text-warning' : commentLength >= 5 ? 'text-success' : ''}">{commentLength}/200</span>
                            </label>
                            <textarea
                                id="review-comment"
                                name="comment"
                                bind:value={comment}
                                placeholder="대회에 대한 솔직한 후기를 남겨주세요 (5-200자)"
                                maxlength="200"
                                rows="3"
                                class="textarea textarea-bordered w-full focus:textarea-primary"
                            ></textarea>
                            {#if errors.comment}
                                <p class="text-error text-sm mt-1" role="alert">{errors.comment[0]}</p>
                            {/if}
                        </div>

                        <!-- Nickname -->
                        <div class="form-control">
                            <label class="label pb-1" for="review-nickname">
                                <span class="label-text font-medium">닉네임</span>
                                <span class="label-text-alt">미입력 시 익명</span>
                            </label>
                            <input
                                type="text"
                                id="review-nickname"
                                name="nickname"
                                placeholder="닉네임을 입력하세요"
                                maxlength="50"
                                class="input input-bordered w-full focus:input-primary"
                            />
                        </div>

                        <!-- Optional Fields Toggle -->
                        <button
                            type="button"
                            class="flex items-center gap-2 text-sm text-base-content/60 hover:text-base-content transition-colors w-full cursor-pointer"
                            onclick={() => showOptional = !showOptional}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 transition-transform duration-200 {showOptional ? 'rotate-90' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                            </svg>
                            추가 정보 입력 (선택)
                            {#if completionTime || courseDifficulty || operationSatisfaction > 0 || selectedTags.length > 0}
                                <span class="badge badge-primary badge-sm text-xs">입력됨</span>
                            {/if}
                        </button>

                        {#if showOptional}
                            <div class="space-y-4 pl-1 border-l-2 border-base-200 ml-1.5 transition-all">
                                <!-- Completion Time -->
                                <div class="form-control pl-4">
                                    <label class="label pb-1" for="review-completion-time">
                                        <span class="label-text text-sm">완주 기록</span>
                                    </label>
                                    <input
                                        type="text"
                                        id="review-completion-time"
                                        name="completion_time"
                                        bind:value={completionTime}
                                        placeholder="예: 4:30:00"
                                        maxlength="20"
                                        class="input input-bordered input-sm w-full focus:input-primary"
                                    />
                                </div>

                                <!-- Course Difficulty -->
                                <div class="form-control pl-4">
                                    <div class="label pb-1">
                                        <span class="label-text text-sm">코스 난이도</span>
                                    </div>
                                    <div class="flex gap-2">
                                        <button type="button" class="btn btn-sm flex-1 {courseDifficulty === 'easy' ? 'btn-success' : 'btn-outline'}" onclick={() => courseDifficulty = courseDifficulty === 'easy' ? '' : 'easy'}>쉬움</button>
                                        <button type="button" class="btn btn-sm flex-1 {courseDifficulty === 'normal' ? 'btn-warning' : 'btn-outline'}" onclick={() => courseDifficulty = courseDifficulty === 'normal' ? '' : 'normal'}>보통</button>
                                        <button type="button" class="btn btn-sm flex-1 {courseDifficulty === 'hard' ? 'btn-error' : 'btn-outline'}" onclick={() => courseDifficulty = courseDifficulty === 'hard' ? '' : 'hard'}>어려움</button>
                                    </div>
                                    <input type="hidden" name="course_difficulty" value={courseDifficulty} />
                                </div>

                                <!-- Operation Satisfaction -->
                                <div class="form-control pl-4">
                                    <div class="label pb-1">
                                        <span class="label-text text-sm">운영 만족도</span>
                                    </div>
                                    <StarRating bind:rating={operationSatisfaction} onchange={(value) => operationSatisfaction = value} size="md" />
                                    <input type="hidden" name="operation_satisfaction" value={operationSatisfaction || ''} />
                                </div>

                                <!-- Recommendation Tags -->
                                <div class="form-control pl-4">
                                    <div class="label pb-1">
                                        <span class="label-text text-sm">추천 태그</span>
                                    </div>
                                    <div class="flex flex-wrap gap-2">
                                        {#each RECOMMENDATION_TAGS as tag}
                                            <button
                                                type="button"
                                                class="badge badge-lg cursor-pointer transition-all {selectedTags.includes(tag) ? 'badge-primary' : 'badge-outline hover:badge-ghost'}"
                                                onclick={() => toggleTag(tag)}
                                            >
                                                {#if selectedTags.includes(tag)}
                                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                                                {/if}
                                                {tag}
                                            </button>
                                        {/each}
                                    </div>
                                    {#each selectedTags as tag}
                                        <input type="hidden" name="recommendation_tags" value={tag} />
                                    {/each}
                                </div>
                            </div>
                        {/if}

                        {#if errors.review}
                            <div class="alert alert-error" role="alert">
                                <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <span class="text-sm">{errors.review[0]}</span>
                            </div>
                        {/if}

                        <!-- Footer / Submit -->
                        <div class="pt-2 pb-1">
                            <button
                                type="submit"
                                disabled={isSubmitting || rating === 0 || commentLength < 5}
                                class="btn btn-primary w-full"
                            >
                                {#if isSubmitting}
                                    <span class="loading loading-spinner loading-sm"></span>
                                    등록 중...
                                {:else}
                                    리뷰 등록
                                {/if}
                            </button>
                            {#if rating === 0 || commentLength < 5}
                                <p class="text-center text-xs text-base-content/50 mt-2">
                                    {#if rating === 0}별점을 선택해주세요{:else}한줄평을 5자 이상 입력해주세요{/if}
                                </p>
                            {/if}
                        </div>
                    </form>
                {/if}
            </div>
        </div>
        <button class="modal-backdrop bg-black/50" onclick={close} aria-label="닫기"></button>
    </div>
{/if}
