<script lang="ts">
	import type { Snippet } from 'svelte';

	type Variant = 'primary' | 'signal' | 'secondary' | 'ghost';
	type Size = 'sm' | 'md' | 'lg';

	let {
		variant = 'primary',
		size = 'md',
		fullWidth = false,
		disabled = false,
		type = 'button',
		href = undefined,
		onclick = undefined,
		children,
		...rest
	}: {
		variant?: Variant;
		size?: Size;
		fullWidth?: boolean;
		disabled?: boolean;
		type?: 'button' | 'submit' | 'reset';
		href?: string;
		onclick?: (e: MouseEvent) => void;
		children: Snippet;
		[key: string]: unknown;
	} = $props();

	const cls = $derived(
		['eh-btn', `eh-btn--${size}`, `eh-btn--${variant}`, fullWidth ? 'eh-btn--full' : '']
			.filter(Boolean)
			.join(' ')
	);
</script>

{#if href}
	<a class={cls} {href} aria-disabled={disabled} {...rest}>{@render children()}</a>
{:else}
	<button class={cls} {type} {disabled} {onclick} {...rest}>{@render children()}</button>
{/if}
