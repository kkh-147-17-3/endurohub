<script lang="ts">
	import { page } from '$app/stores';
	import { afterNavigate } from '$app/navigation';
	import { onMount } from 'svelte';
	import { track } from '$lib/analytics';

	let { children } = $props();

	const TOOL_SLUGS = new Set(['pace-calculator', 'training-plan', 'vo2max', 'race-predictor']);

	/** onMount와 afterNavigate가 첫 로드에서 연달아 호출될 때 중복만 방지 (나중에 같은 도구 재방문은 정상 기록) */
	let lastToolEmit = { path: '', at: 0 };

	function captureToolUse(pathname: string) {
		const seg = pathname.split('/')[2];
		if (!seg || !TOOL_SLUGS.has(seg)) return;
		const now = Date.now();
		if (lastToolEmit.path === pathname && now - lastToolEmit.at < 200) return;
		lastToolEmit = { path: pathname, at: now };
		track('tool_use', { tool: seg });
	}

	onMount(() => {
		captureToolUse($page.url.pathname);
	});

	afterNavigate(() => {
		captureToolUse($page.url.pathname);
	});
</script>

{@render children()}
