<script lang="ts" module>
    declare const Kakao: any;
    declare const kakao: any;
</script>

<script lang="ts">
    import { page } from '$app/stores';
    import { goto } from '$app/navigation';
    import RaceCard from '$lib/components/arena/RaceCard.svelte';
    import ReviewForm from '$lib/components/ReviewForm.svelte';
    import type { Race, Review, ReviewStats, Post, Distance, FavoriteToggleResponse } from '$lib/types';
    import { formatDateFull, formatDateDay, formatDateShort, formatDateSlash, formatDistanceToNow } from '$lib/date';
    import {
        arenaDday,
        arenaDdayLabel,
        arenaFeeFull,
        arenaFeeRange,
        arenaFeeShort,
        arenaSportCode,
    } from '$lib/arena';
    import { track, trackOutboundClick } from '$lib/analytics';
    import { clientApiFetch } from '$lib/api.client';

    let { data } = $props();

    interface RaceSlot {
        label: string;
        races: Race[];
    }

    const race: Race = $derived(data.race);
    const relatedRaceSlots: RaceSlot[] = $derived((data.relatedRaces as unknown as RaceSlot[]) || []);
    const relatedPosts: Post[] = $derived(data.relatedPosts);
    const reviews: Review[] = $derived(data.reviews);
    const reviewStats: ReviewStats = $derived(data.reviewStats);
    const hasReviewed: boolean = $derived(data.hasReviewed);

    const appUrl = $derived(data.appUrl || 'https://www.endurohub.kr');
    const kakaoJsKey = $derived(data.kakaoJsKey as string);
    const isAdmin: boolean = $derived(data.isAdmin ?? false);
    const pageUrl = $derived(`${appUrl}${$page.url.pathname}`);

    const sportCode = $derived(arenaSportCode[race.sport]);
    const dday = $derived(arenaDday(race));
    const ddayLabel = $derived(arenaDdayLabel(race));
    const feeRange = $derived(arenaFeeRange(race));
    const feeRangeLabel = $derived(
        feeRange.min == null
            ? '—'
            : feeRange.min === feeRange.max
                ? arenaFeeShort(feeRange.min)
                : `${arenaFeeShort(feeRange.min)} – ${arenaFeeShort(feeRange.max)}`,
    );
    const courseCodes = $derived(
        (race.distances ?? [])
            .map((d) => (typeof d === 'string' ? d : d.name))
            .slice(0, 4)
            .join(' · '),
    );

    const distanceList = $derived((race.distances ?? []) as Distance[]);
    const hasFee = $derived(distanceList.some((d) => d.fee));
    const hasCutoff = $derived(distanceList.some((d) => d.cutoff));
    const hasDistanceStart = $derived(distanceList.some((d) => d.start_time));

    function isValidUrl(url: string | null | undefined): url is string {
        if (!url) return false;
        try {
            const u = new URL(url);
            return (u.protocol === 'http:' || u.protocol === 'https:') && u.hostname.includes('.');
        } catch {
            return false;
        }
    }
    const validOfficialUrl = $derived(isValidUrl(race.officialUrl) ? race.officialUrl : null);

    const distanceNames = $derived(
        race.distances
            ? race.distances
                  .slice(0, 3)
                  .map((d) => (typeof d === 'string' ? d : d.name))
                  .join(', ')
            : '',
    );

    const metaDesc = $derived(() => {
        let desc = `${race.title} - ${race.raceDate ? formatDateFull(race.raceDate) : ''} ${race.location}에서 개최되는 ${race.sportLabel} 대회입니다.`;
        if (distanceNames) desc += ` 참가 종목: ${distanceNames}.`;
        if (race.status === 'registration_open') desc += ' 지금 접수 중!';
        desc += ' 엔듀로허브에서 대회 정보를 확인하세요.';
        return desc.substring(0, 160);
    });

    const ogImage = $derived(race.imageSrc || `/images/og-${race.sport.replace('_', '-')}.png`);

    let modalOpen = $state(false);
    let modalImageSrc = $state('');
    let modalImageAlt = $state('');
    let shareModalOpen = $state(false);
    let reviewModalOpen = $state(false);

    let favoriteOverride = $state<boolean | null>(null);
    const isFavorited = $derived(favoriteOverride ?? race.isFavorited);
    let isTogglingFavorite = $state(false);

    $effect(() => {
        race.slug;
        modalOpen = false;
        shareModalOpen = false;
        reviewModalOpen = false;
        favoriteOverride = null;
    });

    async function toggleFavorite() {
        if (isTogglingFavorite) return;
        if (!$page.data.user) {
            goto(`/auth/login?next=${encodeURIComponent($page.url.pathname)}`);
            return;
        }
        const prevOverride = favoriteOverride;
        const nextValue = !isFavorited;
        favoriteOverride = nextValue;
        isTogglingFavorite = true;
        try {
            const res = await clientApiFetch<FavoriteToggleResponse>(
                `/races/${race.slug}/favorite/`,
                { method: 'POST' },
            );
            if (res.success) favoriteOverride = res.favorited;
            else favoriteOverride = prevOverride;
        } catch {
            favoriteOverride = prevOverride;
        } finally {
            isTogglingFavorite = false;
        }
    }

    function openImageModal(src: string, alt: string = '') {
        modalImageSrc = src;
        modalImageAlt = alt || `${race.title} 이미지`;
        modalOpen = true;
    }

    function closeImageModal() {
        modalOpen = false;
    }
    function openShareModal() {
        shareModalOpen = true;
    }
    function closeShareModal() {
        shareModalOpen = false;
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Escape') {
            if (reviewModalOpen) reviewModalOpen = false;
            else if (shareModalOpen) closeShareModal();
            else if (modalOpen) closeImageModal();
        }
    }

    function handleRegisterClick(position: 'desktop' | 'mobile') {
        if (race.status === 'registration_open') {
            track('register_click', {
                race_slug: race.slug,
                race_title: race.title,
                race_sport: race.sport,
                position,
            });
        }
        if (validOfficialUrl) {
            trackOutboundClick(validOfficialUrl, race.title);
        }
    }

    function copyLink() {
        navigator.clipboard.writeText(window.location.href).then(() => {
            showToast('링크가 복사되었습니다.');
        });
        track('share', { method: 'copy_link', race_slug: race.slug });
    }

    function showToast(message: string) {
        const toast = document.createElement('div');
        toast.style.cssText =
            'position:fixed;top:24px;left:50%;transform:translateX(-50%);background:var(--arena-ink);color:var(--arena-paper);padding:10px 18px;font-family:var(--arena-f-mono);font-size:12px;letter-spacing:1px;z-index:200;border:1px solid var(--arena-ink);';
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2500);
    }

    function shareKakao() {
        if (typeof Kakao !== 'undefined' && Kakao.isInitialized()) {
            Kakao.Share.sendDefault({
                objectType: 'feed',
                content: {
                    title: race.title,
                    description: `${race.raceDate ? formatDateFull(race.raceDate) : ''} ${race.location}`,
                    imageUrl: race.imageSrc || '',
                    link: { webUrl: window.location.href, mobileWebUrl: window.location.href },
                },
            });
            track('share', { method: 'kakao', race_slug: race.slug });
            return;
        }
        if (typeof navigator !== 'undefined' && navigator.share) {
            navigator.share({
                title: race.title,
                text: `${race.title}${race.raceDate ? ' · ' + formatDateFull(race.raceDate) : ''}`,
                url: window.location.href,
            }).then(() => {
                track('share', { method: 'web_share', race_slug: race.slug });
            }).catch(() => {});
            return;
        }
        copyLink();
        showToast('카카오 공유를 사용할 수 없어 링크를 복사했습니다.');
    }

    const defaultImage = $derived(`${appUrl}/images/og-${race.sport.replace('_', '-')}.png`);
    const eventSchema = $derived({
        '@context': 'https://schema.org',
        '@type': 'SportsEvent',
        name: race.title,
        description: race.description
            ? race.description.substring(0, 200)
            : `${race.title} - ${race.location}에서 개최되는 ${race.sportLabel} 대회`,
        startDate: race.raceDate,
        endDate: race.raceEndDate || race.raceDate,
        eventStatus:
            race.status === 'finished'
                ? 'https://schema.org/EventCancelled'
                : 'https://schema.org/EventScheduled',
        eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode',
        url: pageUrl,
        sport: race.sportLabel,
        location: {
            '@type': 'Place',
            name: race.location,
            address: {
                '@type': 'PostalAddress',
                addressLocality: race.location,
                addressRegion: race.region,
                addressCountry: 'KR',
            },
            geo:
                race.latitude && race.longitude
                    ? {
                          '@type': 'GeoCoordinates',
                          latitude: race.latitude,
                          longitude: race.longitude,
                      }
                    : undefined,
        },
        image: race.imageSrc || defaultImage,
        sameAs: validOfficialUrl || undefined,
        offers: {
            '@type': 'Offer',
            url: validOfficialUrl || pageUrl,
            availability:
                race.status === 'registration_open'
                    ? 'https://schema.org/InStock'
                    : 'https://schema.org/SoldOut',
            price: race.distances?.length
                ? String(
                      Math.min(
                          ...race.distances
                              .filter((d) => typeof d !== 'string' && d.fee)
                              .map((d) => Number((d as Distance).fee))
                              .filter((n) => !isNaN(n) && n > 0),
                      ) || 0,
                  )
                : '0',
            priceCurrency: 'KRW',
            validFrom: race.registrationStart || race.raceDate,
        },
        performer: { '@type': 'SportsTeam', name: race.organizer || '대회 주최측' },
        organizer: {
            '@type': 'Organization',
            name: race.organizer || 'endurohub',
            url: validOfficialUrl || appUrl,
        },
    });

    const breadcrumbSchema = $derived({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        itemListElement: [
            { '@type': 'ListItem', position: 1, name: '홈', item: appUrl },
            { '@type': 'ListItem', position: 2, name: '대회 목록', item: `${appUrl}/races` },
            { '@type': 'ListItem', position: 3, name: race.title, item: pageUrl },
        ],
    });

    function initMap(lat: number | null, lng: number | null, locationName: string) {
        kakao.maps.load(() => {
            const container = document.getElementById('arena-kakao-map');
            if (container) {
                const position = new kakao.maps.LatLng(lat, lng);
                const map = new kakao.maps.Map(container, { center: position, level: 5 });
                const marker = new kakao.maps.Marker({ position, map });
                const infowindow = new kakao.maps.InfoWindow({
                    content: `<div style="padding:8px 12px;font-size:13px;font-weight:500;">${locationName}</div>`,
                });
                infowindow.open(map, marker);
            }
        });
    }

    $effect(() => {
        const lat = race.latitude;
        const lng = race.longitude;
        const loc = race.location;
        if (lat && lng && loc && kakaoJsKey) {
            if (typeof kakao !== 'undefined' && kakao.maps) {
                requestAnimationFrame(() => initMap(lat, lng, loc));
            } else if (!document.querySelector('script[src*="dapi.kakao.com"]')) {
                const script = document.createElement('script');
                script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${kakaoJsKey}&autoload=false`;
                script.onload = () => initMap(lat, lng, loc);
                document.head.appendChild(script);
            }
        }
    });

    const statusLabelEn = $derived(
        race.status === 'registration_open'
            ? '진행중'
            : race.status === 'registration_closed'
                ? '마감'
                : race.status === 'finished'
                    ? '종료'
                    : '예정',
    );

    type TimelineStatus = 'done' | 'now' | 'upcoming';
    const timelineStatusLabel: Record<TimelineStatus, string> = {
        done: '완료',
        now: '진행중',
        upcoming: '예정',
    };
    function timelineStatus(start: string | null | undefined, end?: string | null): TimelineStatus {
        if (!start) return 'upcoming';
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const startD = new Date(start);
        startD.setHours(0, 0, 0, 0);
        if (Number.isNaN(startD.getTime())) return 'upcoming';
        if (end) {
            const endD = new Date(end);
            endD.setHours(0, 0, 0, 0);
            if (Number.isNaN(endD.getTime())) {
                if (today < startD) return 'upcoming';
                if (today > startD) return 'done';
                return 'now';
            }
            if (today < startD) return 'upcoming';
            if (today > endD) return 'done';
            return 'now';
        }
        if (today < startD) return 'upcoming';
        if (today > startD) return 'done';
        return 'now';
    }

    function reviewStarLine(rating: number): string {
        const r = Math.max(0, Math.min(5, Math.round(rating)));
        return '★'.repeat(r) + '☆'.repeat(5 - r);
    }
    const difficultyLabel: Record<string, string> = {
        easy: '쉬움',
        normal: '보통',
        hard: '어려움',
    };
    function reviewYear(iso: string): string {
        const m = /^(\d{4})/.exec(iso ?? '');
        return m ? m[1] : '';
    }

    const atAGlanceLabels: Record<string, { surface: string; difficulty: string; aid: string }> = {
        running: { surface: '노면', difficulty: '코스 난이도', aid: '급수대' },
        trail_running: { surface: '지형', difficulty: '난이도/고도', aid: '보급소' },
    };
    const atAGlance = $derived(atAGlanceLabels[race.sport]);
    const showAtAGlance = $derived(!!atAGlance);

    const sections = $derived.by(() => {
        const list: { id: string; label: string; show: boolean }[] = [];
        list.push({ id: 'overview', label: '개요', show: true });
        list.push({ id: 'courses', label: '종목 · 참가비', show: distanceList.length > 0 });
        list.push({ id: 'course-map', label: '코스 지도', show: !!race.courseImageSrcs?.length });
        list.push({ id: 'location', label: '위치', show: !!(race.latitude && race.longitude) });
        list.push({ id: 'timeline', label: '타임라인', show: !!(race.registrationStart || race.registrationEnd || race.raceDate) });
        list.push({ id: 'includes', label: '구성품', show: !!race.giveaways?.length || !!race.giveawayImageSrcs?.length });
        list.push({ id: 'reviews', label: '후기', show: true });
        list.push({ id: 'related', label: '연관 대회', show: relatedRaceSlots.some((s) => s.races.length > 0) });
        list.push({ id: 'recap', label: '리캡', show: !!race.recapUrl });
        list.push({ id: 'posts', label: '게시글', show: (relatedPosts?.length ?? 0) > 0 });
        return list.filter((s) => s.show).map((s, i) => ({ ...s, n: String(i).padStart(2, '0') }));
    });
    function secN(id: string): string {
        return sections.find((s) => s.id === id)?.n ?? '00';
    }
</script>

<svelte:window onkeydown={handleKeydown} />

<svelte:head>
    <title
        >{race.title} | {race.raceDate ? formatDateFull(race.raceDate) : ''} {race.sportLabel} - 엔듀로허브</title
    >
    <meta name="description" content={metaDesc()} />
    <meta property="og:title" content={race.title} />
    <meta property="og:description" content={metaDesc()} />
    <meta property="og:image" content={ogImage} />
    {@html `<script type="application/ld+json">${JSON.stringify(eventSchema)}</script>`}
    {@html `<script type="application/ld+json">${JSON.stringify(breadcrumbSchema)}</script>`}
</svelte:head>

<div class="arena-detail">
    <!-- ── TOP MONO BAND ────────────────────────── -->
    <div class="detail-head">
        <div class="head-inner">
            <span class="bread-mono">
                <a href="/" class="bm-item">대회</a>
                <span class="sep">/</span>
                <a href="/races" class="bm-item">{race.sportLabel}</a>
                <span class="sep bm-slug-sep">/</span>
                <span class="ellipsis-inline bm-slug">{race.slug}</span>
            </span>
            <span class="bread-meta">
                {#if race.updatedAt}<span class="bm-meta-prefix">마지막 업데이트 : </span>{formatDistanceToNow(race.updatedAt)}{/if}
            </span>
        </div>
    </div>

    <!-- ── HERO BAND ────────────────────────── -->
    <section class="detail-hero">
        <div class="hero-inner">
            <div class="hero-kicker">
                {#if race.edition}
                    <span class="hk-edition">▌{race.edition}</span>
                    <span class="hk-sep">|</span>
                {/if}
                <span class="hk-courses">{race.sportLabel} · {sportCode}{courseCodes ? ' · ' + courseCodes : ''}</span>
                <span class="hk-chip">
                    {#if race.status === 'registration_open'}
                        <span class="arena-live-dot"></span>
                    {/if}
                    {statusLabelEn}{ddayLabel && ddayLabel !== statusLabelEn ? ' · ' + ddayLabel : ''}
                </span>
            </div>
            <h1 class="hero-title">{race.title}</h1>
            <div class="hero-subtitle">
                {#if race.raceDate}{formatDateFull(race.raceDate)} ({formatDateDay(race.raceDate)}){/if}{race.startTime ? ' · ' + race.startTime + ' 출발' : ''}{race.location ? ' · ' + race.location : ''}
            </div>

            <div class="hero-meta">
                <div class="meta-cell">
                    <div class="meta-label">일정</div>
                    <div class="meta-value">{race.raceDate ? formatDateShort(race.raceDate) : '—'}</div>
                    <div class="meta-sub">
                        {#if race.raceDate}{formatDateDay(race.raceDate)}{/if}{race.startTime ? ' · ' + race.startTime : ''}
                    </div>
                </div>
                <div class="meta-cell">
                    <div class="meta-label">장소</div>
                    <div class="meta-value ellipsis-inline">{race.location ?? '—'}</div>
                    <div class="meta-sub">{race.region ?? ''}</div>
                </div>
                <div class="meta-cell">
                    <div class="meta-label">코스</div>
                    <div class="meta-value">{distanceList.length || 0}개 종목</div>
                    <div class="meta-sub ellipsis-inline">{courseCodes || '—'}</div>
                </div>
                {#if race.weatherForecast}
                    {@const w = race.weatherForecast}
                    <div class="meta-cell">
                        <div class="meta-label">날씨 예보</div>
                        <div class="meta-value">
                            {#if w.temp_low != null && w.temp_high != null}
                                {w.temp_low}° / {w.temp_high}°
                            {:else}
                                —
                            {/if}
                            {#if w.rain_prob != null}
                                <span class="weather-rain">· 비 {w.rain_prob}%</span>
                            {/if}
                        </div>
                        <div class="meta-sub">{w.wind ?? ''}</div>
                    </div>
                {:else}
                    <div class="meta-cell">
                        <div class="meta-label">참가비</div>
                        <div class="meta-value">{feeRangeLabel}</div>
                        <div class="meta-sub">참가비 범위</div>
                    </div>
                {/if}
            </div>
        </div>
    </section>

    <!-- ── MAIN GRID ────────────────────────── -->
    <div class="detail-main">
        <!-- ── TOC ────────────────────────── -->
        <nav class="toc" aria-label="목차">
            <div class="toc-title">목차</div>
            {#each sections as s (s.id)}
                <a class="toc-item" href={`#${s.id}`}>
                    <span class="toc-n">{s.n}</span>
                    <span>{s.label}</span>
                </a>
            {/each}
        </nav>

        <!-- ── BODY ────────────────────────── -->
        <div class="body">
            <section id="overview" class="sec">
                <div class="sec-head">
                    <span class="sec-n">{secN('overview')} ·</span>
                    <h2 class="sec-title">개요</h2>
                </div>
                {#if race.aiSummary}
                    <div class="ai-block">
                        <div class="ai-kicker">간단 후기</div>
                        <p>{race.aiSummary}</p>
                    </div>
                {/if}
                {#if race.description}
                    <div class="prose">{@html race.description.replace(/\n/g, '<br>')}</div>
                {/if}
                {#if race.organizer || validOfficialUrl || race.registrationStart || race.registrationEnd || race.organizerContact}
                    <table class="meta-table">
                        <tbody>
                            {#if race.organizer}
                                <tr><td class="mt-key">주최</td><td>{race.organizer}</td></tr>
                            {/if}
                            {#if validOfficialUrl}
                                <tr>
                                    <td class="mt-key">공식 사이트</td>
                                    <td>
                                        <a href={validOfficialUrl} target="_blank" rel="noopener" class="ext">{validOfficialUrl}</a>
                                    </td>
                                </tr>
                            {/if}
                            {#if race.registrationStart || race.registrationEnd}
                                <tr>
                                    <td class="mt-key">접수 기간</td>
                                    <td>
                                        {race.registrationStart ? formatDateSlash(race.registrationStart) : '—'} — {race.registrationEnd ? formatDateSlash(race.registrationEnd) : '—'}
                                    </td>
                                </tr>
                            {/if}
                            {#if race.organizerContact}
                                <tr><td class="mt-key">문의</td><td>{race.organizerContact}</td></tr>
                            {/if}
                        </tbody>
                    </table>
                {/if}
            </section>

            {#if distanceList.length > 0}
                <section id="courses" class="sec">
                    <div class="sec-head">
                        <span class="sec-n">{secN('courses')} ·</span>
                        <h2 class="sec-title">종목 · 참가비</h2>
                    </div>
                    <div class="table-scroll">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>종목</th>
                                    <th>거리</th>
                                    {#if hasDistanceStart}<th>출발 시각</th>{/if}
                                    {#if hasCutoff}<th>제한 시간</th>{/if}
                                    {#if hasFee}<th class="right">참가비</th>{/if}
                                </tr>
                            </thead>
                            <tbody>
                                {#each distanceList as d, i (d.name + i)}
                                    <tr>
                                        <td class="body-font">{d.name}</td>
                                        <td>
                                            {#if d.distance_meter}
                                                {(d.distance_meter / 1000).toFixed(1)} km
                                            {:else}
                                                —
                                            {/if}
                                        </td>
                                        {#if hasDistanceStart}<td>{d.start_time || (race.startTime ?? '—')}</td>{/if}
                                        {#if hasCutoff}<td>{d.cutoff || '—'}</td>{/if}
                                        {#if hasFee}<td class="right bold">{d.fee ? arenaFeeFull(Number(d.fee)) : '—'}</td>{/if}
                                    </tr>
                                {/each}
                            </tbody>
                        </table>
                    </div>
                </section>
            {/if}

            {#if race.courseImageSrcs && race.courseImageSrcs.length > 0}
                <section id="course-map" class="sec">
                    <div class="sec-head">
                        <span class="sec-n">{secN('course-map')} ·</span>
                        <h2 class="sec-title">코스 지도</h2>
                        {#if validOfficialUrl}
                            <span class="sec-meta">
                                <a href={validOfficialUrl} target="_blank" rel="noopener" class="link">공식 페이지에서 원본 확인 →</a>
                            </span>
                        {/if}
                    </div>
                    <div class="map-images" class:multi={race.courseImageSrcs.length > 1}>
                        {#each race.courseImageSrcs as src, idx}
                            <button
                                class="map-image-btn"
                                onclick={() => openImageModal(src, `${race.title} 코스 ${idx + 1}`)}
                            >
                                <img src={src} alt={`${race.title} 코스 ${idx + 1}`} loading="lazy" />
                            </button>
                        {/each}
                    </div>
                </section>
            {/if}

            {#if race.latitude && race.longitude}
                <section id="location" class="sec">
                    <div class="sec-head">
                        <span class="sec-n">{secN('location')} ·</span>
                        <h2 class="sec-title">위치</h2>
                        {#if race.address}<span class="sec-meta">{race.address}</span>{/if}
                    </div>
                    <div id="arena-kakao-map" class="map-frame"></div>
                </section>
            {/if}

            {#if race.registrationStart || race.registrationEnd || race.raceDate}
                <section id="timeline" class="sec">
                    <div class="sec-head">
                        <span class="sec-n">{secN('timeline')} ·</span>
                        <h2 class="sec-title">타임라인</h2>
                    </div>
                    <div class="detail-timeline">
                        {#if race.registrationStart}
                            {@const st = timelineStatus(race.registrationStart)}
                            <div class="t-row" class:current={st === 'now'} class:done={st === 'done'}>
                                <span class="t-dot" class:done={st === 'done'} class:accent={st === 'now'}></span>
                                <span class="t-date">{formatDateSlash(race.registrationStart)}</span>
                                <span class="t-label">접수 오픈</span>
                                <span class="t-status">{timelineStatusLabel[st]}</span>
                            </div>
                        {/if}
                        {#if race.registrationPhases}
                            {#each race.registrationPhases as p, i (i)}
                                {@const st = timelineStatus(p.start, p.end)}
                                <div class="t-row" class:current={st === 'now'} class:done={st === 'done'}>
                                    <span class="t-dot" class:done={st === 'done'} class:accent={st === 'now'}></span>
                                    <span class="t-date">
                                        {#if p.start}{formatDateSlash(p.start)}{/if}{p.end ? ' ~ ' + formatDateSlash(p.end) : ''}
                                    </span>
                                    <span class="t-label">{p.label}</span>
                                    <span class="t-status">{timelineStatusLabel[st]}</span>
                                </div>
                            {/each}
                        {/if}
                        {#if race.registrationEnd}
                            {@const st = timelineStatus(race.registrationEnd)}
                            <div class="t-row" class:current={st === 'now'} class:done={st === 'done'}>
                                <span class="t-dot" class:done={st === 'done'} class:accent={st === 'now'}></span>
                                <span class="t-date">{formatDateSlash(race.registrationEnd)}</span>
                                <span class="t-label">접수 마감</span>
                                <span class="t-status">{timelineStatusLabel[st]}</span>
                            </div>
                        {/if}
                        {#if race.raceDate}
                            {@const st = timelineStatus(race.raceDate, race.raceEndDate)}
                            <div class="t-row" class:current={st === 'now'} class:done={st === 'done'}>
                                <span class="t-dot" class:done={st === 'done'} class:accent={st === 'now'}></span>
                                <span class="t-date">{formatDateSlash(race.raceDate)}</span>
                                <span class="t-label bold">대회일</span>
                                <span class="t-status">{timelineStatusLabel[st]}</span>
                            </div>
                        {/if}
                    </div>
                </section>
            {/if}

            {#if (race.giveaways && race.giveaways.length > 0) || (race.giveawayImageSrcs && race.giveawayImageSrcs.length > 0)}
                <section id="includes" class="sec">
                    <div class="sec-head">
                        <span class="sec-n">{secN('includes')} ·</span>
                        <h2 class="sec-title">참가비에 포함</h2>
                    </div>
                    {#if race.giveaways && race.giveaways.length > 0}
                        <div class="includes">
                            {#each race.giveaways as inc, i (i)}
                                <div class="include-item">
                                    <span class="check">[✓]</span>
                                    <span>{inc}</span>
                                </div>
                            {/each}
                        </div>
                    {/if}
                    {#if race.giveawayImageSrcs && race.giveawayImageSrcs.length > 0}
                        <div
                            class="map-images"
                            class:multi={race.giveawayImageSrcs.length > 1}
                            style="margin-top: 16px;"
                        >
                            {#each race.giveawayImageSrcs as src, idx}
                                <button
                                    class="map-image-btn"
                                    onclick={() => openImageModal(src, `${race.title} 사은품 ${idx + 1}`)}
                                >
                                    <img src={src} alt={`${race.title} 사은품 ${idx + 1}`} loading="lazy" />
                                </button>
                            {/each}
                        </div>
                    {/if}
                </section>
            {/if}

            <section id="reviews" class="sec">
                <div class="sec-head">
                    <span class="sec-n">{secN('reviews')} ·</span>
                    <h2 class="sec-title">지난 대회 후기</h2>
                    {#if reviewStats.count > 0}
                        <span class="sec-meta">
                            ★ {reviewStats.average.toFixed(1)} · {reviewStats.count}개
                        </span>
                    {/if}
                </div>
                {#if reviews.length === 0}
                    <div class="rv-empty">
                        <div class="rv-empty-msg">아직 작성된 후기가 없습니다.</div>
                        {#if !hasReviewed}
                            <button class="rv-empty-btn" onclick={() => (reviewModalOpen = true)}>
                                <span>리뷰 작성하기</span>
                                <span class="rv-empty-arrow">→</span>
                            </button>
                        {/if}
                    </div>
                {:else}
                    <div class="review-grid">
                        {#each reviews as review (review.id)}
                            <article class="review-card">
                                <div class="rv-head">
                                    <span class="rv-user">@{review.nickname}{reviewYear(review.createdAt) ? ' · ' + reviewYear(review.createdAt) : ''}</span>
                                    <span class="rv-stars" aria-label={`${review.rating}점`}>{reviewStarLine(review.rating)}</span>
                                </div>
                                <div class="rv-body">{review.comment}</div>
                                {#if review.completionTime || review.courseDifficulty || review.operationSatisfaction || (review.recommendationTags && review.recommendationTags.length > 0)}
                                    <div class="rv-foot">
                                        {#if review.courseDifficulty && difficultyLabel[review.courseDifficulty]}
                                            <span class="rv-meta">난이도 {difficultyLabel[review.courseDifficulty]}</span>
                                        {/if}
                                        {#if review.completionTime}
                                            <span class="rv-meta">기록 {review.completionTime}</span>
                                        {/if}
                                        {#if review.operationSatisfaction}
                                            <span class="rv-meta">운영 {reviewStarLine(review.operationSatisfaction)}</span>
                                        {/if}
                                        {#if review.recommendationTags && review.recommendationTags.length > 0}
                                            <span class="rv-tags">
                                                {#each review.recommendationTags as tag}
                                                    <span class="rv-tag">#{tag}</span>
                                                {/each}
                                            </span>
                                        {/if}
                                    </div>
                                {/if}
                            </article>
                        {/each}
                    </div>
                {/if}
            </section>

            {#each relatedRaceSlots as slot, slotIdx (slotIdx)}
                {#if slot.races.length > 0}
                    <section id={slotIdx === 0 ? 'related' : `related-${slotIdx}`} class="sec">
                        <div class="sec-head">
                            <span class="sec-n">{secN('related')} ·</span>
                            <h2 class="sec-title">{slot.label}</h2>
                        </div>
                        <div class="related-grid">
                            {#each slot.races.slice(0, 4) as related (related.id)}
                                <RaceCard race={related} />
                            {/each}
                        </div>
                    </section>
                {/if}
            {/each}

            {#if race.recapUrl}
                <section id="recap" class="sec">
                    <div class="sec-head">
                        <span class="sec-n">{secN('recap')} ·</span>
                        <h2 class="sec-title">대회 후기 블로그</h2>
                    </div>
                    <a href={race.recapUrl} target="_blank" rel="noopener" class="ext-card">
                        <span>블로그에서 후기 보기</span>
                        <span class="ext-arrow">↗</span>
                    </a>
                </section>
            {/if}

            {#if relatedPosts && relatedPosts.length > 0}
                <section id="posts" class="sec">
                    <div class="sec-head">
                        <span class="sec-n">{secN('posts')} ·</span>
                        <h2 class="sec-title">관련 게시글</h2>
                        <span class="sec-meta"><a href="/posts?race={race.id}" class="link">전체 →</a></span>
                    </div>
                    <ul class="post-list">
                        {#each relatedPosts as p (p.id)}
                            <li>
                                <a href={`/posts/${p.id}`} class="post-row">
                                    <span class="post-cat">{p.category?.trim() || '자유'}</span>
                                    <span class="post-row-title">{p.title}</span>
                                    <span class="post-row-meta">@{p.nickname} · 💬 {p.commentCount}</span>
                                </a>
                            </li>
                        {/each}
                    </ul>
                </section>
            {/if}
        </div>

        <!-- ── ASIDE ────────────────────────── -->
        <aside class="aside">
            <div class="aside-cta">
                <div class="cta-label">접수마감</div>
                <div class="cta-num">{ddayLabel}</div>
                <div class="cta-sub">
                    {#if race.registrationEnd}
                        마감 {formatDateSlash(race.registrationEnd)}
                    {:else if race.raceDate}
                        대회일 {formatDateSlash(race.raceDate)}
                    {/if}
                </div>
                <div class="cta-stats">
                    <div class="cs-row"><span class="cs-key">참가비</span><span>{feeRangeLabel}</span></div>
                    {#if courseCodes}
                        <div class="cs-row"><span class="cs-key">종목</span><span class="ellipsis-inline">{courseCodes}</span></div>
                    {/if}
                    <div class="cs-row">
                        <span class="cs-key">접수</span>
                        <span class="cs-status">
                            {#if race.status === 'registration_open'}<span class="arena-live-dot"></span>{/if}
                            {statusLabelEn}
                        </span>
                    </div>
                </div>
                {#if validOfficialUrl}
                    <a
                        href={validOfficialUrl}
                        target="_blank"
                        rel="noopener"
                        class="cta-btn"
                        onclick={() => handleRegisterClick('desktop')}
                    >
                        <span>{race.status === 'registration_open' ? '공식 페이지에서 신청' : '공식 페이지로'} →</span>
                        <span class="cta-tag">외부</span>
                    </a>
                {/if}
                <div class="cta-actions">
                    <button onclick={toggleFavorite} aria-pressed={isFavorited}>
                        {isFavorited ? '♥' : '♡'} 찜
                    </button>
                    <button onclick={openShareModal}>↗ 공유</button>
                </div>
            </div>

            {#if showAtAGlance}
                <div class="aside-card">
                    <div class="ac-title">한눈에 보기</div>
                    <div class="ac-list">
                        <div class="ac-row"><span>{atAGlance.surface}</span><span>{race.courseSurface || '—'}</span></div>
                        <div class="ac-row"><span>{atAGlance.difficulty}</span><span>{race.courseDifficulty || '—'}</span></div>
                        <div class="ac-row"><span>{atAGlance.aid}</span><span>{race.aidStations || '—'}</span></div>
                        <div class="ac-row"><span>기록 측정</span><span>{race.timingMethod || '—'}</span></div>
                        <div class="ac-row"><span>주차</span><span>{race.parking || '—'}</span></div>
                    </div>
                </div>
            {/if}

            {#if isAdmin}
                <a class="admin-link" href="/admin/races/race/{race.id}/change/" target="_blank" rel="noopener">
                    🔧 관리자 페이지에서 수정 →
                </a>
            {/if}
        </aside>
    </div>
</div>

<ReviewForm
    raceSlug={race.slug}
    {hasReviewed}
    raceDate={race.raceDate}
    raceEndDate={race.raceEndDate}
    bind:open={reviewModalOpen}
    onclose={() => (reviewModalOpen = false)}
/>

<!-- Mobile sticky CTA -->
{#if validOfficialUrl}
    <div class="mobile-cta">
        <a
            href={validOfficialUrl}
            target="_blank"
            rel="noopener"
            class="arena-btn arena-btn-accent mobile-cta-btn"
            onclick={() => handleRegisterClick('mobile')}
        >
            {race.status === 'registration_open' ? '공식 사이트에서 접수' : '공식 사이트로 이동'} ↗
        </a>
    </div>
{/if}

{#if modalOpen}
    <div
        class="arena-modal"
        role="dialog"
        aria-modal="true"
        aria-label="이미지 확대 보기"
        onclick={(e) => {
            if (e.target === e.currentTarget) closeImageModal();
        }}
        onkeydown={(e) => e.key === 'Escape' && closeImageModal()}
        tabindex="-1"
    >
        <button
            class="modal-close"
            onclick={closeImageModal}
            aria-label="닫기">×</button
        >
        <img
            src={modalImageSrc}
            alt={modalImageAlt}
            class="modal-img"
        />
    </div>
{/if}

{#if shareModalOpen}
    <div
        class="arena-modal"
        role="dialog"
        aria-modal="true"
        aria-label="공유하기"
        onclick={(e) => {
            if (e.target === e.currentTarget) closeShareModal();
        }}
        onkeydown={(e) => e.key === 'Escape' && closeShareModal()}
        tabindex="-1"
    >
        <div class="share-box">
            <div class="share-head">
                <span class="arena-kicker">공유</span>
                <button class="share-close mono" onclick={closeShareModal} aria-label="닫기">✕</button>
            </div>
            <h3>대회 공유하기</h3>
            <div class="share-actions">
                <button
                    class="share-btn primary"
                    onclick={() => {
                        shareKakao();
                        closeShareModal();
                    }}
                >
                    <span>카카오톡으로 공유</span>
                    <span class="mono share-arrow">↗</span>
                </button>
                <button
                    class="share-btn ghost"
                    onclick={() => {
                        copyLink();
                        closeShareModal();
                    }}
                >
                    <span>링크 복사</span>
                    <span class="mono share-arrow">⎘</span>
                </button>
            </div>
        </div>
    </div>
{/if}

<style>
    .arena-detail {
        background: var(--arena-paper);
        color: var(--arena-ink);
        font-family: var(--arena-f-body);
        min-width: 0;
        padding-bottom: 60px;
    }

    /* ── Top mono band ────────────────── */
    .detail-head {
        border-bottom: 1px solid var(--arena-line);
        padding: 18px 0;
    }
    .head-inner {
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
        letter-spacing: 1px;
        gap: 16px;
    }
    @media (min-width: 1024px) {
        .head-inner {
            padding: 0 32px;
        }
    }
    .bread-mono {
        display: inline-flex;
        gap: 8px;
        align-items: center;
        min-width: 0;
        overflow: hidden;
        word-break: keep-all;
    }
    .bread-mono a {
        color: inherit;
        text-decoration: none;
    }
    .bread-mono .bm-item {
        white-space: nowrap;
        flex-shrink: 0;
    }
    .bread-mono a:hover {
        color: var(--arena-ink);
    }
    .bread-mono .sep {
        color: var(--arena-line);
        flex-shrink: 0;
    }
    .bread-meta {
        white-space: nowrap;
    }
    @media (max-width: 720px) {
        .bm-slug,
        .bm-slug-sep {
            display: none;
        }
        .bm-meta-prefix {
            display: none;
        }
    }
    .ellipsis-inline {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        min-width: 0;
    }

    /* ── Hero band ────────────────── */
    .detail-hero {
        border-bottom: 1px solid var(--arena-line);
        padding: 36px 0 44px;
    }
    .hero-inner {
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 24px;
    }
    @media (min-width: 1024px) {
        .hero-inner {
            padding: 0 32px;
        }
    }
    .hero-kicker {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        margin-bottom: 16px;
        display: flex;
        gap: 14px;
        align-items: center;
        flex-wrap: wrap;
    }
    .hk-courses {
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        max-width: 100%;
    }
    .hk-sep {
        color: var(--arena-line);
    }
    .hk-chip {
        display: inline-flex;
        gap: 6px;
        align-items: center;
        background: var(--arena-paper-alt);
        border: 1px solid var(--arena-line);
        padding: 3px 10px;
        font-size: 10px;
        letter-spacing: 1px;
    }
    .hero-title {
        font-family: var(--arena-f-display);
        font-size: clamp(36px, 6vw, 56px);
        font-weight: 700;
        letter-spacing: -2px;
        line-height: 1;
        margin: 0 0 14px;
        color: var(--arena-ink);
        text-wrap: balance;
    }
    .hero-subtitle {
        font-family: var(--arena-f-mono);
        font-size: 13px;
        color: var(--arena-ink-soft);
        margin-bottom: 28px;
    }
    .hero-meta {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        border: 1px solid var(--arena-line);
        background: var(--arena-line);
        gap: 1px;
    }
    @media (min-width: 1024px) {
        .hero-meta {
            grid-template-columns: repeat(4, 1fr);
        }
    }
    .meta-cell {
        padding: 10px 12px;
        background: var(--arena-paper-alt);
        font-family: var(--arena-f-mono);
        font-size: 12px;
        min-width: 0;
    }
    @media (min-width: 720px) {
        .meta-cell {
            padding: 14px 18px;
        }
    }
    .meta-label {
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .meta-value {
        font-family: var(--arena-f-display);
        font-size: 15px;
        font-weight: 600;
        letter-spacing: -0.3px;
        line-height: 1.2;
    }
    @media (min-width: 720px) {
        .meta-value {
            font-size: 18px;
        }
    }
    .meta-sub {
        font-size: 11px;
        color: var(--arena-ink-soft);
        margin-top: 3px;
    }
    .weather-rain {
        font-size: 13px;
        color: var(--arena-ink-soft);
        font-weight: 500;
        letter-spacing: 0;
        margin-left: 4px;
    }

    /* ── Main 3-col grid ────────────────── */
    .detail-main {
        max-width: 1400px;
        margin: 0 auto;
        padding: 36px 24px;
        display: grid;
        grid-template-columns: 1fr;
        gap: 32px;
        align-items: flex-start;
    }
    @media (min-width: 1024px) {
        .detail-main {
            grid-template-columns: 200px minmax(0, 1fr) 280px;
            gap: 40px;
            padding: 40px 32px;
        }
    }

    /* ── TOC ────────────────── */
    .toc {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        order: 1;
    }
    @media (min-width: 1024px) {
        .toc {
            position: sticky;
            top: 80px;
        }
    }
    .toc-title {
        font-size: 10px;
        letter-spacing: 2px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        margin-bottom: 14px;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--arena-line);
    }
    .toc-item {
        display: flex;
        gap: 10px;
        padding: 7px 0;
        color: var(--arena-ink-soft);
        text-decoration: none;
        letter-spacing: 1px;
    }
    .toc-item:hover {
        color: var(--arena-ink);
    }
    .toc-n {
        color: var(--arena-ink-mute);
    }

    /* ── Body ────────────────── */
    .body {
        order: 2;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 56px;
    }
    .sec {
        scroll-margin-top: 80px;
    }
    .sec-head {
        display: flex;
        align-items: baseline;
        gap: 16px;
        margin-bottom: 20px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--arena-line);
        flex-wrap: wrap;
    }
    .sec-n {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
        letter-spacing: 1.5px;
    }
    .sec-title {
        font-family: var(--arena-f-display);
        font-size: 24px;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin: 0;
    }
    .sec-meta {
        margin-left: auto;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
        display: inline-flex;
        gap: 14px;
        align-items: baseline;
    }

    .ai-block {
        background: var(--arena-paper-alt);
        border-left: 3px solid var(--arena-accent);
        padding: 14px 18px;
        margin-bottom: 16px;
    }
    .ai-kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .ai-block p {
        margin: 0;
        font-size: 13px;
        line-height: 1.6;
        color: var(--arena-ink-soft);
    }
    .prose {
        font-size: 14px;
        line-height: 1.7;
        color: var(--arena-ink);
        margin-bottom: 16px;
    }

    /* ── Tables ────────────────── */
    .table-scroll {
        max-width: 100%;
        overflow-x: auto;
    }
    .meta-table,
    .data-table {
        width: 100%;
        border-collapse: collapse;
        font-family: var(--arena-f-mono);
        font-size: 12px;
        border: 1px solid var(--arena-line);
        margin-top: 4px;
    }
    .meta-table td,
    .data-table td {
        padding: 12px 14px;
        border-bottom: 1px solid var(--arena-line-soft);
        vertical-align: top;
    }
    .meta-table tr:last-child td,
    .data-table tr:last-child td {
        border-bottom: none;
    }
    .data-table th {
        text-align: left;
        padding: 10px 14px;
        background: var(--arena-paper-alt);
        border-bottom: 1px solid var(--arena-line);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        font-weight: 500;
        white-space: nowrap;
    }
    .data-table th.right,
    .data-table td.right {
        text-align: right;
    }
    .meta-table .mt-key {
        background: var(--arena-paper-alt);
        color: var(--arena-ink-soft);
        width: 140px;
        white-space: nowrap;
    }
    .meta-table td:not(.mt-key) {
        overflow-wrap: anywhere;
        word-break: break-word;
    }
    .data-table td.bold {
        font-weight: 700;
    }
    .data-table td.body-font {
        font-family: var(--arena-f-body);
        font-weight: 600;
        font-size: 13px;
    }

    /* ── Map images ────────────────── */
    .map-images {
        display: grid;
        grid-template-columns: 1fr;
        gap: 12px;
    }
    @media (min-width: 720px) {
        .map-images.multi {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    .map-image-btn {
        padding: 0;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper-alt);
        cursor: pointer;
        overflow: hidden;
    }
    .map-image-btn img {
        width: 100%;
        display: block;
    }
    .map-image-btn:hover {
        border-color: var(--arena-ink);
    }
    .map-frame {
        width: 100%;
        height: 360px;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper-alt);
    }

    /* ── Timeline ────────────────── */
    /* renamed from .timeline to escape daisyUI 5's bare .timeline rule (display:flex) */
    .detail-timeline {
        border: 1px solid var(--arena-line);
    }
    .t-row {
        display: grid;
        grid-template-columns: 16px auto 1fr auto;
        gap: 10px;
        padding: 12px 12px;
        border-bottom: 1px solid var(--arena-line-soft);
        font-family: var(--arena-f-mono);
        font-size: 12px;
        align-items: center;
    }
    .t-row > * {
        line-height: 1;
    }
    @media (min-width: 720px) {
        .t-row {
            grid-template-columns: 24px minmax(140px, max-content) 1fr auto;
            gap: 16px;
            padding: 14px 16px;
        }
    }
    .t-date {
        color: var(--arena-ink);
        white-space: nowrap;
        font-size: 11px;
    }
    @media (min-width: 720px) {
        .t-date {
            font-size: 12px;
        }
    }
    .t-row:last-child {
        border-bottom: none;
    }
    .t-row.current {
        background: var(--arena-paper-alt);
    }
    .t-row.done .t-date,
    .t-row.done .t-label {
        color: var(--arena-ink-mute);
    }
    .t-dot {
        width: 10px;
        height: 10px;
        border: 1.5px solid var(--arena-ink);
        background: var(--arena-paper);
    }
    .t-dot.done {
        background: var(--arena-ink);
    }
    .t-dot.accent {
        background: var(--arena-accent);
        border-color: var(--arena-accent-deep);
    }
    .t-label {
        font-family: var(--arena-f-body);
        font-size: 14px;
        font-weight: 500;
        color: var(--arena-ink);
    }
    .t-label.bold {
        font-weight: 700;
    }
    .t-status {
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
    }

    /* ── Reviews ────────────────── */
    .review-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 16px;
    }
    @media (min-width: 720px) {
        .review-grid {
            grid-template-columns: 1fr 1fr;
        }
    }
    .review-card {
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .rv-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
        letter-spacing: 0.5px;
    }
    .rv-user {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        min-width: 0;
    }
    .rv-stars {
        font-family: var(--arena-f-mono);
        color: var(--arena-ink);
        letter-spacing: 1px;
        white-space: nowrap;
    }
    .rv-body {
        font-size: 13px;
        line-height: 1.55;
        color: var(--arena-ink-soft);
        white-space: pre-wrap;
        word-break: break-word;
    }
    .rv-foot {
        display: flex;
        flex-wrap: wrap;
        gap: 8px 16px;
        align-items: center;
        padding-top: 10px;
        border-top: 1px dashed var(--arena-line-soft);
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
    }
    .rv-meta {
        display: inline-flex;
        gap: 4px;
        align-items: baseline;
    }
    .rv-tags {
        display: inline-flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-left: auto;
    }
    .rv-tag {
        border: 1px solid var(--arena-line);
        background: var(--arena-paper-alt);
        padding: 2px 8px;
        font-size: 10px;
        letter-spacing: 0.5px;
        color: var(--arena-ink);
    }
    .rv-empty {
        border: 1px solid var(--arena-line);
        background: var(--arena-paper-alt);
        padding: 32px 24px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 14px;
        font-family: var(--arena-f-mono);
        font-size: 12px;
        color: var(--arena-ink-soft);
        letter-spacing: 0.5px;
    }
    .rv-empty-msg {
        text-align: center;
    }
    .rv-empty-btn {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border: 1px solid var(--arena-ink);
        padding: 10px 18px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 10px;
    }
    .rv-empty-btn:hover {
        background: var(--arena-ink-soft);
    }
    .rv-empty-arrow {
        opacity: 0.7;
    }

    /* ── Includes ────────────────── */
    .includes {
        display: grid;
        grid-template-columns: 1fr;
        gap: 4px 32px;
        border: 1px solid var(--arena-line);
        padding: 16px 20px;
    }
    @media (min-width: 720px) {
        .includes {
            grid-template-columns: 1fr 1fr;
        }
    }
    .include-item {
        display: flex;
        gap: 12px;
        padding: 8px 0;
        font-size: 13px;
        border-bottom: 1px dashed var(--arena-line-soft);
    }
    /* Mobile (1-col): only the last item drops the line */
    .include-item:last-child {
        border-bottom: none;
    }
    @media (min-width: 720px) {
        /* 2-col: also drop the 2nd-to-last when it sits in the same (last) row.
           That happens only when total count is even: last item is at an even
           position, so 2nd-to-last is at an odd position. */
        .include-item:nth-last-child(2):nth-child(odd) {
            border-bottom: none;
        }
    }
    .check {
        font-family: var(--arena-f-mono);
        color: var(--arena-accent-deep);
    }

    /* ── Related ────────────────── */
    .related-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 16px;
    }
    @media (min-width: 720px) {
        .related-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    @media (min-width: 1280px) {
        .related-grid {
            grid-template-columns: repeat(3, 1fr);
        }
    }

    /* ── Ext / Posts ────────────────── */
    .ext-card {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 18px 20px;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper-alt);
        font-family: var(--arena-f-display);
        font-weight: 600;
        font-size: 15px;
        color: var(--arena-ink);
        text-decoration: none;
    }
    .ext-card:hover {
        border-color: var(--arena-ink);
    }
    .ext-arrow {
        font-family: var(--arena-f-mono);
        font-size: 13px;
        color: var(--arena-ink-soft);
    }

    .post-list {
        list-style: none;
        margin: 0;
        padding: 0;
        border: 1px solid var(--arena-line);
    }
    .post-row {
        display: grid;
        grid-template-columns: 60px 1fr auto;
        align-items: center;
        gap: 14px;
        padding: 12px 16px;
        border-bottom: 1px solid var(--arena-line-soft);
        text-decoration: none;
        color: var(--arena-ink);
    }
    .post-list li:last-child .post-row {
        border-bottom: none;
    }
    .post-cat {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
    }
    .post-row-title {
        font-size: 14px;
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .post-row-meta {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
    }

    .link {
        color: var(--arena-ink-soft);
        text-decoration: none;
        border-bottom: 1px solid var(--arena-line);
        padding-bottom: 1px;
    }
    .link:hover {
        color: var(--arena-ink);
        border-color: var(--arena-ink);
    }
    .link-btn {
        background: transparent;
        border: none;
        font: inherit;
        cursor: pointer;
        padding: 0;
    }
    .ext {
        color: var(--arena-ink);
        text-decoration: none;
        border-bottom: 1px solid var(--arena-ink-soft);
        overflow-wrap: anywhere;
        word-break: break-all;
    }

    /* ── Aside ────────────────── */
    .aside {
        order: 0; /* mobile: aside between hero and TOC; desktop overrides below */
        display: flex;
        flex-direction: column;
        gap: 20px;
        min-width: 0;
    }
    @media (min-width: 1024px) {
        .aside {
            order: 3;
            position: sticky;
            top: 80px;
        }
    }
    .aside-cta {
        background: var(--arena-ink);
        color: var(--arena-paper);
        padding: 20px;
        font-family: var(--arena-f-mono);
        min-width: 0;
        overflow: hidden;
    }
    .cta-label {
        font-size: 10px;
        letter-spacing: 2px;
        opacity: 0.6;
        margin-bottom: 6px;
    }
    .cta-num {
        font-family: var(--arena-f-display);
        font-size: 32px;
        font-weight: 700;
        letter-spacing: -0.5px;
        line-height: 1;
        color: var(--arena-accent);
    }
    .cta-sub {
        font-size: 11px;
        opacity: 0.7;
        margin-top: 4px;
    }
    .cta-stats {
        margin-top: 16px;
        padding: 12px 0;
        border-top: 1px dashed rgba(255, 255, 255, 0.2);
        border-bottom: 1px dashed rgba(255, 255, 255, 0.2);
        font-size: 11px;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .cs-row {
        display: flex;
        align-items: baseline;
        gap: 12px;
        min-width: 0;
    }
    .cs-key {
        opacity: 0.6;
        flex: 0 0 56px;
        white-space: nowrap;
    }
    .cs-row > :nth-child(2) {
        flex: 1 1 0;
        min-width: 0;
        max-width: 100%;
        text-align: right;
        white-space: pre-wrap;
        word-break: break-word;
    }
    .cs-status {
        color: var(--arena-accent);
        justify-content: flex-end;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .cta-btn {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 14px;
        padding: 14px 16px;
        background: var(--arena-accent);
        color: var(--arena-ink);
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: 14px;
        letter-spacing: -0.2px;
        text-decoration: none;
    }
    .cta-btn:hover {
        opacity: 0.9;
    }
    .cta-tag {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        opacity: 0.6;
    }
    .cta-actions {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        margin-top: 8px;
    }
    .cta-actions button {
        padding: 10px;
        background: transparent;
        color: var(--arena-paper);
        border: 1px solid rgba(255, 255, 255, 0.2);
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1px;
        cursor: pointer;
    }
    .cta-actions button:hover {
        background: rgba(255, 255, 255, 0.08);
    }
    .aside-card {
        border: 1px solid var(--arena-line);
        padding: 16px 18px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
    }
    .ac-title {
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        margin-bottom: 12px;
    }
    .ac-list {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .ac-row {
        display: flex;
        justify-content: space-between;
        gap: 12px;
    }
    .ac-row > span:first-child {
        color: var(--arena-ink-soft);
    }
    .ac-row > span:last-child {
        font-family: var(--arena-f-body);
        font-size: 13px;
        text-align: right;
        max-width: 60%;
    }
    .admin-link {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        padding: 12px 18px;
        background: var(--arena-paper);
        border: 1px dashed var(--arena-line);
        color: var(--arena-ink-soft);
        text-decoration: none;
        text-align: center;
    }
    .admin-link:hover {
        color: var(--arena-ink);
        border-style: solid;
    }

    /* ── Mobile sticky CTA ────────────────── */
    .mobile-cta {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 40;
        background: var(--arena-paper);
        border-top: 1px solid var(--arena-line);
        padding: 12px 16px;
        padding-bottom: max(12px, env(safe-area-inset-bottom));
    }
    .mobile-cta-btn {
        width: 100%;
        justify-content: center;
        padding: 14px;
        font-size: 14px;
    }
    @media (min-width: 1024px) {
        .mobile-cta {
            display: none;
        }
    }

    /* ── Modals ────────────────── */
    .arena-modal {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.85);
        z-index: 200;
        display: grid;
        place-items: center;
        padding: 24px;
        cursor: pointer;
    }
    .modal-close {
        position: absolute;
        top: 20px;
        right: 24px;
        background: transparent;
        border: 1px solid rgba(255, 255, 255, 0.4);
        color: white;
        width: 36px;
        height: 36px;
        font-size: 22px;
        cursor: pointer;
        line-height: 1;
    }
    .modal-img {
        max-width: 100%;
        max-height: 90vh;
        cursor: default;
    }
    .share-box {
        background: var(--arena-paper);
        border: 1px solid var(--arena-ink);
        box-shadow: 6px 6px 0 var(--arena-ink);
        max-width: 380px;
        width: 100%;
        cursor: default;
    }
    .share-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 18px;
        border-bottom: 1px solid var(--arena-line);
        background: var(--arena-paper-alt);
    }
    .share-close {
        background: transparent;
        border: 1px solid var(--arena-line);
        padding: 3px 8px;
        font-size: 12px;
        cursor: pointer;
        line-height: 1;
        color: var(--arena-ink);
    }
    .share-close:hover {
        background: var(--arena-ink);
        color: var(--arena-paper);
    }
    .share-box h3 {
        font-family: var(--arena-f-display);
        font-size: 22px;
        font-weight: 700;
        letter-spacing: -0.6px;
        margin: 0;
        padding: 16px 18px 4px;
    }
    .share-actions {
        padding: 12px 18px 18px;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .share-btn {
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
    }
    .share-btn:active {
        transform: translateY(1px);
    }
    .share-btn.primary {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border: 1px solid var(--arena-ink);
    }
    .share-btn.primary:hover {
        background: var(--arena-accent-deep);
        border-color: var(--arena-accent-deep);
        color: var(--arena-paper);
    }
    .share-btn.ghost {
        background: var(--arena-paper);
        color: var(--arena-ink);
        border: 1px solid var(--arena-line);
    }
    .share-btn.ghost:hover {
        background: var(--arena-paper-alt);
        border-color: var(--arena-ink);
    }
    .share-arrow {
        font-size: 13px;
        opacity: 0.7;
    }
</style>
