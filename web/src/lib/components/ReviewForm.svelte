<script lang="ts">
    import { enhance } from '$app/forms';

    interface Props {
        raceSlug: string;
        hasReviewed: boolean;
        raceDate: string | null;
        raceEndDate?: string | null;
        open: boolean;
        onclose: () => void;
        errors?: Record<string, string[]>;
    }

    let {
        raceSlug,
        hasReviewed,
        raceDate,
        raceEndDate,
        open = $bindable(false),
        onclose,
        errors = {},
    }: Props = $props();

    const isFinished = $derived.by(() => {
        const endDate = raceEndDate || raceDate;
        if (!endDate) return false;
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return new Date(endDate + 'T00:00:00') <= today;
    });

    let rating = $state(0);
    let hoverRating = $state(0);
    let comment = $state('');
    let completionTime = $state('');
    let courseDifficulty = $state('');
    let operationSatisfaction = $state(0);
    let operationHover = $state(0);
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

    const DIFFICULTY_OPTIONS: Array<[string, string]> = [
        ['easy', '쉬움'],
        ['normal', '보통'],
        ['hard', '어려움'],
    ];

    function toggleTag(tag: string) {
        selectedTags = selectedTags.includes(tag)
            ? selectedTags.filter(t => t !== tag)
            : [...selectedTags, tag];
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
        hoverRating = 0;
        comment = '';
        completionTime = '';
        courseDifficulty = '';
        operationSatisfaction = 0;
        operationHover = 0;
        selectedTags = [];
        showOptional = false;
    }

    const optionalFilled = $derived(
        !!completionTime
        || !!courseDifficulty
        || operationSatisfaction > 0
        || selectedTags.length > 0,
    );
</script>

{#if open}
    <div
        class="rv-modal"
        role="dialog"
        aria-modal="true"
        aria-label="리뷰 작성"
        onclick={(e) => { if (e.target === e.currentTarget) close(); }}
        onkeydown={handleKeydown}
        tabindex="-1"
    >
        <div class="rv-box">
            <div class="rv-head">
                <span class="rv-kicker">리뷰 작성</span>
                <button class="rv-close" onclick={close} aria-label="닫기">✕</button>
            </div>

            <div class="rv-body">
                {#if !isFinished}
                    <div class="rv-state">
                        <div class="rv-state-tag">작성 불가</div>
                        <h3>대회가 끝난 뒤에 리뷰를 작성할 수 있어요.</h3>
                        <p>대회가 종료되면 다시 방문해주세요.</p>
                    </div>
                {:else if hasReviewed}
                    <div class="rv-state">
                        <div class="rv-state-tag accent">작성 완료</div>
                        <h3>이미 이 대회의 리뷰를 작성하셨어요.</h3>
                        <p>소중한 후기 감사합니다.</p>
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
                        class="rv-form"
                    >
                        <!-- Rating -->
                        <div class="rv-field">
                            <div class="rv-label">
                                <span class="rv-flabel">별점</span>
                                <span class="rv-required">*</span>
                            </div>
                            <div class="rv-stars-input" role="radiogroup" aria-label="별점">
                                {#each [1, 2, 3, 4, 5] as star}
                                    <button
                                        type="button"
                                        class="rv-star {(hoverRating || rating) >= star ? 'on' : ''}"
                                        onclick={() => (rating = star)}
                                        onmouseenter={() => (hoverRating = star)}
                                        onmouseleave={() => (hoverRating = 0)}
                                        aria-label="{star}점"
                                    >★</button>
                                {/each}
                                {#if (hoverRating || rating) > 0}
                                    <span class="rv-rating-label">{RATING_LABELS[hoverRating || rating]}</span>
                                {/if}
                            </div>
                            <input type="hidden" name="rating" value={rating} />
                            {#if errors.rating}
                                <p class="rv-error" role="alert">{errors.rating[0]}</p>
                            {/if}
                        </div>

                        <!-- Comment -->
                        <div class="rv-field">
                            <div class="rv-label">
                                <span class="rv-flabel">한줄평</span>
                                <span class="rv-required">*</span>
                                <span class="rv-counter {commentLength > 180 ? 'warn' : ''}">{commentLength}/200</span>
                            </div>
                            <textarea
                                id="review-comment"
                                name="comment"
                                bind:value={comment}
                                placeholder="대회에 대한 솔직한 후기를 남겨주세요 (5–200자)"
                                maxlength="200"
                                rows="3"
                                class="rv-input"
                            ></textarea>
                            {#if errors.comment}
                                <p class="rv-error" role="alert">{errors.comment[0]}</p>
                            {/if}
                        </div>

                        <!-- Nickname -->
                        <div class="rv-field">
                            <div class="rv-label">
                                <span class="rv-flabel">닉네임</span>
                                <span class="rv-hint">미입력 시 익명</span>
                            </div>
                            <input
                                type="text"
                                id="review-nickname"
                                name="nickname"
                                placeholder="닉네임을 입력하세요"
                                maxlength="50"
                                class="rv-input"
                            />
                        </div>

                        <!-- Optional toggle -->
                        <button
                            type="button"
                            class="rv-toggle"
                            onclick={() => (showOptional = !showOptional)}
                        >
                            <span class="rv-toggle-arrow {showOptional ? 'open' : ''}">▸</span>
                            <span>추가 정보 입력 (선택)</span>
                            {#if optionalFilled}
                                <span class="rv-toggle-badge">입력됨</span>
                            {/if}
                        </button>

                        {#if showOptional}
                            <div class="rv-optional">
                                <div class="rv-field">
                                    <div class="rv-label">
                                        <span class="rv-flabel">완주 기록</span>
                                    </div>
                                    <input
                                        type="text"
                                        id="review-completion-time"
                                        name="completion_time"
                                        bind:value={completionTime}
                                        placeholder="예: 4:30:00"
                                        maxlength="20"
                                        class="rv-input rv-input-mono"
                                    />
                                </div>

                                <div class="rv-field">
                                    <div class="rv-label">
                                        <span class="rv-flabel">코스 난이도</span>
                                    </div>
                                    <div class="rv-diff">
                                        {#each DIFFICULTY_OPTIONS as [val, label]}
                                            <button
                                                type="button"
                                                class="rv-diff-btn {courseDifficulty === val ? 'on' : ''}"
                                                onclick={() => (courseDifficulty = courseDifficulty === val ? '' : val)}
                                            >
                                                {label}
                                            </button>
                                        {/each}
                                    </div>
                                    <input type="hidden" name="course_difficulty" value={courseDifficulty} />
                                </div>

                                <div class="rv-field">
                                    <div class="rv-label">
                                        <span class="rv-flabel">운영 만족도</span>
                                    </div>
                                    <div class="rv-stars-input" role="radiogroup" aria-label="운영 만족도">
                                        {#each [1, 2, 3, 4, 5] as star}
                                            <button
                                                type="button"
                                                class="rv-star sm {(operationHover || operationSatisfaction) >= star ? 'on' : ''}"
                                                onclick={() => (operationSatisfaction = star)}
                                                onmouseenter={() => (operationHover = star)}
                                                onmouseleave={() => (operationHover = 0)}
                                                aria-label="{star}점"
                                            >★</button>
                                        {/each}
                                    </div>
                                    <input type="hidden" name="operation_satisfaction" value={operationSatisfaction || ''} />
                                </div>

                                <div class="rv-field">
                                    <div class="rv-label">
                                        <span class="rv-flabel">추천 태그</span>
                                    </div>
                                    <div class="rv-tags">
                                        {#each RECOMMENDATION_TAGS as tag}
                                            <button
                                                type="button"
                                                class="rv-tag {selectedTags.includes(tag) ? 'on' : ''}"
                                                onclick={() => toggleTag(tag)}
                                            >
                                                {#if selectedTags.includes(tag)}
                                                    <span class="rv-tag-check">✓</span>
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
                            <div class="rv-alert" role="alert">! {errors.review[0]}</div>
                        {/if}

                        <div class="rv-submit">
                            <button
                                type="submit"
                                disabled={isSubmitting || rating === 0 || commentLength < 5}
                                class="rv-btn-primary"
                            >
                                <span>{isSubmitting ? '등록 중…' : '리뷰 등록'}</span>
                                <span class="rv-arrow">→</span>
                            </button>
                            {#if rating === 0 || commentLength < 5}
                                <p class="rv-hint-center">
                                    {rating === 0 ? '별점을 선택해주세요' : '한줄평을 5자 이상 입력해주세요'}
                                </p>
                            {/if}
                        </div>
                    </form>
                {/if}
            </div>
        </div>
    </div>
{/if}

<style>
    .rv-modal {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.85);
        z-index: 200;
        display: grid;
        place-items: center;
        padding: 24px;
        cursor: pointer;
    }

    .rv-box {
        background: var(--arena-paper);
        border: 1px solid var(--arena-ink);
        box-shadow: 6px 6px 0 var(--arena-ink);
        max-width: 540px;
        width: 100%;
        max-height: 90vh;
        display: flex;
        flex-direction: column;
        cursor: default;
    }

    .rv-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 18px;
        border-bottom: 1px solid var(--arena-line);
        background: var(--arena-paper-alt);
        flex-shrink: 0;
    }

    .rv-kicker {
        font-family: var(--arena-f-mono);
        font-size: 12px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: var(--arena-ink);
        font-weight: 600;
    }

    /* Form field label — readable, not a tiny instrumentation kicker */
    .rv-flabel {
        font-family: var(--arena-f-body);
        font-size: 14px;
        font-weight: 600;
        color: var(--arena-ink);
    }

    .rv-close {
        background: transparent;
        border: 1px solid var(--arena-line);
        padding: 4px 10px;
        font-size: 14px;
        cursor: pointer;
        line-height: 1;
        color: var(--arena-ink);
        font-family: var(--arena-f-mono);
    }
    .rv-close:hover {
        background: var(--arena-ink);
        color: var(--arena-paper);
    }

    .rv-body {
        overflow-y: auto;
        overscroll-behavior: contain;
        flex: 1;
    }

    /* States (unavailable / already reviewed) */
    .rv-state {
        padding: 48px 28px;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
    }
    .rv-state-tag {
        display: inline-block;
        padding: 5px 12px;
        border: 1px solid var(--arena-ink);
        font-family: var(--arena-f-body);
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        color: var(--arena-ink);
    }
    .rv-state-tag.accent {
        background: var(--arena-accent);
        border-color: var(--arena-accent);
    }
    .rv-state h3 {
        font-family: var(--arena-f-display);
        font-size: 20px;
        font-weight: 700;
        letter-spacing: -0.4px;
        margin: 0;
        color: var(--arena-ink);
        line-height: 1.4;
    }
    .rv-state p {
        font-size: 14px;
        color: var(--arena-ink-soft);
        margin: 0;
    }

    /* Form */
    .rv-form {
        padding: 18px 22px 22px;
        display: flex;
        flex-direction: column;
        gap: 18px;
    }
    .rv-field {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .rv-label {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .rv-required {
        color: var(--arena-urgent);
        font-size: 14px;
        font-weight: 700;
        line-height: 1;
    }
    .rv-hint {
        color: var(--arena-ink-soft);
        font-family: var(--arena-f-body);
        font-size: 12px;
        margin-left: auto;
    }
    .rv-counter {
        margin-left: auto;
        font-family: var(--arena-f-mono);
        font-size: 13px;
        color: var(--arena-ink-soft);
    }
    .rv-counter.warn {
        color: var(--arena-urgent);
    }

    .rv-input {
        font-family: var(--arena-f-body);
        font-size: 14px;
        padding: 10px 12px;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
        color: var(--arena-ink);
        outline: none;
        width: 100%;
        line-height: 1.5;
        resize: vertical;
        border-radius: 0;
    }
    .rv-input::placeholder {
        color: var(--arena-ink-mute);
    }
    .rv-input:focus {
        border-color: var(--arena-ink);
        box-shadow: 2px 2px 0 var(--arena-ink);
    }
    .rv-input-mono {
        font-family: var(--arena-f-mono);
    }

    /* Star rating input */
    .rv-stars-input {
        display: flex;
        align-items: center;
        gap: 2px;
    }
    .rv-star {
        background: transparent;
        border: none;
        padding: 0 3px;
        font-size: 32px;
        line-height: 1;
        cursor: pointer;
        color: var(--arena-line-soft);
        font-family: var(--arena-f-mono);
        transition: color 0.1s, transform 0.1s;
    }
    .rv-star:hover { transform: scale(1.1); }
    .rv-star.on { color: var(--arena-ink); }
    .rv-star.sm { font-size: 24px; }
    .rv-rating-label {
        margin-left: 12px;
        font-family: var(--arena-f-body);
        font-size: 14px;
        font-weight: 600;
        color: var(--arena-ink);
    }

    /* Optional toggle */
    .rv-toggle {
        display: flex;
        align-items: center;
        gap: 8px;
        background: transparent;
        border: none;
        padding: 6px 0;
        font-family: var(--arena-f-body);
        font-size: 13px;
        font-weight: 600;
        color: var(--arena-ink-soft);
        cursor: pointer;
        text-align: left;
    }
    .rv-toggle:hover { color: var(--arena-ink); }
    .rv-toggle-arrow {
        font-size: 12px;
        transition: transform 0.15s;
        display: inline-block;
    }
    .rv-toggle-arrow.open { transform: rotate(90deg); }
    .rv-toggle-badge {
        margin-left: auto;
        padding: 3px 8px;
        background: var(--arena-accent);
        color: var(--arena-ink);
        font-family: var(--arena-f-body);
        font-weight: 600;
        font-size: 12px;
    }

    .rv-optional {
        display: flex;
        flex-direction: column;
        gap: 14px;
        padding-left: 14px;
        border-left: 1px solid var(--arena-line);
    }

    /* Difficulty buttons */
    .rv-diff {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 6px;
    }
    .rv-diff-btn {
        font-family: var(--arena-f-body);
        font-size: 13px;
        font-weight: 600;
        padding: 9px 12px;
        background: var(--arena-paper);
        color: var(--arena-ink);
        border: 1px solid var(--arena-line);
        cursor: pointer;
        transition: transform 0.1s;
        border-radius: 0;
    }
    .rv-diff-btn:hover { background: var(--arena-paper-alt); }
    .rv-diff-btn:active { transform: translateY(1px); }
    .rv-diff-btn.on {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border-color: var(--arena-ink);
    }

    /* Tags */
    .rv-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }
    .rv-tag {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 7px 12px;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
        color: var(--arena-ink);
        font-family: var(--arena-f-body);
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        border-radius: 0;
        transition: transform 0.1s;
    }
    .rv-tag:hover { background: var(--arena-paper-alt); }
    .rv-tag:active { transform: translateY(1px); }
    .rv-tag.on {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border-color: var(--arena-ink);
    }
    .rv-tag-check {
        font-family: var(--arena-f-mono);
        font-size: 12px;
        font-weight: 700;
    }

    /* Errors */
    .rv-error {
        font-family: var(--arena-f-body);
        font-size: 13px;
        color: var(--arena-urgent);
        margin: 0;
    }
    .rv-alert {
        padding: 11px 14px;
        border: 1px solid var(--arena-urgent);
        color: var(--arena-urgent);
        font-family: var(--arena-f-body);
        font-size: 14px;
        background: var(--arena-paper);
    }

    /* Submit */
    .rv-submit {
        padding-top: 4px;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .rv-btn-primary {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        width: 100%;
        padding: 12px 14px;
        font-family: var(--arena-f-body);
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        text-align: left;
        transition: transform 0.1s;
        background: var(--arena-ink);
        color: var(--arena-paper);
        border: 1px solid var(--arena-ink);
        border-radius: 0;
    }
    .rv-btn-primary:hover:not(:disabled) {
        background: var(--arena-accent-deep);
        border-color: var(--arena-accent-deep);
    }
    .rv-btn-primary:active:not(:disabled) {
        transform: translateY(1px);
    }
    .rv-btn-primary:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }
    .rv-arrow {
        font-family: var(--arena-f-mono);
        font-size: 13px;
        opacity: 0.7;
    }
    .rv-hint-center {
        text-align: center;
        font-family: var(--arena-f-body);
        font-size: 13px;
        color: var(--arena-ink-soft);
        margin: 0;
    }

    @media (max-width: 480px) {
        .rv-modal { padding: 0; }
        .rv-box {
            max-width: 100%;
            max-height: 100vh;
            box-shadow: none;
            border: none;
        }
        .rv-form { padding: 16px 16px 18px; }
    }
</style>
