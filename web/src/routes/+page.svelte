<script lang="ts">
    import RaceCard from '$lib/components/arena/RaceCard.svelte';
    import RaceRow from '$lib/components/arena/RaceRow.svelte';
    import type { Race, Post, RecommendationsResponse } from '$lib/types';
    import { formatDistanceToNow } from '$lib/date';
    import { sportLabels } from '$lib/race';

    let { data } = $props();

    const closingSoon = $derived((data.closingSoon as Race[]) ?? []);
    const upcomingRaces = $derived((data.upcomingRaces as Race[]) ?? []);
    const recentlyAdded = $derived((data.recentlyAdded as Race[]) ?? []);
    const recentPosts = $derived((data.recentPosts as Post[]) ?? []);
    const sportCounts = $derived(data.sportCounts ?? {});
    const totalUpcoming = $derived(data.totalUpcoming as number);
    const recommendations = $derived(data.recommendations as RecommendationsResponse | null);

    const closingSoonCount = $derived(closingSoon.length);
    const recentlyAddedCount = $derived(recentlyAdded.length);

    const upcomingTop8 = $derived(upcomingRaces.slice(0, 8));
    const recommendedPicks = $derived((recommendations?.races ?? []).slice(0, 6));

    const sportRows = $derived([
        { key: 'running', label: sportLabels.running, count: sportCounts.running ?? 0, sub: '풀·하프·10K', href: '/running' },
        { key: 'swimming', label: sportLabels.swimming, count: sportCounts.swimming ?? 0, sub: '오픈워터·마스터즈', href: '/swimming' },
        { key: 'cycling', label: sportLabels.cycling, count: sportCounts.cycling ?? 0, sub: '로드·MTB·그란폰도', href: '/cycling' },
        { key: 'triathlon', label: sportLabels.triathlon, count: sportCounts.triathlon ?? 0, sub: '스프린트·올림픽·풀', href: '/triathlon' },
        { key: 'trail_running', label: sportLabels.trail_running, count: (sportCounts as any).trailRunning ?? sportCounts.trail_running ?? 0, sub: '산악·숲길·울트라', href: '/trail-running' },
    ]);

    let appUrl = $derived(data.appUrl || 'https://www.endurohub.kr');

    let websiteSchema = $derived({
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        name: 'endurohub',
        url: appUrl,
        description:
            '국내 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정과 접수 정보를 한곳에서 확인하세요.',
        potentialAction: {
            '@type': 'SearchAction',
            target: `${appUrl}/races?search={search_term_string}`,
            'query-input': 'required name=search_term_string',
        },
    });

    let itemListSchema = $derived({
        '@context': 'https://schema.org',
        '@type': 'ItemList',
        name: '다가오는 대회',
        numberOfItems: upcomingRaces.length,
        itemListElement: upcomingRaces.map((race, index) => ({
            '@type': 'ListItem',
            position: index + 1,
            name: race.title,
            url: race.url,
        })),
    });

    function postCategoryLabel(p: Post): string {
        return p.category?.trim() || '자유';
    }
</script>

<svelte:head>
    <title>엔듀로허브 - 국내 지구력 스포츠 대회 정보 플랫폼</title>
    <meta
        name="description"
        content="엔듀로허브에서 국내 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정과 접수 정보를 한곳에서 확인하세요."
    />
    <meta property="og:title" content="엔듀로허브 - 국내 지구력 스포츠 대회 정보 플랫폼" />
    <meta
        property="og:description"
        content="엔듀로허브에서 국내 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정과 접수 정보를 한곳에서 확인하세요."
    />
    {@html `<script type="application/ld+json">${JSON.stringify(websiteSchema)}</script>`}
    {@html `<script type="application/ld+json">${JSON.stringify(itemListSchema)}</script>`}
</svelte:head>

<main class="wrap">
    <!-- Hero ────────────────────────────────────────── -->
    <section class="home-hero">
        <div>
            <div class="hero-count">
                <span>접수중 <b>{totalUpcoming}</b></span>
                <span class="hero-sep">|</span>
                <span>마감 임박 <b class="urgent">{closingSoonCount}</b></span>
                <span class="hero-sep">|</span>
                <span>최근 추가 <b>{recentlyAddedCount}</b></span>
            </div>
            <h1>
                다음 레이스가<br />
                <em>당신을 기다리고 있습니다.</em>
            </h1>
        </div>
        <!-- <aside class="entry-panel">
            <div class="arena-kicker">두 가지 방식으로 탐색</div>
            <a href="/timeline" class="entry-link">
                <span>타임라인 <span class="entry-sub">→ 내 시즌 보기</span></span>
                <span class="entry-arrow">↗</span>
            </a>
            <a href="/calendar" class="entry-link live">
                <span>캘린더 <span class="entry-sub muted">→ 월간 일정</span></span>
                <span class="entry-arrow">↗</span>
            </a>
            <div class="entry-foot">
                <span>SESSION · {data.user ? 'MEMBER' : 'GUEST'}</span>
                <span>KR · {new Date().toLocaleDateString('en-CA').slice(5).replace('-', '.')}</span>
            </div>
        </aside> -->
    </section>

    <!-- 01 Closing Soon ─────────────────────────────── -->
    {#if closingSoon.length > 0}
        <section class="sec">
            <div class="sec-head">
                <div>
                    <div class="sec-index">01</div>
                    <h2>마감 임박 <span class="sec-suffix urgent">7일 이내</span></h2>
                </div>
                <a href="/races?status=closing_soon&reset=1" class="sec-link">전체 →</a>
            </div>
            <div class="grid-4">
                {#each closingSoon.slice(0, 4) as race, i (race.id)}
                    <RaceCard {race} eager={i < 3} />
                {/each}
            </div>
        </section>
    {/if}
</main>

<!-- 02 Recommended (paper-alt full-bleed) ───────────── -->
{#if recommendedPicks.length > 0}
    <section class="sec sec-bleed">
        <div class="wrap inner-wrap">
            <div class="sec-head">
                <div>
                    <div class="sec-index">02</div>
                    <h2>
                        {recommendations?.type === 'personalized' ? '맞춤 추천' : '인기 대회'}
                        <span class="sec-suffix mono">{recommendations?.type === 'personalized' ? '관심사 기반' : '이번 달'}</span>
                    </h2>
                </div>
            </div>
            <div class="grid-3">
                {#each recommendedPicks as race (race.id)}
                    <RaceCard {race} />
                {/each}
            </div>
        </div>
    </section>
{/if}

<main class="wrap">
    <!-- 03 By Sport ─────────────────────────────────── -->
    <section class="sec">
        <div class="sec-head">
            <div>
                <div class="sec-index">03</div>
                <h2>종목별 대회</h2>
            </div>
        </div>
        <div class="sports-strip">
            {#each sportRows as s (s.key)}
                <a href={s.href} class="sport-tile">
                    <div class="sport-text">
                        <div class="sport-name">{s.label}</div>
                        <div class="sport-sub">{s.sub}</div>
                    </div>
                    <div class="sport-count">{s.count}<small>개 접수중</small></div>
                    <span class="sport-arrow">→</span>
                </a>
            {/each}
        </div>
    </section>

    <!-- 04 Recently Added ──────────────────────────── -->
    {#if recentlyAdded.length > 0}
        <section class="sec">
            <div class="sec-head">
                <div>
                    <div class="sec-index">04</div>
                    <h2>방금 추가된 대회</h2>
                </div>
            </div>
            <div class="grid-4">
                {#each recentlyAdded.slice(0, 8) as race (race.id)}
                    <div class="new-wrap">
                        <div class="new-tag">NEW</div>
                        <RaceCard {race} />
                    </div>
                {/each}
            </div>
        </section>
    {/if}

    <!-- 05 Upcoming (table) ────────────────────────── -->
    {#if upcomingTop8.length > 0}
        <section class="sec">
            <div class="sec-head">
                <div>
                    <div class="sec-index">05</div>
                    <h2>다가오는 대회</h2>
                </div>
                <a href="/calendar" class="sec-link">캘린더에서 보기 →</a>
            </div>
            <div class="upcoming-table">
                <div class="upcoming-thead">
                    <span>접수마감</span>
                    <span>대회명</span>
                    <span>일정</span>
                    <span>종목</span>
                    <span>거리</span>
                    <span>지역</span>
                    <span>참가비</span>
                </div>
                {#each upcomingTop8 as race (race.id)}
                    <RaceRow {race} />
                {/each}
            </div>
        </section>
    {/if}

    <!-- 06 Community ────────────────────────────────── -->
    <section class="sec sec-last">
        <div class="sec-head">
            <div>
                <div class="sec-index">06</div>
                <h2>자유게시판</h2>
            </div>
            <a href="/posts" class="sec-link">전체 글 →</a>
        </div>
        {#if recentPosts.length === 0}
            <div class="empty-card">
                <p>아직 작성된 글이 없습니다.</p>
                <a href="/posts/create" class="arena-btn arena-btn-primary">첫 글 작성하기</a>
            </div>
        {:else}
            <div class="posts">
                {#each recentPosts.slice(0, 6) as post (post.id)}
                    <a class="post" href={`/posts/${post.id}`}>
                        <div class="post-meta">
                            <span>{postCategoryLabel(post)}</span>
                            <span>{formatDistanceToNow(post.createdAt)}</span>
                        </div>
                        <h3 class="post-title">{post.title}</h3>
                        <p class="post-excerpt">{post.contentText}</p>
                        <div class="post-tail">
                            <span>@{post.nickname}</span>
                            <span>💬 {post.commentCount}</span>
                        </div>
                    </a>
                {/each}
            </div>
        {/if}
    </section>
</main>

<style>
    .wrap {
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 24px;
    }
    @media (min-width: 1024px) {
        .wrap {
            padding: 0 32px;
        }
    }

    /* ── Hero ─────────────────────────── */
    /* renamed from .hero to escape daisyUI 5's .hero rule that forces all children into cell 1/1 */
    .home-hero {
        padding: 48px 0 40px;
        display: grid;
        grid-template-columns: 1fr;
        gap: 32px;
        border-bottom: 1px solid var(--arena-line);
    }
    @media (min-width: 1024px) {
        .home-hero {
            grid-template-columns: 1fr;
            gap: 48px;
            padding: 56px 0 40px;
        }
    }
    .home-hero h1 {
        font-family: var(--arena-f-display);
        font-size: clamp(40px, 8vw, 104px);
        font-weight: 700;
        letter-spacing: -3px;
        line-height: 0.92;
        margin: 16px 0 0;
        color: var(--arena-ink);
        text-wrap: balance;
    }
    .home-hero h1 em {
        font-style: normal;
        color: var(--arena-accent-deep);
    }
    .hero-count {
        font-family: var(--arena-f-mono);
        font-size: 12px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: var(--arena-ink-soft);
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }
    .hero-count b {
        color: var(--arena-ink);
        font-weight: 600;
    }
    .hero-count b.urgent {
        color: var(--arena-urgent);
    }
    .hero-sep {
        color: var(--arena-line-soft);
    }
    .entry-panel {
        border: 1px solid var(--arena-line);
        background: var(--arena-paper-alt);
        padding: 24px;
        display: flex;
        flex-direction: column;
        gap: 14px;
        align-self: end;
    }
    .entry-link {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 16px;
        background: var(--arena-paper);
        border: 1px solid var(--arena-line);
        font-family: var(--arena-f-display);
        font-weight: 600;
        font-size: 15px;
        color: var(--arena-ink);
        text-decoration: none;
        transition: all 0.15s;
    }
    .entry-link:hover {
        background: var(--arena-ink);
        color: var(--arena-paper);
    }
    .entry-link.live {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border-color: var(--arena-ink);
    }
    .entry-link.live:hover {
        background: var(--arena-accent);
        color: var(--arena-ink);
        border-color: var(--arena-accent);
    }
    .entry-sub {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        opacity: 0.7;
        margin-left: 8px;
    }
    .entry-sub.muted {
        opacity: 0.6;
    }
    .entry-arrow {
        font-family: var(--arena-f-mono);
    }
    .entry-foot {
        margin-top: 8px;
        padding-top: 14px;
        border-top: 1px solid var(--arena-line-soft);
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.2px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        display: flex;
        justify-content: space-between;
    }

    /* ── Sections ─────────────────────────── */
    .sec {
        padding: 48px 0 36px;
        border-bottom: 1px solid var(--arena-line);
    }
    @media (min-width: 1024px) {
        .sec {
            padding: 56px 0 40px;
        }
    }
    .sec-last {
        border-bottom: none;
    }
    .sec-bleed {
        background: var(--arena-paper-alt);
        padding: 48px 0;
    }
    @media (min-width: 1024px) {
        .sec-bleed {
            padding: 56px 0 48px;
        }
    }
    .inner-wrap {
        padding: 0 24px;
    }
    @media (min-width: 1024px) {
        .inner-wrap {
            padding: 0 32px;
        }
    }
    .sec-head {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        margin-bottom: 24px;
        gap: 16px;
        flex-wrap: wrap;
    }
    .sec-head h2 {
        font-family: var(--arena-f-display);
        font-size: clamp(24px, 3vw, 36px);
        font-weight: 700;
        letter-spacing: -1px;
        margin: 6px 0 0;
        color: var(--arena-ink);
    }
    .sec-index {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 2px;
        color: var(--arena-ink-soft);
    }
    .sec-suffix {
        margin-left: 12px;
        font-size: 14px;
        font-family: var(--arena-f-mono);
        color: var(--arena-ink-soft);
        letter-spacing: 1.5px;
        font-weight: 500;
    }
    .sec-suffix.urgent {
        color: var(--arena-urgent);
        font-size: 18px;
    }
    .sec-link {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
        border-bottom: 1px solid var(--arena-line-soft);
        padding-bottom: 2px;
        text-decoration: none;
    }
    .sec-link:hover {
        color: var(--arena-ink);
        border-color: var(--arena-ink);
    }

    /* ── Grids ─────────────────────────── */
    .grid-4 {
        display: grid;
        grid-template-columns: repeat(1, minmax(0, 1fr));
        gap: 16px;
    }
    @media (min-width: 640px) {
        .grid-4 {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }
    @media (min-width: 1024px) {
        .grid-4 {
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 20px;
        }
    }
    .grid-3 {
        display: grid;
        grid-template-columns: repeat(1, minmax(0, 1fr));
        gap: 16px;
    }
    @media (min-width: 768px) {
        .grid-3 {
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 20px;
        }
    }

    /* ── Sports strip ─────────────────────────── */
    .sports-strip {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        border: 1px solid var(--arena-line);
    }
    @media (min-width: 768px) {
        .sports-strip {
            grid-template-columns: repeat(5, minmax(0, 1fr));
        }
    }
    .sport-tile {
        padding: 24px 20px;
        border-right: 1px solid var(--arena-line);
        border-bottom: 1px solid var(--arena-line);
        background: var(--arena-paper);
        display: flex;
        flex-direction: column;
        gap: 14px;
        min-height: 200px;
        position: relative;
        transition: background 0.15s;
        text-decoration: none;
        color: var(--arena-ink);
    }
    @media (min-width: 768px) {
        .sport-tile {
            padding: 28px 24px;
            border-bottom: none;
            min-height: 220px;
        }
        .sport-tile:last-child {
            border-right: none;
        }
    }
    @media (max-width: 767px) {
        .sports-strip {
            grid-template-columns: 1fr;
        }
        .sport-tile {
            flex-direction: row;
            align-items: center;
            gap: 16px;
            min-height: auto;
            padding: 16px 20px;
            border-right: none;
        }
        .sport-tile:last-child {
            border-bottom: none;
        }
        .sport-text {
            flex: 1;
            min-width: 0;
        }
        .sport-name {
            font-size: 16px;
        }
        .sport-sub {
            font-size: 10px;
            margin-top: 2px;
        }
        .sport-count {
            font-size: 22px;
            letter-spacing: -0.5px;
            margin-top: 0;
            white-space: nowrap;
        }
        .sport-count small {
            font-size: 10px;
        }
        .sport-arrow {
            position: static;
            margin-left: 4px;
        }
    }
    .sport-tile:hover {
        background: var(--arena-paper-alt);
    }
    .sport-tile:hover .sport-arrow {
        transform: translateX(4px);
    }
    .sport-name {
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: 22px;
        letter-spacing: -0.5px;
    }
    .sport-sub {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
    }
    .sport-count {
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: 38px;
        letter-spacing: -1.5px;
        color: var(--arena-ink);
        margin-top: auto;
    }
    .sport-count small {
        font-size: 13px;
        color: var(--arena-ink-soft);
        font-weight: 500;
        margin-left: 4px;
    }
    .sport-arrow {
        position: absolute;
        top: 24px;
        right: 24px;
        font-family: var(--arena-f-mono);
        font-size: 16px;
        transition: transform 0.15s;
    }

    /* ── New badge ─────────────────────────── */
    .new-wrap {
        position: relative;
    }
    .new-tag {
        position: absolute;
        top: -10px;
        left: -1px;
        z-index: 2;
        background: var(--arena-accent);
        color: var(--arena-ink);
        padding: 3px 10px;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1px;
    }

    /* ── Upcoming table ─────────────────────────── */
    .upcoming-table {
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
    }
    .upcoming-thead {
        display: grid;
        grid-template-columns: 56px 1fr 90px 60px 100px 110px 90px;
        gap: 16px;
        padding: 10px 20px;
        background: var(--arena-paper-alt);
        border-bottom: 1px solid var(--arena-line);
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.3px;
        color: var(--arena-ink-soft);
    }
    /* Mobile: hide thead — RaceRow reflows into a 2-line self-describing layout */
    @media (max-width: 879px) {
        .upcoming-thead {
            display: none;
        }
    }

    /* ── Posts ─────────────────────────── */
    .empty-card {
        border: 1px solid var(--arena-line);
        padding: 40px 24px;
        text-align: center;
        background: var(--arena-paper);
    }
    .empty-card p {
        color: var(--arena-ink-soft);
        margin: 0 0 16px;
    }
    .posts {
        display: grid;
        grid-template-columns: repeat(1, minmax(0, 1fr));
        border-top: 1px solid var(--arena-line);
    }
    @media (min-width: 768px) {
        .posts {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .posts .post:nth-child(odd) {
            border-right: 1px solid var(--arena-line-soft);
        }
    }
    @media (min-width: 1024px) {
        .posts {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }
        .posts .post:nth-child(odd) {
            border-right: 1px solid var(--arena-line-soft);
        }
        .posts .post:nth-child(3n) {
            border-right: none !important;
        }
        .posts .post:not(:nth-child(3n)) {
            border-right: 1px solid var(--arena-line-soft);
        }
    }
    .post {
        padding: 20px;
        border-bottom: 1px solid var(--arena-line-soft);
        text-decoration: none;
        color: var(--arena-ink);
        background: var(--arena-paper);
    }
    .post:hover {
        background: var(--arena-paper-alt);
    }
    .post-meta {
        display: flex;
        justify-content: space-between;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.2px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .post-title {
        font-family: var(--arena-f-body);
        font-weight: 600;
        font-size: 15px;
        line-height: 1.4;
        letter-spacing: -0.2px;
        margin: 0 0 8px;
        color: var(--arena-ink);
    }
    .post-excerpt {
        font-size: 12px;
        color: var(--arena-ink-soft);
        line-height: 1.5;
        margin: 0;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .post-tail {
        margin-top: 12px;
        display: flex;
        gap: 12px;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        color: var(--arena-ink-soft);
    }
</style>
