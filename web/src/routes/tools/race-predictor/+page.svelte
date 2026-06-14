<script lang="ts">
	import { page } from '$app/stores';
	import ToolsShell from '$lib/components/arena/ToolsShell.svelte';
	import StatBlock from '$lib/components/eh/StatBlock.svelte';
	import FilterChip from '$lib/components/eh/FilterChip.svelte';
	import Field from '$lib/components/eh/Field.svelte';
	import Prefill from '$lib/components/eh/Prefill.svelte';
	import { STD_DISTANCES, MAIN_GOAL, daysUntil, fmtPace, fmtTime, parseTime, riegel } from '$lib/tools';

	let { data } = $props();
	const pf = data.prefill;

	let km = $state(pf?.distKm ?? 21.0975);
	let time = $state(pf?.timeStr ?? '1:42:15');

	const sec = $derived(parseTime(time || '0'));
	const rows = $derived(
		STD_DISTANCES.map((d) => {
			const pred = sec > 60 ? riegel(sec, km, d.km) : NaN;
			return { ...d, pred, pace: d.km > 0 ? pred / d.km : NaN };
		}),
	);

	const goal = MAIN_GOAL;
	const goalDaysOut = daysUntil(goal.date);
	const goalPred = $derived(sec > 60 ? riegel(sec, km, goal.distKm) : NaN);
	const gap = $derived(goalPred - goal.targetTimeSec);
</script>

<svelte:head>
	<title>기록 예측 — endurohub</title>
</svelte:head>

<ToolsShell currentPath={$page.url.pathname}>
<div class="page v-container">
	<div class="tool-layout">
		<!-- INPUT -->
		<div class="panel">
			<span class="eh-micro"><span class="acc">INPUT</span> · 기준 레이스</span>
			<div class="row">
				{#each STD_DISTANCES as d (d.code)}
					<FilterChip selected={Math.abs(km - d.km) < 0.01} onclick={() => (km = d.km)}>{d.label}</FilterChip>
				{/each}
			</div>
			<Field label="Race time" placeholder="예: 1:42:15" bind:value={time} />
			{#if pf}
				<Prefill label={pf.label} onApply={() => { km = pf.distKm; time = pf.timeStr; }} />
			{/if}
			<p class="src-note">Riegel 공식 (지수 1.06). 동일한 트레이닝 상태 · 평탄 코스 가정입니다.</p>
		</div>

		<!-- OUTPUT -->
		<div class="out">
			<div class="v-table pred">
				<div class="v-thead pred-cols">
					<span>DIST</span>
					<span></span>
					<span>예상 기록</span>
					<span class="hide-m">PACE/KM</span>
				</div>
				{#each rows as r (r.code)}
					<div class="v-trow pred-cols" class:pred--base={Math.abs(r.km - km) < 0.01}>
						<b class="eh-data">{r.label}</b>
						<span class="pred-note">{Math.abs(r.km - km) < 0.01 ? '기준 거리' : ''}</span>
						<b class="eh-data pred-time">{fmtTime(r.pred)}</b>
						<span class="hide-m eh-data pred-pace">{fmtPace(r.pace)}</span>
					</div>
				{/each}
			</div>

			<!-- main season goal (demo data — see MAIN_GOAL in $lib/tools) -->
			<div class="v-card goal-card">
				<div class="eh-micro">
					<span class="acc">MAIN GOAL</span> · {goal.raceName} · <span class="eh-data">D-{goalDaysOut}</span>
				</div>
				<div class="goal-stats">
					<StatBlock label="목표" value={goal.targetTimeStr} size="lg" />
					<StatBlock label="현재 예측" value={Number.isFinite(goalPred) ? fmtTime(goalPred) : '—'} size="lg" accent />
					<div class="goal-gap eh-data" style="color:{gap > 0 ? 'var(--caution)' : 'var(--text-accent)'}">
						{#if Number.isFinite(gap)}{gap > 0 ? `목표까지 ${fmtTime(gap)} 단축 필요` : `목표 대비 ${fmtTime(-gap)} 여유`}{/if}
					</div>
				</div>
			</div>
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
	.src-note { margin: 0; font-size: 12px; color: var(--text-faint); line-height: 1.6; }

	.out { display: flex; flex-direction: column; gap: var(--sp-6); }

	.pred-cols { grid-template-columns: 90px 1fr 130px 130px; gap: 14px; }
	.pred--base { background: var(--paper-50); }
	.pred-note { font-size: 12px; color: var(--text-faint); }
	.pred-time { font-size: 17px; }
	.pred-pace { color: var(--text-muted); }

	.goal-card { padding: 20px 22px; border-color: var(--ink-900); }
	.goal-stats {
		display: flex;
		gap: 40px;
		margin-top: 14px;
		flex-wrap: wrap;
		align-items: flex-end;
	}
	.goal-gap { font-size: 13px; font-weight: 700; padding-bottom: 4px; }

	@media (max-width: 768px) {
		.panel { padding: 18px; min-width: 0; }
		.pred-cols { grid-template-columns: 70px 1fr 110px; }
		.hide-m { display: none; }
	}
</style>
