<script lang="ts">
	export type TabItem = { id: string; label: string; count?: number | null; href?: string };

	let {
		items = [],
		activeId,
		onchange = undefined
	}: {
		items: TabItem[];
		activeId: string;
		onchange?: (id: string) => void;
	} = $props();
</script>

<div class="eh-tabs" role="tablist">
	{#each items as it (it.id)}
		{#if it.href}
			<a
				class="eh-tab {it.id === activeId ? 'eh-tab--on' : ''}"
				href={it.href}
				role="tab"
				aria-selected={it.id === activeId}
			>
				{it.label}
				{#if it.count != null}<span class="eh-tab__count">{it.count}</span>{/if}
			</a>
		{:else}
			<button
				type="button"
				role="tab"
				aria-selected={it.id === activeId}
				class="eh-tab {it.id === activeId ? 'eh-tab--on' : ''}"
				onclick={() => onchange?.(it.id)}
			>
				{it.label}
				{#if it.count != null}<span class="eh-tab__count">{it.count}</span>{/if}
			</button>
		{/if}
	{/each}
</div>
