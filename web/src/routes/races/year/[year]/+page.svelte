<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import type { Race } from '$lib/types';
    import type { Sport } from '$lib/types';
    import { formatDateSlash, formatDateDay } from '$lib/date';

    let { data } = $props();

    const races = $derived(data.races as Record<string, Race[]>);
    const year = $derived(data.year as number);
    const totalCount = $derived(data.totalCount as number);

    type StatusType = 'registration_open' | 'registration_closed' | 'upcoming' | 'finished';

    const statuses: { key: StatusType; label: string; color: string }[] = [
        { key: 'registration_open', label: '접수중', color: 'bg-success' },
        { key: 'upcoming', label: '예정', color: 'bg-info' },
        { key: 'registration_closed', label: '접수마감', color: 'bg-warning' },
        { key: 'finished', label: '종료', color: 'bg-base-300' },
    ];

    const regions = ['서울', '경기', '인천', '강원', '충북', '충남', '대전', '세종', '전북', '전남', '광주', '경북', '경남', '대구', '울산', '부산', '제주'];

    const STORAGE_KEY = 'yearly-filter';
    const ALL_SPORTS: Sport[] = ['running', 'swimming', 'cycling', 'triathlon', 'trail_running'];
    const ALL_STATUSES: StatusType[] = ['registration_open', 'registration_closed', 'upcoming', 'finished'];

    let selectedSports = $state<Set<Sport>>(new Set(ALL_SPORTS));
    let selectedRegions = $state<Set<string>>(new Set(regions));
    let selectedStatuses = $state<Set<StatusType>>(new Set(ALL_STATUSES));
    let mobileFilterOpen = $state(false);

    let hasActiveFilter = $derived(
        selectedSports.size < ALL_SPORTS.length ||
        selectedStatuses.size < ALL_STATUSES.length ||
        selectedRegions.size < regions.length
    );

    function saveFilter() {
        const d = {
            sports: [...selectedSports],
            statuses: [...selectedStatuses],
            regions: [...selectedRegions],
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(d));
    }

    let activeMonth = $state<number | null>(null);
    let observer: IntersectionObserver | null = null;

    onMount(() => {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            try {
                const saved = JSON.parse(stored);
                if (saved.sports?.length > 0) selectedSports = new Set(saved.sports.filter((s: string) => ALL_SPORTS.includes(s as Sport)));
                if (saved.statuses?.length > 0) selectedStatuses = new Set(saved.statuses.filter((s: string) => ALL_STATUSES.includes(s as StatusType)));
                if (saved.regions?.length > 0) selectedRegions = new Set(saved.regions.filter((r: string) => regions.includes(r)));
            } catch { /* ignore */ }
        }

        const sections = document.querySelectorAll('section[id^="month-"]');
        observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const month = parseInt(entry.target.id.replace('month-', ''));
                    activeMonth = month;
                    document.getElementById(`month-nav-${month}`)?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
                }
            });
        }, { root: null, rootMargin: '-20% 0px -60% 0px', threshold: 0 });
        sections.forEach(section => observer?.observe(section));
    });

    onDestroy(() => { observer?.disconnect(); });

    const sports = [
        { key: 'running' as Sport, label: '마라톤', color: 'bg-blue-500' },
        { key: 'trail_running' as Sport, label: '트레일러닝', color: 'bg-emerald-500' },
        { key: 'cycling' as Sport, label: '자전거', color: 'bg-amber-500' },
        { key: 'swimming' as Sport, label: '수영', color: 'bg-cyan-500' },
        { key: 'triathlon' as Sport, label: '철인3종', color: 'bg-purple-500' },
    ];

    const sportColorsBg: Record<Sport, string> = {
        running: 'bg-blue-500', swimming: 'bg-cyan-500', cycling: 'bg-amber-500',
        triathlon: 'bg-purple-500', trail_running: 'bg-emerald-500',
    };

    const sportBgColors: Record<Sport, string> = {
        running: 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400',
        swimming: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-500/20 dark:text-cyan-400',
        cycling: 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400',
        triathlon: 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400',
        trail_running: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400',
    };

    const sportBorderColors: Record<Sport, string> = {
        running: 'border-l-blue-500', swimming: 'border-l-cyan-500', cycling: 'border-l-amber-500',
        triathlon: 'border-l-purple-500', trail_running: 'border-l-emerald-500',
    };

    function getMonthRaces(month: number): Race[] {
        const monthRaces = races[String(month)] || [];
        return monthRaces.filter(race => {
            const sportMatch = selectedSports.has(race.sport as Sport);
            const regionMatch = !race.region || selectedRegions.size === 0 || Array.from(selectedRegions).some(r => race.region?.includes(r));
            const statusMatch = selectedStatuses.has(race.status as StatusType);
            return sportMatch && regionMatch && statusMatch;
        });
    }

    function toggleSport(sport: Sport) {
        if (selectedSports.has(sport)) selectedSports.delete(sport);
        else selectedSports.add(sport);
        selectedSports = new Set(selectedSports);
        saveFilter();
    }

    function toggleRegion(region: string) {
        if (selectedRegions.has(region)) selectedRegions.delete(region);
        else selectedRegions.add(region);
        selectedRegions = new Set(selectedRegions);
        saveFilter();
    }

    function toggleStatus(status: StatusType) {
        if (selectedStatuses.has(status)) selectedStatuses.delete(status);
        else selectedStatuses.add(status);
        selectedStatuses = new Set(selectedStatuses);
        saveFilter();
    }

    function resetFilters() {
        selectedSports = new Set(ALL_SPORTS);
        selectedRegions = new Set(regions);
        selectedStatuses = new Set(ALL_STATUSES);
        localStorage.removeItem(STORAGE_KEY);
    }

    function openMobileFilter() { mobileFilterOpen = true; document.body.style.overflow = 'hidden'; }
    function closeMobileFilter() { mobileFilterOpen = false; document.body.style.overflow = ''; }
</script>

<svelte:head>
    <title>{year}년 대회 일정 - EnduroHub</title>
    <meta name="description" content="{year}년 국내 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정을 월별로 확인하세요. 총 {totalCount}개 대회" />
    <meta property="og:title" content="{year}년 대회 일정 - EnduroHub" />
    <meta property="og:description" content="{year}년 국내 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정을 월별로 확인하세요. 총 {totalCount}개 대회" />
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-primary/5 via-base-100 to-secondary/5">
    <div>
        <div class="max-w-6xl mx-auto px-4 py-6 md:py-10">
            <div class="flex flex-col gap-4 md:hidden">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <span class="inline-flex items-center justify-center w-9 h-9 rounded-lg bg-primary/10 text-primary">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                        </span>
                        <h1 class="text-xl font-bold text-base-content">{year}년 대회 일정</h1>
                    </div>
                    <div class="flex items-center gap-0.5 bg-base-100 rounded-lg p-1 shadow-sm border border-base-200">
                        <a href="/races/year/{year - 1}" class="flex items-center justify-center w-8 h-8 rounded-md text-base-content/60 hover:bg-base-200 hover:text-base-content transition-colors cursor-pointer" aria-label="{year - 1}년으로 이동">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" /></svg>
                        </a>
                        <span class="px-3 py-1.5 rounded-md text-sm font-bold bg-primary text-primary-content min-w-[52px] text-center">{year}</span>
                        <a href="/races/year/{year + 1}" class="flex items-center justify-center w-8 h-8 rounded-md text-base-content/60 hover:bg-base-200 hover:text-base-content transition-colors cursor-pointer" aria-label="{year + 1}년으로 이동">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg>
                        </a>
                    </div>
                </div>
                <p class="text-sm text-base-content/60">총 <span class="font-semibold text-primary">{totalCount.toLocaleString()}</span>개 대회</p>
            </div>

            <div class="hidden md:flex items-center justify-between">
                <div>
                    <div class="flex items-center gap-3 mb-2">
                        <span class="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-primary/10 text-primary">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                        </span>
                        <h1 class="text-3xl font-bold text-base-content">{year}년 대회 일정</h1>
                    </div>
                    <p class="text-base-content/60 ml-13">총 <span class="font-semibold text-primary">{totalCount.toLocaleString()}</span>개 대회가 등록되어 있습니다</p>
                </div>
                <div class="flex items-center gap-1 bg-base-100 rounded-xl p-1.5 shadow-sm border border-base-200">
                    <a href="/races/year/{year - 1}" class="flex items-center gap-1.5 px-4 py-2.5 rounded-lg text-base font-medium text-base-content/70 hover:bg-base-200 hover:text-base-content transition-colors cursor-pointer">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" /></svg>
                        {year - 1}
                    </a>
                    <span class="px-5 py-2.5 rounded-lg text-base font-bold bg-primary text-primary-content">{year}</span>
                    <a href="/races/year/{year + 1}" class="flex items-center gap-1.5 px-4 py-2.5 rounded-lg text-base font-medium text-base-content/70 hover:bg-base-200 hover:text-base-content transition-colors cursor-pointer">
                        {year + 1}
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg>
                    </a>
                </div>
            </div>
        </div>
    </div>

    <div class="sticky top-16 z-20 backdrop-blur-lg">
        <div class="max-w-7xl mx-auto px-4 py-3">
            <div class="flex gap-2 overflow-x-auto pb-1 scrollbar-hide" id="month-nav">
                {#each Array(12) as _, i}
                    {@const m = i + 1}
                    {@const monthRaces = getMonthRaces(m)}
                    <a id="month-nav-{m}" href="#month-{m}" class="flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all cursor-pointer {activeMonth === m ? 'bg-primary text-primary-content' : monthRaces.length > 0 ? 'bg-base-200/70 text-base-content hover:bg-primary hover:text-primary-content' : 'bg-base-200/30 text-base-content/30 pointer-events-none'}">
                        <span>{m}월</span>
                        {#if monthRaces.length > 0}
                            <span class="inline-flex items-center justify-center min-w-5 h-5 px-1.5 rounded-md text-xs font-semibold {activeMonth === m ? 'bg-primary-content/20' : 'bg-base-content/10'}">{monthRaces.length}</span>
                        {/if}
                    </a>
                {/each}
            </div>
        </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 py-6">
        <div class="flex gap-6">
            <div class="flex-1 min-w-0">
                {#each Array(12) as _, i}
                    {@const m = i + 1}
                    {@const monthRaces = getMonthRaces(m)}
                    <section id="month-{m}" class="scroll-mt-32 {m > 1 ? 'mt-8' : ''}">
                        <div class="py-3 mb-3">
                            <div class="flex items-center gap-4">
                                <div class="flex items-baseline gap-1.5">
                                    <span class="text-3xl font-bold {monthRaces.length > 0 ? 'text-base-content' : 'text-base-content/20'}">{m}</span>
                                    <span class="text-lg text-base-content/40 font-medium">월</span>
                                </div>
                                {#if monthRaces.length > 0}
                                    <div class="h-px flex-1 bg-gradient-to-r from-base-300 to-transparent"></div>
                                    <span class="text-sm bg-primary/10 text-primary px-3 py-1 rounded-full font-semibold">{monthRaces.length}개 대회</span>
                                {:else}
                                    <div class="h-px flex-1 bg-base-200/50"></div>
                                {/if}
                            </div>
                        </div>

                        {#if monthRaces.length > 0}
                            <div class="hidden md:block overflow-hidden rounded-2xl border border-base-200/70 bg-base-100/80 backdrop-blur-sm shadow-sm">
                                <table class="table w-full">
                                    <thead><tr class="bg-base-200/50"><th class="w-28 py-3 text-sm font-semibold text-base-content/70">날짜</th><th class="w-24 py-3 text-sm font-semibold text-base-content/70">종목</th><th class="py-3 text-sm font-semibold text-base-content/70">대회명</th><th class="w-24 py-3 text-sm font-semibold text-base-content/70">지역</th><th class="w-24 py-3 text-sm font-semibold text-base-content/70 text-center">상태</th></tr></thead>
                                    <tbody class="divide-y divide-base-200/50">
                                        {#each monthRaces as race}
                                            <tr class="hover:bg-base-200/50 transition-colors cursor-pointer group" onclick={() => window.location.href = race.url} tabindex="0" role="link">
                                                <td class="py-3">
                                                    <div class="flex items-center gap-2.5">
                                                        <span class="w-1 h-10 rounded-full {sportColorsBg[race.sport as Sport] || 'bg-gray-400'}"></span>
                                                        <div>
                                                            <div class="text-base font-semibold text-base-content">{race.raceDate ? formatDateSlash(race.raceDate) : '-'}</div>
                                                            <div class="text-sm text-base-content/50">{race.raceDate ? formatDateDay(race.raceDate) + '요일' : ''}</div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td class="py-3"><span class="inline-flex min-w-24"><span class="inline-flex px-2.5 py-1 rounded-md text-sm font-semibold whitespace-nowrap justify-center {sportBgColors[race.sport as Sport] || 'bg-gray-100 text-gray-700'}">{race.sportLabel}</span></span></td>
                                                <td class="py-3"><span class="text-base font-medium text-base-content group-hover:text-primary transition-colors">{race.title.length > 45 ? race.title.substring(0, 45) + '...' : race.title}</span></td>
                                                <td class="py-3"><span class="text-base text-base-content/70">{race.region || '-'}</span></td>
                                                <td class="py-3 text-center">
                                                    {#if race.status === 'registration_open'}
                                                        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm font-semibold whitespace-nowrap min-w-14 justify-center bg-success/15 text-success"><span class="w-1.5 h-1.5 rounded-full bg-success animate-pulse"></span>접수중</span>
                                                    {:else if race.status === 'registration_closed'}
                                                        <span class="inline-flex px-2.5 py-1 rounded-full text-sm font-medium whitespace-nowrap min-w-14 justify-center bg-warning/10 text-warning">접수마감</span>
                                                    {:else if race.status === 'finished'}
                                                        <span class="inline-flex px-2.5 py-1 rounded-full text-sm font-medium whitespace-nowrap min-w-14 justify-center bg-base-200 text-base-content/50">종료</span>
                                                    {:else}
                                                        <span class="inline-flex px-2.5 py-1 rounded-full text-sm font-medium whitespace-nowrap min-w-14 justify-center bg-info/10 text-info">예정</span>
                                                    {/if}
                                                </td>
                                            </tr>
                                        {/each}
                                    </tbody>
                                </table>
                            </div>

                            <div class="md:hidden space-y-2.5">
                                {#each monthRaces as race}
                                    <a href={race.url} class="block p-4 rounded-xl border border-base-200/70 bg-base-100/80 backdrop-blur-sm border-l-4 {sportBorderColors[race.sport as Sport] || 'border-l-gray-400'} hover:shadow-md hover:border-base-300 transition-all cursor-pointer active:scale-[0.99]">
                                        <div class="flex items-start justify-between gap-3">
                                            <div class="flex-1 min-w-0">
                                                <h3 class="text-base font-semibold text-base-content line-clamp-2">{race.title}</h3>
                                                <div class="flex items-center gap-2 mt-2 text-sm text-base-content/60">
                                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-base-content/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                                    <span class="font-medium">{race.raceDate ? `${formatDateSlash(race.raceDate)}(${formatDateDay(race.raceDate)})` : '-'}</span>
                                                    {#if race.region}<span class="text-base-content/30">&#8226;</span><span>{race.region}</span>{/if}
                                                </div>
                                                <div class="flex items-center gap-2 mt-2.5">
                                                    <span class="inline-flex px-2.5 py-1 rounded-md text-sm font-semibold min-w-16 justify-center {sportBgColors[race.sport as Sport] || 'bg-gray-100 text-gray-700'}">{race.sportLabel}</span>
                                                    {#if race.status === 'registration_open'}
                                                        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm font-semibold min-w-14 justify-center bg-success/15 text-success"><span class="w-1.5 h-1.5 rounded-full bg-success animate-pulse"></span>접수중</span>
                                                    {:else if race.status === 'registration_closed'}
                                                        <span class="inline-flex px-2.5 py-1 rounded-full text-sm font-medium min-w-14 justify-center bg-warning/10 text-warning">접수마감</span>
                                                    {:else if race.status === 'finished'}
                                                        <span class="inline-flex px-2.5 py-1 rounded-full text-sm font-medium min-w-14 justify-center bg-base-200 text-base-content/50">종료</span>
                                                    {:else}
                                                        <span class="inline-flex px-2.5 py-1 rounded-full text-sm font-medium min-w-14 justify-center bg-info/10 text-info">예정</span>
                                                    {/if}
                                                </div>
                                            </div>
                                            <div class="flex items-center justify-center w-8 h-8 rounded-full bg-base-200/50 flex-shrink-0 mt-1">
                                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-base-content/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg>
                                            </div>
                                        </div>
                                    </a>
                                {/each}
                            </div>
                        {:else}
                            <div class="text-center py-12 px-4">
                                <div class="inline-flex items-center justify-center w-14 h-14 rounded-full bg-base-200/50 mb-4">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 text-base-content/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                </div>
                                <p class="text-base-content/40 text-base">등록된 대회가 없습니다</p>
                            </div>
                        {/if}
                    </section>
                {/each}
            </div>

            <aside class="hidden lg:block w-64 flex-shrink-0">
                <div class="sticky top-36">
                    <div class="bg-base-100/80 backdrop-blur-sm rounded-2xl border border-base-200/70 p-5 shadow-sm">
                        <h3 class="text-sm font-semibold text-base-content/70 uppercase tracking-wider mb-4">필터</h3>
                        <div class="mb-6">
                            <h4 class="text-sm font-medium text-base-content mb-3">종목</h4>
                            <div class="space-y-2">
                                {#each sports as sport}
                                    <label class="flex items-center gap-3 cursor-pointer group">
                                        <input type="checkbox" class="checkbox checkbox-sm checkbox-primary" checked={selectedSports.has(sport.key)} onchange={() => toggleSport(sport.key)} />
                                        <span class="w-2 h-2 rounded-full {sport.color}"></span>
                                        <span class="text-sm text-base-content/80 group-hover:text-base-content transition-colors">{sport.label}</span>
                                    </label>
                                {/each}
                            </div>
                        </div>
                        <div class="mb-6">
                            <h4 class="text-sm font-medium text-base-content mb-3">상태</h4>
                            <div class="space-y-2">
                                {#each statuses as status}
                                    <label class="flex items-center gap-3 cursor-pointer group">
                                        <input type="checkbox" class="checkbox checkbox-sm checkbox-primary" checked={selectedStatuses.has(status.key)} onchange={() => toggleStatus(status.key)} />
                                        <span class="w-2 h-2 rounded-full {status.color}"></span>
                                        <span class="text-sm text-base-content/80 group-hover:text-base-content transition-colors">{status.label}</span>
                                    </label>
                                {/each}
                            </div>
                        </div>
                        <div>
                            <h4 class="text-sm font-medium text-base-content mb-3">지역</h4>
                            <div class="space-y-2 max-h-64 overflow-y-auto pr-2">
                                {#each regions as region}
                                    <label class="flex items-center gap-3 cursor-pointer group">
                                        <input type="checkbox" class="checkbox checkbox-sm checkbox-primary" checked={selectedRegions.has(region)} onchange={() => toggleRegion(region)} />
                                        <span class="text-sm text-base-content/80 group-hover:text-base-content transition-colors">{region}</span>
                                    </label>
                                {/each}
                            </div>
                        </div>
                        {#if hasActiveFilter}
                            <button onclick={resetFilters} class="btn btn-sm btn-outline btn-error w-full mt-5 cursor-pointer">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                                필터 모두 지우기
                            </button>
                        {/if}
                    </div>
                </div>
            </aside>
        </div>
    </div>

    <button onclick={openMobileFilter} class="lg:hidden fixed bottom-6 left-6 flex items-center gap-2 px-4 py-3 rounded-full bg-base-100 text-base-content shadow-lg border border-base-200 hover:shadow-xl transition-all cursor-pointer z-30">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>
        <span class="text-sm font-medium">필터</span>
    </button>

    <button onclick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} class="fixed bottom-6 right-6 flex items-center justify-center w-12 h-12 rounded-full bg-primary text-primary-content shadow-lg hover:shadow-xl hover:scale-105 transition-all cursor-pointer z-30" aria-label="맨 위로 이동">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" /></svg>
    </button>
</div>

{#if mobileFilterOpen}
    <div class="lg:hidden fixed inset-0 z-[9999]">
        <div class="absolute inset-0 bg-black/50" onclick={closeMobileFilter} role="button" tabindex="0" aria-label="모달 닫기"></div>
        <div class="absolute bottom-0 left-0 right-0 bg-base-100 rounded-t-3xl p-6 max-h-[80vh] overflow-y-auto animate-slide-up">
            <div class="flex items-center justify-between mb-6">
                <h3 class="text-lg font-semibold text-base-content">필터</h3>
                <button onclick={closeMobileFilter} class="btn btn-sm btn-circle btn-ghost" aria-label="닫기">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
            </div>
            <div class="mb-6">
                <h4 class="text-sm font-medium text-base-content mb-3">종목</h4>
                <div class="flex flex-wrap gap-2">
                    {#each sports as sport}
                        <button onclick={() => toggleSport(sport.key)} class="inline-flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium transition-all cursor-pointer {selectedSports.has(sport.key) ? 'bg-primary text-primary-content border-primary' : 'border-base-200'}">
                            <span class="w-2 h-2 rounded-full {sport.color}"></span>{sport.label}
                        </button>
                    {/each}
                </div>
            </div>
            <div class="mb-6">
                <h4 class="text-sm font-medium text-base-content mb-3">상태</h4>
                <div class="flex flex-wrap gap-2">
                    {#each statuses as status}
                        <button onclick={() => toggleStatus(status.key)} class="inline-flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium transition-all cursor-pointer {selectedStatuses.has(status.key) ? 'bg-primary text-primary-content border-primary' : 'border-base-200'}">
                            <span class="w-2 h-2 rounded-full {status.color}"></span>{status.label}
                        </button>
                    {/each}
                </div>
            </div>
            <div class="mb-6">
                <h4 class="text-sm font-medium text-base-content mb-3">지역</h4>
                <div class="flex flex-wrap gap-2">
                    {#each regions as region}
                        <button onclick={() => toggleRegion(region)} class="inline-flex px-3 py-2 rounded-lg border text-sm font-medium transition-all cursor-pointer {selectedRegions.has(region) ? 'bg-primary text-primary-content border-primary' : 'border-base-200'}">{region}</button>
                    {/each}
                </div>
            </div>
            <div class="flex gap-2">
                {#if hasActiveFilter}
                    <button onclick={resetFilters} class="btn btn-outline btn-error cursor-pointer">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                        초기화
                    </button>
                {/if}
                <button onclick={closeMobileFilter} class="btn btn-primary flex-1 cursor-pointer">필터 적용</button>
            </div>
        </div>
    </div>
{/if}

<style>
    @keyframes slide-up { from { transform: translateY(100%); } to { transform: translateY(0); } }
    .animate-slide-up { animation: slide-up 0.3s ease-out; }
    .scrollbar-hide::-webkit-scrollbar { display: none; }
    .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
    .line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>
