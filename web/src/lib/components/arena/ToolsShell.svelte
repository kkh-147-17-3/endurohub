<script lang="ts">
	import type { Snippet } from 'svelte';
	import { page } from '$app/stores';
	import Tabs from '$lib/components/eh/Tabs.svelte';
	import ToolGuide from '$lib/components/Tools/ToolGuide.svelte';
	import { getToolPage } from '$lib/seo/tool-pages';

	let {
		children,
		currentPath,
	}: {
		children: Snippet;
		currentPath: string;
	} = $props();

	const tool = $derived(getToolPage(currentPath));
	const appUrl = $derived(($page.data.appUrl || 'https://www.endurohub.kr').replace(/\/$/, ''));
	const ogImage = $derived(`${appUrl}/images/og-image.png`);
	const tabs = [
		{ id: 'pace', label: '페이스 계산', href: '/tools/pace-calculator' },
		{ id: 'vo2', label: 'VDOT', href: '/tools/vo2max' },
		{ id: 'predict', label: '기록 예측', href: '/tools/race-predictor' },
		{ id: 'plan', label: '트레이닝 플랜', href: '/tools/training-plan' },
	];
	const activeId = $derived(tabs.find((t) => t.href === currentPath)?.id ?? '');
</script>

<svelte:head>
	{#if tool}
		<title>{tool.title}</title>
		<meta name="description" content={tool.description} />
		<meta property="og:type" content="website" />
		<meta property="og:title" content={tool.title} />
		<meta property="og:description" content={tool.description} />
		<meta property="og:image" content={ogImage} />
		<meta property="og:image:width" content="1200" />
		<meta property="og:image:height" content="630" />
		<meta name="twitter:image" content={ogImage} />
	{/if}
</svelte:head>

<div class="tools-shell">
<div class="v-container">
	<div class="hd">
		<h1>{tool?.h1 ?? '러닝 도구'}</h1>
		{#if tool}<p class="intro">{tool.intro}</p>{/if}
	</div>
	<div class="tabs-wrap">
		<Tabs items={tabs} {activeId} />
	</div>
</div>

{@render children()}
{#if tool}<ToolGuide {tool} />{/if}
</div>

<style>
	.hd { padding: 40px 0 0; }
	.hd h1 {
		font-size: var(--text-h1);
		font-weight: var(--w-display);
		letter-spacing: var(--track-display);
		line-height: var(--leading-heading);
		color: var(--text-strong);
		margin: 0;
	}
	.intro { margin: var(--sp-3) 0 0; max-width: 68ch; font-size: var(--text-body-sm); color: var(--text-muted); line-height: var(--leading-body); }
	.tabs-wrap { margin-top: 22px; }
	/* 4 tabs always fit — no horizontal scrollbar; wrap on very narrow screens */
	.tabs-wrap :global(.eh-tabs) {
		overflow-x: visible;
		flex-wrap: wrap;
	}

	@media (max-width: 768px) {
		.hd { padding-top: 22px; }
		.hd h1 { font-size: var(--text-h2); }
	}
</style>
