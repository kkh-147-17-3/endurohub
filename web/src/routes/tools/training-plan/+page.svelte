<script lang="ts">
	import { page } from '$app/stores';
	import ToolsShell from '$lib/components/arena/ToolsShell.svelte';
	import StatBlock from '$lib/components/eh/StatBlock.svelte';
	import Select from '$lib/components/eh/Select.svelte';
	import FilterChip from '$lib/components/eh/FilterChip.svelte';
	import { buildPlan, vdot, PHASE_DEFS, type PlanZone, type RunDays } from '$lib/tools';
	import {
		MIN_TRAINING_PLAN_WEEKS,
		referencePlanWeeks,
		trainingPlanTiming,
	} from '$lib/tools/public-training-example';

	let { data } = $props();
	const publicExample = $derived(data.publicExample);
	const goalRaces = $derived(data.goalRaces);
	const hasGoals = $derived(goalRaces.length > 0);
	let chosenMode = $state<'example' | 'personal' | null>(null);
	const isExample = $derived(!hasGoals || chosenMode === 'example');
	const personalVdot = $derived(data.prefill ? vdot(data.prefill.distKm, data.prefill.timeSec) : NaN);
	const usesSampleRecord = $derived(isExample || !data.prefill || !Number.isFinite(personalVdot) || personalVdot <= 0);
	const basis = $derived(usesSampleRecord ? publicExample.record : data.prefill!);

	let raceId = $state('');
	let days = $state<RunDays>(5);
	let lenChoice = $state<number | null>(null);
	let focus = $state(0);
	const race = $derived(isExample ? publicExample.goal : (goalRaces.find((r) => r.id === raceId) ?? goalRaces[0]));
	const raceOptions = $derived(goalRaces.map((r) => ({
		value: r.id,
		label: `${r.name} · ${r.date.slice(5).replace('-', '.')}`,
	})));
	const timing = $derived(trainingPlanTiming(race?.date ?? '', publicExample.referenceDateKst));
	const weeks = $derived(!timing.canPlan ? 0
		: lenChoice != null && timing.lengths.includes(lenChoice) ? lenChoice
		: isExample ? publicExample.weeks
		: (timing.lengths.find((w) => w >= 12 && w <= 16) ?? timing.lengths[timing.lengths.length - 1]));

	const modelVdot = $derived(vdot(basis.distKm, basis.timeSec));
	const built = $derived(timing.canPlan && race ? buildPlan(weeks, modelVdot, days, race.date, race.name) : null);
	const plan = $derived(built && race ? referencePlanWeeks(built.plan, race.date) : []);
	const focusIndex = $derived(Math.min(focus, Math.max(0, plan.length - 1)));
	const focusedWeek = $derived(plan[focusIndex]);
	const peakLoad = $derived(built?.peak.weekKm ?? 1);
	const loadIndex = (weekKm: number) => Math.round(weekKm / peakLoad * 100);
	const baseRunDays = $derived(days === 5 ? 4 : 5);
	const weekRunDays = $derived(focusedWeek?.days.filter((day) => day.zone !== 'REST').length ?? 0);

	const DAY_LABELS: Record<string, string> = { MON: '월', TUE: '화', WED: '수', THU: '목', FRI: '금', SAT: '토', SUN: '일' };
	const ZONE_LABELS: Record<PlanZone, string> = {
		E: '가벼운 러닝', LONG: '긴 거리 러닝', T: '템포 러닝', I: '인터벌 러닝', M: '마라톤 페이스 구간', REST: '휴식', RACE: '목표 대회',
	};
	const PHASE_LABELS: Record<string, string> = { BASE: '기초', BUILD: '빌드', PEAK: '피크', TAPER: '테이퍼' };

	function chooseMode(mode: 'example' | 'personal') {
		chosenMode = mode;
		lenChoice = null;
		focus = 0;
	}
</script>

<ToolsShell currentPath={$page.url.pathname}>
	<div class="page v-container">
		{#if hasGoals}
			<div class="mode-switch" aria-label="플랜 보기 선택">
				<FilterChip selected={!isExample} onclick={() => chooseMode('personal')}>내 관심 대회</FilterChip>
				<FilterChip selected={isExample} onclick={() => chooseMode('example')}>공개 예시</FilterChip>
			</div>
		{/if}

		<section class="plan-context" aria-labelledby="plan-context-title">
			<div class="eh-micro">{isExample ? '공개 예시 · 가상의 기록과 목표' : '내 관심 대회 · 참고 모형'}</div>
			<h2 id="plan-context-title">{isExample ? `가상 풀코스 목표로 ${weeks}주 구성 살펴보기` : '내 대회 날짜로 주차별 구성 살펴보기'}</h2>
			{#if isExample}
				<p>예시 기록은 하프 21.0975km · 1:42:15, 예시 목표는 기준일로부터 16주 후의 가상 풀코스 42.195km입니다. 실제 대회나 회원 기록을 사용하지 않습니다.</p>
			{:else}
				<p>선택한 도로 마라톤의 풀코스 42.195km를 기준으로 주차를 배치합니다. 이 참고 모형은 풀코스 종목이 있는 도로 달리기 대회를 지원합니다.</p>
			{/if}
			<p class="basis-note"><strong>{usesSampleRecord ? '계산 기준 · 예시 기록' : '계산 기준 · 내 최근 기록'}</strong> {basis.label}
				{#if !isExample && usesSampleRecord} · 사용할 수 있는 러닝 기록이 없어 예시 기록을 사용합니다.{/if}
			</p>
			<p class="model-note">주간 부하 지수는 이 모형의 가장 높은 주를 100으로 놓은 상대값입니다. 요일별 활동 종류를 비교하는 참고 예시이며, 개인별 훈련 거리·강도를 처방하지 않습니다.</p>
			{#if !hasGoals}
				{#if data.signedIn}
					<p>내 일정으로 보려면 30일 이상 남은 풀코스 도로 마라톤을 관심 등록해 주세요. 하프·10km·트레일 대회는 현재 모형의 대상에 포함되지 않습니다.</p>
					<a class="context-cta" href="/races">풀코스 마라톤 찾아보기 →</a>
				{:else}
					<a class="context-cta" href="/auth/login?next=/tools/training-plan">로그인 후 관심 대회 일정으로 보기 →</a>
				{/if}
			{/if}
		</section>

		<div class="tool-layout">
			<div class="panel">
				<h2 class="panel-title">플랜 구성</h2>
				{#if isExample}
					<p class="sample-target"><strong>예시 목표</strong><br />가상 풀코스 마라톤 · 42.195km<br />기준일로부터 16주 후</p>
				{:else}
					<Select label="목표 대회 (관심 대회의 풀코스 기준)" options={raceOptions} value={race.id} onchange={(event) => { raceId = (event.target as HTMLSelectElement).value; focus = 0; }} />
				{/if}

				{#if timing.canPlan}
					<div>
						<span class="eh-micro field-label">살펴볼 기간</span>
						<div class="row">
							{#each timing.lengths as length (length)}
								<FilterChip selected={weeks === length} onclick={() => { lenChoice = length; focus = 0; }}>{length}주</FilterChip>
							{/each}
						</div>
					</div>
					<div>
						<span class="eh-micro field-label">기본 러닝 횟수</span>
						<div class="row">
							{#each [5, 6] as pattern (pattern)}
								<FilterChip selected={days === pattern} onclick={() => (days = pattern as RunDays)}>주 {pattern === 5 ? 4 : 5}회</FilterChip>
							{/each}
						</div>
						<p class="field-note">테이퍼와 대회 주간에는 실제 활동 횟수가 줄어들 수 있습니다. 선택한 주의 횟수를 아래에서 확인하세요.</p>
					</div>
				{/if}
				<div class="panel-stats">
					<StatBlock label={isExample ? '가상 목표까지' : '목표 대회까지'} value={String(timing.daysOut)} unit="일" size="md" accent />
				</div>
			</div>

			<div class="out">
				{#if built && focusedWeek}
					<div class="out-hero">
						<StatBlock label="살펴볼 기간" value={String(weeks)} unit="주" size="xl" accent />
						<StatBlock label="단계" value="4" unit="단계" size="lg" />
						<StatBlock label="기본 러닝" value={String(baseRunDays)} unit="회/주" size="lg" />
					</div>

					<section aria-labelledby="phase-title">
						<div class="sechead"><h2 id="phase-title">주차별 단계와 상대 부하</h2><span>{race.name} 기준</span></div>
						<div class="phaseband">
							{#each PHASE_DEFS as phase, index (phase.name)}
								<div style="flex:{built.alloc[index]};background:{phase.color};color:{phase.ink}">{PHASE_LABELS[phase.name]} {built.alloc[index]}주</div>
							{/each}
						</div>
						<div class="loadchart" aria-label="주차를 선택하면 요일별 참고 패턴이 표시됩니다">
							{#each plan as week, index (week.wk)}
								<button type="button" class="week-bar" class:active={index === focusIndex} aria-pressed={index === focusIndex} aria-label={`${week.wk}주차 · ${PHASE_LABELS[week.phase]} · 부하 지수 ${loadIndex(week.weekKm)}`} onclick={() => (focus = index)}>
									<span class="bar-fill" style="height:{Math.max(8, loadIndex(week.weekKm))}px;background:{week.color};border-top:3px solid {week.ink}"></span>
									<span class="bar-label">{week.wk}</span>
								</button>
							{/each}
						</div>
						<p class="field-note">막대를 선택해 해당 주의 구성을 살펴보세요. 부하 지수 100은 선택한 예시 안에서 가장 높은 주입니다.</p>
					</section>

					<section aria-labelledby="week-detail-title">
						<div class="sechead"><h2 id="week-detail-title">{focusedWeek.wk}주차 · {PHASE_LABELS[focusedWeek.phase]}</h2><span>목표까지 {weeks - focusedWeek.wk + 1}주 구간</span></div>
						<div class="week-meta">
							<StatBlock label="상대 부하 지수" value={String(loadIndex(focusedWeek.weekKm))} size="lg" accent />
							<StatBlock label="이번 주 활동" value={String(weekRunDays)} unit="회" size="md" />
						</div>
						<div class="daygrid">
							{#each focusedWeek.days as day (day.dow)}
								<div class="daycell" class:rest={day.zone === 'REST'} class:race={day.zone === 'RACE'}>
									<span class="day-name">{DAY_LABELS[day.dow]}요일</span>
									<strong>{ZONE_LABELS[day.zone]}</strong>
									{#if day.zone === 'RACE'}<span class="day-note">{isExample ? '가상 풀코스 목표' : race.name}</span>{/if}
								</div>
							{/each}
						</div>
						<p class="field-note">요일별 활동은 참고 패턴입니다. 목표 대회 표시는 마지막 주에 한 번만 표시합니다.</p>
					</section>
				{:else}
					<section class="too-soon" aria-labelledby="too-soon-title">
						<h2 id="too-soon-title">목표 대회가 가까워 주차별 구성을 만들 수 없습니다</h2>
						<p>이 모형은 네 단계를 배치할 최소 {MIN_TRAINING_PLAN_WEEKS}주가 필요합니다. 다른 관심 대회를 선택하거나 공개 예시를 살펴보세요.</p>
						<FilterChip selected={false} onclick={() => chooseMode('example')}>16주 공개 예시 보기</FilterChip>
					</section>
				{/if}
			</div>
		</div>
	</div>
</ToolsShell>

<style>
	.page { padding-top: 28px; padding-bottom: var(--sp-20); }
	.mode-switch, .row { display: flex; flex-wrap: wrap; gap: 8px; }
	.mode-switch { margin-bottom: 18px; }
	.plan-context { border: 1px solid var(--line); padding: 22px 24px; margin-bottom: 28px; background: var(--paper-50); }
	.plan-context h2 { margin: 8px 0 10px; font-size: var(--text-h3); color: var(--text-strong); }
	.plan-context p { margin: 8px 0 0; max-width: 78ch; font-size: 14px; line-height: 1.7; color: var(--text-muted); word-break: keep-all; }
	.plan-context .basis-note { color: var(--text-strong); }
	.context-cta { display: inline-block; margin-top: 14px; color: var(--text-accent); font-size: 14px; font-weight: 700; }
	.tool-layout { display: grid; grid-template-columns: 1fr; gap: var(--sp-6); align-items: start; }
	.panel { border: 1px solid var(--ink-900); padding: var(--sp-6); background: var(--paper-0); display: flex; flex-direction: column; gap: 22px; min-width: 0; }
	.panel-title, .sechead h2, .too-soon h2 { margin: 0; font-size: var(--text-h3); font-weight: var(--w-strong); color: var(--text-strong); }
	.sample-target { margin: 0; font-size: 14px; line-height: 1.7; color: var(--text-muted); }
	.field-label { display: block; margin-bottom: 8px; }
	.field-note { margin: 10px 0 0; font-size: 12px; line-height: 1.6; color: var(--text-muted); }
	.panel-stats { border-top: var(--border-hair); padding-top: 16px; }
	.out { display: flex; flex-direction: column; gap: 30px; min-width: 0; }
	.out-hero { display: flex; flex-wrap: wrap; gap: 24px 36px; border-top: var(--border-rule); padding-top: 16px; }
	.sechead { display: flex; flex-wrap: wrap; gap: 10px 18px; align-items: baseline; justify-content: space-between; border-bottom: var(--border-hair); padding-bottom: 10px; }
	.sechead > span { font-size: 12px; color: var(--text-muted); }
	.phaseband { display: flex; border: 1px solid var(--line); margin-top: 14px; min-height: 32px; }
	.phaseband > div { display: grid; place-items: center; min-width: 0; font-size: 11px; font-weight: 700; padding: 5px 2px; text-align: center; }
	.loadchart { display: flex; gap: 3px; align-items: stretch; border: 1px solid var(--line); padding: 14px 12px 8px; margin-top: 8px; }
	.week-bar { flex: 1; min-width: 0; height: 132px; padding: 0; border: 0; background: none; cursor: pointer; display: flex; flex-direction: column; justify-content: flex-end; gap: 8px; color: var(--text-muted); }
	.week-bar.active { color: var(--text-strong); font-weight: 800; }
	.week-bar:focus-visible { outline: 2px solid var(--text-accent); outline-offset: 2px; }
	.bar-fill { display: block; width: 100%; opacity: 0.65; }
	.week-bar.active .bar-fill, .week-bar:hover .bar-fill { opacity: 1; }
	.bar-label { font-size: 11px; text-align: center; }
	.week-meta { display: flex; flex-wrap: wrap; gap: 24px 36px; align-items: flex-end; margin: 16px 0; }
	.daygrid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 1px; background: var(--line); border: 1px solid var(--line); }
	.daycell { display: flex; flex-direction: column; gap: 10px; min-width: 0; min-height: 110px; padding: 12px 10px; background: var(--paper-0); }
	.daycell.rest { background: var(--paper-50); }
	.daycell.race { background: var(--signal-100); }
	.day-name, .day-note { font-size: 11px; color: var(--text-muted); line-height: 1.5; }
	.daycell strong { font-size: 13px; line-height: 1.4; word-break: keep-all; }
	.too-soon { padding: 24px; border: 1px solid var(--line); }
	.too-soon p { font-size: 14px; line-height: 1.7; color: var(--text-muted); margin: 14px 0 18px; }
	@media (min-width: 960px) { .tool-layout { grid-template-columns: 320px minmax(0, 1fr); gap: var(--sp-10); } }
	@media (max-width: 768px) {
		.panel, .plan-context { padding: 18px; }
		.daygrid { grid-template-columns: 1fr; }
		.daycell { flex-direction: row; min-height: 0; align-items: center; padding: 12px 14px; gap: 16px; }
		.day-name { flex: 0 0 42px; }
		.daycell strong { flex: 1; }
		.day-note { flex: 1; }
		.loadchart { padding: 12px 6px 8px; gap: 2px; }
		.bar-label { font-size: 10px; }
	}
</style>
