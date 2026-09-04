<script lang="ts">
    import { enhance } from '$app/forms';
    import { Button } from '$lib/components/eh';
    import { raceCourseOptions } from '$lib/race-result';
    import type { Distance, Sport } from '$lib/types';

    interface Props {
        raceSlug: string;
        raceTitle: string;
        raceMeta?: string;
        hasReviewed: boolean;
        raceDate: string | null;
        raceEndDate?: string | null;
        distances?: Distance[] | null;
        sport: Sport;
        sportLabel: string;
        reviewerNickname: string;
        open: boolean;
        onclose: () => void;
        onsubmitted?: (detail: { rating: number; message: string }) => void;
        errors?: Record<string, string[]>;
    }

    let {
        raceSlug,
        raceTitle,
        raceMeta = '',
        hasReviewed,
        raceDate,
        raceEndDate,
        distances = [],
        sport,
        sportLabel,
        reviewerNickname,
        open = $bindable(false),
        onclose,
        onsubmitted,
        errors = {},
    }: Props = $props();

    const isFinished = $derived.by(() => {
        const endDate = raceEndDate || raceDate;
        if (!endDate) return false;
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return new Date(endDate + 'T00:00:00') <= today;
    });

    const STAR_PATH =
        'M12 2.2l2.95 6.32 6.85.74-5.1 4.63 1.42 6.75L12 17.6l-6.12 3.84 1.42-6.75-5.1-4.63 6.85-.74z';
    const RV_MAX = 200;

    const RECOMMENDATION_TAGS = [
        '초보자 추천', '경치 좋은', '잘 운영된', '기념품 좋은',
        '코스 좋은', '접근성 좋은', '다시 참가하고 싶은',
    ];

    const DIFFICULTY_OPTIONS: Array<[string, string]> = [
        ['easy', '쉬움'],
        ['normal', '보통'],
        ['hard', '어려움'],
    ];

    let rating = $state(0);
    let hoverRating = $state(0);
    let comment = $state('');
    let courseCode = $state('');
    let recordHours = $state(0);
    let recordMinutes = $state(0);
    let recordSeconds = $state(0);
    let courseDifficulty = $state('');
    let operationSatisfaction = $state(0);
    let operationHover = $state(0);
    let selectedTags = $state<string[]>([]);
    let isSubmitting = $state(false);
    let showOptional = $state(false);

    const courseOptions = $derived(raceCourseOptions(distances, sport, sportLabel));
    const lit = $derived(hoverRating || rating);
    const opsLit = $derived(operationHover || operationSatisfaction);
    const over = $derived(comment.length > RV_MAX);
    const recordSecondsTotal = $derived(
        recordHours * 3600 + recordMinutes * 60 + recordSeconds,
    );
    const recordTimeValid = $derived(
        Number.isInteger(recordHours) && recordHours >= 0 && recordHours <= 99
        && Number.isInteger(recordMinutes) && recordMinutes >= 0 && recordMinutes <= 59
        && Number.isInteger(recordSeconds) && recordSeconds >= 0 && recordSeconds <= 59
        && recordSecondsTotal > 0,
    );
    const canSubmit = $derived(
        rating > 0
        && comment.trim().length >= 5
        && !over
        && !!courseCode
        && recordTimeValid,
    );
    const moreCount = $derived(
        (courseDifficulty ? 1 : 0)
        + (operationSatisfaction ? 1 : 0)
        + selectedTags.length,
    );

    $effect(() => {
        raceSlug;
        const options = courseOptions;
        if (!options.some((course) => course.code === courseCode)) {
            courseCode = options.length === 1 ? options[0].code : '';
        }
    });

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

    function getSuccessMessage(data: unknown): string {
        if (data && typeof data === 'object' && 'message' in data) {
            const message = (data as { message?: unknown }).message;
            if (typeof message === 'string' && message) return message;
        }
        return '리뷰와 참가 기록이 등록되었습니다.';
    }

    function resetForm() {
        rating = 0;
        hoverRating = 0;
        comment = '';
        courseCode = courseOptions.length === 1 ? courseOptions[0].code : '';
        recordHours = 0;
        recordMinutes = 0;
        recordSeconds = 0;
        courseDifficulty = '';
        operationSatisfaction = 0;
        operationHover = 0;
        selectedTags = [];
        showOptional = false;
    }
</script>

{#if open}
    <div
        class="v-scrim"
        role="dialog"
        aria-modal="true"
        aria-label="대회 리뷰 작성"
        onmousedown={(e) => { if (e.target === e.currentTarget) close(); }}
        onkeydown={handleKeydown}
        tabindex="-1"
    >
        <div class="v-modal rvm">
            <button class="rvm-close" onclick={close} aria-label="닫기">×</button>

            <div class="rvm-head">
                <span class="eh-micro"><span class="acc">WRITE REVIEW</span> · 리뷰 작성</span>
                <h2 class="race">{raceTitle}</h2>
                {#if raceMeta}
                    <p class="meta eh-data">{raceMeta}</p>
                {/if}
            </div>

            {#if !isFinished}
                <div class="rvm-state">
                    <div class="rvm-state__tag">작성 불가</div>
                    <h3>대회가 끝난 뒤에 리뷰를 작성할 수 있어요</h3>
                    <p>대회가 종료되면 다시 방문해주세요.</p>
                </div>
                <div class="rvm-foot">
                    <span style="flex:1"></span>
                    <Button variant="ghost" onclick={close}>닫기</Button>
                </div>
            {:else if hasReviewed}
                <div class="rvm-state">
                    <div class="rvm-state__tag rvm-state__tag--acc">작성 완료</div>
                    <h3>이미 이 대회의 리뷰를 작성하셨어요</h3>
                    <p>소중한 후기 감사합니다.</p>
                </div>
                <div class="rvm-foot">
                    <span style="flex:1"></span>
                    <Button variant="ghost" onclick={close}>닫기</Button>
                </div>
            {:else}
                <form
                    method="POST"
                    action="?/review"
                    class="rvm-form"
                    use:enhance={() => {
                        isSubmitting = true;
                        return async ({ result, update }) => {
                            isSubmitting = false;
                            if (result.type === 'success') {
                                onsubmitted?.({ rating, message: getSuccessMessage(result.data) });
                                resetForm();
                                close();
                            }
                            await update();
                        };
                    }}
                >
                    <div class="rvm-scroll">
                        <!-- 별점 -->
                        <div class="rvm-sec">
                            <div class="rvm-flabel">
                                <span class="l">별점<span class="req">*</span></span>
                            </div>
                            <div class="rv-stars" role="group" aria-label="별점 선택" onmouseleave={() => (hoverRating = 0)}>
                                {#each [1, 2, 3, 4, 5] as n (n)}
                                    <button
                                        type="button"
                                        class="rv-star {n <= lit ? 'on' : ''}"
                                        onmouseenter={() => (hoverRating = n)}
                                        onclick={() => (rating = rating === n ? 0 : n)}
                                        aria-label="{n}점"
                                    >
                                        <svg viewBox="0 0 24 24" fill={n <= lit ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"><path d={STAR_PATH}></path></svg>
                                    </button>
                                {/each}
                                <span class="rv-score {rating ? '' : 'empty'}">
                                    {#if rating}<span class="n eh-data">{rating}</span> / 5{:else}평가 안 함{/if}
                                </span>
                            </div>
                            <input type="hidden" name="rating" value={rating} />
                            {#if errors.rating}<p class="rvm-err" role="alert">{errors.rating[0]}</p>{/if}
                        </div>

                        <!-- 한줄평 -->
                        <div class="rvm-sec">
                            <div class="rvm-flabel">
                                <span class="l">한줄평<span class="req">*</span></span>
                                <span class="r eh-data {over ? 'over' : ''}">{comment.length} / {RV_MAX}</span>
                            </div>
                            <textarea
                                class="rvm-ta"
                                name="comment"
                                bind:value={comment}
                                placeholder="대회에 대한 솔직한 후기를 남겨주세요. 코스·급수·운영 등 다음 러너에게 도움이 될 정보를 사실 위주로. (5–200자)"
                            ></textarea>
                            {#if errors.comment}<p class="rvm-err" role="alert">{errors.comment[0]}</p>{/if}
                        </div>

                        <!-- 작성 회원 -->
                        <div class="rvm-sec">
                            <div class="rvm-flabel">
                                <span class="l">작성 회원</span>
                                <span class="r">이메일 인증 완료</span>
                            </div>
                            <div class="rvm-member">@{reviewerNickname}</div>
                            <p class="rvm-member-note">작성한 리뷰는 회원 계정에 연결되어 대회 후기와 평가에 표시됩니다.</p>
                        </div>

                        <!-- 참가 기록 (필수) -->
                        <div class="rvm-sec">
                            <div class="rvm-flabel">
                                <span class="l">참가 기록<span class="req">*</span></span>
                                <span class="r">리뷰와 함께 등록</span>
                            </div>
                            <p class="rvm-record-note">완주한 종목과 공식 기록을 입력해주세요.</p>

                            <label class="rvm-record-label" for="review-course">종목 / 코스</label>
                            <select
                                id="review-course"
                                class="rvm-text rvm-select"
                                name="course_code"
                                bind:value={courseCode}
                                required
                                aria-invalid={errors.course_code ? 'true' : undefined}
                                aria-describedby={errors.course_code ? 'review-course-error' : undefined}
                            >
                                {#if courseOptions.length > 1}
                                    <option value="" disabled>완주한 종목을 선택해주세요</option>
                                {/if}
                                {#each courseOptions as course, index (`${course.code}-${index}`)}
                                    <option value={course.code}>{course.label}</option>
                                {/each}
                            </select>
                            {#if errors.course_code}
                                <p id="review-course-error" class="rvm-err" role="alert">{errors.course_code[0]}</p>
                            {/if}

                            <fieldset
                                class="rvm-time-field"
                                class:error={!!(errors.time || errors.hours || errors.minutes || errors.seconds || errors.race_record)}
                                aria-describedby={errors.time || errors.hours || errors.minutes || errors.seconds || errors.race_record ? 'review-time-error' : undefined}
                            >
                                <legend class="rvm-record-label">완주 시간</legend>
                                <div class="rvm-time-grid">
                                    <label class="rvm-time-part">
                                        <input
                                            class="rvm-time-input eh-data"
                                            type="number"
                                            name="hours"
                                            min="0"
                                            max="99"
                                            step="1"
                                            inputmode="numeric"
                                            required
                                            bind:value={recordHours}
                                            aria-invalid={errors.hours || errors.time || errors.race_record ? 'true' : undefined}
                                        />
                                        <span>시</span>
                                    </label>
                                    <span class="rvm-time-colon" aria-hidden="true">:</span>
                                    <label class="rvm-time-part">
                                        <input
                                            class="rvm-time-input eh-data"
                                            type="number"
                                            name="minutes"
                                            min="0"
                                            max="59"
                                            step="1"
                                            inputmode="numeric"
                                            required
                                            bind:value={recordMinutes}
                                            aria-invalid={errors.minutes || errors.time || errors.race_record ? 'true' : undefined}
                                        />
                                        <span>분</span>
                                    </label>
                                    <span class="rvm-time-colon" aria-hidden="true">:</span>
                                    <label class="rvm-time-part">
                                        <input
                                            class="rvm-time-input eh-data"
                                            type="number"
                                            name="seconds"
                                            min="0"
                                            max="59"
                                            step="1"
                                            inputmode="numeric"
                                            required
                                            bind:value={recordSeconds}
                                            aria-invalid={errors.seconds || errors.time || errors.race_record ? 'true' : undefined}
                                        />
                                        <span>초</span>
                                    </label>
                                </div>
                                <p class="rvm-record-hint">최소 1초 이상의 기록을 입력해주세요.</p>
                            </fieldset>
                            {#if errors.time || errors.hours || errors.minutes || errors.seconds || errors.race_record}
                                <p id="review-time-error" class="rvm-err" role="alert">
                                    {(errors.time || errors.hours || errors.minutes || errors.seconds || errors.race_record)[0]}
                                </p>
                            {/if}
                        </div>

                        <!-- 추가 정보 (선택) -->
                        <div class="rvm-more">
                            <button type="button" class="rvm-toggle" aria-expanded={showOptional} onclick={() => (showOptional = !showOptional)}>
                                <svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 6 15 12 9 18"></polyline></svg>
                                <span class="t">추가 정보 입력 <span class="opt">(선택)</span></span>
                                {#if moreCount > 0}<span class="h eh-data">{moreCount}개 입력됨</span>{/if}
                            </button>

                            {#if showOptional}
                                <div class="rvm-morebody">
                                    <!-- 코스 난이도 -->
                                    <div class="rvm-sub">
                                        <span class="sl">코스 난이도</span>
                                        <div class="seg3" role="group" aria-label="코스 난이도">
                                            {#each DIFFICULTY_OPTIONS as [val, label] (val)}
                                                <button
                                                    type="button"
                                                    class={courseDifficulty === val ? 'on' : ''}
                                                    onclick={() => (courseDifficulty = courseDifficulty === val ? '' : val)}
                                                >{label}</button>
                                            {/each}
                                        </div>
                                        <input type="hidden" name="course_difficulty" value={courseDifficulty} />
                                    </div>

                                    <!-- 운영 만족도 -->
                                    <div class="rvm-sub">
                                        <span class="sl">운영 만족도</span>
                                        <div class="rv-stars sm" role="group" aria-label="운영 만족도 선택" onmouseleave={() => (operationHover = 0)}>
                                            {#each [1, 2, 3, 4, 5] as n (n)}
                                                <button
                                                    type="button"
                                                    class="rv-star ink {n <= opsLit ? 'on' : ''}"
                                                    onmouseenter={() => (operationHover = n)}
                                                    onclick={() => (operationSatisfaction = operationSatisfaction === n ? 0 : n)}
                                                    aria-label="{n}점"
                                                >
                                                    <svg viewBox="0 0 24 24" fill={n <= opsLit ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"><path d={STAR_PATH}></path></svg>
                                                </button>
                                            {/each}
                                        </div>
                                        <input type="hidden" name="operation_satisfaction" value={operationSatisfaction || ''} />
                                    </div>

                                    <!-- 추천 태그 -->
                                    <div class="rvm-sub">
                                        <span class="sl">추천 태그</span>
                                        <div class="rvm-tags">
                                            {#each RECOMMENDATION_TAGS as tag (tag)}
                                                <button
                                                    type="button"
                                                    class="rvm-tag {selectedTags.includes(tag) ? 'on' : ''}"
                                                    onclick={() => toggleTag(tag)}
                                                >{tag}</button>
                                            {/each}
                                        </div>
                                        {#each selectedTags as tag (tag)}
                                            <input type="hidden" name="recommendation_tags" value={tag} />
                                        {/each}
                                    </div>
                                </div>
                            {/if}
                        </div>

                        {#if errors.review}
                            <div class="rvm-alert" role="alert">! {errors.review[0]}</div>
                        {/if}
                    </div>

                    <div class="rvm-foot">
                        <p class="note">리뷰와 참가 기록이 함께 등록되며, 리뷰는 <b>검수 후 노출</b>됩니다</p>
                        <span style="flex:1"></span>
                        <Button variant="ghost" type="button" onclick={close}>취소</Button>
                        <span class="grow">
                            <Button variant="primary" type="submit" disabled={!canSubmit || isSubmitting} fullWidth>
                                {isSubmitting ? '등록 중…' : '등록하기 →'}
                            </Button>
                        </span>
                    </div>
                </form>
            {/if}
        </div>
    </div>
{/if}

<style>
    .rvm {
        max-width: 600px;
        display: flex;
        flex-direction: column;
        max-height: min(90vh, 800px);
    }
    .rvm-close {
        position: absolute;
        top: 14px;
        right: 14px;
        z-index: 3;
        width: 34px;
        height: 34px;
        border: 0;
        background: transparent;
        color: var(--text-faint);
        font-size: 20px;
        line-height: 1;
        display: grid;
        place-items: center;
        cursor: pointer;
        transition: color var(--dur-fast) var(--ease-out);
    }
    .rvm-close:hover { color: var(--text-strong); }

    .rvm-head {
        padding: 30px 32px 18px;
        border-bottom: var(--border-rule);
    }
    .rvm-head .race {
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.022em;
        line-height: 1.12;
        margin: 11px 0 0;
        padding-right: 28px;
        text-wrap: balance;
        color: var(--text-strong);
    }
    .rvm-head .meta {
        font-size: 12.5px;
        color: var(--text-muted);
        margin: 8px 0 0;
        letter-spacing: 0.01em;
    }

    .rvm-member {
        padding: 12px 14px;
        border: var(--border-rule);
        border-radius: var(--r-2);
        background: var(--paper-50);
        color: var(--text-strong);
        font-weight: 700;
    }
    .rvm-member-note {
        margin: 9px 0 0;
        color: var(--text-muted);
        font-size: 12px;
        line-height: 1.55;
    }

    /* form fills remaining height; scroll body + sticky foot */
    .rvm-form {
        display: flex;
        flex-direction: column;
        flex: 1;
        min-height: 0;
    }
    .rvm-scroll {
        overflow-y: auto;
        overscroll-behavior: contain;
        padding: 4px 32px;
        flex: 1;
    }
    .rvm-sec {
        padding: 24px 0;
        border-bottom: var(--border-hair);
    }
    .rvm-flabel {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 13px;
    }
    .rvm-flabel .l {
        font-size: 14px;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: var(--text-strong);
    }
    .rvm-flabel .l .req { color: var(--accent); font-weight: 800; margin-left: 4px; }
    .rvm-flabel .r { font-size: 11px; color: var(--text-faint); letter-spacing: 0.02em; }
    .rvm-flabel .r.over { color: var(--danger); }

    /* star rating */
    .rv-stars { display: flex; align-items: center; gap: 6px; }
    .rv-star {
        width: 38px;
        height: 38px;
        border: 0;
        background: transparent;
        padding: 0;
        display: grid;
        place-items: center;
        color: var(--line);
        cursor: pointer;
        transition: color var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out);
    }
    .rv-star:active { transform: translateY(1px); }
    .rv-star.on { color: var(--accent); }
    .rv-star.on.ink { color: var(--ink-900); }
    .rv-star svg { width: 100%; height: 100%; }
    .rv-stars.sm .rv-star { width: 30px; height: 30px; }
    .rv-score {
        margin-left: 10px;
        font-size: 13px;
        font-weight: 700;
        color: var(--text-muted);
        letter-spacing: 0.01em;
        align-self: center;
    }
    .rv-score .n {
        font-size: 19px;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: var(--text-strong);
    }
    .rv-score.empty { color: var(--text-faint); font-weight: 600; }

    /* textarea / inputs */
    .rvm-ta {
        width: 100%;
        min-height: 104px;
        resize: vertical;
        border: 1px solid var(--line);
        border-radius: var(--r-2);
        padding: 13px 15px;
        font-size: 14.5px;
        line-height: 1.6;
        color: var(--text-body);
        background: var(--paper-0);
        font-family: inherit;
    }
    .rvm-ta:focus { outline: 0; border-color: var(--ink-900); }
    .rvm-ta::placeholder { color: var(--text-faint); }
    .rvm-text {
        width: 100%;
        border: 1px solid var(--line);
        border-radius: var(--r-2);
        padding: 11px 14px;
        font-size: 14px;
        color: var(--text-body);
        background: var(--paper-0);
        font-family: inherit;
        font-variant-numeric: tabular-nums;
    }
    .rvm-text:focus { outline: 0; border-color: var(--ink-900); }
    .rvm-text::placeholder { color: var(--text-faint); font-variant-numeric: normal; }
    .rvm-select { cursor: pointer; }
    .rvm-text[aria-invalid='true'] { border-color: var(--danger); }

    /* required linked race record */
    .rvm-record-note {
        margin: -4px 0 16px;
        color: var(--text-muted);
        font-size: 12.5px;
        line-height: 1.5;
    }
    .rvm-record-label {
        display: block;
        margin: 0 0 8px;
        color: var(--text-muted);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.01em;
    }
    .rvm-time-field {
        min-width: 0;
        margin: 16px 0 0;
        padding: 0;
        border: 0;
    }
    .rvm-time-grid {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr) auto minmax(0, 1fr);
        align-items: center;
        gap: 8px;
    }
    .rvm-time-part {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: center;
        gap: 7px;
        color: var(--text-muted);
        font-size: 12px;
    }
    .rvm-time-input {
        width: 100%;
        min-width: 0;
        border: 1px solid var(--line);
        border-radius: var(--r-2);
        padding: 11px 8px;
        color: var(--text-strong);
        background: var(--paper-0);
        font-family: inherit;
        font-size: 14px;
        text-align: center;
    }
    .rvm-time-input:focus { outline: 0; border-color: var(--ink-900); }
    .rvm-time-field.error .rvm-time-input { border-color: var(--danger); }
    .rvm-time-colon { color: var(--text-faint); font-weight: 700; }
    .rvm-record-hint {
        margin: 8px 0 0;
        color: var(--text-faint);
        font-size: 11.5px;
    }

    /* collapsible 추가 정보 */
    .rvm-more { border-top: var(--border-hair); }
    .rvm-toggle {
        width: 100%;
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 18px 0;
        border: 0;
        background: transparent;
        text-align: left;
        cursor: pointer;
    }
    .rvm-toggle .chev {
        width: 16px;
        height: 16px;
        color: var(--text-faint);
        transition: transform var(--dur-base) var(--ease-out);
        flex-shrink: 0;
    }
    .rvm-toggle[aria-expanded='true'] .chev { transform: rotate(90deg); }
    .rvm-toggle .t { font-size: 13px; font-weight: 700; color: var(--text-strong); }
    .rvm-toggle .t .opt { color: var(--text-faint); font-weight: 500; }
    .rvm-toggle .h { font-size: 11.5px; color: var(--text-faint); margin-left: auto; letter-spacing: 0.02em; }
    .rvm-morebody { padding-bottom: 4px; }
    .rvm-sub { padding: 16px 0; border-top: var(--border-hair); }
    .rvm-sub:first-child { border-top: 0; padding-top: 4px; }
    .rvm-sub .sl {
        font-size: var(--text-micro);
        font-weight: 700;
        letter-spacing: var(--track-micro);
        text-transform: uppercase;
        color: var(--text-faint);
        display: block;
        margin-bottom: 11px;
    }

    /* 3-way difficulty */
    .seg3 {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        border: 1px solid var(--line);
        border-radius: var(--r-2);
        overflow: hidden;
    }
    .seg3 button {
        border: 0;
        border-left: 1px solid var(--line);
        background: var(--paper-0);
        padding: 11px 8px;
        font-size: 13px;
        font-weight: 600;
        color: var(--text-muted);
        cursor: pointer;
        transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
    }
    .seg3 button:first-child { border-left: 0; }
    .seg3 button:hover { background: var(--paper-50); }
    .seg3 button.on { background: var(--ink-900); color: var(--paper-0); }

    /* recommend tags */
    .rvm-tags { display: flex; flex-wrap: wrap; gap: 7px; }
    .rvm-tag {
        border: 1px solid var(--line);
        border-radius: var(--r-4);
        background: var(--paper-0);
        padding: 7px 13px;
        font-size: 12.5px;
        font-weight: 500;
        color: var(--text-muted);
        cursor: pointer;
        transition: border-color var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out);
    }
    .rvm-tag:hover { border-color: var(--ink-700); color: var(--text-strong); }
    .rvm-tag.on { background: var(--ink-900); border-color: var(--ink-900); color: var(--paper-0); }

    /* inline errors */
    .rvm-err {
        font-size: 13px;
        color: var(--danger);
        margin: 10px 0 0;
    }
    .rvm-alert {
        margin: 4px 0 20px;
        padding: 11px 14px;
        border: 1px solid var(--danger);
        color: var(--danger);
        font-size: 14px;
        background: var(--paper-0);
    }

    /* footer */
    .rvm-foot {
        padding: 16px 32px 22px;
        border-top: var(--border-rule);
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .rvm-foot .note { font-size: 11.5px; color: var(--text-faint); line-height: 1.45; margin: 0; }
    .rvm-foot .note b { color: var(--text-muted); font-weight: 700; }
    .rvm-foot .grow { display: flex; }

    /* state (작성 불가 / 작성 완료) */
    .rvm-state {
        flex: 1;
        padding: 44px 32px;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
    }
    .rvm-state__tag {
        display: inline-block;
        padding: 5px 12px;
        border: 1px solid var(--ink-900);
        font-weight: 700;
        font-size: 12px;
        letter-spacing: 0.04em;
        margin-bottom: 6px;
        color: var(--text-strong);
    }
    .rvm-state__tag--acc { background: var(--accent); border-color: var(--accent); color: #fff; }
    .rvm-state h3 {
        font-size: 18px;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        color: var(--text-strong);
        line-height: 1.35;
    }
    .rvm-state p { font-size: 14px; color: var(--text-muted); margin: 0; }

    @media (max-width: 768px) {
        .rvm { max-height: 92vh; }
        .rvm-head { padding: 26px 22px 16px; }
        .rvm-scroll { padding: 0 22px; }
        .rvm-foot { padding: 14px 22px 20px; }
        .rvm-foot .note { display: none; }
        .rvm-foot .grow { flex: 1; display: flex; }
    }

    @media (max-width: 480px) {
        .rvm { max-width: 100%; max-height: 100vh; }
    }
</style>
