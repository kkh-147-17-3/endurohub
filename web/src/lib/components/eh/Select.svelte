<script lang="ts">
	type Option = string | { value: string; label: string };

	let {
		label = undefined,
		options = [],
		value = $bindable(''),
		disabled = false,
		name = undefined,
		onchange = undefined
	}: {
		label?: string;
		options?: Option[];
		value?: string;
		disabled?: boolean;
		name?: string;
		onchange?: (e: Event) => void;
	} = $props();

	const normalized = $derived(
		options.map((o) => (typeof o === 'string' ? { value: o, label: o } : o))
	);
</script>

<label class="eh-select-wrap">
	{#if label}<span class="eh-field__label">{label}</span>{/if}
	<select class="eh-select" {name} {disabled} bind:value {onchange}>
		{#each normalized as opt}
			<option value={opt.value}>{opt.label}</option>
		{/each}
	</select>
	<svg
		class="eh-select-wrap__chev"
		width="16"
		height="16"
		viewBox="0 0 24 24"
		fill="none"
		stroke="currentColor"
		stroke-width="1.5"
		stroke-linecap="round"
		stroke-linejoin="round"
	>
		<path d="m6 9 6 6 6-6" />
	</svg>
</label>
