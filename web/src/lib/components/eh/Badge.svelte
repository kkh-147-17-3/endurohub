<script lang="ts">
	import type { Snippet } from 'svelte';
	import { BADGE_LABELS, type DsBadgeStatus } from './meta';

	let {
		status = 'open',
		children
	}: { status?: DsBadgeStatus; children?: Snippet } = $props();
</script>

<span class="eh-badge eh-badge--{status}">
	{#if children}{@render children()}{:else}{BADGE_LABELS[status]}{/if}
</span>
