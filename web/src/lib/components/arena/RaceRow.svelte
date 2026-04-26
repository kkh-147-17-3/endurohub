<script lang="ts">
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

    let { race }: { race: Race } = $props();

    const sportLabel = $derived(arenaSportShort[race.sport]);
    const dday = $derived(arenaDday(race));
    const ddayLabel = $derived(arenaDdayLabel(race));
    const dist = $derived(arenaDistLabel(race));
    const fee = $derived(arenaFeeShort(arenaMinFee(race)));
    const date = $derived(arenaShortDate(race.raceDate));

    function handleAnalytics() {
        track('race_click', {
            race_slug: race.slug,
            race_title: race.title,
            race_sport: race.sport,
            race_status: race.status,
            variant: 'arena_row',
        });
    }
</script>

<a class="row" href={race.url} onclick={handleAnalytics}>
    <span class="dday" class:urgent={dday.urgent}>{ddayLabel}</span>
    <span class="title">{race.title}</span>
    <span class="meta">
        <span class="cell muted">{date}</span>
        <span class="cell sport sport-{race.sport}">{sportLabel}</span>
        <span class="cell">{dist}</span>
        <span class="cell body-font">{race.region ?? ''}</span>
        <span class="cell">{fee}</span>
    </span>
</a>

<style>
    .row {
        display: grid;
        grid-template-columns: 56px 1fr 90px 60px 100px 110px 90px;
        align-items: center;
        gap: 16px;
        padding: 10px 20px;
        border-bottom: 1px solid var(--arena-line-soft);
        font-family: var(--arena-f-mono);
        font-size: 12px;
        background: var(--arena-paper);
        text-decoration: none;
        color: var(--arena-ink);
        transition: background 0.1s;
    }
    .row:hover {
        background: var(--arena-paper-alt);
    }
    .row:last-child {
        border-bottom: none;
    }
    /* Desktop: .meta is transparent — its children become direct grid items */
    .meta {
        display: contents;
    }
    .dday {
        font-weight: 700;
        color: var(--arena-ink);
    }
    .dday.urgent {
        color: var(--arena-urgent);
    }
    .title {
        font-family: var(--arena-f-body);
        font-weight: 600;
        font-size: 14px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .cell {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .body-font {
        font-family: var(--arena-f-body);
        font-size: 12px;
    }
    .muted {
        color: var(--arena-ink-soft);
    }
    /* Sport-specific tinting on the SPORT code cell — arena-toned palette */
    .sport {
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .sport-running        { color: oklch(48% 0.18 280); }   /* violet */
    .sport-swimming       { color: oklch(50% 0.14 220); }   /* cyan-blue */
    .sport-cycling        { color: oklch(55% 0.16 60); }    /* amber */
    .sport-triathlon      { color: oklch(48% 0.18 320); }   /* magenta */
    .sport-trail_running  { color: oklch(42% 0.14 145); }   /* deep green */

    /* Mobile (<880px): 2-line reflow — D-DAY + NAME on top, meta line below */
    @media (max-width: 879px) {
        .row {
            grid-template-columns: 56px minmax(0, 1fr);
            grid-template-rows: auto auto;
            row-gap: 4px;
            column-gap: 12px;
            padding: 12px 16px;
            align-items: baseline;
        }
        .dday {
            grid-column: 1;
            grid-row: 1;
        }
        .title {
            grid-column: 2;
            grid-row: 1;
            font-size: 14px;
        }
        .meta {
            display: flex;
            flex-wrap: wrap;
            grid-column: 1 / -1;
            grid-row: 2;
            color: var(--arena-ink-soft);
            font-size: 11px;
            padding-left: 0;
            row-gap: 2px;
        }
        .meta .cell {
            display: inline-flex;
            align-items: baseline;
            overflow: visible;
        }
        .meta .cell:not(:first-child)::before {
            content: '·';
            margin: 0 8px;
            color: var(--arena-line);
        }
    }
</style>
