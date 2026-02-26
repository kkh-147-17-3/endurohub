<script lang="ts">
    import type { DistancePreset } from '$lib/tools/types';

    let {
        selected = $bindable('full'),
        customDistance = $bindable(10),
    }: {
        selected: DistancePreset;
        customDistance: number;
    } = $props();

    const presets: { key: DistancePreset; label: string }[] = [
        { key: '5k', label: '5K' },
        { key: '10k', label: '10K' },
        { key: 'half', label: '하프' },
        { key: 'full', label: '풀' },
        { key: 'custom', label: '직접입력' },
    ];
</script>

<div class="form-control">
    <label class="label" for="distance-selector">
        <span class="label-text font-medium">거리</span>
    </label>
    <div class="flex flex-wrap gap-2" id="distance-selector" role="radiogroup" aria-label="거리 선택">
        {#each presets as preset (preset.key)}
            <button
                type="button"
                role="radio"
                aria-checked={selected === preset.key}
                class="btn btn-sm cursor-pointer transition-colors duration-200 {selected === preset.key ? 'btn-primary' : 'btn-outline'}"
                onclick={() => selected = preset.key}
            >
                {preset.label}
            </button>
        {/each}
    </div>
    {#if selected === 'custom'}
        <div class="flex items-center gap-2 mt-3">
            <input
                type="number"
                bind:value={customDistance}
                min="0.1"
                max="200"
                step="0.1"
                class="input input-bordered input-sm w-24"
                aria-label="거리 직접 입력"
            />
            <span class="text-sm text-base-content/60">km</span>
        </div>
    {/if}
</div>
