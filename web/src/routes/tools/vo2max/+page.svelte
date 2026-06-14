<script lang="ts">
	import { page } from '$app/stores';
	import ToolsShell from '$lib/components/arena/ToolsShell.svelte';
	import StatBlock from '$lib/components/eh/StatBlock.svelte';
	import FilterChip from '$lib/components/eh/FilterChip.svelte';
	import Field from '$lib/components/eh/Field.svelte';
	import Prefill from '$lib/components/eh/Prefill.svelte';
	import { STD_DISTANCES, ZONE_INK, type ZoneKey, fmtPace, parseTime, trainingPaces, vdot } from '$lib/tools';

	let { data } = $props();
	const pf = data.prefill;

	let km = $state(pf?.distKm ?? 21.0975);
	let time = $state(pf?.timeStr ?? '1:42:15');

	const sec = $derived(parseTime(time || '0'));
	const v = $derived(sec > 60 ? vdot(km, sec) : NaN);
	const paces = $derived(Number.isFinite(v) ? trainingPaces(v) : null);
	const grade = $derived(
		!Number.isFinite(v) ? '—' : v >= 55 ? '상위 5%' : v >= 48 ? '상위 15%' : v >= 42 ? '상위 35%' : '평균',
	);

	const zoneUse: Record<ZoneKey, string> = {
		E: '회복 / 베이스 빌딩',
		M: '마라톤 목표 페이스',
		T: '젖산 역치 자극',
		I: 'VO₂max 인터벌',
		R: '스피드 / 폼',
	};
</script>

<svelte:head>
	<title>VO₂max — endurohub</title>
</svelte:head>

<ToolsShell currentPath={$page.url.pathname}>
<div class="page v-container">
	<div class="tool-layout">
		<!-- INPUT -->
		<div class="panel">
			<span class="eh-micro"><span class="acc">INPUT</span> · 최근 레이스 결과</span>
			<div class="row">
				{#each STD_DISTANCES as d (d.code)}
					<FilterChip selected={Math.abs(km - d.km) < 0.01} onclick={() => (km = d.km)}>{d.label}</FilterChip>
				{/each}
			</div>
			<Field label="Race time" placeholder="예: 1:42:15" bind:value={time} hint="최근 전력 레이스 기록일수록 정확합니다" />
			{#if pf}
				<Prefill label={pf.label} onApply={() => { km = pf.distKm; time = pf.timeStr; }} />
			{/if}
			<p class="src-note">Daniels &amp; Gilbert VDOT 근사식 기반. 트랙 실측 VO₂max와 다를 수 있습니다.</p>
		</div>

		<!-- OUTPUT -->
		<div class="out">
			<div class="out-hero">
				<StatBlock label="VDOT" value={Number.isFinite(v) ? v.toFixed(1) : '—'} size="xl" accent />
				<StatBlock label="등급 (동연령)" value={grade} size="lg" />
			</div>

			{#if paces}
			<div>
				<div class="v-sechead">
					<h2 class="sechead-title">트레이닝 페이스</h2>
					<span class="eh-micro sechead-aux">DANIELS RUNNING FORMULA</span>
				</div>
				<div class="v-table ztable" style="margin-top:12px">
					<div class="v-thead zcols">
						<span></span>
						<span>ZONE</span>
						<span>용도</span>
						<span>PACE/KM</span>
						<span class="hide-m">HR</span>
					</div>
					{#each Object.entries(paces) as [z, p] (z)}
						<div class="v-trow zcols">
							<span class="zone-dot" style="background:{ZONE_INK[z as ZoneKey]}"></span>
							<b>{z} · {p.label}</b>
							<span class="zone-use">{zoneUse[z as ZoneKey]}</span>
							<b class="eh-data">{fmtPace(p.sec)}</b>
							<span class="hide-m eh-data zone-hr">{p.hr}</span>
						</div>
					{/each}
				</div>
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
	.src-note { margin: 0; font-size: 12px; color: var(--text-faint); line-height: 1.6; }

	.out { display: flex; flex-direction: column; gap: var(--sp-6); }
	.out-hero {
		border-top: var(--border-rule);
		padding-top: var(--sp-4);
		display: flex;
		gap: 48px;
		flex-wrap: wrap;
		align-items: flex-end;
	}

	.sechead-title {
		margin: 0;
		font-size: var(--text-h3);
		font-weight: var(--w-strong);
		letter-spacing: var(--track-heading);
		color: var(--text-strong);
	}
	.sechead-aux { color: var(--text-faint); }

	.zcols { grid-template-columns: 14px 110px 1fr 110px 90px; gap: 14px; }
	.zone-dot { width: 10px; height: 10px; border-radius: 50%; align-self: center; }
	.zone-use { color: var(--text-muted); font-size: 13px; }
	.zone-hr { color: var(--text-faint); font-size: 12px; }

	@media (max-width: 768px) {
		.panel { padding: 18px; min-width: 0; }
		.out-hero { gap: 22px 28px; }
		.zcols { grid-template-columns: 14px 90px 1fr 90px; }
		.hide-m { display: none; }
	}
</style>
