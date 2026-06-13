<script lang="ts">
	let {
		label = undefined,
		placeholder = undefined,
		value = $bindable(''),
		type = 'text',
		hint = undefined,
		error = false,
		disabled = false,
		name = undefined,
		multiline = false,
		rows = 4,
		oninput = undefined,
		...rest
	}: {
		label?: string;
		placeholder?: string;
		value?: string;
		type?: string;
		hint?: string;
		error?: boolean;
		disabled?: boolean;
		name?: string;
		multiline?: boolean;
		rows?: number;
		oninput?: (e: Event) => void;
		[key: string]: unknown;
	} = $props();

	// Dynamic `type` cannot coexist with bind:value, so we update the bindable
	// value manually and forward the event.
	function handleInput(e: Event) {
		value = (e.currentTarget as HTMLInputElement | HTMLTextAreaElement).value;
		oninput?.(e);
	}
</script>

<label class="eh-field {error ? 'eh-field--error' : ''}">
	{#if label}<span class="eh-field__label">{label}</span>{/if}
	{#if multiline}
		<textarea
			class="eh-textarea"
			{placeholder}
			{name}
			{rows}
			{disabled}
			{value}
			oninput={handleInput}
			{...rest}
		></textarea>
	{:else}
		<input
			class="eh-input"
			{type}
			{placeholder}
			{name}
			{disabled}
			{value}
			oninput={handleInput}
			{...rest}
		/>
	{/if}
	{#if hint}<span class="eh-field__hint">{hint}</span>{/if}
</label>
