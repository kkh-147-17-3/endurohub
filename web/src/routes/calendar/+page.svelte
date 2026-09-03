<script lang="ts">
    import { onMount } from 'svelte';
    import type { Race, SportOption } from '$lib/types';
    import { track } from '$lib/analytics';
    import CalendarBoard from '$lib/components/calendar/CalendarBoard.svelte';

    let { data } = $props();

    const year = $derived(data.year as number);
    const month = $derived(data.month as number);
    const hasRaces = $derived(
        Object.values(data.racesGrouped as Record<string, Race[]>).some((races) => races.length > 0)
    );

    onMount(() => {
        track('calendar_view', { year, month });
    });
</script>

<svelte:head>
    <title>{year}년 {month}월 대회 캘린더 - 엔듀로허브</title>
    <meta name="description" content="{year}년 {month}월 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정입니다." />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="{year}년 {month}월 대회 캘린더 - 엔듀로허브" />
    <meta property="og:description" content="{year}년 {month}월 마라톤, 수영, 자전거, 철인3종, 트레일러닝 대회 일정입니다." />
    <meta property="og:image" content="{data.appUrl}/images/og-image.png" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta name="twitter:image" content="{data.appUrl}/images/og-image.png" />
    {#if !hasRaces}
        <meta name="robots" content="noindex, follow" />
    {/if}
</svelte:head>

<CalendarBoard
    {year}
    {month}
    startOfMonth={data.startOfMonth as string}
    racesGrouped={data.racesGrouped as Record<string, Race[]>}
    previousMonth={data.previousMonth}
    nextMonth={data.nextMonth}
    sports={data.sports as SportOption[]}
    sportFilter={(Array.isArray(data.sport) ? data.sport : data.sport ? [data.sport] : []) as string[]}
    basePath="/calendar"
/>
