<script lang="ts">
	type Size = 'sm' | 'md' | 'lg' | 'xl';

	let {
		label,
		value,
		unit = undefined,
		size = 'md',
		accent = false
	}: {
		label: string;
		value: string | number;
		unit?: string;
		size?: Size;
		accent?: boolean;
	} = $props();
</script>

<div class="eh-stat eh-stat--{size} {accent ? 'eh-stat--accent' : ''}">
	<span class="eh-stat__label">{label}</span>
	<span class="eh-stat__value">{value}{#if unit}<small>{unit}</small>{/if}</span>
</div>
