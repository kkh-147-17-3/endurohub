<script lang="ts">
	import { page } from '$app/stores';
	import ToolsShell from '$lib/components/arena/ToolsShell.svelte';
	import FilterChip from '$lib/components/eh/FilterChip.svelte';
	import Field from '$lib/components/eh/Field.svelte';
	import Prefill from '$lib/components/eh/Prefill.svelte';
	import { STD_DISTANCES, fmtPace, fmtTime, parseTime, riegel } from '$lib/tools';

	let { data } = $props();
	const pf = data.prefill;

	let km = $state(pf?.distKm ?? 21.0975);
	let time = $state(pf?.timeStr ?? '1:42:15');

	const sec = $derived(parseTime(time));
	const valid = $derived(Number.isFinite(sec) && sec > 0);
	const rows = $derived(
		STD_DISTANCES.map((d) => {
			const pred = valid ? riegel(sec, km, d.km) : NaN;
			return { ...d, pred, pace: d.km > 0 ? pred / d.km : NaN };
		}),
	);
</script>

<ToolsShell currentPath={$page.url.pathname}>
<div class="page v-container">
	<div class="tool-layout">
		<!-- INPUT -->
		<div class="panel">
			<span class="eh-micro"><span class="acc">INPUT</span> · {pf ? '내 기록 기준 · 수정 가능' : '계산 예시 · 내 기록으로 변경해 보세요'}</span>
			<div class="row">
				{#each STD_DISTANCES as d (d.code)}
					<FilterChip selected={Math.abs(km - d.km) < 0.01} onclick={() => (km = d.km)}>{d.label}</FilterChip>
				{/each}
			</div>
			<Field label="기준 완주 기록" placeholder="예: 1:42:15" bind:value={time} error={!valid} aria-invalid={!valid} hint="시:분:초 또는 분:초 · 숫자만 입력하면 분으로 계산" />
			{#if !valid}<p class="input-error" role="status">0보다 큰 시간을 입력해 주세요. 분·초 칸은 0–59까지 사용할 수 있습니다.</p>{/if}
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

			<p class="src-note">입력한 기록의 거리별 환산값입니다. 장거리 훈련량·코스·날씨에 따라 실제 결과는 달라집니다. <a href="/tools/training-plan">공개 훈련 예제 보기 →</a></p>
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

	.pred-cols { grid-template-columns: 90px 1fr 130px 130px; gap: 14px; }
	.pred--base { background: var(--paper-50); }
	.pred-note { font-size: 12px; color: var(--text-faint); }
	.pred-time { font-size: 17px; }
	.pred-pace { color: var(--text-muted); }


	@media (max-width: 768px) {
		.panel { padding: 18px; min-width: 0; }
		.pred-cols { grid-template-columns: 70px 1fr 110px; }
		.hide-m { display: none; }
	}
</style>
