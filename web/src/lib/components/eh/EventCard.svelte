<script lang="ts">
	import SportTag from './SportTag.svelte';
	import Badge from './Badge.svelte';
	import type { DsSport, DsBadgeStatus } from './meta';

	export type Spec = { label: string; value: string; accent?: boolean };

	let {
		variant = 'tile',
		sport = 'run',
		showSport = true,
		title,
		date,
		location = '',
		status = 'open',
		note = undefined,
		image = undefined,
		specs = [],
		href = undefined,
		onclick = undefined
	}: {
		variant?: 'tile' | 'row';
		sport?: DsSport;
		showSport?: boolean;
		title: string;
		date: string;
		location?: string;
		status?: DsBadgeStatus;
		note?: string;
		image?: string | null;
		specs?: Spec[];
		href?: string;
		onclick?: (e: MouseEvent) => void;
	} = $props();

	const tag = $derived(href ? 'a' : 'button');
</script>

<svelte:element
	this={tag}
	class="eh-event {variant === 'row' ? 'eh-event--row' : ''}"
	href={href}
	type={href ? undefined : 'button'}
	{onclick}
>
	{#if variant === 'row'}
		<div class="eh-event__body">
			<div class="eh-event__main">
				<div class="eh-event__top" style="justify-content:flex-start;gap:12px;">
					{#if showSport}<SportTag {sport} />{/if}
					<span class="eh-event__date"><span>{date}</span>{#if location}<span>{location}</span>{/if}</span>
					<Badge {status} />
				</div>
				<h3 class="eh-event__title">{title}</h3>
				{#if note}<p class="eh-event__note">{note}</p>{/if}
			</div>
			{#if specs.length}
				<div class="eh-event__specs">
					{#each specs as sp}
						<div class="eh-event__spec">
							<b class={sp.accent ? 'accent' : ''}>{sp.value}</b>
							<span>{sp.label}</span>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	{:else}
		{#if image}
			<div class="eh-event__photo">
				<Badge {status} />
				<img src={image} alt="" />
			</div>
		{/if}
		<div class="eh-event__body">
			{#if showSport || !image}
				<div class="eh-event__top">
					{#if showSport}<SportTag {sport} />{/if}
					{#if !image}<Badge {status} />{/if}
				</div>
			{/if}
			<h3 class="eh-event__title">{title}</h3>
			<span class="eh-event__meta"><span>{date}</span>{#if location}<span>{location}</span>{/if}</span>
			{#if specs.length}
				<div class="eh-event__specs">
					{#each specs as sp}
						<div class="eh-event__spec">
							<b class={sp.accent ? 'accent' : ''}>{sp.value}</b>
							<span>{sp.label}</span>
						</div>
					{/each}
				</div>
			{/if}
			{#if note}<p class="eh-event__note">{note}</p>{/if}
		</div>
	{/if}
</svelte:element>
