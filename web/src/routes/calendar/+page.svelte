<script lang="ts">
    import { goto } from '$app/navigation';
    import type { Race, SportOption } from '$lib/types';

    let { data } = $props();

    const year = $derived(data.year as number);
    const month = $derived(data.month as number);
    const startOfMonth = $derived(data.startOfMonth as string);
    const racesGrouped = $derived(data.racesGrouped as Record<string, Race[]>);
    const previousMonth = $derived(data.previousMonth);
    const nextMonth = $derived(data.nextMonth);
    const sport = $derived(data.sport as string | null);
    const sports = $derived(data.sports as SportOption[]);

    type StatusType = 'registration_open' | 'registration_closed' | 'upcoming' | 'finished';

    const statusOptions: { key: StatusType; label: string; color: string }[] = [
        { key: 'registration_open', label: '접수중', color: 'bg-success' },
        { key: 'upcoming', label: '예정', color: 'bg-info' },
        { key: 'registration_closed', label: '접수마감', color: 'bg-warning' },
        { key: 'finished', label: '종료', color: 'bg-base-300' },
    ];

    let selectedStatuses = $state<Set<StatusType>>(new Set(['registration_open', 'registration_closed', 'upcoming', 'finished']));

    function toggleStatus(status: StatusType) {
        if (selectedStatuses.has(status)) selectedStatuses.delete(status);
        else selectedStatuses.add(status);
        selectedStatuses = new Set(selectedStatuses);
    }

    const dayNames = ['일', '월', '화', '수', '목', '금', '토'];

    const sportColors: Record<string, { bg: string; 'bg-light': string; text: string; border: string }> = {
        running: { bg: 'bg-primary', 'bg-light': 'bg-primary/10', text: 'text-primary', border: 'border-primary' },
        swimming: { bg: 'bg-info', 'bg-light': 'bg-info/10', text: 'text-info', border: 'border-info' },
        cycling: { bg: 'bg-warning', 'bg-light': 'bg-warning/10', text: 'text-warning', border: 'border-warning' },
        triathlon: { bg: 'bg-secondary', 'bg-light': 'bg-secondary/10', text: 'text-secondary', border: 'border-secondary' },
        trail_running: { bg: 'bg-success', 'bg-light': 'bg-success/10', text: 'text-success', border: 'border-success' },
    };

    const startDate = $derived(new Date(startOfMonth));
    const firstDayOfMonth = $derived(startDate.getDay());
    const daysInMonth = $derived(new Date(year, month, 0).getDate());
    const today = $derived(new Date().toISOString().split('T')[0]);
    const filteredRaces = $derived(Object.values(racesGrouped).flat().filter(r => selectedStatuses.has(r.status as StatusType)));
    const totalRacesThisMonth = $derived(filteredRaces.length);
    const sortedMonthRaces = $derived([...filteredRaces].sort((a, b) => (a.raceDate || '').localeCompare(b.raceDate || '')));

    function getDateString(day: number): string {
        return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    }

    function getDayRaces(day: number): Race[] {
        const dateStr = getDateString(day);
        const races = racesGrouped[dateStr] || [];
        return races.filter(race => selectedStatuses.has(race.status as StatusType));
    }

    function getColors(sportType: string) {
        return sportColors[sportType] || sportColors.running;
    }

    function getSportCount(sportKey: string): number {
        return filteredRaces.filter(r => r.sport === sportKey).length;
    }

    function handleSportFilter(value: string | null) {
        const params = new URLSearchParams();
        params.set('year', String(year));
        params.set('month', String(month));
        if (value) params.set('sport', value);
        goto(`/calendar?${params.toString()}`, { replaceState: true });
    }

    let dayModalOpen = $state(false);
    let dayModalTitle = $state('');
    let dayModalRaces = $state<Race[]>([]);

    function openDayModal(title: string, races: Race[]) {
        if (window.innerWidth >= 768) return;
        dayModalTitle = title;
        dayModalRaces = races;
        dayModalOpen = true;
    }

    function closeDayModal() { dayModalOpen = false; }
</script>

<svelte:head>
    <title>{year}년 {month}월 대회 캘린더 - 엔듀로허브</title>
    <meta name="description" content="{year}년 {month}월 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정" />
    <meta property="og:title" content="{year}년 {month}월 대회 캘린더 - 엔듀로허브" />
    <meta property="og:description" content="{year}년 {month}월 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정" />
</svelte:head>

<div class="container mx-auto px-4 py-8">
    <div class="flex items-center justify-between gap-2 mb-1 md:mb-2">
        <div>
            <h1 class="text-xl md:text-2xl font-bold">대회 캘린더</h1>
            <p class="text-base-content/50 text-xs md:text-sm hidden md:block">월별 대회 일정을 확인하세요</p>
        </div>
        <div class="text-xs md:text-sm text-base-content/50">
            <span class="font-semibold text-base-content">{totalRacesThisMonth}</span>개
        </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-4 gap-2">
        <div class="xl:col-span-3 -mx-4 md:mx-0">
            <div class="border-y md:border border-base-300 md:rounded-lg bg-base-100">
                <div class="p-1 md:p-2">
                    <div class="flex items-center justify-between mb-1 md:mb-2">
                        <a href="/calendar?year={previousMonth.year}&month={previousMonth.month}{sport ? `&sport=${sport}` : ''}" class="text-sm md:text-base text-base-content/60 hover:text-primary cursor-pointer">
                            ← <span class="hidden md:inline">{previousMonth.month}월</span>
                        </a>
                        <div class="flex items-center gap-1 md:gap-2">
                            <h2 class="text-lg md:text-xl font-bold">{year}.{month}</h2>
                            <a href="/calendar{sport ? `?sport=${sport}` : ''}" class="text-xs text-base-content/40 hover:text-primary cursor-pointer" title="오늘">오늘</a>
                        </div>
                        <a href="/calendar?year={nextMonth.year}&month={nextMonth.month}{sport ? `&sport=${sport}` : ''}" class="text-sm md:text-base text-base-content/60 hover:text-primary cursor-pointer">
                            <span class="hidden md:inline">{nextMonth.month}월</span> →
                        </a>
                    </div>

                    <div class="grid grid-cols-7 gap-px">
                        {#each dayNames as dayName, index}
                            <div class="text-center text-xs md:text-sm font-medium py-0.5 md:py-1 {index === 0 ? 'text-error' : index === 6 ? 'text-info' : 'text-base-content/50'}">{dayName}</div>
                        {/each}

                        {#each Array(firstDayOfMonth) as _}
                            <div class="h-[100px] md:h-[130px] bg-base-200/30 rounded"></div>
                        {/each}

                        {#each Array(daysInMonth) as _, i}
                            {@const day = i + 1}
                            {@const dateStr = getDateString(day)}
                            {@const dayRaces = getDayRaces(day)}
                            {@const isToday = dateStr === today}
                            {@const dayOfWeek = (firstDayOfMonth + i) % 7}
                            {@const hasRaces = dayRaces.length > 0}

                            <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
                            <div
                                class="h-[100px] md:h-[130px] rounded border transition-colors cursor-pointer md:cursor-default overflow-hidden {isToday ? 'bg-primary/5 border-primary' : hasRaces ? 'bg-base-100 border-base-300 hover:border-base-400' : 'bg-base-100 border-base-200'}"
                                onclick={() => hasRaces && openDayModal(`${month}월 ${day}일`, dayRaces)}
                                onkeydown={(e) => { if (hasRaces && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); openDayModal(`${month}월 ${day}일`, dayRaces); } }}
                                tabindex={hasRaces ? 0 : undefined}
                                role={hasRaces ? 'button' : undefined}
                                aria-label={hasRaces ? `${month}월 ${day}일 대회 ${dayRaces.length}개 보기` : undefined}
                            >
                                <div class="flex items-center justify-between p-0.5 md:p-1">
                                    <span class="text-sm md:text-base font-medium {isToday ? 'bg-primary text-primary-content w-5 h-5 md:w-6 md:h-6 rounded flex items-center justify-center text-xs' : ''} {dayOfWeek === 0 && !isToday ? 'text-error' : ''} {dayOfWeek === 6 && !isToday ? 'text-info' : ''}">{day}</span>
                                    {#if hasRaces}
                                        <span class="text-[10px] md:text-xs text-base-content/40">{dayRaces.length}</span>
                                    {/if}
                                </div>
                                <div class="px-0.5 pb-0.5 space-y-0.5">
                                    {#each dayRaces.slice(0, 2) as race}
                                        {@const colors = getColors(race.sport)}
                                        <div>
                                            <a href={race.url} class="block text-[10px] md:text-xs p-0.5 rounded cursor-pointer pointer-events-none md:pointer-events-auto {colors['bg-light']} {colors.text} border-l {colors.border}" title="{race.title} - {race.location}" onclick={(e) => e.stopPropagation()}>
                                                <span class="line-clamp-2">{race.title}</span>
                                            </a>
                                        </div>
                                    {/each}
                                    {#if dayRaces.length > 2}
                                        {@const dropdownPosition = dayOfWeek <= 3 ? 'dropdown-start' : 'dropdown-end'}
                                        <div class="dropdown dropdown-top {dropdownPosition} w-full">
                                            <div tabindex="0" role="button" class="text-xs text-center py-0.5 text-base-content/40 hover:text-primary hover:bg-primary/10 rounded cursor-pointer transition-colors">
                                                +{dayRaces.length - 2}개 더보기
                                            </div>
                                            <div class="dropdown-content z-50 bg-base-100 shadow-lg rounded-lg p-3 w-64 max-h-80 overflow-y-auto border border-base-300">
                                                <div class="flex items-center gap-2 mb-2 pb-2 border-b border-base-200">
                                                    <span class="text-sm font-semibold">{month}월 {day}일</span>
                                                    <span class="text-xs text-base-content/50">{dayRaces.length}개</span>
                                                </div>
                                                <div class="space-y-1.5">
                                                    {#each dayRaces as race}
                                                        {@const colors = getColors(race.sport)}
                                                        <a href={race.url} class="block p-2 rounded cursor-pointer {colors['bg-light']} border-l-2 {colors.border}">
                                                            <div class="text-xs font-medium {colors.text}">{race.title}</div>
                                                            <div class="text-[10px] text-base-content/50 mt-0.5">{race.location}</div>
                                                        </a>
                                                    {/each}
                                                </div>
                                            </div>
                                        </div>
                                    {/if}
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            </div>
        </div>

        <div class="xl:col-span-1 space-y-4">
            <div class="border border-base-300 rounded-lg bg-base-100 p-4">
                <h3 class="font-semibold text-sm mb-3">종목 필터</h3>
                <div class="space-y-1.5">
                    <label class="flex items-center gap-2 p-2 rounded cursor-pointer transition-colors {!sport ? 'bg-primary/10' : 'hover:bg-base-200'}">
                        <input type="radio" name="sport" value="" class="radio radio-primary radio-xs" checked={!sport} onchange={() => handleSportFilter(null)} />
                        <span class="text-sm {!sport ? 'text-primary font-medium' : ''}">전체</span>
                    </label>
                    {#each sports as s}
                        {@const colors = getColors(s.value)}
                        <label class="flex items-center gap-2 p-2 rounded cursor-pointer transition-colors {sport === s.value ? colors['bg-light'] : 'hover:bg-base-200'}">
                            <input type="radio" name="sport" value={s.value} class="radio radio-xs {colors.text}" checked={sport === s.value} onchange={() => handleSportFilter(s.value)} />
                            <span class="w-2 h-2 rounded-full {colors.bg}"></span>
                            <span class="text-sm {sport === s.value ? colors.text + ' font-medium' : ''}">{s.label}</span>
                        </label>
                    {/each}
                </div>
            </div>

            <div class="border border-base-300 rounded-lg bg-base-100 p-4">
                <h3 class="font-semibold text-sm mb-3">상태 필터</h3>
                <div class="space-y-1.5">
                    {#each statusOptions as status}
                        <label class="flex items-center gap-2 p-2 rounded cursor-pointer transition-colors hover:bg-base-200">
                            <input type="checkbox" class="checkbox checkbox-xs checkbox-primary" checked={selectedStatuses.has(status.key)} onchange={() => toggleStatus(status.key)} />
                            <span class="w-2 h-2 rounded-full {status.color}"></span>
                            <span class="text-sm">{status.label}</span>
                        </label>
                    {/each}
                </div>
            </div>

            <div class="border border-base-300 rounded-lg bg-base-100 p-4">
                <h3 class="font-semibold text-sm mb-3">범례</h3>
                <div class="space-y-2">
                    {#each [{ key: 'running', name: '마라톤' }, { key: 'swimming', name: '수영' }, { key: 'cycling', name: '자전거' }, { key: 'triathlon', name: '철인3종' }, { key: 'trail_running', name: '트레일러닝' }] as item}
                        {@const colors = getColors(item.key)}
                        <div class="flex items-center gap-2"><div class="w-3 h-3 rounded {colors.bg}"></div><span class="text-xs">{item.name}</span></div>
                    {/each}
                </div>
            </div>

            <div class="bg-neutral rounded-lg p-4 text-neutral-content">
                <h3 class="font-semibold text-sm mb-3">{month}월 요약</h3>
                <div class="space-y-2">
                    {#each [{ key: 'running', name: '마라톤' }, { key: 'swimming', name: '수영' }, { key: 'cycling', name: '자전거' }, { key: 'triathlon', name: '철인3종' }, { key: 'trail_running', name: '트레일러닝' }] as item}
                        {@const colors = getColors(item.key)}
                        {@const count = getSportCount(item.key)}
                        <div class="flex items-center justify-between text-sm">
                            <div class="flex items-center gap-2"><div class="w-1.5 h-1.5 rounded-full {colors.bg}"></div><span class="text-neutral-content/60">{item.name}</span></div>
                            <span class="font-medium">{count}</span>
                        </div>
                    {/each}
                    <div class="pt-2 mt-2 border-t border-neutral-content/10 flex items-center justify-between">
                        <span class="text-sm text-neutral-content/60">총</span>
                        <span class="font-bold">{totalRacesThisMonth}개</span>
                    </div>
                </div>
            </div>

            <div class="border border-base-300 rounded-lg bg-base-100 p-4">
                <h3 class="font-semibold text-sm mb-3">바로가기</h3>
                <div class="space-y-1">
                    <a href="/races" class="block text-sm text-base-content/60 hover:text-primary py-1 cursor-pointer">전체 대회 목록 →</a>
                    <a href="/" class="block text-sm text-base-content/60 hover:text-primary py-1 cursor-pointer">홈으로 →</a>
                </div>
            </div>
        </div>
    </div>

    {#if sortedMonthRaces.length > 0}
        <div class="mt-6 border border-base-300 rounded-lg bg-base-100">
            <div class="p-4 border-b border-base-200">
                <h2 class="font-bold text-lg">{month}월 대회 일정</h2>
                <p class="text-sm text-base-content/50">{sortedMonthRaces.length}개 대회</p>
            </div>
            <div class="divide-y divide-base-200">
                {#each sortedMonthRaces as race}
                    {@const colors = getColors(race.sport)}
                    {@const raceDay = race.raceDate ? parseInt(race.raceDate.split('-')[2]) : 0}
                    {@const dayOfWeekIdx = race.raceDate ? new Date(race.raceDate).getDay() : 0}
                    {@const dayLabel = dayNames[dayOfWeekIdx]}
                    <a href={race.url} class="flex items-center gap-4 p-4 hover:bg-base-200/50 transition-colors cursor-pointer">
                        <div class="text-center shrink-0 w-12">
                            <div class="text-lg font-bold">{raceDay}</div>
                            <div class="text-xs text-base-content/50 {dayOfWeekIdx === 0 ? 'text-error' : dayOfWeekIdx === 6 ? 'text-info' : ''}">{dayLabel}</div>
                        </div>
                        <div class="w-1 h-8 rounded-full {colors.bg} shrink-0"></div>
                        <div class="flex-1 min-w-0">
                            <div class="font-medium text-sm truncate">{race.title}</div>
                            <div class="flex items-center gap-2 mt-0.5">
                                <span class="inline-flex items-center shrink-0 px-1.5 py-px rounded text-[11px] font-medium leading-none whitespace-nowrap {colors['bg-light']} {colors.text}">{race.sportLabel}</span>
                                {#if race.distances && race.distances.length > 0}
                                    <span class="text-xs text-base-content/50 truncate">{race.distances.join(', ')}</span>
                                {/if}
                            </div>
                        </div>
                        <div class="shrink-0">
                            {#if race.status === 'registration_open'}
                                <span class="badge badge-success badge-sm">접수중</span>
                            {:else if race.status === 'upcoming'}
                                <span class="badge badge-info badge-sm">예정</span>
                            {:else if race.status === 'registration_closed'}
                                <span class="badge badge-warning badge-sm">접수마감</span>
                            {:else}
                                <span class="badge badge-ghost badge-sm">종료</span>
                            {/if}
                        </div>
                    </a>
                {/each}
            </div>
        </div>
    {/if}
</div>

{#if dayModalOpen}
    <div class="modal modal-open md:hidden">
        <div class="modal-box max-w-sm">
            <h3 class="font-bold text-lg mb-4">{dayModalTitle}</h3>
            <div class="space-y-2">
                {#each dayModalRaces as race}
                    {@const colors = getColors(race.sport)}
                    <a href={race.url} class="block p-3 rounded {colors['bg-light']} border-l-2 {colors.border}">
                        <div class="font-medium {colors.text}">{race.title}</div>
                        <div class="text-xs text-base-content/50 mt-1">{race.location}</div>
                    </a>
                {/each}
            </div>
            <div class="modal-action">
                <button class="btn btn-sm cursor-pointer" onclick={closeDayModal}>닫기</button>
            </div>
        </div>
        <button class="modal-backdrop" onclick={closeDayModal} aria-label="닫기"></button>
    </div>
{/if}
