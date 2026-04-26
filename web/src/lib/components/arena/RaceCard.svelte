<script lang="ts">
    import { goto } from '$app/navigation';
    import type { Race } from '$lib/types';
    import {
        arenaDday,
        arenaDdayLabel,
        arenaDistLabel,
        arenaFeeShort,
        arenaMinFee,
        arenaShortDate,
        arenaSportShort,
    } from '$lib/arena';
    import { track } from '$lib/analytics';

    let { race, eager = false }: { race: Race; eager?: boolean } = $props();

    const sportKr = $derived(arenaSportShort[race.sport]);
    const dday = $derived(arenaDday(race));
    const ddayLabel = $derived(arenaDdayLabel(race));
    const dist = $derived(arenaDistLabel(race));
    const fee = $derived(arenaFeeShort(arenaMinFee(race)));
    const date = $derived(arenaShortDate(race.raceDate));
    const deadline = $derived(
        race.registrationEnd ? `접수마감 ${arenaShortDate(race.registrationEnd)}` : '',
    );

    function handleClick() {
        track('race_click', {
            race_slug: race.slug,
            race_title: race.title,
            race_sport: race.sport,
            race_status: race.status,
            variant: 'arena',
        });
        goto(race.url);
    }
</script>

<a
    href={race.url}
    class="arena-card"
    onclick={(e) => {
        e.preventDefault();
        handleClick();
    }}
>
    <div class="strip" class:urgent={dday.urgent}>
        <span class="dday">{ddayLabel}</span>
        <span class="sport">{sportKr}</span>
    </div>
    <div class="body">
        <div class="title">{race.title}</div>
        <div class="meta">
            <span>{date}</span>
            <span>{race.region ?? ''}</span>
            <span>{dist}</span>
        </div>
        <div class="foot">
            <span>{deadline}</span>
            <span>{fee}</span>
        </div>
    </div>
</a>

<style>
    .arena-card {
        cursor: pointer;
    }
    .strip {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 14px;
        background: var(--arena-paper-alt);
        color: var(--arena-ink);
        border-bottom: 1px solid var(--arena-line);
        font-family: var(--arena-f-mono);
        font-size: 11px;
        line-height: 1.4;
    }
    .strip.urgent {
        background: var(--arena-urgent);
        color: var(--arena-paper);
    }
    .dday {
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .sport {
        opacity: 0.7;
        font-family: var(--arena-f-body);
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0;
    }
    .strip.urgent .sport {
        opacity: 0.9;
    }
    .body {
        padding: 20px 16px 16px;
        flex: 1;
        display: flex;
        flex-direction: column;
        min-width: 0;
    }
    .title {
        font-family: var(--arena-f-body);
        font-weight: 700;
        font-size: 17px;
        letter-spacing: -0.3px;
        line-height: 1.3;
        margin-bottom: 10px;
        text-wrap: balance;
        color: var(--arena-ink);
        /* Reserve 2-line height so meta/foot align across 1- and 2-line cards */
        min-height: calc(17px * 1.3 * 2);
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        word-break: keep-all;
    }
    .meta {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        line-height: 1.4;
        color: var(--arena-ink-soft);
        display: flex;
        justify-content: space-between;
        margin-bottom: 14px;
        gap: 8px;
    }
    .meta span {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .foot {
        margin-top: auto;
        padding-top: 10px;
        border-top: 1px solid var(--arena-line-soft);
        display: flex;
        justify-content: space-between;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        line-height: 1.4;
        color: var(--arena-ink-soft);
    }
</style>
