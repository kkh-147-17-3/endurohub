<script lang="ts">
	let {
		placeholder = '대회, 지역, 거리 검색',
		value = $bindable(''),
		shortcutHint = undefined,
		name = undefined,
		onsubmit = undefined,
		oninput = undefined
	}: {
		placeholder?: string;
		value?: string;
		shortcutHint?: string;
		name?: string;
		onsubmit?: (value: string) => void;
		oninput?: (e: Event) => void;
	} = $props();

	function handleSubmit(e: SubmitEvent) {
		if (onsubmit) {
			e.preventDefault();
			onsubmit(value);
		}
	}
</script>

<form class="eh-search" onsubmit={handleSubmit} role="search">
	<svg
		class="eh-search__icon"
		width="18"
		height="18"
		viewBox="0 0 24 24"
		fill="none"
		stroke="currentColor"
		stroke-width="1.5"
		stroke-linecap="round"
		stroke-linejoin="round"
	>
		<circle cx="11" cy="11" r="8" />
		<path d="m21 21-4.3-4.3" />
	</svg>
	<input type="search" {name} {placeholder} bind:value {oninput} />
	{#if shortcutHint}<span class="eh-search__kbd">{shortcutHint}</span>{/if}
</form>
