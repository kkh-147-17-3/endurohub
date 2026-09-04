<script lang="ts">
    import { onMount } from 'svelte';
    import { track } from '$lib/analytics';
    import type { Race, SportOption } from '$lib/types';
    import CalendarBoard from '$lib/components/calendar/CalendarBoard.svelte';

    let { data } = $props();

    let appUrl = $derived(data.appUrl || 'https://www.endurohub.kr');

    onMount(() => {
        track('home_view', { year: data.year as number, month: data.month as number });
    });

    let websiteSchema = $derived({
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        name: 'endurohub',
        url: appUrl,
        description:
            '국내 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정과 접수 정보를 한곳에서 확인하세요.',
        potentialAction: {
            '@type': 'SearchAction',
            target: `${appUrl}/races?name={search_term_string}`,
            'query-input': 'required name=search_term_string'
        }
    });
</script>

<svelte:head>
    <title>엔듀로허브 - 국내 지구력 스포츠 대회 캘린더</title>
    <meta
        name="description"
        content="엔듀로허브에서 국내 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정을 캘린더 · 리스트 · 지도로 확인하세요."
    />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="엔듀로허브 - 국내 지구력 스포츠 대회 캘린더" />
    <meta
        property="og:description"
        content="국내 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정을 캘린더 · 리스트 · 지도로 확인하세요."
    />
    <meta property="og:image" content="{appUrl}/images/og-image.png" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta name="twitter:image" content="{appUrl}/images/og-image.png" />
    {@html `<script type="application/ld+json">${JSON.stringify(websiteSchema)}</script>`}
</svelte:head>

<!-- ── Hero (DS: desaturated-cool photo + ink protection gradient, r-0, no shadow) ── -->
<section class="home-hero">
    <picture>
        <source type="image/webp" media="(max-width: 768px)" srcset="/images/home-hero-mobile.webp" />
        <source type="image/webp" srcset="/images/home-hero.webp" />
        <source media="(max-width: 768px)" srcset="/images/home-hero-mobile.jpg" />
        <img
            class="home-hero__img"
            src="/images/home-hero.jpg"
            alt="마라톤, 사이클, 수영, 트레일 러닝, 철인3종 — 다섯 종목의 선수들"
            loading="eager"
            fetchpriority="high"
        />
    </picture>
    <div class="home-hero__ink">
        <div class="v-container home-hero__copy">
            <div class="home-hero__micro eh-data">
                MARATHON · TRAIL · CYCLE · SWIM <span class="sl">/</span> TRIATHLON
            </div>
            <h2 class="home-hero__title">전국의 모든 지구력 대회,<br />한 곳에서.</h2>
        </div>
    </div>
</section>

<CalendarBoard
    year={data.year as number}
    month={data.month as number}
    startOfMonth={data.startOfMonth as string}
    racesGrouped={data.racesGrouped as Record<string, Race[]>}
    previousMonth={data.previousMonth}
    nextMonth={data.nextMonth}
    sports={data.sports as SportOption[]}
    sportFilter={(Array.isArray(data.sport) ? data.sport : data.sport ? [data.sport] : []) as string[]}
    basePath="/calendar"
/>

<style>
    .home-hero {
        position: relative;
        overflow: hidden;
        background: var(--bg-inverse, #101312);
        border-bottom: var(--border-rule);
    }
    .home-hero__img {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center 20%;
        display: block;
        filter: saturate(0.35);
    }
    .home-hero__ink {
        position: relative;
        min-height: clamp(230px, 30vw, 420px);
        display: flex;
        align-items: flex-end;
        background: linear-gradient(transparent 30%, rgba(16, 19, 18, 0.78));
    }
    .home-hero__copy {
        width: 100%;
        padding-bottom: 34px;
    }
    .home-hero__micro {
        color: rgba(255, 255, 255, 0.82);
        font-size: var(--text-micro);
        font-weight: var(--w-strong);
        letter-spacing: var(--track-micro);
        text-transform: uppercase;
    }
    .home-hero__micro .sl {
        color: var(--accent);
    }
    .home-hero__title {
        margin-top: 10px;
        color: #fff;
        font-size: clamp(28px, 3.6vw, 46px);
        font-weight: var(--w-display);
        letter-spacing: var(--track-display);
        line-height: 1.08;
        text-wrap: pretty;
    }
    @media (max-width: 768px) {
        .home-hero__ink {
            min-height: 210px;
        }
        .home-hero__copy {
            padding-bottom: 22px;
        }
    }
</style>
