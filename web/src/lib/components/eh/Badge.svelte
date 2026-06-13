<script lang="ts">
	import type { Snippet } from 'svelte';
	import { BADGE_LABELS, type DsBadgeStatus } from './meta';

	let {
		status = 'open',
		children
	}: { status?: DsBadgeStatus; children?: Snippet } = $props();

	const pulse = $derived(status === 'live' || status === 'closing');
</script>

<span class="eh-badge eh-badge--{status}">
	{#if pulse}<span class="eh-badge__pulse"></span>{/if}
	{#if children}{@render children()}{:else}{BADGE_LABELS[status]}{/if}
</span>
