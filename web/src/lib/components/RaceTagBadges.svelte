<script lang="ts">
    import type { TaggedRace, Sport } from '$lib/types';
    import { sportStyles } from '$lib/race';

    let { races }: { races: TaggedRace[] } = $props();
</script>

{#if races && races.length > 0}
    <div class="flex flex-wrap gap-1.5">
        {#each races as race}
            {@const style = sportStyles[race.sport as Sport] || sportStyles.running}
            <a
                href="/races/{race.slug}"
                class="badge {style.badge} badge-sm hover:opacity-80 transition-opacity"
                onclick={(e) => e.stopPropagation()}
            >
                {race.title.length > 15 ? race.title.slice(0, 15) + '...' : race.title}
            </a>
        {/each}
    </div>
{/if}
