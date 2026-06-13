<script lang="ts">
	import type { Snippet } from 'svelte';
	import Tabs from '$lib/components/eh/Tabs.svelte';

	let {
		children,
		currentPath,
	}: {
		children: Snippet;
		currentPath: string;
	} = $props();

	// Mirrors the v2 design: 4 tool tabs, no hub/overview, no meta line.
	const tabs = [
		{ id: 'pace', label: '페이스 계산', href: '/tools/pace-calculator' },
		{ id: 'vo2', label: 'VO₂max', href: '/tools/vo2max' },
		{ id: 'predict', label: '기록 예측', href: '/tools/race-predictor' },
		{ id: 'plan', label: '트레이닝 플랜', href: '/tools/training-plan' },
	];
	const activeId = $derived(tabs.find((t) => t.href === currentPath)?.id ?? 'pace');
</script>

<div class="v-container">
	<div class="hd">
		<div class="eh-micro"><span class="acc">TOOLS</span> · 페이스 / VO₂ / 예측 / 플랜</div>
		<h1>러닝 도구</h1>
	</div>
	<div class="tabs-wrap">
		<Tabs items={tabs} {activeId} />
	</div>
</div>

{@render children()}

<style>
	.hd { padding: 40px 0 0; }
	.hd h1 {
		font-size: var(--text-h1);
		font-weight: var(--w-display);
		letter-spacing: var(--track-display);
		line-height: var(--leading-heading);
		color: var(--text-strong);
		margin: 8px 0 0;
	}
	.tabs-wrap { margin-top: 22px; }
	/* 4 tabs always fit — no horizontal scrollbar; wrap on very narrow screens */
	.tabs-wrap :global(.eh-tabs) {
		overflow-x: visible;
		flex-wrap: wrap;
	}

	@media (max-width: 768px) {
		.hd { padding-top: 22px; }
	}
</style>
