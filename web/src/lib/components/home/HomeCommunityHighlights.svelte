<script lang="ts">
    import { clientApiFetch } from '$lib/api.client';
    import { SPORT_META, dsSport } from '$lib/components/eh/meta';
    import { formatDate } from '$lib/date';
    import type { HomeRaceRecord, HomeReview, LikeToggleResponse } from '$lib/types';

    let {
        reviews = [],
        records = [],
    }: {
        reviews?: HomeReview[];
        records?: HomeRaceRecord[];
    } = $props();

    const difficultyLabel: Record<string, string> = {
        easy: '쉬움',
        normal: '보통',
        hard: '어려움',
    };

    let likeOverrides = $state<Record<number, { liked: boolean; count: number }>>({});
    let likingId = $state<number | null>(null);

    function starLine(rating: number): string {
        const rounded = Math.max(0, Math.min(5, Math.round(rating)));
        return '★'.repeat(rounded) + '☆'.repeat(5 - rounded);
    }

    function reviewLike(review: HomeReview): { liked: boolean; count: number } {
        return likeOverrides[review.id] ?? { liked: review.hasLiked, count: review.likeCount };
    }

    async function toggleReviewLike(review: HomeReview) {
        if (likingId !== null) return;
        const previous = likeOverrides[review.id];
        const current = reviewLike(review);
        const restore = () => {
            const next = { ...likeOverrides };
            if (previous === undefined) delete next[review.id];
            else next[review.id] = previous;
            likeOverrides = next;
        };

        likeOverrides = {
            ...likeOverrides,
            [review.id]: {
                liked: !current.liked,
                count: Math.max(0, current.count + (current.liked ? -1 : 1)),
            },
        };
        likingId = review.id;

        try {
            const response = await clientApiFetch<LikeToggleResponse>(
                `/races/${review.race.slug}/reviews/${review.id}/like/`,
                { method: 'POST' },
            );
            if (!response.success) {
                restore();
                return;
            }
            likeOverrides = {
                ...likeOverrides,
                [review.id]: { liked: response.liked, count: response.likeCount },
            };
        } catch {
            restore();
        } finally {
            likingId = null;
        }
    }
</script>

<section
    id="recent-reviews"
    class="home-community home-community--reviews"
    aria-labelledby="home-reviews-title"
>
    <div class="home-community__inner">
        <div class="home-community__head">
            <div>
                <div class="eh-micro">
                    <span class="home-community__accent">RUNNER REVIEW</span> · 실제 참가자 후기
                </div>
                <h2 id="home-reviews-title" class="home-community__title">
                    다녀온 러너의 경험이 다음 대회의 기준이 됩니다.
                </h2>
            </div>
            <p class="home-community__intro">
                {#if reviews.length > 0}
                    전체 대회에서 가장 최근에 등록된 공개 리뷰 {reviews.length}건입니다. 일정만으로 알기
                    어려운 코스와 운영의 실제 경험을 확인해보세요.
                {:else}
                    아직 등록된 참가자 리뷰가 없습니다. 완주한 대회에서 첫 경험을 들려주세요.
                {/if}
            </p>
        </div>

        <div class="home-review-stories">
            {#if reviews.length === 0}
                <div class="home-review-stories__empty">
                    <strong>첫 번째 리뷰를 기다리고 있어요.</strong>
                    <span>완주한 대회를 찾아 코스와 운영 경험을 알려주세요.</span>
                </div>
            {:else}
                {#each reviews as review (review.id)}
                    <article class="home-review-story">
                        <p class="home-review-story__quote">“{review.comment}”</p>
                        <div class="home-review-story__event">
                            <a href={`/races/${review.race.slug}#reviews`}>
                                {review.race.title} <span aria-hidden="true">↗</span>
                            </a>
                            {#if review.race.raceDate}
                                <span class="eh-data">{formatDate(review.race.raceDate)}</span>
                            {/if}
                        </div>
                        <div class="home-review-story__footer">
                            <div class="home-review-story__meta">
                                {#if review.completionTime || review.courseDifficulty || review.operationSatisfaction || (review.recommendationTags && review.recommendationTags.length > 0)}
                                    <div class="home-review-story__facts">
                                        {#if review.completionTime}
                                            <span>완주 <b class="eh-data">{review.completionTime}</b></span>
                                        {/if}
                                        {#if review.courseDifficulty && difficultyLabel[review.courseDifficulty]}
                                            <span>난이도 <b>{difficultyLabel[review.courseDifficulty]}</b></span>
                                        {/if}
                                        {#if review.operationSatisfaction}
                                            <span>운영 <b class="eh-data">{review.operationSatisfaction} / 5</b></span>
                                        {/if}
                                        {#if review.recommendationTags && review.recommendationTags.length > 0}
                                            <span>추천 <b>{review.recommendationTags.join(' · ')}</b></span>
                                        {/if}
                                    </div>
                                {/if}
                                <div class="home-review-story__identity">
                                    <span
                                        class="home-review-story__stars"
                                        aria-label={`5점 만점에 ${review.rating}점`}
                                    >
                                        {starLine(review.rating)}
                                    </span>
                                    <div class="home-review-story__byline">
                                        <strong>@{review.nickname}</strong>
                                        <span aria-hidden="true">·</span>
                                        <time class="eh-data" datetime={review.createdAt}>
                                            {formatDate(review.createdAt.split('T')[0])}
                                        </time>
                                    </div>
                                </div>
                            </div>
                            <button
                                type="button"
                                class="home-review-story__like"
                                class:home-review-story__like--on={reviewLike(review).liked}
                                onclick={() => toggleReviewLike(review)}
                                disabled={likingId === review.id}
                                aria-pressed={reviewLike(review).liked}
                                aria-label={`${review.nickname}님의 리뷰에 ${reviewLike(review).liked ? '공감 취소' : '공감'}, 현재 ${reviewLike(review).count}명`}
                            >
                                <svg viewBox="0 0 24 24" aria-hidden="true">
                                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78Z" />
                                </svg>
                                <span class="home-sr-only" aria-live="polite">
                                    공감 {reviewLike(review).count}명
                                </span>
                            </button>
                        </div>
                    </article>
                {/each}
            {/if}
        </div>

        <div class="home-review-prompt">
            <p>
                완주한 대회가 있나요?
                <span>당신의 경험이 다음 참가자에게 더 정확한 기준이 됩니다.</span>
            </p>
            <a class="home-review-prompt__action" href="/races">리뷰 남길 대회 찾기 →</a>
        </div>
    </div>
</section>

<section
    id="recent-records"
    class="home-community home-community--records"
    aria-labelledby="home-records-title"
>
    <div class="home-community__inner">
        <div class="home-community__head home-community__head--records">
            <div>
                <div class="eh-micro">
                    <span class="home-community__accent">MEMBER FINISHES</span> · 회원 완주 기록
                </div>
                <h2
                    id="home-records-title"
                    class="home-community__title home-community__title--records"
                >
                    회원이 직접 남긴 완주 기록.
                </h2>
            </div>
            <p class="home-community__intro home-community__intro--records">
                {#if records.length > 0}
                    회원이 직접 등록하고 공개한 최신 완주 기록 {records.length}건입니다. 종목별 완주
                    시간과 평균 페이스·속도를 확인해보세요.
                {:else}
                    아직 공개된 완주 기록이 없습니다. 시즌 탭에서 첫 기록을 남겨보세요.
                {/if}
            </p>
        </div>

        <div class="home-member-records" aria-label={`최근 회원 완주 기록 ${records.length}건`}>
            <div class="home-member-records__columns" aria-hidden="true">
                <span>러너</span>
                <span>대회 · 종목</span>
                <span>완주 기록</span>
                <span>평균 페이스 · 속도</span>
            </div>
            <div class="home-member-records__list">
                {#if records.length === 0}
                    <div class="home-member-records__empty">
                        <strong>아직 등록된 기록이 없습니다.</strong>
                        <span>시즌 탭에서 완주 기록을 남기면 공개 설정한 기록이 여기에 표시됩니다.</span>
                        <a href="/timeline">시즌 탭에서 입력 →</a>
                    </div>
                {:else}
                    {#each records as record, index (record.id)}
                        {@const sportMeta = SPORT_META[dsSport(record.sport)]}
                        <article class="home-member-record" class:home-member-record--me={record.me}>
                            <div class="home-member-record__runner">
                                <span class="home-member-record__number eh-data" aria-hidden="true">
                                    {String(index + 1).padStart(2, '0')}
                                </span>
                                <strong>@{record.nickname}</strong>
                                {#if record.me}
                                    <span class="home-member-record__mine">MY RECORD</span>
                                {/if}
                            </div>
                            <div class="home-member-record__race">
                                <a href={`/races/${record.race.slug}#records`}>
                                    {record.race.title} <span aria-hidden="true">↗</span>
                                </a>
                                <span>
                                    <i style={`--record-sport:${sportMeta.color}`} aria-hidden="true"></i>
                                    {sportMeta.ko} · {record.courseLabel}{record.race.raceDate ? ` · ${formatDate(record.race.raceDate)}` : ''}
                                </span>
                            </div>
                            <div class="home-member-record__metric" data-label="완주 기록">
                                <strong class="eh-data">{record.time}</strong>
                            </div>
                            <div class="home-member-record__metric" data-label={record.metricLabel}>
                                <strong class="eh-data">{record.metricValue}</strong>
                            </div>
                        </article>
                    {/each}
                {/if}
            </div>
            <div class="home-member-records__foot">
                <span><strong>회원 직접 등록</strong> · 공식 기록과 다를 수 있습니다.</span>
                <span>회원이 공개로 설정하고 대회에 연결한 기록만 표시됩니다. <a href="/timeline">내 기록 입력하기</a></span>
            </div>
        </div>
    </div>
</section>

<style>
    .home-community__inner {
        width: 100%;
        max-width: var(--container-max);
        margin: 0 auto;
        padding-inline: var(--container-pad);
    }
    .home-community--reviews {
        padding: 72px 0 80px;
        border-top: var(--border-rule);
        border-bottom: var(--border-hair);
        background: var(--paper-50);
    }
    .home-community__head {
        display: grid;
        grid-template-columns: minmax(0, 1.15fr) minmax(280px, 0.85fr);
        gap: clamp(32px, 5vw, 72px);
        align-items: end;
    }
    .home-community__accent {
        color: var(--text-accent);
    }
    .home-community__title {
        max-width: 790px;
        margin: 10px 0 0;
        color: var(--text-strong);
        font-size: clamp(34px, 3.4vw, 50px);
        font-weight: 800;
        letter-spacing: -0.04em;
        line-height: 1.06;
        text-wrap: balance;
    }
    .home-community__intro {
        max-width: 48ch;
        margin: 0 0 4px auto;
        color: var(--text-muted);
        font-size: 15px;
        line-height: 1.75;
    }
    .home-review-stories {
        margin-top: 40px;
        border-top: var(--border-rule);
        border-bottom: var(--border-rule);
        background: var(--paper-0);
    }
    .home-review-story + .home-review-story {
        border-top: var(--border-hair);
    }
    .home-review-story {
        display: flex;
        min-width: 0;
        flex-direction: column;
        gap: 18px;
        padding: 28px 24px;
    }
    .home-review-story__quote {
        max-width: 940px;
        margin: 0;
        color: var(--text-strong);
        font-size: clamp(19px, 1.8vw, 26px);
        font-weight: 700;
        letter-spacing: -0.025em;
        line-height: 1.38;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
        text-wrap: pretty;
    }
    .home-review-story__event {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 4px 12px;
    }
    .home-review-story__event a,
    .home-member-record__race a {
        color: var(--text-strong);
        font-weight: 750;
        text-underline-offset: 4px;
    }
    .home-review-story__event a {
        display: inline-flex;
        min-height: 44px;
        max-width: 100%;
        align-items: center;
        margin: -9px 0 -9px -8px;
        padding: 0 8px;
        font-size: 14px;
        line-height: 1.35;
    }
    .home-review-story__event a:hover,
    .home-member-record__race a:hover {
        background: var(--paper-100);
    }
    .home-review-story__event > span {
        margin-left: auto;
        color: var(--text-muted);
        font-size: 11px;
    }
    .home-review-story__footer {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 20px;
    }
    .home-review-story__meta {
        display: flex;
        min-width: 0;
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
    }
    .home-review-story__facts {
        display: flex;
        flex-wrap: wrap;
        gap: 7px 14px;
        color: var(--text-muted);
        font-size: 11px;
    }
    .home-review-story__facts b {
        color: var(--text-strong);
        font-weight: 700;
    }
    .home-review-story__identity {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 10px 14px;
    }
    .home-review-story__stars {
        color: var(--caution);
        font-size: 13px;
        letter-spacing: 0.14em;
        white-space: nowrap;
    }
    .home-review-story__byline {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 4px 8px;
        color: var(--text-muted);
        font-size: 12px;
    }
    .home-review-story__byline strong {
        color: var(--text-strong);
        font-weight: 700;
    }
    .home-review-story__like {
        display: inline-grid;
        width: 44px;
        height: 44px;
        flex: 0 0 44px;
        place-items: center;
        padding: 0;
        border: 0;
        border-radius: 50%;
        color: var(--text-muted);
        background: transparent;
        cursor: pointer;
        transition: color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out);
    }
    .home-review-story__like svg {
        width: 19px;
        height: 19px;
        overflow: visible;
        fill: transparent;
        stroke: currentColor;
        stroke-linecap: round;
        stroke-linejoin: round;
        stroke-width: 1.8;
        transition: fill 0.16s var(--ease-out), transform 0.16s var(--ease-out);
    }
    .home-review-story__like:hover:not(:disabled) {
        color: var(--text-strong);
        background: var(--paper-100);
    }
    .home-review-story__like:hover:not(:disabled) svg {
        transform: scale(1.08);
    }
    .home-review-story__like--on {
        color: var(--positive);
        background: var(--positive-bg);
    }
    .home-review-story__like--on svg {
        fill: currentColor;
    }
    .home-review-story__like:disabled {
        cursor: default;
        opacity: 0.6;
    }
    .home-review-stories__empty {
        display: flex;
        min-height: 180px;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        gap: 5px;
        padding: 36px 24px;
        text-align: center;
    }
    .home-review-stories__empty strong {
        color: var(--text-strong);
        font-size: 21px;
        letter-spacing: -0.02em;
    }
    .home-review-stories__empty span {
        color: var(--text-muted);
        font-size: 14px;
    }
    .home-review-prompt {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 28px;
        padding: 24px 28px;
        border-right: 1px solid var(--ink-900);
        border-bottom: 1px solid var(--ink-900);
        border-left: 1px solid var(--ink-900);
        color: var(--paper-0);
        background: var(--ink-900);
    }
    .home-review-prompt p {
        margin: 0;
        font-size: 15px;
        font-weight: 600;
    }
    .home-review-prompt p span {
        color: var(--ink-300);
        font-weight: 500;
    }
    .home-review-prompt__action {
        display: inline-flex;
        min-height: 44px;
        flex: none;
        align-items: center;
        justify-content: center;
        padding: 0 18px;
        border: 1px solid var(--accent);
        border-radius: var(--r-1);
        color: #101312;
        background: var(--accent);
        font-size: 13px;
        font-weight: 700;
        text-decoration: none;
        transition: color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
    }
    .home-review-prompt__action:hover {
        border-color: var(--paper-0);
        color: var(--ink-900);
        background: var(--paper-0);
    }
    .home-community--records {
        padding: 68px 0 80px;
        border-bottom: var(--border-hair);
        background: var(--paper-0);
    }
    :global(.eh-main:has(.home-community--records) + .v-footer) {
        margin-top: 0;
    }
    .home-community__head--records {
        grid-template-columns: minmax(0, 1fr) minmax(300px, 0.72fr);
        margin-bottom: 30px;
    }
    .home-community__title--records {
        max-width: 720px;
        font-size: clamp(30px, 2.8vw, 42px);
        letter-spacing: -0.035em;
        line-height: 1.08;
    }
    .home-community__intro--records {
        max-width: 44ch;
        margin-bottom: 3px;
        font-size: 14px;
        line-height: 1.7;
    }
    .home-member-records {
        border: 1px solid var(--ink-900);
        border-top: var(--border-rule);
        background: var(--paper-0);
    }
    .home-member-records__columns,
    .home-member-record {
        display: grid;
        grid-template-columns: minmax(150px, 0.75fr) minmax(280px, 1.4fr) 170px 130px;
    }
    .home-member-records__columns {
        min-height: 42px;
        align-items: center;
        border-bottom: 1px solid var(--ink-900);
        background: var(--paper-50);
    }
    .home-member-records__columns span {
        padding: 0 18px;
        color: var(--text-muted);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.09em;
        text-transform: uppercase;
    }
    .home-member-record {
        min-height: 94px;
        align-items: center;
        border-bottom: var(--border-hair);
        transition: background var(--dur-fast) var(--ease-out);
    }
    .home-member-record:last-child {
        border-bottom: 0;
    }
    .home-member-record:hover,
    .home-member-record--me {
        background: var(--paper-50);
    }
    .home-member-record--me {
        box-shadow: inset 3px 0 0 var(--accent);
    }
    .home-member-record > div {
        min-width: 0;
        padding: 18px;
    }
    .home-member-record__runner {
        display: grid;
        grid-template-columns: 28px minmax(0, 1fr);
        gap: 4px 10px;
        align-items: center;
    }
    .home-member-record__number {
        color: var(--text-faint);
        font-size: 11px;
        font-weight: 700;
    }
    .home-member-record__runner strong {
        overflow: hidden;
        color: var(--text-strong);
        font-size: 14px;
        font-weight: 750;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .home-member-record__mine {
        grid-column: 2;
        color: var(--text-accent);
        font-size: 9px;
        font-weight: 800;
        letter-spacing: 0.09em;
    }
    .home-member-record__race {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 2px;
    }
    .home-member-record__race a {
        display: inline-flex;
        min-height: 44px;
        max-width: 100%;
        align-items: center;
        margin: -8px 0 -8px -8px;
        padding: 0 8px;
        overflow: hidden;
        font-size: 14px;
        line-height: 1.35;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .home-member-record__race > span {
        display: flex;
        max-width: 100%;
        align-items: center;
        gap: 7px;
        overflow: hidden;
        color: var(--text-muted);
        font-size: 11px;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .home-member-record__race i {
        width: 6px;
        height: 6px;
        flex: none;
        border-radius: 50%;
        background: var(--record-sport);
    }
    .home-member-record__metric {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 2px;
    }
    .home-member-record__metric::before {
        display: none;
        content: attr(data-label);
        color: var(--text-muted);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.08em;
    }
    .home-member-record__metric strong {
        color: var(--text-strong);
        font-size: 18px;
        font-weight: 800;
        letter-spacing: -0.015em;
        line-height: 1.2;
        white-space: nowrap;
    }
    .home-member-records__foot {
        display: flex;
        min-height: 48px;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
        padding: 10px 18px;
        border-top: var(--border-hair);
        color: var(--text-muted);
        background: var(--paper-50);
        font-size: 11px;
        line-height: 1.5;
    }
    .home-member-records__foot strong,
    .home-member-records__foot a,
    .home-member-records__empty a {
        color: var(--text-strong);
        font-weight: 700;
        text-underline-offset: 3px;
    }
    .home-member-records__empty {
        display: flex;
        min-height: 190px;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        gap: 5px;
        padding: 36px 24px;
        text-align: center;
    }
    .home-member-records__empty > strong {
        color: var(--text-strong);
        font-size: 18px;
    }
    .home-member-records__empty > span {
        color: var(--text-muted);
        font-size: 13px;
    }
    .home-member-records__empty > a {
        min-height: 36px;
        margin-top: 12px;
        padding: 7px 4px;
        font-size: 12px;
    }
    .home-sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }

    @media (max-width: 820px) {
        .home-member-records__columns {
            display: none;
        }
        .home-member-record {
            min-height: 0;
            grid-template-columns: 1fr 1fr;
            gap: 18px 20px;
            padding: 22px 20px;
        }
        .home-member-record > div {
            padding: 0;
        }
        .home-member-record__runner,
        .home-member-record__race {
            grid-column: 1 / -1;
        }
        .home-member-record__race {
            padding-bottom: 14px !important;
            border-bottom: var(--border-hair);
        }
        .home-member-record__runner strong {
            white-space: normal;
        }
        .home-member-record__metric::before {
            display: block;
        }
        .home-member-records__foot {
            align-items: flex-start;
            flex-direction: column;
            gap: 5px;
            padding: 14px 20px;
        }
    }

    @media (max-width: 768px) {
        .home-community__inner {
            padding-inline: var(--container-pad-mobile);
        }
        .home-community--reviews {
            padding: 52px 0 56px;
        }
        .home-community__head,
        .home-community__head--records {
            grid-template-columns: 1fr;
            gap: 20px;
        }
        .home-community__title {
            font-size: 34px;
        }
        .home-community__intro,
        .home-community__intro--records {
            margin: 0;
        }
        .home-review-stories {
            margin-top: 30px;
        }
        .home-review-story {
            padding: 26px 20px;
        }
        .home-review-story__quote {
            font-size: 23px;
        }
        .home-review-story__event {
            align-items: flex-start;
        }
        .home-review-story__event > span {
            width: 100%;
            margin-left: 0;
        }
        .home-review-prompt {
            align-items: flex-start;
            flex-direction: column;
            padding: 22px 20px;
        }
        .home-review-prompt__action {
            width: 100%;
        }
        .home-community--records {
            padding: 50px 0 56px;
        }
        .home-community__head--records {
            gap: 16px;
            margin-bottom: 24px;
        }
        .home-community__title--records {
            font-size: 32px;
        }
    }
</style>
