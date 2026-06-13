<script lang="ts">
	import { onMount } from 'svelte';
	import type { PageData } from './$types';
	import type { Race } from '$lib/types';
	import { track } from '$lib/analytics';
	import RegionCartogram from '$lib/components/calendar/RegionCartogram.svelte';

	let { data }: { data: PageData } = $props();

	const year = $derived(data.year);
	const month = $derived(data.month);
	const racesGrouped = $derived(data.racesGrouped);
	const previousMonth = $derived(data.previousMonth);
	const nextMonth = $derived(data.nextMonth);
	const sport = $derived(
		(Array.isArray(data.sport) ? data.sport : data.sport ? [data.sport] : []) as string[]
	);

	const allRaces = $derived(Object.values(racesGrouped).flat() as Race[]);
	const totalRaces = $derived(allRaces.length);

	onMount(() => {
		track('calendar_map_view', { year, month });
	});

	function navQuery(targetYear: number, targetMonth: number): string {
		const p = new URLSearchParams();
		p.set('year', String(targetYear));
		p.set('month', String(targetMonth));
		for (const s of sport) p.append('sport', s);
		return p.toString();
	}

	const todayDate = new Date();
	const currentMonth = todayDate.getMonth() + 1;
	const currentYear = todayDate.getFullYear();
	const mm = $derived(String(month).padStart(2, '0'));
</script>

<svelte:head>
	<title>{year}년 {month}월 대회 지도 - 엔듀로허브</title>
	<meta
		name="description"
		content="{year}년 {month}월 마라톤·수영·자전거·철인3종·트레일러닝 대회를 시·도별 타일 지도에서 확인하세요."
	/>
</svelte:head>

<div class="carto-wrap">
	<header class="carto-head">
		<div class="head-left">
			<div class="head-kicker eh-micro">엔듀로허브 · 캘린더 · 지도</div>
			<h1 class="head-title eh-data">
				{year}<span class="head-sep">·</span><span class="head-month">{mm}</span>
			</h1>
			<div class="head-meta eh-micro">
				17개 시·도 · 대회 <span class="meta-accent">{totalRaces}</span>개
			</div>
		</div>

		<div class="head-right">
			<div class="view-toggle" role="group" aria-label="보기 모드">
				<a class="vt-btn" href="/calendar?{navQuery(year, month)}">캘린더</a>
				<span class="vt-btn active" aria-current="page">지도</span>
			</div>
			<nav class="month-nav" aria-label="월 이동">
				<a class="nav-btn" href="/calendar/map?{navQuery(previousMonth.year, previousMonth.month)}" aria-label="이전 달">← {previousMonth.month}월</a>
				<a class="nav-btn nav-today" class:active={year === currentYear && month === currentMonth} href="/calendar/map?{navQuery(currentYear, currentMonth)}">{currentMonth}월</a>
				<a class="nav-btn" href="/calendar/map?{navQuery(nextMonth.year, nextMonth.month)}" aria-label="다음 달">{nextMonth.month}월 →</a>
			</nav>
		</div>
	</header>

	<RegionCartogram races={allRaces} {month} />
</div>

<style>
	.carto-wrap { max-width: 1400px; margin: 0 auto; padding: 24px 16px 48px; color: var(--text-strong); }
	@media (min-width: 1024px) { .carto-wrap { padding: 36px 32px 64px; } }

	.carto-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; padding-bottom: 20px; border-bottom: 2px solid var(--ink-900); }
	.head-kicker { margin-bottom: 4px; }
	.head-title { font-family: var(--font-mono); font-size: clamp(36px, 5vw, 52px); font-weight: 700; letter-spacing: -2px; line-height: 1; margin: 4px 0; display: inline-flex; align-items: baseline; gap: 6px; }
	.head-sep { color: var(--text-muted); font-weight: 400; }
	.head-month { color: var(--accent); }
	.head-meta { margin-top: 4px; }
	.meta-accent { color: var(--accent-strong); font-weight: 700; }
	.head-right { display: flex; gap: 10px; flex-wrap: wrap; align-items: flex-end; }

	.view-toggle { display: inline-flex; border: var(--border-hair); background: var(--paper-0); }
	.vt-btn { padding: 8px 14px; font-family: var(--font-mono); font-size: 11px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-muted); text-decoration: none; border-right: var(--border-hair); white-space: nowrap; background: transparent; cursor: pointer; }
	.vt-btn:last-child { border-right: none; }
	.vt-btn:hover { background: var(--paper-50); color: var(--text-strong); }
	.vt-btn.active { background: var(--ink-900); color: var(--paper-0); cursor: default; }

	.month-nav { display: inline-flex; border: var(--border-hair); background: var(--paper-0); }
	.nav-btn { padding: 8px 14px; font-family: var(--font-mono); font-size: 11px; font-weight: 600; letter-spacing: 0.06em; color: var(--text-strong); border-right: var(--border-hair); text-decoration: none; white-space: nowrap; }
	.nav-btn:last-child { border-right: none; }
	.nav-btn:hover { background: var(--paper-50); }
	.nav-today { background: var(--ink-900); color: var(--paper-0); letter-spacing: 0.12em; }
	.nav-today:hover, .nav-today.active { background: var(--ink-700); }
</style>
