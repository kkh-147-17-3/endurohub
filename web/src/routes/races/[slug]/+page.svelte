<script lang="ts" module>
    declare const Kakao: any;
    declare const kakao: any;
</script>

<script lang="ts">
    import { page } from '$app/stores';
    import RaceCard from '$lib/components/RaceCard.svelte';
    import PostCard from '$lib/components/PostCard.svelte';
    import ReviewForm from '$lib/components/ReviewForm.svelte';
    import ReviewList from '$lib/components/ReviewList.svelte';
    import type { Race, Review, ReviewStats, Post } from '$lib/types';
    import type { Sport } from '$lib/types';
    import { sportStyles } from '$lib/race';
    import { formatDateFull, formatDateDay, formatDateShort, formatDateSlash } from '$lib/date';

    let { data } = $props();

    interface RaceSlot { label: string; races: Race[]; }
    const race: Race = $derived(data.race);
    const relatedRaceSlots: RaceSlot[] = $derived((data.relatedRaces as unknown as RaceSlot[]) || []);
    const relatedPosts: Post[] = $derived(data.relatedPosts);
    const reviews: Review[] = $derived(data.reviews);
    const reviewStats: ReviewStats = $derived(data.reviewStats);
    const hasReviewed: boolean = $derived(data.hasReviewed);

    const style = $derived(sportStyles[race.sport as Sport] || sportStyles.running);

    const appUrl = $derived(data.appUrl || 'https://www.endurohub.kr');
    const kakaoJsKey = $derived(data.kakaoJsKey as string);
    const isAdmin: boolean = $derived(data.isAdmin ?? false);
    const pageUrl = $derived(`${appUrl}${$page.url.pathname}`);

    const distances = $derived(race.distances ? race.distances.slice(0, 3).join(', ') : '');
    const metaDesc = $derived(() => {
        let desc = `${race.title} - ${race.raceDate ? formatDateFull(race.raceDate) : ''} ${race.location}에서 개최되는 ${race.sportLabel} 대회입니다.`;
        if (distances) desc += ` 참가 종목: ${distances}.`;
        if (race.status === 'registration_open') desc += ' 지금 접수 중!';
        desc += ' 엔듀로허브에서 대회 정보를 확인하세요.';
        return desc.substring(0, 160);
    });

    const ogImage = $derived(race.imageSrc || `/images/og-${race.sport.replace('_', '-')}.png`);

    type SportType = 'running' | 'swimming' | 'cycling' | 'triathlon' | 'trail_running';
    const gradients: Record<SportType, string> = {
        running: 'from-primary to-primary/70',
        swimming: 'from-info to-info/70',
        cycling: 'from-warning to-warning/70',
        triathlon: 'from-secondary to-secondary/70',
        trail_running: 'from-success to-success/70',
    };
    const gradient = $derived(gradients[race.sport as SportType] || 'from-primary to-secondary');

    let modalOpen = $state(false);
    let modalImageSrc = $state('');
    let shareModalOpen = $state(false);
    let modalImageAlt = $state('');

    // Reset modal state on navigation
    $effect(() => {
        race.slug;
        modalOpen = false;
        shareModalOpen = false;
    });

    function openImageModal(src: string, alt: string = '') {
        modalImageSrc = src;
        modalImageAlt = alt || `${race.title} 이미지`;
        modalOpen = true;
    }

    function closeImageModal() { modalOpen = false; }
    function openShareModal() { shareModalOpen = true; }
    function closeShareModal() { shareModalOpen = false; }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Escape') {
            if (shareModalOpen) closeShareModal();
            if (modalOpen) closeImageModal();
        }
    }

    function copyLink() {
        navigator.clipboard.writeText(window.location.href).then(() => {
            showToast('링크가 복사되었습니다.');
        });
    }

    function showToast(message: string) {
        const toast = document.createElement('div');
        toast.className = 'toast toast-top toast-center z-50';
        toast.innerHTML = `<div class="alert" style="background:#1e293b;color:#fff;border:none;">${message}</div>`;
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
                    link: {
                        webUrl: window.location.href,
                        mobileWebUrl: window.location.href,
                    },
                },
            });
        } else {
            showToast('카카오 공유 기능을 사용할 수 없습니다.');
        }
    }

    const defaultImage = $derived(`${appUrl}/images/og-${race.sport.replace('_', '-')}.png`);
    const eventSchema = $derived({
        '@context': 'https://schema.org',
        '@type': 'SportsEvent',
        'name': race.title,
        'description': race.description ? race.description.substring(0, 200) : `${race.title} - ${race.location}에서 개최되는 ${race.sportLabel} 대회`,
        'startDate': race.raceDate,
        'endDate': race.raceEndDate || race.raceDate,
        'eventStatus': race.status === 'finished' ? 'https://schema.org/EventCancelled' : 'https://schema.org/EventScheduled',
        'eventAttendanceMode': 'https://schema.org/OfflineEventAttendanceMode',
        'url': pageUrl,
        'sport': race.sportLabel,
        'location': {
            '@type': 'Place',
            'name': race.location,
            'address': {
                '@type': 'PostalAddress',
                'addressLocality': race.location,
                'addressRegion': race.region,
                'addressCountry': 'KR',
            },
            'geo': race.latitude && race.longitude ? {
                '@type': 'GeoCoordinates',
                'latitude': race.latitude,
                'longitude': race.longitude,
            } : undefined,
        },
        'image': race.imageSrc || defaultImage,
        'sameAs': race.officialUrl || undefined,
        'offers': {
            '@type': 'Offer',
            'url': race.officialUrl || pageUrl,
            'availability': race.status === 'registration_open' ? 'https://schema.org/InStock' : 'https://schema.org/SoldOut',
            'price': race.entryFee?.length ? String(Math.min(...race.entryFee.filter(e => e.fee).map(e => Number(e.fee))) || 0) : '0',
            'priceCurrency': 'KRW',
            'validFrom': race.registrationStart || race.raceDate,
        },
        'performer': {
            '@type': 'SportsTeam',
            'name': race.organizer || '대회 주최측',
        },
        'organizer': {
            '@type': 'Organization',
            'name': race.organizer || 'EnduroHub',
            'url': race.officialUrl || appUrl,
        },
    });

    const breadcrumbSchema = $derived({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            { '@type': 'ListItem', 'position': 1, 'name': '홈', 'item': appUrl },
            { '@type': 'ListItem', 'position': 2, 'name': '대회 목록', 'item': `${appUrl}/races` },
            { '@type': 'ListItem', 'position': 3, 'name': race.title, 'item': pageUrl },
        ],
    });

    function initMap(lat: number | null, lng: number | null, locationName: string) {
        kakao.maps.load(() => {
            const container = document.getElementById('kakao-map');
            if (container) {
                const position = new kakao.maps.LatLng(lat, lng);
                const map = new kakao.maps.Map(container, {
                    center: position,
                    level: 5,
                });
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
                // Use tick to ensure DOM is updated before initializing map
                requestAnimationFrame(() => initMap(lat, lng, loc));
            } else if (!document.querySelector('script[src*="dapi.kakao.com"]')) {
                const script = document.createElement('script');
                script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${kakaoJsKey}&autoload=false`;
                script.onload = () => initMap(lat, lng, loc);
                document.head.appendChild(script);
            }
        }
    });
</script>

<svelte:window onkeydown={handleKeydown} />

<svelte:head>
    <title>{race.title} | {race.raceDate ? formatDateFull(race.raceDate) : ''} {race.sportLabel} - 엔듀로허브</title>
    <meta name="description" content={metaDesc()} />
    <meta property="og:title" content={race.title} />
    <meta property="og:description" content={metaDesc()} />
    <meta property="og:image" content={ogImage} />
    {@html `<script type="application/ld+json">${JSON.stringify(eventSchema)}</script>`}
    {@html `<script type="application/ld+json">${JSON.stringify(breadcrumbSchema)}</script>`}
</svelte:head>

<div class="container mx-auto px-4 py-8">
    <div class="breadcrumbs text-sm mb-6">
        <ul>
            <li><a href="/">홈</a></li>
            <li><a href="/races">대회 목록</a></li>
            <li>{race.title}</li>
        </ul>
    </div>

    <!-- Hero Banner -->
    <div class="relative rounded-xl overflow-hidden mb-8">
        {#if race.imageSrc}
            <img src={race.imageSrc} alt={race.title} class="w-full h-[240px] sm:h-[300px] lg:h-[360px] object-cover" />
        {:else}
            <div class="w-full h-[240px] sm:h-[300px] lg:h-[360px] bg-gradient-to-br {gradient}"></div>
        {/if}
        <div class="absolute inset-0 bg-gradient-to-t from-black/85 via-black/50 to-black/15"></div>
        <div class="absolute bottom-0 left-0 right-0 p-4 sm:p-6">
            <div class="flex flex-wrap gap-2 mb-3">
                <span class="badge badge-lg shrink-0 min-w-16 {style.badge}">{race.sportLabel}</span>
                <span class="badge badge-lg bg-white/20 text-white border-white/30 shrink-0 min-w-12">{race.region}</span>
                {#if race.status === 'registration_open'}
                    <span class="badge badge-lg badge-success shrink-0 min-w-14">접수중</span>
                {:else if race.status === 'registration_closed'}
                    <span class="badge badge-lg badge-error shrink-0 min-w-14">접수마감</span>
                {:else if race.status === 'finished'}
                    <span class="badge badge-lg badge-ghost shrink-0 min-w-12">종료</span>
                {:else}
                    <span class="badge badge-lg shrink-0 min-w-12">{race.statusLabel}</span>
                {/if}
            </div>
            <h1 class="text-2xl sm:text-3xl font-bold text-white drop-shadow-lg" style="text-shadow: 0 2px 8px rgba(0,0,0,0.6)">{race.title}</h1>
            <div class="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-sm text-white/80" style="text-shadow: 0 1px 4px rgba(0,0,0,0.5)">
                {#if race.raceDate}
                    <span class="flex items-center gap-1">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                        {formatDateFull(race.raceDate)} ({formatDateDay(race.raceDate)})
                        {#if race.daysUntilRace !== null && race.daysUntilRace >= 0}
                            <span class="text-yellow-300 font-semibold">{race.daysUntilRace === 0 ? 'D-Day' : `D-${race.daysUntilRace}`}</span>
                        {/if}
                    </span>
                {/if}
                <span class="flex items-center gap-1">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                    {race.location}
                </span>
            </div>
        </div>
        <div class="absolute top-3 right-3 flex gap-2">
            {#if isAdmin}
                <a
                    href="/admin/races/race/{race.id}/change/"
                    target="_blank"
                    class="btn btn-circle btn-sm bg-black/40 hover:bg-black/60 text-white border-none shadow-lg"
                    aria-label="관리자 수정"
                    title="관리자 페이지에서 수정"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                </a>
            {/if}
            <button onclick={openShareModal} class="btn btn-circle btn-sm bg-black/40 hover:bg-black/60 text-white border-none shadow-lg" aria-label="공유하기">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" /></svg>
            </button>
        </div>
    </div>

    {#if race.aiSummary}
        <div class="flex items-start gap-3 px-4 py-3 mb-8 rounded-lg bg-base-200/60 border border-base-300">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
            <p class="text-sm text-base-content/80 leading-relaxed">{race.aiSummary}</p>
        </div>
    {/if}

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div class="lg:col-span-2">
            <div class="card bg-base-100 shadow-xl">
                <div class="card-body">
                    <p class="text-sm text-base-content/60 mb-4">조회수 {race.viewCount.toLocaleString()}</p>

                    {#if race.description}
                        <div class="prose max-w-none mb-6">
                            {@html race.description.replace(/\n/g, '<br>')}
                        </div>
                    {/if}

                    {#if race.distances && race.distances.length > 0}
                        <div class="mb-6">
                            <h3 class="text-lg font-semibold mb-3">참가 종목</h3>
                            <div class="flex flex-wrap gap-2">
                                {#each race.distances as distance}
                                    <span class="badge badge-lg badge-outline">{distance}</span>
                                {/each}
                            </div>
                        </div>
                    {/if}

                    {#if race.courseImageSrcs && race.courseImageSrcs.length > 0}
                        <div class="mb-6">
                            <h3 class="text-lg font-semibold mb-3">코스 안내</h3>
                            <div class="grid grid-cols-1 {race.courseImageSrcs.length > 1 ? 'md:grid-cols-2' : ''} gap-4">
                                {#each race.courseImageSrcs as src, index}
                                    <button onclick={() => openImageModal(src, `${race.title} 코스 안내 ${index + 1}`)} class="cursor-pointer group">
                                        <img src={src} alt="{race.title} 코스 안내 {index + 1}" class="w-full rounded-lg group-hover:opacity-90 group-hover:shadow-lg transition-all" loading="lazy" />
                                    </button>
                                {/each}
                            </div>
                        </div>
                    {/if}

                    {#if race.latitude && race.longitude}
                        <div class="mb-6">
                            <h3 class="text-lg font-semibold mb-3">대회 장소</h3>
                            <div id="kakao-map" class="w-full h-64 rounded-lg"></div>
                            {#if race.address}
                                <p class="text-sm text-base-content/70 mt-2">{race.address}</p>
                            {/if}
                        </div>
                    {/if}

                    {#if (race.giveaways && race.giveaways.length > 0) || (race.giveawayImageSrcs && race.giveawayImageSrcs.length > 0)}
                        <div class="mb-6">
                            <h3 class="text-lg font-semibold mb-3">사은품</h3>
                            {#if race.giveaways && race.giveaways.length > 0}
                                <div class="flex flex-wrap gap-2 mb-3">
                                    {#each race.giveaways as giveaway}
                                        <span class="badge badge-lg badge-secondary">{giveaway}</span>
                                    {/each}
                                </div>
                            {/if}
                            {#if race.giveawayImageSrcs && race.giveawayImageSrcs.length > 0}
                                <div class="grid grid-cols-1 {race.giveawayImageSrcs.length > 1 ? 'md:grid-cols-2' : ''} gap-4">
                                    {#each race.giveawayImageSrcs as src, index}
                                        <button onclick={() => openImageModal(src, `${race.title} 참가 사은품 ${index + 1}`)} class="cursor-pointer group">
                                            <img src={src} alt="{race.title} 참가 사은품 {index + 1}" class="w-full rounded-lg group-hover:opacity-90 group-hover:shadow-lg transition-all" loading="lazy" />
                                        </button>
                                    {/each}
                                </div>
                            {/if}
                        </div>
                    {/if}
                </div>
            </div>
        </div>

        <div class="space-y-6 lg:sticky lg:top-20 lg:self-start">
            <div class="card bg-base-100 shadow-xl {race.status === 'registration_open' ? 'ring-2 ring-primary/30' : ''}">
                <div class="card-body">
                    {#if race.status === 'registration_open'}
                        <div class="flex items-center gap-2 mb-2">
                            <span class="w-2 h-2 rounded-full bg-success animate-pulse"></span>
                            <span class="text-sm font-semibold text-success">접수중</span>
                        </div>
                    {/if}
                    <h2 class="card-title text-lg mb-4">대회 정보</h2>

                    <div class="space-y-4">
                        {#if race.raceDate}
                            <div class="flex items-start gap-3">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                <div>
                                    <p class="text-sm text-base-content/70">대회일</p>
                                    <p class="font-semibold">
                                        {formatDateFull(race.raceDate)} ({formatDateDay(race.raceDate)})
                                        {#if race.raceEndDate && race.raceEndDate !== race.raceDate}
                                            <br>~ {formatDateShort(race.raceEndDate)}
                                        {/if}
                                    </p>
                                    {#if race.daysUntilRace >= 0}
                                        <p class="text-sm text-primary">{race.daysUntilRace === 0 ? 'D-Day' : `D-${race.daysUntilRace}`}</p>
                                    {/if}
                                </div>
                            </div>
                        {/if}

                        <div class="flex items-start gap-3">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                            <div>
                                <p class="text-sm text-base-content/70">장소</p>
                                <p class="font-semibold">{race.location}</p>
                            </div>
                        </div>

                        {#if race.registrationStart || race.registrationEnd}
                            <div class="flex items-start gap-3">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                <div>
                                    <p class="text-sm text-base-content/70">접수 기간</p>
                                    <p class="font-semibold">
                                        {#if race.registrationStart}{formatDateSlash(race.registrationStart)}{/if}
                                        ~
                                        {#if race.registrationEnd}
                                            {formatDateSlash(race.registrationEnd)}
                                            {#if race.daysUntilRegistrationEnd !== null && race.daysUntilRegistrationEnd >= 0}
                                                <span class="text-error">({race.daysUntilRegistrationEnd === 0 ? 'D-Day' : `D-${race.daysUntilRegistrationEnd}`})</span>
                                            {/if}
                                        {/if}
                                    </p>
                                </div>
                            </div>
                        {/if}

                        {#if race.entryFee && race.entryFee.length > 0}
                            <div class="flex items-start gap-3">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                <div>
                                    <p class="text-sm text-base-content/70">참가비</p>
                                    <div class="space-y-1">
                                        {#each race.entryFee as item}
                                            <p class="font-semibold">
                                                {#if item.distance}<span class="text-base-content/70">{item.distance}</span>{/if}
                                                {#if item.fee}{item.distance ? ' ' : ''}{Number(item.fee).toLocaleString()}원{/if}
                                                {#if !item.distance && !item.fee}-{/if}
                                            </p>
                                        {/each}
                                    </div>
                                </div>
                            </div>
                        {/if}
                    </div>

                    <div class="card-actions mt-6 hidden lg:flex flex-col gap-2">
                        {#if race.officialUrl}
                            <a href={race.officialUrl} target="_blank" rel="noopener" class="btn {race.status === 'registration_open' ? 'btn-primary btn-lg' : 'btn-primary'} btn-block cursor-pointer">
                                {race.status === 'registration_open' ? '공식 사이트에서 접수하기' : '공식사이트로 이동하기'}
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                            </a>
                            {#if race.status === 'registration_open' && race.daysUntilRegistrationEnd !== null && race.daysUntilRegistrationEnd >= 0 && race.daysUntilRegistrationEnd <= 7}
                                <p class="text-center text-sm text-error">
                                    마감까지 {race.daysUntilRegistrationEnd === 0 ? '오늘!' : `${race.daysUntilRegistrationEnd}일 남음`}
                                </p>
                            {/if}
                        {/if}
                    </div>
                </div>
            </div>

            <div class="pt-2 border-t-2 border-base-300">
                <h3 class="text-lg font-bold mb-3 flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" /></svg>
                    참가 후기
                </h3>
                <ReviewList {reviews} stats={reviewStats} />
                <ReviewForm raceSlug={race.slug} {hasReviewed} raceStatus={race.status} />
            </div>
        </div>
    </div>

    {#each relatedRaceSlots as slot}
        {#if slot.races.length > 0}
            <section class="mt-12">
                <h2 class="text-xl font-bold mb-6">{slot.label}</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {#each slot.races as related (related.id)}
                        <RaceCard race={related} />
                    {/each}
                </div>
            </section>
        {/if}
    {/each}

    {#if race.recapUrl}
        <section class="mt-12">
            <h2 class="text-xl font-bold mb-6">대회 후기</h2>
            <div class="card bg-base-100 shadow-lg">
                <div class="card-body flex-row items-center justify-between">
                    <p class="text-base-content/70">블로그에서 대회 후기를 확인해보세요.</p>
                    <a href={race.recapUrl} target="_blank" rel="noopener" class="btn btn-primary btn-sm">
                        대회 후기 보기
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                    </a>
                </div>
            </div>
        </section>
    {/if}

    {#if relatedPosts && relatedPosts.length > 0}
        <section class="mt-12">
            <div class="flex items-center justify-between mb-6">
                <h2 class="text-xl font-bold">관련 게시글</h2>
                <a href="/posts?race={race.id}" class="text-base text-base-content/60 hover:text-primary cursor-pointer">전체보기 →</a>
            </div>
            <div class="space-y-3">
                {#each relatedPosts as post (post.id)}
                    <PostCard {post} />
                {/each}
            </div>
        </section>
    {/if}
</div>

{#if race.officialUrl}
    <div class="h-20 lg:hidden"></div>
    <div class="fixed bottom-0 left-0 right-0 z-40 lg:hidden bg-base-100 border-t border-base-300 px-4 py-3" style="padding-bottom: max(0.75rem, env(safe-area-inset-bottom))">
        <a href={race.officialUrl} target="_blank" rel="noopener" class="btn btn-primary btn-block cursor-pointer">
            {race.status === 'registration_open' ? '공식 사이트에서 접수하기' : '공식사이트로 이동하기'}
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
        </a>
    </div>
{/if}

{#if modalOpen}
    <div class="modal modal-open" role="dialog" aria-modal="true" aria-label="이미지 확대 보기">
        <div class="modal-box max-w-4xl p-2 relative">
            <button onclick={closeImageModal} class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2 z-10" aria-label="닫기">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
            <img src={modalImageSrc} alt={modalImageAlt} class="w-full rounded-lg" />
        </div>
        <button class="modal-backdrop" onclick={closeImageModal} aria-label="닫기"></button>
    </div>
{/if}

{#if shareModalOpen}
    <div class="modal modal-open" role="dialog" aria-modal="true" aria-label="공유하기">
        <div class="modal-box max-w-sm relative">
            <button onclick={closeShareModal} class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2" aria-label="닫기">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
            <h3 class="font-bold text-lg mb-4">공유하기</h3>
            <div class="flex flex-col gap-3">
                <button onclick={() => { shareKakao(); closeShareModal(); }} class="btn btn-block justify-start gap-3 bg-[#FEE500] hover:bg-[#FDD835] text-[#191919] border-none">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" viewBox="0 0 24 24" fill="#191919"><path d="M12 3C6.48 3 2 6.48 2 10.5c0 2.55 1.7 4.8 4.25 6.08-.13.47-.85 3.02-.88 3.24 0 0-.02.17.08.24.1.07.22.03.22.03.3-.04 3.44-2.27 3.98-2.66.77.1 1.56.17 2.35.17 5.52 0 10-3.48 10-7.78C22 6.48 17.52 3 12 3z"/></svg>
                    카카오톡으로 공유
                </button>
                <button onclick={() => { copyLink(); closeShareModal(); }} class="btn btn-block justify-start gap-3">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                    링크 복사
                </button>
            </div>
        </div>
        <button class="modal-backdrop" onclick={closeShareModal} aria-label="닫기"></button>
    </div>
{/if}
