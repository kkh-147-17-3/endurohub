<script lang="ts">
    import type { TaggedRace, Sport } from '$lib/types';
    import { arenaSportShort } from '$lib/arena';

    let { races }: { races: TaggedRace[] } = $props();

    function shortTitle(t: string) {
        return t.length > 16 ? t.slice(0, 16) + '…' : t;
    }
</script>

{#if races && races.length > 0}
    <div class="tag-row">
        {#each races as race}
            <a
                href="/races/{race.slug}"
                class="tag sport-{race.sport}"
                onclick={(e) => e.stopPropagation()}
                title={race.title}
            >
                <span class="dot"></span>
                <span class="sport-code">{arenaSportShort[race.sport as Sport] ?? race.sport}</span>
                <span class="tag-title">{shortTitle(race.title)}</span>
            </a>
        {/each}
    </div>
{/if}

<style>
    .tag-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }
    .tag {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 3px 8px;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink);
        text-decoration: none;
        line-height: 1.3;
        transition: background 0.1s;
    }
    .tag:hover {
        background: var(--arena-paper-alt);
    }
    .dot {
        width: 6px;
        height: 6px;
        border-radius: 0;
    }
    .sport-code {
        font-size: 10px;
        letter-spacing: 1px;
        color: var(--arena-ink-soft);
    }
    .tag-title {
        font-family: var(--arena-f-body);
        font-size: 12px;
        font-weight: 500;
    }

    .sport-running .dot { background: oklch(48% 0.18 280); }
    .sport-swimming .dot { background: oklch(50% 0.14 220); }
    .sport-cycling .dot { background: oklch(55% 0.16 60); }
    .sport-triathlon .dot { background: oklch(48% 0.18 320); }
    .sport-trail_running .dot { background: oklch(42% 0.14 145); }
</style>
