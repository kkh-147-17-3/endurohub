<script lang="ts">
    import { goto } from '$app/navigation';
    import type { Race, Sport } from '$lib/types';
    import { sportStyles, sportEmojis } from '$lib/race';
    import { formatDate, formatDateShort, formatDateSlash } from '$lib/date';
    import { track } from '$lib/analytics';

    let { race, variant = 'default', eager = false }: { race: Race; variant?: 'default' | 'minimal'; eager?: boolean } = $props();

    let style = $derived(sportStyles[race.sport as Sport] || sportStyles.running);
    let emoji = $derived(sportEmojis[race.sport as Sport] || '🏃');

    let dDayBadgeClass = $derived(
        race.daysUntilRegistrationEnd !== null && race.daysUntilRegistrationEnd <= 3
            ? 'bg-error text-error-content'
            : 'bg-neutral text-neutral-content'
    );

    function handleClick() {
        track('race_click', {
            race_slug: race.slug,
            race_title: race.title,
            race_sport: race.sport,
            race_status: race.status,
            variant,
        });
        goto(race.url);
    }
</script>

{#if variant === 'minimal'}
    <div
        class="bg-base-100 border border-base-200 rounded-xl p-3 hover:border-primary/50 transition-colors cursor-pointer group flex items-start gap-3 min-h-[48px]"
        onclick={handleClick}
        onkeypress={(e) => e.key === 'Enter' && handleClick()}
        role="button"
        tabindex="0"
    >
        <div class="w-12 h-12 rounded-lg {style.bgLight} flex items-center justify-center shrink-0 text-2xl">
            {emoji}
        </div>
        <div class="flex flex-col min-w-0 flex-1">
            <h4 class="text-[13px] lg:text-sm font-bold text-base-content leading-snug group-hover:text-primary transition-colors truncate">
                {race.title}
            </h4>
            <div class="flex items-center gap-2 mt-1">
                <span class="text-[10px] lg:text-xs text-base-content/50">{race.raceDate ?? ''}</span>
                {#if race.daysUntilRegistrationEnd != null}
                    <span class="text-[10px] lg:text-xs text-base-content/50">·</span>
                    <span class="text-[10px] lg:text-xs font-bold {race.daysUntilRegistrationEnd <= 3 ? 'text-error' : 'text-success'}">
                        {race.daysUntilRegistrationEnd === 0 ? 'D-Day' : `D-${race.daysUntilRegistrationEnd}`}
                    </span>
                {/if}
            </div>
        </div>
    </div>
{:else}
    <div
        class="bg-base-100 border border-base-300 rounded-lg {style.hoverBorder} transition-colors duration-200 cursor-pointer group relative overflow-hidden flex flex-col"
        onclick={handleClick}
        onkeypress={(e) => e.key === 'Enter' && handleClick()}
        role="button"
        tabindex="0"
    >
        <div class="absolute left-0 top-0 bottom-0 w-1 {style.bg} rounded-l-lg z-10"></div>

        {#if race.imageSrc}
            <figure class="relative">
                <img src={race.imageSrcThumb || race.imageSrc} alt={race.title} class="w-full aspect-[5/3] object-cover rounded-t-lg" loading={eager ? 'eager' : 'lazy'} fetchpriority={eager ? 'high' : 'auto'} />
                <div class="absolute inset-0 rounded-t-lg ring-1 ring-inset ring-black/5 pointer-events-none"></div>
                {#if race.daysUntilRegistrationEnd !== null && race.daysUntilRegistrationEnd <= 7 && race.daysUntilRegistrationEnd >= 0}
                    <div class="absolute top-2 right-2">
                        <span class="text-xs font-bold px-2.5 py-1 rounded-full {dDayBadgeClass}">{race.daysUntilRegistrationEnd === 0 ? 'D-Day' : `D-${race.daysUntilRegistrationEnd}`}</span>
                    </div>
                {/if}
            </figure>
        {:else}
            <figure class="relative aspect-[5/3] {style.bgLight} flex items-center justify-center rounded-t-lg">
                <div class="text-4xl">{emoji}</div>
                {#if race.daysUntilRegistrationEnd !== null && race.daysUntilRegistrationEnd <= 7 && race.daysUntilRegistrationEnd >= 0}
                    <div class="absolute top-2 right-2">
                        <span class="text-xs font-bold px-2.5 py-1 rounded-full {dDayBadgeClass}">{race.daysUntilRegistrationEnd === 0 ? 'D-Day' : `D-${race.daysUntilRegistrationEnd}`}</span>
                    </div>
                {/if}
            </figure>
        {/if}

        <div class="p-4 flex flex-col flex-1">
            <div class="flex flex-wrap items-center gap-1.5 mb-2 min-h-[44px]">
                <span class="badge {style.badge} badge-sm shrink-0 min-w-14">{race.sportLabel}</span>
                <span class="badge badge-ghost badge-sm shrink-0 min-w-10">{race.region}</span>
                {#if race.status === 'registration_open'}
                    <span class="badge badge-success badge-sm font-semibold shrink-0 min-w-10">접수중</span>
                {/if}
                {#if race.officialUrl}
                    <a
                        href={race.officialUrl}
                        target="_blank"
                        rel="noopener"
                        onclick={(e) => e.stopPropagation()}
                        class="text-xs text-base-content/50 {style.hoverText} cursor-pointer inline-flex items-center gap-1 ml-auto"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                        공식
                    </a>
                {/if}
            </div>

            <h2 class="font-semibold text-base leading-snug mb-2 min-h-[44px] flex items-center">
                <a href={race.url} class="group-hover:text-primary transition-colors line-clamp-2">
                    {race.title}
                </a>
            </h2>

            <div class="text-sm text-base-content/50 space-y-1.5">
                <p class="flex items-center gap-1.5">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {formatDate(race.raceDate ?? '')}
                    {#if race.raceEndDate && race.raceEndDate !== race.raceDate}
                        - {formatDateShort(race.raceEndDate ?? '')}
                    {/if}
                </p>
                <p class="flex items-center gap-1.5">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <span class="truncate">{race.location}</span>
                </p>
                {#if race.registrationEnd}
                    <p class="flex items-center gap-1.5">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        접수마감 {formatDateSlash(race.registrationEnd)}
                        {#if race.daysUntilRegistrationEnd !== null && race.daysUntilRegistrationEnd >= 0}
                            <span class="{race.daysUntilRegistrationEnd !== null && race.daysUntilRegistrationEnd <= 3 ? 'text-error' : 'text-base-content/70'} font-semibold">({race.daysUntilRegistrationEnd === 0 ? 'D-Day' : `D-${race.daysUntilRegistrationEnd}`})</span>
                        {/if}
                    </p>
                {/if}
            </div>

            {#if race.distances && race.distances.length > 0}
                <div class="flex flex-wrap gap-1.5 mt-3 mb-2">
                    {#each race.distances.slice(0, 3) as d}
                        <span class="text-xs px-2 py-0.5 bg-base-200 rounded">{typeof d === 'string' ? d : d.name}</span>
                    {/each}
                    {#if race.distances.length > 3}
                        <span class="text-xs px-2 py-0.5 bg-base-200 rounded">+{race.distances.length - 3}</span>
                    {/if}
                </div>
            {/if}

        </div>
    </div>
{/if}

<style>
    .line-clamp-2 {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
</style>
