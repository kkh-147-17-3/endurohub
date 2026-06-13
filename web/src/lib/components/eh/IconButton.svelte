<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		label,
		variant = 'plain',
		size = 'md',
		active = false,
		href = undefined,
		onclick = undefined,
		children
	}: {
		label: string;
		variant?: 'plain' | 'outline';
		size?: 'sm' | 'md';
		active?: boolean;
		href?: string;
		onclick?: (e: MouseEvent) => void;
		children: Snippet;
	} = $props();

	const cls = $derived(
		[
			'eh-iconbtn',
			variant === 'outline' ? 'eh-iconbtn--outline' : '',
			size === 'sm' ? 'eh-iconbtn--sm' : '',
			active ? 'eh-iconbtn--active' : ''
		]
			.filter(Boolean)
			.join(' ')
	);
</script>

{#if href}
	<a class={cls} {href} aria-label={label} title={label}>{@render children()}</a>
{:else}
	<button type="button" class={cls} aria-label={label} title={label} {onclick}>
		{@render children()}
	</button>
{/if}
