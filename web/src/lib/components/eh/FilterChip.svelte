<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		selected = false,
		count = undefined,
		onclick = undefined,
		children
	}: {
		selected?: boolean;
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
	{@render children()}
	{#if count != null}<span class="eh-chip__count">{count}</span>{/if}
</button>
