<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		selected = false,
		dotColor = undefined,
		count = undefined,
		onclick = undefined,
		children
	}: {
		selected?: boolean;
		dotColor?: string;
		count?: number | string | null;
		onclick?: (e: MouseEvent) => void;
		children: Snippet;
	} = $props();
</script>

<button
	type="button"
	class="eh-chip {selected ? 'eh-chip--on' : ''}"
	aria-pressed={selected}
	{onclick}
>
	{#if dotColor}<span class="eh-chip__dot" style:background={dotColor}></span>{/if}
	{@render children()}
	{#if count != null}<span class="eh-chip__count">{count}</span>{/if}
</button>
