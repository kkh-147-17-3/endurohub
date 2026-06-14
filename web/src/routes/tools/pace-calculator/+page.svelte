<script lang="ts">
	import { page } from '$app/stores';
	import ToolsShell from '$lib/components/arena/ToolsShell.svelte';
	import StatBlock from '$lib/components/eh/StatBlock.svelte';
	import FilterChip from '$lib/components/eh/FilterChip.svelte';
	import Field from '$lib/components/eh/Field.svelte';
	import Prefill from '$lib/components/eh/Prefill.svelte';
	import { STD_DISTANCES, fmtPace, fmtTime, parseTime } from '$lib/tools';

	let { data } = $props();
	const pf = data.prefill;

	let km = $state(pf?.distKm ?? 21.0975);
	let time = $state(pf?.timeStr ?? '1:42:15');

	const sec = $derived(parseTime(time || '0'));
	const paceSec = $derived(sec > 0 && km > 0 ? sec / km : NaN);
	const kmh = $derived(sec > 0 ? km / (sec / 3600) : NaN);

	const splits = $derived.by(() => {
		if (!Number.isFinite(paceSec)) return [];
		const marks = [5, 10, 15, 20, 21.0975, 25, 30, 35, 40, 42.195].filter((m) => m <= km + 0.01);
		return marks.map((m) => ({ at: m, clock: paceSec * m }));
	});

	function distLabel(d: number): string {
		return d === 21.0975 ? '하프' : d === 42.195 ? '풀코스' : `${d}K`;
	}
	function markLabel(at: number): string {
		return at === 21.0975 ? 'HALF' : at === 42.195 ? 'FULL' : String(at);
	}
</script>

<svelte:head>
	<title>페이스 계산 — endurohub</title>
</svelte:head>

<ToolsShell currentPath={$page.url.pathname}>
<div class="page v-container">
	<div class="tool-layout">
		<!-- INPUT -->
		<div class="panel">
			<span class="eh-micro"><span class="acc">INPUT</span> · 거리 + 목표 시간</span>
			<div class="row">
				{#each STD_DISTANCES as d (d.code)}
					<FilterChip selected={Math.abs(km - d.km) < 0.01} onclick={() => (km = d.km)}>{d.label}</FilterChip>
				{/each}
			</div>
			<Field label="Time" placeholder="예: 1:45:00" bind:value={time} hint="시:분:초 또는 분:초" />
			{#if pf}
				<Prefill label={pf.label} onApply={() => { km = pf.distKm; time = pf.timeStr; }} />
			{/if}
		</div>

		<!-- OUTPUT -->
		<div class="out">
			<div class="out-hero">
				<StatBlock label="Pace / km" value={fmtPace(paceSec)} size="xl" accent />
				<StatBlock label="Speed" value={Number.isFinite(kmh) ? kmh.toFixed(1) : '—'} unit="KM/H" size="lg" />
				<StatBlock label="Distance" value={distLabel(km)} size="lg" />
			</div>

			{#if splits.length > 0}
			<div class="v-table splits">
				<div class="v-thead splits-cols">
					<span>KM</span>
					<span></span>
					<span style="text-align:right">CLOCK</span>
				</div>
				{#each splits as s (s.at)}
					<div class="v-trow splits-cols">
						<b class="eh-data">{markLabel(s.at)}</b>
						<span class="split-bar"><span class="split-fill" style="width:{(s.at / km) * 100}%"></span></span>
						<b class="eh-data" style="text-align:right">{fmtTime(s.clock)}</b>
					</div>
				{/each}
			</div>
			{/if}
		</div>
	</div>
</div>
</ToolsShell>

<style>
	.page { padding-top: 28px; padding-bottom: var(--sp-20); }

	.tool-layout {
		display: grid;
		grid-template-columns: 1fr;
		gap: var(--sp-6);
		align-items: start;
	}
	@media (min-width: 960px) {
		.tool-layout { grid-template-columns: 380px minmax(0, 1fr); gap: var(--sp-10); }
	}

	.panel {
		border: 1px solid var(--ink-900);
		padding: var(--sp-6);
		background: var(--paper-0);
		display: flex;
		flex-direction: column;
		gap: var(--sp-5);
	}
	.row { display: flex; gap: var(--sp-2); flex-wrap: wrap; }

	.out { display: flex; flex-direction: column; gap: var(--sp-6); }
	.out-hero {
		border-top: var(--border-rule);
		padding-top: var(--sp-4);
		display: flex;
		gap: 48px;
		flex-wrap: wrap;
		align-items: flex-end;
	}

	.splits-cols { grid-template-columns: 70px 1fr 110px; gap: 14px; }
	.splits .v-trow { padding: 9px 18px; }
	.split-bar { height: 4px; background: var(--paper-100); position: relative; align-self: center; }
	.split-fill { position: absolute; inset: 0; background: var(--accent); }

	@media (max-width: 768px) {
		.panel { padding: 18px; min-width: 0; }
		.out-hero { gap: 22px 28px; }
	}
</style>
