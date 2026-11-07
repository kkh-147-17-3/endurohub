<script lang="ts">
	import { page } from '$app/stores';
	import ToolsShell from '$lib/components/arena/ToolsShell.svelte';
	import StatBlock from '$lib/components/eh/StatBlock.svelte';
	import FilterChip from '$lib/components/eh/FilterChip.svelte';
	import Field from '$lib/components/eh/Field.svelte';
	import Prefill from '$lib/components/eh/Prefill.svelte';
	import { STD_DISTANCES, fmtPace, fmtTime, parseTime, timeFromVdot, vdot } from '$lib/tools';

	let { data } = $props();
	const pf = data.prefill;

	let km = $state(pf?.distKm ?? 21.0975);
	let time = $state(pf?.timeStr ?? '1:42:15');

	const sec = $derived(parseTime(time));
	const v = $derived(vdot(km, sec));
	const valid = $derived(Number.isFinite(v) && v > 0);
	const equivalents = $derived(valid ? STD_DISTANCES.map((d) => ({ ...d, sec: timeFromVdot(v, d.km) })) : []);
</script>

<ToolsShell currentPath={$page.url.pathname}>
<div class="page v-container">
	<div class="tool-layout">
		<!-- INPUT -->
		<div class="panel">
			<span class="eh-micro">{pf ? '내 기록 기준 · 수정 가능' : '계산 예시 · 내 기록으로 변경해 보세요'}</span>
			<div class="row">
				{#each STD_DISTANCES as d (d.code)}
					<FilterChip selected={Math.abs(km - d.km) < 0.01} onclick={() => (km = d.km)}>{d.label}</FilterChip>
				{/each}
			</div>
			<Field label="최근 완주 기록" placeholder="예: 1:42:15" bind:value={time} error={!valid} aria-invalid={!valid} hint="시:분:초 또는 분:초 · 최근 평탄한 코스의 레이스 기록을 사용하세요" />
			{#if !valid}<p class="input-error" role="status">거리와 0보다 큰 완주 시간을 확인해 주세요. 분·초 칸은 0–59까지 입력하며, 양수 VDOT를 계산할 수 있는 기록이 필요합니다.</p>{/if}
			{#if pf}
				<Prefill label={pf.label} onApply={() => { km = pf.distKm; time = pf.timeStr; }} />
			{/if}
			<p class="src-note">Daniels &amp; Gilbert 근사식으로 계산하는 기록 기반 수행 지수입니다. VDOT는 실측 VO₂max나 연령별 등급이 아닙니다. <a href="https://support.vdoto2.com/v-o2-faq/" target="_blank" rel="noopener noreferrer">VDOT 공식 설명</a></p>
		</div>

		<!-- OUTPUT -->
		<div class="out">
			<div class="out-hero">
				<StatBlock label="VDOT · 기록 기반 지수" value={valid ? v.toFixed(1) : '—'} size="xl" accent />
			</div>
			<p class="src-note">입력한 {km}km 기록을 바탕으로 계산합니다. 나이·성별·실측 산소 섭취량을 입력받지 않으므로 체력 등급과 백분위는 제공하지 않습니다.</p>

			{#if valid}
			<div>
				<div class="v-sechead">
					<h2 class="sechead-title">같은 VDOT의 거리별 참고 기록</h2>
				</div>
				<div class="v-table ztable" style="margin-top:12px">
					<div class="v-thead zcols">
						<span>거리</span>
						<span>동등 기록</span>
						<span>PACE/KM</span>
					</div>
					{#each equivalents as result (result.code)}
						<div class="v-trow zcols">
							<b>{result.label}</b>
							<b class="eh-data">{fmtTime(result.sec)}</b>
							<span class="eh-data">{fmtPace(result.sec / result.km)}</span>
						</div>
					{/each}
				</div>
				<p class="src-note" style="margin-top:12px">동일한 지수를 만드는 기록을 역산한 수학적 참고값입니다. 완주 예측이나 훈련 페이스 처방이 아니며, 거리별 훈련량·코스·날씨에 따라 실제 기록은 달라집니다.</p>
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
	.input-error { margin: 0; font-size: 13px; color: var(--danger); }

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
	.zcols { grid-template-columns: minmax(50px, 1fr) minmax(90px, 1fr) minmax(80px, 1fr); gap: 12px; }

	@media (max-width: 768px) {
		.panel { padding: 18px; min-width: 0; }
		.out-hero { gap: 22px 28px; }
	}
</style>
