<script lang="ts">
	import type { Snippet } from 'svelte';
	import { SPORT_META, type DsSport } from './meta';

	let {
		sport = 'run',
		muted = false,
		children
	}: { sport?: DsSport; muted?: boolean; children?: Snippet } = $props();

	const meta = $derived(SPORT_META[sport] ?? SPORT_META.run);
</script>

<span class="eh-sport {muted ? 'eh-sport--muted' : ''}">
	<span class="eh-sport__dot" style:background={meta.color}></span>
	{#if children}{@render children()}{:else}{meta.label}{/if}
</span>
