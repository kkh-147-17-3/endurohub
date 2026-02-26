<script lang="ts">
    import type { SplitRow } from '$lib/tools/types';

    let {
        splits,
        highlightHalf = false,
    }: {
        splits: SplitRow[];
        highlightHalf?: boolean;
    } = $props();

    let halfIndex = $derived(
        highlightHalf ? Math.floor(splits.length / 2) - 1 : -1
    );
</script>

<div class="overflow-x-auto rounded-lg border border-base-300">
    <table class="table table-sm table-zebra">
        <thead>
            <tr class="bg-base-200">
                <th class="text-center">구간</th>
                <th class="text-center">페이스</th>
                <th class="text-center">구간 시간</th>
                <th class="text-center">누적 시간</th>
            </tr>
        </thead>
        <tbody>
            {#each splits as split, i (split.km)}
                <tr class="{i === halfIndex ? 'bg-primary/5 border-b-2 border-primary/20' : ''}">
                    <td class="text-center font-medium tabular-nums">{split.label}</td>
                    <td class="text-center tabular-nums">{split.pace}/km</td>
                    <td class="text-center tabular-nums">{split.splitTime}</td>
                    <td class="text-center tabular-nums font-medium">{split.cumulativeTime}</td>
                </tr>
            {/each}
        </tbody>
    </table>
</div>
