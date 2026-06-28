<script lang="ts" module>
    declare const Kakao: any;
    declare const kakao: any;
</script>

<script lang="ts">
    import { page } from '$app/stores';
    import { goto } from '$app/navigation';
    import ReviewForm from '$lib/components/ReviewForm.svelte';
    import { Badge, Button } from '$lib/components/eh';
    import { dsBadgeStatus, SPORT_META, dsSport } from '$lib/components/eh/meta';
    import type { Race, Review, ReviewStats, Distance, FavoriteToggleResponse } from '$lib/types';
    import { formatDateFull, formatDateDay, formatDateShort, formatDistanceToNow } from '$lib/date';
    import {
        arenaDday,
        arenaDdayLabel,
        arenaDistLabel,
        arenaFeeFull,
        arenaFeeRange,
        arenaFeeShort,
        arenaMinFee,
        arenaShortDate,
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
    const reviews: Review[] = $derived(data.reviews);
    const reviewStats: ReviewStats = $derived(data.reviewStats);
    const hasReviewed: boolean = $derived(data.hasReviewed);

    const appUrl = $derived(data.appUrl || 'https://www.endurohub.kr');
    const kakaoJsKey = $derived(data.kakaoJsKey as string);
    const isAdmin: boolean = $derived(data.isAdmin ?? false);
    const pageUrl = $derived(`${appUrl}${$page.url.pathname}`);

    const badgeStatus = $derived(dsBadgeStatus(race.status, race.daysUntilRegistrationEnd));
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

    const distanceList = $derived((race.distances ?? []) as Distance[]);
    const hasFee = $derived(distanceList.some((d) => d.fee));
    const hasCutoff = $derived(distanceList.some((d) => d.cutoff));
    const hasDistanceStart = $derived(distanceList.some((d) => d.startTime));
    const feeDistances = $derived(distanceList.filter((d) => d.fee));

    /** AI summary — used as the 개요 lead/description fallback. */
    const tagline = $derived(race.aiSummary?.trim() || '');

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
    const officialHost = $derived.by(() => {
        if (!validOfficialUrl) return '';
        try {
            return new URL(validOfficialUrl).hostname.replace(/^www\./, 'www.');
        } catch {
            return validOfficialUrl;
        }
    });

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

    const ogImage = $derived(`${appUrl}/og/races/${race.slug}`);

    // ── hero ──────────────────────────────────────────────
    const sportMeta = $derived(SPORT_META[dsSport(race.sport)]);
    const lastUpdated = $derived(race.updatedAt ? formatDistanceToNow(race.updatedAt) : '');

    const venueName = $derived((race.location ?? '').split(' (')[0]);
    const venueHead = $derived.by(() => {
        const v = venueName.trim();
        const sp = v.indexOf(' ');
        return sp > 0 ? v.slice(0, sp) : v;
    });
    const venueSub = $derived.by(() => {
        const v = venueName.trim();
        const sp = v.indexOf(' ');
        const rest = sp > 0 ? v.slice(sp + 1) : '';
        return [rest, race.region].filter(Boolean).join(' · ');
    });

    /** Race-day stat: "06.13" with weekday · start time. */
    const heroDate = $derived.by(() => {
        if (!race.raceDate) return '';
        const [, mm, dd] = race.raceDate.split('-');
        return `${mm}.${dd}`;
    });

    /** ENTRY hero stat — registration status + deadline. */
    const entryStat = $derived.by(() => {
        const regEnd = race.registrationEnd ? arenaShortDate(race.registrationEnd) : '';
        const regStart = race.registrationStart ? arenaShortDate(race.registrationStart) : '';
        if (race.status === 'registration_open') {
            const d = race.daysUntilRegistrationEnd;
            const value =
                d == null ? '접수 중' : d < 0 ? '마감' : d === 0 ? '오늘' : `D-${String(d).padStart(2, '0')}`;
            return { value, sub: regEnd ? `${regEnd} 마감` : '접수 중' };
        }
        if (race.status === 'upcoming') {
            return { value: '예정', sub: regStart ? `${regStart} 오픈` : '오픈 예정' };
        }
        return { value: '마감', sub: regEnd ? `${regEnd} 종료` : race.statusLabel || '마감' };
    });

    /** Distance chips for the hero sport line: "21.0975KM · 10KM · 5KM". */
    const heroDistLabels = $derived.by<string[]>(() =>
        distanceList
            .map((d) => {
                if (d.distanceMeter && d.distanceMeter > 0) {
                    const km = Math.round((d.distanceMeter / 1000) * 10000) / 10000;
                    return `${km}KM`;
                }
                return (d.name || '').toUpperCase();
            })
            .filter(Boolean),
    );

    /** Hero weather strip (race-window forecast). */
    const heroWeather = $derived.by(() => {
        const w = race.weatherForecast;
        if (!w) return null;
        const rw = w.raceWindow;
        const condition = rw?.condition ?? w.condition;
        const tempMin = rw?.tempMin ?? w.tempLow;
        const tempMax = rw?.tempMax ?? w.tempHigh;
        const rain = rw?.rainProbMax ?? w.rainProb;
        const wind = rw?.wind ?? w.wind;
        const hasTemp = tempMin != null && tempMax != null;
        if (!condition && !hasTemp && rain == null && !wind) return null;
        return { condition, tempMin, tempMax, rain, wind, hasTemp };
    });

    // ── register card ─────────────────────────────────────
    const regBig = $derived.by(() => {
        if (dday.value == null) return race.statusLabel || '—';
        if (dday.value < 0) return '접수 마감';
        if (dday.value === 0) return '오늘 마감';
        return `D-${String(dday.value).padStart(2, '0')}`;
    });

    /** km label for the courses table (trim trailing zeros): 21098 → "21.098K" */
    function fmtKm(m: number | null | undefined): string {
        if (!m || m <= 0) return '';
        const s = (m / 1000).toFixed(3).replace(/\.?0+$/, '');
        return `${s}K`;
    }

    let modalOpen = $state(false);
    let modalImageSrc = $state('');
    let modalImageAlt = $state('');
    let shareModalOpen = $state(false);
    let reviewModalOpen = $state(false);
    let descExpanded = $state(false);

    let favoriteOverride = $state<boolean | null>(null);
    const isFavorited = $derived(favoriteOverride ?? race.isFavorited);
    let isTogglingFavorite = $state(false);

    $effect(() => {
        race.slug;
        modalOpen = false;
        shareModalOpen = false;
        reviewModalOpen = false;
        favoriteOverride = null;
        descExpanded = false;
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
            'position:fixed;top:24px;left:50%;transform:translateX(-50%);background:var(--ink-900);color:var(--paper-0);padding:10px 18px;font-family:var(--font-sans);font-size:12px;letter-spacing:1px;z-index:200;border:1px solid var(--ink-900);';
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
            price: String(arenaMinFee(race) ?? 0),
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
            const container = document.getElementById('detail-kakao-map');
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

    type TimelineStatus = 'done' | 'now' | 'upcoming';
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

    interface TimelineItem {
        date: string;
        label: string;
        done: boolean;
        current: boolean;
        bold: boolean;
    }
    /** Registration milestones for the 타임라인 section. */
    const timelineItems = $derived.by<TimelineItem[]>(() => {
        const raw: { date: string; label: string; end?: string | null; bold?: boolean }[] = [];
        if (race.registrationStart) raw.push({ date: race.registrationStart, label: '접수 오픈' });
        for (const p of race.registrationPhases ?? []) {
            if (p.start || p.end) raw.push({ date: (p.start ?? p.end) as string, label: p.label, end: p.end });
        }
        if (race.registrationEnd) raw.push({ date: race.registrationEnd, label: '접수 마감' });
        if (race.raceDate) raw.push({ date: race.raceDate, label: '대회일', bold: true });

        let currentAssigned = false;
        return raw.map((r) => {
            const done = timelineStatus(r.date, r.end) === 'done';
            let current = false;
            if (!done && !currentAssigned) {
                current = true;
                currentAssigned = true;
            }
            return { date: r.date, label: r.label, done, current, bold: !!r.bold };
        });
    });

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

    // ── 개요 info table (folds in organizer + course meta) ─
    const overviewRows = $derived.by<{ k: string; v: string; href?: string }[]>(() => {
        const rows: { k: string; v: string; href?: string }[] = [];
        if (race.organizer) rows.push({ k: '주최', v: race.organizer });
        if (validOfficialUrl) rows.push({ k: '공식 사이트', v: officialHost, href: validOfficialUrl });
        if (race.registrationStart || race.registrationEnd) {
            const s = race.registrationStart ? arenaShortDate(race.registrationStart) : '';
            const e = race.registrationEnd ? arenaShortDate(race.registrationEnd) : '';
            rows.push({ k: '접수 기간', v: s && e ? `${s} — ${e}` : s || e });
        }
        if (race.organizerContact) rows.push({ k: '문의', v: race.organizerContact });
        const surfaceLabel = race.sport === 'trail_running' ? '지형' : '노면';
        if (race.courseSurface) rows.push({ k: surfaceLabel, v: race.courseSurface });
        if (race.courseDifficulty) rows.push({ k: '코스 난이도', v: race.courseDifficulty });
        if (race.aidStations)
            rows.push({ k: race.sport === 'trail_running' ? '보급소' : '급수대', v: race.aidStations });
        if (race.timingMethod) rows.push({ k: '기록 측정', v: race.timingMethod });
        if (race.parking) rows.push({ k: '주차', v: race.parking });
        return rows;
    });

    const descBody = $derived(race.description?.trim() || tagline || '');
    const descNeedsClamp = $derived(descBody.replace(/<[^>]+>/g, '').length > 140);
    const hasOverview = $derived(!!descBody || overviewRows.length > 0);

    // ── related races (flattened, deduped) ───────────────
    const relatedFlat = $derived.by<Race[]>(() => {
        const seen = new Set<number>();
        const out: Race[] = [];
        for (const s of relatedRaceSlots) {
            for (const r of s.races) {
                if (!seen.has(r.id)) {
                    seen.add(r.id);
                    out.push(r);
                }
            }
        }
        return out.slice(0, 6);
    });

    /** Dynamic grid-template-columns for the courses table */
    const coursesGridTemplate = $derived.by(() => {
        const parts: string[] = ['minmax(0, 1fr)'];
        if (hasDistanceStart) parts.push('86px');
        if (hasCutoff) parts.push('86px');
        if (hasFee) parts.push('104px');
        return parts.join(' ');
    });

    // ── section list + table of contents ─────────────────
    const sections = $derived.by(() => {
        const list: { id: string; label: string; show: boolean }[] = [
            { id: 'overview', label: '개요', show: hasOverview },
            { id: 'courses', label: '종목 · 참가비', show: distanceList.length > 0 },
            { id: 'course-map', label: '코스 지도', show: !!race.courseImageSrcs?.length },
            { id: 'location', label: '위치', show: !!(race.latitude && race.longitude) },
            { id: 'timeline', label: '타임라인', show: timelineItems.length > 0 },
            {
                id: 'includes',
                label: '구성품',
                show: !!race.giveaways?.length || !!race.giveawayImageSrcs?.length,
            },
            { id: 'reviews', label: '후기', show: true },
            { id: 'related', label: '연관 대회', show: relatedFlat.length > 0 },
        ];
        return list.filter((s) => s.show).map((s, i) => ({ ...s, n: String(i).padStart(2, '0') }));
    });
    function secN(id: string): string {
        return sections.find((s) => s.id === id)?.n ?? '00';
    }

    // ── scroll-spy for the table of contents ─────────────
    let activeSection = $state('overview');
    $effect(() => {
        const ids = sections.map((s) => s.id);
        if (ids.length === 0) return;
        function syncActive() {
            const y = window.scrollY + 120;
            let cur = ids[0];
            for (const id of ids) {
                const el = document.getElementById(id);
                if (el && el.getBoundingClientRect().top + window.scrollY <= y) cur = id;
            }
            activeSection = cur;
        }
        syncActive();
        window.addEventListener('scroll', syncActive, { passive: true });
        window.addEventListener('resize', syncActive);
        return () => {
            window.removeEventListener('scroll', syncActive);
            window.removeEventListener('resize', syncActive);
        };
    });
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
    <meta property="og:image:type" content="image/png" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="twitter:image" content={ogImage} />
    {@html `<script type="application/ld+json">${JSON.stringify(eventSchema)}</script>`}
    {@html `<script type="application/ld+json">${JSON.stringify(breadcrumbSchema)}</script>`}
</svelte:head>

<!-- Reusable numbered section head -->
{#snippet sechead(n: string, title: string, aux?: string)}
    <div class="rd-sh">
        <div class="rd-sh__l">
            <span class="eh-micro eh-data rd-sh__n">{n}</span>
            <h2 class="rd-sh__t">{title}</h2>
        </div>
        {#if aux}<span class="eh-micro rd-sh__aux">{aux}</span>{/if}
    </div>
{/snippet}

<!-- ══════════════════════════════════════════════════
     HERO — INK BLOCK
══════════════════════════════════════════════════ -->
<section class="rd-hero">
    <div class="rd-hero__inner">
        <div class="rd-hero__top">
            <nav class="rd-crumb" aria-label="breadcrumb">
                <a href="/races">대회</a><span class="rd-crumb__sep">/</span>
                <a href={`/races?sport=${race.sport}`}>{race.sportLabel}</a>
                {#if race.region}
                    <span class="rd-crumb__sep">/</span>
                    <span class="rd-crumb__cur">{race.region}</span>
                {/if}
            </nav>
            {#if lastUpdated}
                <span class="rd-hero__updated">마지막 업데이트 {lastUpdated}</span>
            {/if}
        </div>

        <div class="rd-hero__meta">
            <div class="rd-hero__sport">
                <span class="rd-hero__dot" style="background:{sportMeta.color}"></span>
                <span class="rd-hero__sportcode eh-data">{sportMeta.label}</span>
                {#if heroDistLabels.length > 0}
                    <span class="rd-hero__dists eh-data">{heroDistLabels.join(' · ')}</span>
                {/if}
            </div>
            <Badge status={badgeStatus} />
        </div>

        <h1 class="rd-hero__title">{race.title}</h1>

        <div class="rd-hstats">
            <div class="rd-hstat">
                <div class="rd-hstat__k">ENTRY</div>
                <div class="rd-hstat__v eh-data">
                    {entryStat.value}{#if entryStat.sub}<small>{entryStat.sub}</small>{/if}
                </div>
            </div>
            {#if race.raceDate}
                <div class="rd-hstat">
                    <div class="rd-hstat__k">RACE DAY</div>
                    <div class="rd-hstat__v eh-data">
                        {heroDate}<small>{formatDateDay(race.raceDate)}{race.startTime ? ` · ${race.startTime}` : ''}</small>
                    </div>
                </div>
            {/if}
            {#if distanceList.length > 0}
                <div class="rd-hstat">
                    <div class="rd-hstat__k">COURSES</div>
                    <div class="rd-hstat__v eh-data">{distanceList.length}<small>개 종목</small></div>
                </div>
            {/if}
            {#if venueName}
                <div class="rd-hstat">
                    <div class="rd-hstat__k">VENUE</div>
                    <div class="rd-hstat__v rd-hstat__v--venue">
                        {venueHead}{#if venueSub}<small>{venueSub}</small>{/if}
                    </div>
                </div>
            {/if}
        </div>

        {#if heroWeather}
            <div class="rd-hero__wx">
                <span class="rd-hero__wx-label eh-micro">WEATHER · 대회시간 기준</span>
                {#if heroWeather.condition || heroWeather.hasTemp}
                    <span class="rd-hero__wx-item">
                        {#if heroWeather.condition}<b>{heroWeather.condition}</b>{/if}
                        {#if heroWeather.hasTemp}<span class="eh-data">{heroWeather.tempMin}° / {heroWeather.tempMax}°</span>{/if}
                    </span>
                {/if}
                {#if heroWeather.rain != null}
                    <span class="rd-hero__wx-item"><i>강수</i> <b class="eh-data">{heroWeather.rain}%</b></span>
                {/if}
                {#if heroWeather.wind}
                    <span class="rd-hero__wx-item"><i>바람</i> <b class="eh-data">{heroWeather.wind}</b></span>
                {/if}
            </div>
        {/if}
    </div>
</section>

<!-- ══════════════════════════════════════════════════
     BODY — 3-COLUMN GRID
══════════════════════════════════════════════════ -->
<main class="rd-wrap">
    <div class="rd-grid">

        <!-- ── TABLE OF CONTENTS ──────────────────── -->
        <nav class="rd-toc" aria-label="목차">
            <div class="rd-toc__label eh-micro">CONTENTS</div>
            <ul class="rd-toc__list">
                {#each sections as s (s.id)}
                    <li>
                        <a
                            href={`#${s.id}`}
                            class="rd-toc__link"
                            class:rd-toc__link--active={activeSection === s.id}
                        >
                            <span class="rd-toc__n eh-data">{s.n}</span>
                            <span class="rd-toc__t">{s.label}</span>
                        </a>
                    </li>
                {/each}
            </ul>
        </nav>

        <!-- ── MAIN COLUMN ──────────────────────── -->
        <div class="rd-main">

            <!-- 개요 -->
            {#if hasOverview}
                <section id="overview" class="rd-sec">
                    {@render sechead(
                        secN('overview'),
                        '개요',
                    )}
                    {#if descBody}
                        <div
                            class="rd-prose rd-ov-desc"
                            class:rd-ov-desc--clamp={descNeedsClamp && !descExpanded}
                        >
                            {@html descBody.replace(/\n/g, '<br>')}
                        </div>
                        {#if descNeedsClamp}
                            <button class="rd-more" onclick={() => (descExpanded = !descExpanded)}>
                                {descExpanded ? '접기' : '더보기'}
                            </button>
                        {/if}
                    {/if}
                    {#if overviewRows.length > 0}
                        <div class="v-table rd-ov-table">
                            {#each overviewRows as row (row.k)}
                                <div class="v-trow rd-meta-row">
                                    <span class="eh-micro rd-meta-key">{row.k}</span>
                                    {#if row.href}
                                        <a
                                            class="rd-meta-link"
                                            href={row.href}
                                            target="_blank"
                                            rel="noopener"
                                            onclick={() => trackOutboundClick(row.href as string, race.title)}
                                        >
                                            {row.v} <span class="rd-meta-link__arrow">↗</span>
                                        </a>
                                    {:else}
                                        <span class="rd-meta-val">{row.v}</span>
                                    {/if}
                                </div>
                            {/each}
                        </div>
                    {/if}
                </section>
            {/if}

            <!-- 종목 · 참가비 -->
            {#if distanceList.length > 0}
                <section id="courses" class="rd-sec">
                    {@render sechead(
                        secN('courses'),
                        '종목 · 참가비',
                        race.registrationEnd ? `ENTRY CLOSES ${arenaShortDate(race.registrationEnd)}` : undefined,
                    )}
                    <div class="rd-table-scroll">
                        <div class="v-table">
                            <div class="v-thead rd-crow" style="grid-template-columns: {coursesGridTemplate}">
                                <span>코스</span>
                                {#if hasDistanceStart}<span class="rd-hide-m">START</span>{/if}
                                {#if hasCutoff}<span class="rd-hide-m">CUT-OFF</span>{/if}
                                {#if hasFee}<span class="rd-cell-r">FEE</span>{/if}
                            </div>
                            {#each distanceList as d, i (d.name + i)}
                                <div class="v-trow rd-crow" style="grid-template-columns: {coursesGridTemplate}">
                                    <span class="rd-cname">
                                        {d.name}
                                        {#if d.distanceMeter}<span class="rd-cdist eh-data">{fmtKm(d.distanceMeter)}</span>{/if}
                                    </span>
                                    {#if hasDistanceStart}
                                        <span class="rd-hide-m rd-cmuted eh-data">{d.startTime || race.startTime || '—'}</span>
                                    {/if}
                                    {#if hasCutoff}
                                        <span class="rd-hide-m rd-cmuted">{d.cutoff || '—'}</span>
                                    {/if}
                                    {#if hasFee}
                                        <b class="rd-cell-r eh-data">{d.fee ? arenaFeeFull(Number(d.fee)) : '—'}</b>
                                    {/if}
                                </div>
                            {/each}
                        </div>
                    </div>
                </section>
            {/if}

            <!-- 코스 지도 -->
            {#if race.courseImageSrcs && race.courseImageSrcs.length > 0}
                <section id="course-map" class="rd-sec">
                    {@render sechead(
                        secN('course-map'),
                        '코스 지도',
                        race.courseImageSrcs.length > 1 ? `${race.courseImageSrcs.length} IMAGES` : undefined,
                    )}
                    <div class="rd-map-images" class:rd-map-images--multi={race.courseImageSrcs.length > 1}>
                        {#each race.courseImageSrcs as src, idx}
                            <button
                                class="rd-map-btn"
                                onclick={() => openImageModal(src, `${race.title} 코스 ${idx + 1}`)}
                            >
                                <img src={src} alt={`${race.title} 코스 ${idx + 1}`} loading="lazy" />
                            </button>
                        {/each}
                    </div>
                </section>
            {/if}

            <!-- 위치 -->
            {#if race.latitude && race.longitude}
                <section id="location" class="rd-sec">
                    {@render sechead(secN('location'), '위치', race.address || undefined)}
                    <div id="detail-kakao-map" class="rd-map-frame"></div>
                </section>
            {/if}

            <!-- 타임라인 -->
            {#if timelineItems.length > 0}
                <section id="timeline" class="rd-sec">
                    {@render sechead(secN('timeline'), '타임라인', '접수 → 대회일')}
                    <div class="rd-tl">
                        {#each timelineItems as t, i (i)}
                            <div
                                class="rd-tl__item"
                                class:rd-tl__item--done={t.done}
                                class:rd-tl__item--current={t.current}
                                class:rd-tl__item--bold={t.bold}
                            >
                                <span class="rd-tl__mark"></span>
                                <span class="rd-tl__date eh-data">{formatDateShort(t.date)}</span>
                                <span class="rd-tl__label">{t.label}</span>
                            </div>
                        {/each}
                    </div>
                </section>
            {/if}

            <!-- 구성품 -->
            {#if (race.giveaways && race.giveaways.length > 0) || (race.giveawayImageSrcs && race.giveawayImageSrcs.length > 0)}
                <section id="includes" class="rd-sec">
                    {@render sechead(
                        secN('includes'),
                        '구성품',
                        race.giveaways?.length ? `${race.giveaways.length} ITEMS` : undefined,
                    )}
                    {#if race.giveaways && race.giveaways.length > 0}
                        <div class="rd-incl-grid">
                            {#each race.giveaways as inc, i (i)}
                                <div class="rd-incl-cell">{inc}</div>
                            {/each}
                        </div>
                    {/if}
                    {#if race.giveawayImageSrcs && race.giveawayImageSrcs.length > 0}
                        <div class="rd-map-images rd-map-images--mt" class:rd-map-images--multi={race.giveawayImageSrcs.length > 1}>
                            {#each race.giveawayImageSrcs as src, idx}
                                <button
                                    class="rd-map-btn"
                                    onclick={() => openImageModal(src, `${race.title} 사은품 ${idx + 1}`)}
                                >
                                    <img src={src} alt={`${race.title} 사은품 ${idx + 1}`} loading="lazy" />
                                </button>
                            {/each}
                        </div>
                    {/if}
                </section>
            {/if}

            <!-- 후기 -->
            <section id="reviews" class="rd-sec">
                {@render sechead(
                    secN('reviews'),
                    '후기',
                    reviewStats.count > 0 ? `${reviewStats.count} REVIEWS · ★ ${reviewStats.average.toFixed(1)}` : undefined,
                )}
                {#if reviews.length === 0}
                    <div class="rd-rv-empty">
                        <p class="rd-rv-empty__msg">아직 작성된 후기가 없습니다.</p>
                        {#if !hasReviewed}
                            <button class="rd-rv-empty__btn" onclick={() => (reviewModalOpen = true)}>
                                리뷰 작성하기 →
                            </button>
                        {/if}
                    </div>
                {:else}
                    <div class="rd-rv-list">
                        {#each reviews as review (review.id)}
                            <article class="v-card rd-review">
                                <div class="rd-review__head">
                                    <span class="rd-review__stars" aria-label={`${review.rating}점`}>{reviewStarLine(review.rating)}</span>
                                    <span class="eh-micro rd-review__user">@{review.nickname}{reviewYear(review.createdAt) ? ` · ${reviewYear(review.createdAt)}` : ''}</span>
                                </div>
                                <p class="rd-review__body">{review.comment}</p>
                                {#if review.completionTime || review.courseDifficulty || review.operationSatisfaction || (review.recommendationTags && review.recommendationTags.length > 0)}
                                    <div class="rd-review__foot">
                                        {#if review.courseDifficulty && difficultyLabel[review.courseDifficulty]}
                                            <span class="eh-micro rd-review__meta">난이도 <b>{difficultyLabel[review.courseDifficulty]}</b></span>
                                        {/if}
                                        {#if review.completionTime}
                                            <span class="eh-micro rd-review__meta">기록 <b class="eh-data">{review.completionTime}</b></span>
                                        {/if}
                                        {#if review.operationSatisfaction}
                                            <span class="eh-micro rd-review__meta">운영 <b>{reviewStarLine(review.operationSatisfaction)}</b></span>
                                        {/if}
                                        {#if review.recommendationTags && review.recommendationTags.length > 0}
                                            <span class="rd-review__tags">
                                                {#each review.recommendationTags as tag}
                                                    <span class="rd-review__tag">#{tag}</span>
                                                {/each}
                                            </span>
                                        {/if}
                                    </div>
                                {/if}
                            </article>
                        {/each}
                        {#if !hasReviewed}
                            <button class="rd-rv-write-btn" onclick={() => (reviewModalOpen = true)}>
                                후기 작성하기 →
                            </button>
                        {/if}
                    </div>
                {/if}
            </section>

            <!-- 연관 대회 -->
            {#if relatedFlat.length > 0}
                <section id="related" class="rd-sec">
                    {@render sechead(secN('related'), '연관 대회', `${relatedFlat.length} RACES`)}
                    <div class="rd-rel-grid">
                        {#each relatedFlat as r (r.id)}
                            <a class="v-card rd-relcard" href={`/races/${r.slug}`}>
                                <div class="rd-relcard__top">
                                    <span class="rd-relcard__sport eh-data" style="color:{SPORT_META[dsSport(r.sport)].color}">{SPORT_META[dsSport(r.sport)].label}</span>
                                    <Badge status={dsBadgeStatus(r.status, r.daysUntilRegistrationEnd)}>
                                        <span class="eh-data">{arenaDdayLabel(r)}</span>
                                    </Badge>
                                </div>
                                <div class="rd-relcard__nm">{r.title}</div>
                                <div class="rd-relcard__meta eh-data">
                                    {r.raceDate ? formatDateShort(r.raceDate) : '—'} · {arenaDistLabel(r)} · {arenaFeeShort(arenaMinFee(r))}
                                </div>
                            </a>
                        {/each}
                    </div>
                </section>
            {/if}

        </div><!-- /rd-main -->

        <!-- ── RAIL ─────────────────────────────── -->
        <aside class="rd-rail">

            <!-- Register card -->
            <div class="v-card rd-reg">
                <div class="rd-reg__top">
                    <Badge status={badgeStatus} />
                    {#if race.registrationEnd}
                        <span class="eh-micro eh-data rd-reg__closes">CLOSES {arenaShortDate(race.registrationEnd)}</span>
                    {/if}
                </div>
                <div class="rd-reg__dday">
                    <span class="eh-data rd-reg__num">{regBig}</span>
                    {#if race.raceDate}
                        <span class="rd-reg__date">{formatDateFull(race.raceDate)} ({formatDateDay(race.raceDate)})</span>
                    {/if}
                </div>

                {#if feeDistances.length > 0}
                    <div class="rd-reg__fees">
                        {#each feeDistances as d (d.name)}
                            <div class="rd-reg__fee">
                                <span class="rd-reg__fee-nm">{d.name}</span>
                                <b class="eh-data">{arenaFeeFull(Number(d.fee))}</b>
                            </div>
                        {/each}
                    </div>
                {:else if feeRangeLabel !== '—'}
                    <div class="rd-reg__fees">
                        <div class="rd-reg__fee">
                            <span class="rd-reg__fee-nm">참가비</span>
                            <b class="eh-data">{feeRangeLabel}</b>
                        </div>
                    </div>
                {/if}

                {#if validOfficialUrl}
                    <Button
                        variant={race.status === 'registration_open' ? 'signal' : 'primary'}
                        size="lg"
                        fullWidth
                        href={validOfficialUrl}
                        target="_blank"
                        rel="noopener"
                        onclick={() => handleRegisterClick('desktop')}
                    >
                        {race.status === 'registration_open' ? '접수하기 ↗' : '공식 페이지로 ↗'}
                    </Button>
                {/if}

                <div class="rd-reg__acts">
                    <button
                        class="rd-reg__act"
                        onclick={toggleFavorite}
                        aria-pressed={isFavorited}
                        disabled={isTogglingFavorite}
                    >
                        {isFavorited ? '♥' : '♡'} 관심 대회 저장
                    </button>
                    <button class="rd-reg__act" onclick={openShareModal}>↗ 공유하기</button>
                </div>
            </div><!-- /rd-reg -->

            <!-- Contact note -->
            {#if race.organizer || race.organizerContact}
                <p class="rd-railnote">
                    {#if race.organizer}주최 {race.organizer}{/if}{#if race.organizer && race.organizerContact} · {/if}{#if race.organizerContact}문의 {race.organizerContact}{/if}<br />
                    정보 오류 제보는 <a href="mailto:contact@endurohub.kr" class="rd-railnote__link">문의하기</a> 페이지를 이용해 주세요.
                </p>
            {/if}

            {#if isAdmin}
                <a class="rd-admin-link" href="/admin/races/{race.slug}">관리자 페이지에서 수정 →</a>
            {/if}

        </aside><!-- /rd-rail -->

    </div>
</main>

<!-- Review form modal -->
<ReviewForm
    raceSlug={race.slug}
    raceTitle={race.title}
    raceMeta={[race.raceDate ? race.raceDate.slice(0, 4) : null, race.sportLabel, race.region].filter(Boolean).join(' · ')}
    {hasReviewed}
    raceDate={race.raceDate}
    raceEndDate={race.raceEndDate}
    bind:open={reviewModalOpen}
    onclose={() => (reviewModalOpen = false)}
    onsubmitted={({ rating }) =>
        track('review_submit', {
            item_type: 'race',
            item_id: race.id,
            sport: race.sport,
            rating,
        })}
/>

<!-- Mobile sticky CTA -->
<div class="rd-mcta">
    <div class="rd-mcta__info">
        {#if race.status === 'registration_open'}
            <span class="rd-mcta__lbl eh-data" style="color: var(--text-accent);">
                {dday.value != null && dday.value > 0 ? `D-${String(dday.value).padStart(2, '0')} 접수` : '접수 중'}
            </span>
            <b class="eh-data">{arenaFeeShort(arenaMinFee(race))}~</b>
        {:else}
            <span class="rd-mcta__lbl" style="color: var(--text-faint);">{race.statusLabel}</span>
            <b class="eh-data">{heroDate}{race.raceDate ? ` (${formatDateDay(race.raceDate)})` : ''}</b>
        {/if}
    </div>

    <button
        class="eh-iconbtn eh-iconbtn--outline {isFavorited ? 'eh-iconbtn--active' : ''}"
        onclick={toggleFavorite}
        aria-pressed={isFavorited}
        aria-label="관심 대회 저장"
        disabled={isTogglingFavorite}
    >
        <svg viewBox="0 0 24 24" width="20" height="20" fill={isFavorited ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.29 1.51 4.04 3 5.5l7 7Z" />
        </svg>
    </button>
    <button class="eh-iconbtn eh-iconbtn--outline" onclick={openShareModal} aria-label="공유하기">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true">
            <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z" />
        </svg>
    </button>

    <span class="rd-mcta__sep"></span>

    <span class="rd-mcta__action">
        {#if race.status === 'registration_open' && validOfficialUrl}
            <a
                href={validOfficialUrl}
                target="_blank"
                rel="noopener"
                class="eh-btn eh-btn--md eh-btn--signal eh-btn--full"
                onclick={() => handleRegisterClick('mobile')}
            >
                접수하기 ↗
            </a>
        {:else if validOfficialUrl}
            <a
                href={validOfficialUrl}
                target="_blank"
                rel="noopener"
                class="eh-btn eh-btn--md eh-btn--primary eh-btn--full"
                onclick={() => handleRegisterClick('mobile')}
            >
                공식 페이지
            </a>
        {:else}
            <button class="eh-btn eh-btn--md eh-btn--primary eh-btn--full" type="button" disabled>
                {race.statusLabel}
            </button>
        {/if}
    </span>
</div>

<!-- Image lightbox -->
{#if modalOpen}
    <div
        class="rd-modal"
        role="dialog"
        aria-modal="true"
        aria-label="이미지 확대 보기"
        onclick={(e) => { if (e.target === e.currentTarget) closeImageModal(); }}
        onkeydown={(e) => e.key === 'Escape' && closeImageModal()}
        tabindex="-1"
    >
        <button class="rd-modal__close" onclick={closeImageModal} aria-label="닫기">×</button>
        <img src={modalImageSrc} alt={modalImageAlt} class="rd-modal__img" />
    </div>
{/if}

<!-- Share modal -->
{#if shareModalOpen}
    <div
        class="rd-modal"
        role="dialog"
        aria-modal="true"
        aria-label="공유하기"
        onclick={(e) => { if (e.target === e.currentTarget) closeShareModal(); }}
        onkeydown={(e) => e.key === 'Escape' && closeShareModal()}
        tabindex="-1"
    >
        <div class="rd-share-box">
            <div class="rd-share-head">
                <span class="rd-share-head__label">공유</span>
                <button class="rd-share-head__close" onclick={closeShareModal} aria-label="닫기">✕</button>
            </div>
            <h3 class="rd-share-title">대회 공유하기</h3>
            <div class="rd-share-actions">
                <button
                    class="rd-share-btn rd-share-btn--primary"
                    onclick={() => { shareKakao(); closeShareModal(); }}
                >
                    <span>카카오톡으로 공유</span>
                    <span class="rd-share-btn__arrow">↗</span>
                </button>
                <button
                    class="rd-share-btn rd-share-btn--ghost"
                    onclick={() => { copyLink(); closeShareModal(); }}
                >
                    <span>링크 복사</span>
                    <span class="rd-share-btn__arrow">⎘</span>
                </button>
            </div>
        </div>
    </div>
{/if}

<style>
    /* ══════════════════════════════════════════
       HERO — INK BLOCK
    ══════════════════════════════════════════ */
    .rd-hero {
        background: var(--bg-inverse);
        color: var(--text-inverse);
        border-bottom: var(--border-rule);
    }
    .rd-hero__inner {
        max-width: var(--container-max);
        margin: 0 auto;
        padding: 44px var(--container-pad) 36px;
    }
    @media (max-width: 768px) {
        .rd-hero__inner { padding: 28px var(--container-pad-mobile) 24px; }
    }

    .rd-hero__top {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 16px;
        flex-wrap: wrap;
    }
    .rd-crumb {
        display: flex;
        gap: 8px;
        align-items: center;
        font-size: 13px;
        flex-wrap: wrap;
    }
    .rd-crumb a {
        color: inherit;
        opacity: 0.55;
        text-decoration: none;
    }
    .rd-crumb a:hover { opacity: 1; }
    .rd-crumb__sep { opacity: 0.35; }
    .rd-crumb__cur { opacity: 1; }
    .rd-hero__updated {
        font-size: var(--text-micro);
        letter-spacing: var(--track-micro);
        text-transform: uppercase;
        opacity: 0.45;
        white-space: nowrap;
    }

    .rd-hero__meta {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        margin-top: 22px;
    }
    .rd-hero__sport {
        display: flex;
        align-items: center;
        gap: 12px;
        min-width: 0;
        flex-wrap: wrap;
    }
    .rd-hero__dot {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        flex: none;
    }
    .rd-hero__sportcode {
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0.08em;
    }
    .rd-hero__dists {
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.04em;
        opacity: 0.66;
    }

    .rd-hero__title {
        font-size: clamp(32px, 4.4vw, 56px);
        font-weight: var(--w-display);
        letter-spacing: var(--track-display);
        line-height: var(--leading-display);
        margin-top: 16px;
        color: var(--text-inverse);
        text-wrap: balance;
    }

    .rd-hstats {
        display: flex;
        gap: var(--sp-10);
        margin-top: 32px;
        flex-wrap: wrap;
        align-items: flex-start;
    }
    @media (max-width: 768px) {
        .rd-hstats { gap: var(--sp-6); margin-top: 24px; }
    }
    .rd-hstat__k {
        font-size: var(--text-micro);
        font-weight: 600;
        letter-spacing: var(--track-micro);
        text-transform: uppercase;
        opacity: 0.55;
        white-space: nowrap;
    }
    .rd-hstat__v {
        font-size: 32px;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1;
        margin-top: 8px;
        white-space: nowrap;
        display: flex;
        align-items: flex-end;
        gap: 7px;
        min-height: 32px;
    }
    @media (max-width: 768px) {
        .rd-hstat__v { font-size: 24px; min-height: 24px; }
    }
    .rd-hstat__v small { font-size: 14px; font-weight: 600; opacity: 0.6; letter-spacing: 0; }
    .rd-hstat__v--venue {
        font-size: 23px;
        font-weight: 700;
        letter-spacing: -0.01em;
        max-width: 280px;
        overflow: hidden;
    }
    .rd-hstat__v--venue small { font-size: 13px; }

    .rd-hero__wx {
        display: flex;
        align-items: center;
        gap: 22px;
        margin-top: 28px;
        padding-top: 20px;
        border-top: 1px solid rgba(255, 255, 255, 0.16);
        flex-wrap: wrap;
    }
    .rd-hero__wx-label { opacity: 0.45; white-space: nowrap; }
    .rd-hero__wx-item {
        display: inline-flex;
        align-items: baseline;
        gap: 7px;
        font-size: 14px;
        white-space: nowrap;
    }
    .rd-hero__wx-item i { font-style: normal; opacity: 0.5; font-size: var(--text-micro); letter-spacing: var(--track-micro); text-transform: uppercase; }
    .rd-hero__wx-item b { font-weight: 700; }

    /* ══════════════════════════════════════════
       BODY GRID — 3 COLUMN
    ══════════════════════════════════════════ */
    .rd-wrap {
        max-width: var(--container-max);
        margin: 0 auto;
        padding: 0 var(--container-pad);
    }
    @media (max-width: 768px) {
        .rd-wrap { padding: 0 var(--container-pad-mobile); }
    }
    .rd-grid {
        display: grid;
        grid-template-columns: 192px minmax(0, 1fr) 344px;
        gap: var(--sp-10);
        padding-top: var(--sp-10);
        padding-bottom: var(--sp-16);
        align-items: start;
    }
    @media (max-width: 1180px) {
        .rd-grid { grid-template-columns: minmax(0, 1fr) 320px; }
        .rd-toc { display: none; }
    }
    @media (max-width: 960px) {
        .rd-grid { grid-template-columns: 1fr; gap: var(--sp-8); padding-bottom: 96px; }
    }

    /* ── table of contents ── */
    .rd-toc {
        position: sticky;
        top: 84px;
        align-self: start;
        min-width: 0;
    }
    .rd-toc__label {
        color: var(--text-faint);
        padding-bottom: 12px;
        border-bottom: var(--border-hair);
    }
    .rd-toc__list { list-style: none; margin: 6px 0 0; padding: 0; }
    .rd-toc__link {
        display: flex;
        align-items: baseline;
        gap: 12px;
        padding: 9px 0 9px 13px;
        margin-left: -2px;
        border-left: 2px solid transparent;
        text-decoration: none;
        color: var(--text-muted);
        font-size: 13.5px;
        font-weight: 500;
        transition: color var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
    }
    .rd-toc__n { font-size: 11px; font-weight: 600; color: var(--text-faint); }
    .rd-toc__link:hover { color: var(--text-strong); }
    .rd-toc__link--active {
        border-left-color: var(--accent);
        color: var(--text-strong);
        font-weight: 700;
    }
    .rd-toc__link--active .rd-toc__n { color: var(--text-accent); }

    /* ── main column ── */
    .rd-main { min-width: 0; display: flex; flex-direction: column; gap: var(--sp-12); }

    /* section head */
    .rd-sec { scroll-margin-top: 80px; }
    .rd-sh {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: var(--sp-4);
        flex-wrap: wrap;
        border-top: 1.5px solid var(--ink-900);
        padding-top: 14px;
        margin-bottom: 18px;
    }
    .rd-sh__l { display: flex; align-items: baseline; gap: 12px; }
    .rd-sh__n { color: var(--text-accent); }
    .rd-sh__t {
        font-size: var(--text-h3);
        font-weight: var(--w-strong);
        letter-spacing: var(--track-heading);
        color: var(--text-strong);
    }
    .rd-sh__aux { color: var(--text-faint); }

    /* overview prose */
    .rd-prose {
        font-size: 15px;
        line-height: var(--leading-body);
        color: var(--text-body);
        max-width: 640px;
    }
    .rd-ov-desc { white-space: normal; word-break: break-word; }
    .rd-ov-desc--clamp {
        display: -webkit-box;
        -webkit-line-clamp: 4;
        line-clamp: 4;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .rd-more {
        margin-top: 10px;
        background: none;
        border: none;
        padding: 0;
        font-size: 13px;
        font-weight: 600;
        color: var(--text-strong);
        cursor: pointer;
        text-decoration: underline;
        text-underline-offset: 3px;
    }
    .rd-more:hover { color: var(--text-accent); }
    .rd-ov-table { margin-top: 22px; }

    /* meta table (개요 정보) */
    .rd-meta-row { grid-template-columns: 120px 1fr; gap: 16px; }
    .rd-meta-key { color: var(--text-faint); white-space: nowrap; }
    .rd-meta-val { font-weight: 600; color: var(--text-body); }
    .rd-meta-link {
        font-weight: 600;
        color: var(--text-strong);
        text-decoration: none;
        border-bottom: 1px solid var(--line);
        width: fit-content;
    }
    .rd-meta-link:hover { border-bottom-color: var(--ink-900); }
    .rd-meta-link__arrow { font-size: 11px; color: var(--text-faint); }

    /* courses table */
    .rd-table-scroll { overflow-x: auto; max-width: 100%; }
    .rd-crow { gap: 14px; }
    .rd-cell-r { text-align: right; }
    .rd-cname { font-weight: 600; }
    .rd-cdist { color: var(--text-faint); font-weight: 500; margin-left: 4px; }
    .rd-cmuted { color: var(--text-muted); }
    @media (max-width: 768px) {
        .rd-hide-m { display: none !important; }
    }

    /* course / giveaway images */
    .rd-map-images { display: grid; grid-template-columns: 1fr; gap: 12px; }
    @media (min-width: 720px) {
        .rd-map-images--multi { grid-template-columns: repeat(2, 1fr); }
    }
    .rd-map-images--mt { margin-top: 16px; }
    .rd-map-btn {
        padding: 0;
        border: var(--border-hair);
        background: var(--paper-50);
        cursor: pointer;
        overflow: hidden;
        border-radius: var(--r-0);
    }
    .rd-map-btn img { width: 100%; display: block; }
    .rd-map-btn:hover { border-color: var(--ink-900); }
    .rd-map-frame { width: 100%; height: 360px; border: var(--border-hair); background: var(--paper-50); }

    /* timeline (main section) */
    .rd-tl { display: flex; flex-direction: column; border: var(--border-hair); background: var(--surface-card); padding: 4px 18px; }
    .rd-tl__item {
        display: grid;
        grid-template-columns: 18px 110px 1fr;
        gap: 14px;
        align-items: baseline;
        padding: 13px 0;
        border-bottom: var(--border-hair);
    }
    .rd-tl__item:last-child { border-bottom: 0; }
    .rd-tl__mark {
        width: 10px;
        height: 10px;
        border: 1px solid var(--ink-300);
        background: var(--paper-0);
        align-self: center;
    }
    .rd-tl__item--done .rd-tl__mark { background: var(--ink-900); border-color: var(--ink-900); }
    .rd-tl__item--current .rd-tl__mark { background: var(--accent); border-color: var(--accent-strong); }
    .rd-tl__date { font-size: 13px; font-weight: 600; color: var(--text-muted); white-space: nowrap; }
    .rd-tl__label { font-size: 14px; font-weight: 500; color: var(--text-strong); }
    .rd-tl__item--current .rd-tl__label { font-weight: 700; color: var(--text-accent); }
    .rd-tl__item--bold .rd-tl__label { font-weight: 800; }
    .rd-tl__item--done .rd-tl__date,
    .rd-tl__item--done .rd-tl__label { color: var(--text-faint); }

    /* includes grid */
    .rd-incl-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 1px;
        background: var(--line);
        border: 1px solid var(--line);
    }
    .rd-incl-cell {
        background: var(--surface-card);
        padding: 14px 16px;
        font-size: 14px;
        font-weight: 500;
    }

    /* reviews */
    .rd-rv-empty {
        border: var(--border-hair);
        background: var(--paper-50);
        padding: 32px 24px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 14px;
        font-size: 13px;
        color: var(--text-muted);
    }
    .rd-rv-empty__msg { margin: 0; text-align: center; }
    .rd-rv-empty__btn {
        background: var(--ink-900);
        color: var(--paper-0);
        border: 1px solid var(--ink-900);
        padding: 10px 20px;
        font-size: 12px;
        letter-spacing: 0.5px;
        cursor: pointer;
    }
    .rd-rv-empty__btn:hover { background: var(--ink-700); }
    .rd-rv-list { display: flex; flex-direction: column; gap: 10px; }
    .rd-review { padding: 18px 20px; }
    .rd-review__head { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
    .rd-review__stars {
        color: var(--text-accent);
        letter-spacing: 2px;
        font-size: 13px;
        white-space: nowrap;
    }
    .rd-review__user { color: var(--text-faint); margin-left: auto; }
    .rd-review__body {
        font-size: 14px;
        color: var(--text-body);
        line-height: var(--leading-body);
        margin-top: 8px;
        white-space: pre-wrap;
        word-break: break-word;
    }
    .rd-review__foot {
        display: flex;
        gap: 8px 16px;
        margin-top: 12px;
        flex-wrap: wrap;
        align-items: baseline;
    }
    .rd-review__meta { color: var(--text-faint); }
    .rd-review__meta b { color: var(--text-strong); font-weight: 700; }
    .rd-review__tags { display: inline-flex; flex-wrap: wrap; gap: 6px; margin-left: auto; }
    .rd-review__tag {
        border: var(--border-hair);
        background: var(--paper-50);
        padding: 2px 8px;
        font-size: 10px;
        letter-spacing: 0.5px;
        color: var(--text-muted);
    }
    .rd-rv-write-btn {
        background: transparent;
        border: var(--border-hair);
        color: var(--text-muted);
        font-size: 12px;
        letter-spacing: 0.5px;
        padding: 12px;
        cursor: pointer;
        text-align: center;
        margin-top: 2px;
    }
    .rd-rv-write-btn:hover { border-color: var(--ink-900); color: var(--text-strong); }

    /* related races grid */
    .rd-rel-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
    }
    @media (max-width: 560px) {
        .rd-rel-grid { grid-template-columns: 1fr; }
    }
    .rd-relcard {
        padding: 16px 18px;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .rd-relcard:hover { border-color: var(--ink-900); }
    .rd-relcard__top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
    .rd-relcard__sport { font-size: 11px; font-weight: 800; letter-spacing: 0.06em; }
    .rd-relcard__nm {
        font-weight: 600;
        font-size: 14px;
        color: var(--text-strong);
        line-height: 1.35;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .rd-relcard:hover .rd-relcard__nm { text-decoration: underline; text-underline-offset: 3px; }
    .rd-relcard__meta { font-size: 12px; color: var(--text-muted); }

    /* ══════════════════════════════════════════
       RAIL
    ══════════════════════════════════════════ */
    .rd-rail { display: flex; flex-direction: column; gap: var(--sp-4); min-width: 0; }
    @media (min-width: 961px) {
        .rd-rail { position: sticky; top: 84px; }
    }

    /* register card */
    .rd-reg { padding: 24px 24px 22px; border-color: var(--ink-900); }
    @media (max-width: 960px) {
        .rd-reg { display: none; }
    }
    .rd-reg__top { display: flex; align-items: center; gap: 8px; }
    .rd-reg__closes { color: var(--text-faint); margin-left: auto; }
    .rd-reg__dday {
        display: flex;
        align-items: baseline;
        gap: 10px;
        margin: 18px 0 0;
        flex-wrap: wrap;
    }
    .rd-reg__num {
        font-size: 38px;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1;
        color: var(--text-strong);
    }
    .rd-reg__date { color: var(--text-muted); font-size: 13px; }
    .rd-reg__fees { margin: 18px 0 4px; }
    .rd-reg__fee {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        padding: 9px 0;
        border-bottom: var(--border-hair);
        font-size: 14px;
    }
    .rd-reg__fee:last-child { border-bottom: 0; }
    .rd-reg__fee-nm { color: var(--text-muted); }
    .rd-reg__fee b { font-weight: 700; }
    .rd-reg :global(.eh-btn) { margin-top: 18px; }
    .rd-reg__acts { display: flex; gap: 8px; margin-top: 10px; }
    .rd-reg__act {
        flex: 1;
        padding: 10px;
        background: var(--paper-0);
        color: var(--text-strong);
        border: var(--border-hair);
        font-size: 12px;
        letter-spacing: 0.3px;
        cursor: pointer;
    }
    .rd-reg__act:hover { border-color: var(--ink-900); background: var(--paper-50); }
    .rd-reg__act:disabled { opacity: 0.5; cursor: not-allowed; }

    /* contact note */
    .rd-railnote {
        font-size: 12px;
        color: var(--text-faint);
        line-height: 1.6;
        padding: 0 4px;
    }
    .rd-railnote__link {
        color: var(--text-body);
        text-decoration: none;
        border-bottom: 1px solid var(--line);
    }
    .rd-railnote__link:hover { color: var(--text-strong); border-bottom-color: var(--ink-900); }

    /* admin link */
    .rd-admin-link {
        font-size: 12px;
        padding: 12px 18px;
        background: var(--paper-0);
        border: 1px dashed var(--line);
        color: var(--text-faint);
        text-decoration: none;
        text-align: center;
        display: block;
    }
    .rd-admin-link:hover { color: var(--text-strong); border-style: solid; }

    /* ══════════════════════════════════════════
       MOBILE STICKY CTA
    ══════════════════════════════════════════ */
    .rd-mcta {
        display: none;
        position: fixed;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 95;
        background: var(--paper-0);
        border-top: 1px solid var(--ink-900);
        padding: 10px var(--container-pad-mobile) calc(10px + env(safe-area-inset-bottom, 0px));
        gap: 12px;
        align-items: center;
    }
    @media (max-width: 960px) {
        .rd-mcta { display: flex; }
    }
    .rd-mcta__info { display: flex; flex-direction: column; gap: 1px; flex: none; min-width: 0; padding-right: 2px; }
    .rd-mcta__lbl {
        font-size: var(--text-micro);
        font-weight: var(--w-strong);
        letter-spacing: var(--track-micro);
        text-transform: uppercase;
        white-space: nowrap;
    }
    .rd-mcta__info b {
        font-size: 15px;
        font-weight: 800;
        line-height: 1.05;
        letter-spacing: -0.01em;
        color: var(--text-strong);
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
    }
    .rd-mcta .eh-iconbtn { width: 44px; height: 44px; flex: none; color: var(--ink-900); }
    .rd-mcta__sep { align-self: stretch; width: 1px; background: var(--line); margin: 4px 0; flex: none; }
    .rd-mcta__action { flex: 1; display: flex; min-width: 92px; }

    /* ══════════════════════════════════════════
       LIGHTBOX + SHARE MODALS
    ══════════════════════════════════════════ */
    .rd-modal {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.88);
        z-index: 200;
        display: grid;
        place-items: center;
        padding: 24px;
        cursor: pointer;
    }
    .rd-modal__close {
        position: absolute;
        top: 20px;
        right: 24px;
        background: transparent;
        border: 1px solid rgba(255, 255, 255, 0.4);
        color: #fff;
        width: 36px;
        height: 36px;
        font-size: 22px;
        cursor: pointer;
        line-height: 1;
    }
    .rd-modal__img { max-width: 100%; max-height: 90vh; cursor: default; }

    .rd-share-box {
        background: var(--paper-0);
        border: 2px solid var(--ink-900);
        box-shadow: 6px 6px 0 var(--ink-900);
        max-width: 380px;
        width: 100%;
        cursor: default;
    }
    .rd-share-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 18px;
        border-bottom: var(--border-hair);
        background: var(--paper-50);
    }
    .rd-share-head__label {
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--text-faint);
        text-transform: uppercase;
    }
    .rd-share-head__close {
        background: transparent;
        border: var(--border-hair);
        padding: 3px 8px;
        font-size: 12px;
        cursor: pointer;
        color: var(--text-strong);
    }
    .rd-share-head__close:hover { background: var(--ink-900); color: var(--paper-0); }
    .rd-share-title {
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.03em;
        padding: 16px 18px 4px;
        color: var(--text-strong);
    }
    .rd-share-actions { padding: 12px 18px 18px; display: flex; flex-direction: column; gap: 8px; }
    .rd-share-btn {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        width: 100%;
        padding: 12px 14px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        text-align: left;
    }
    .rd-share-btn--primary { background: var(--ink-900); color: var(--paper-0); border: 1px solid var(--ink-900); }
    .rd-share-btn--primary:hover { background: var(--ink-700); }
    .rd-share-btn--ghost { background: var(--paper-0); color: var(--text-strong); border: var(--border-hair); }
    .rd-share-btn--ghost:hover { background: var(--paper-50); border-color: var(--ink-900); }
    .rd-share-btn__arrow { font-size: 13px; opacity: 0.6; }
</style>
