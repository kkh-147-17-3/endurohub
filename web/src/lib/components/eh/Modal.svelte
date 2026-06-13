<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		open = $bindable(false),
		maxWidth = '520px',
		onclose = undefined,
		children
	}: {
		open?: boolean;
		maxWidth?: string;
		onclose?: () => void;
		children: Snippet;
	} = $props();

	function close() {
		open = false;
		onclose?.();
	}

	function onKey(e: KeyboardEvent) {
		if (e.key === 'Escape') close();
	}
</script>

<svelte:window onkeydown={open ? onKey : undefined} />

{#if open}
	<div
		class="v-scrim"
		role="presentation"
		onclick={(e) => {
			if (e.target === e.currentTarget) close();
		}}
	>
		<div class="v-modal" role="dialog" aria-modal="true" style:max-width={maxWidth}>
			{@render children()}
		</div>
	</div>
{/if}
