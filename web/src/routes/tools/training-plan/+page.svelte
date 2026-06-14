<script lang="ts">
	import { page } from '$app/stores';
	import ToolsShell from '$lib/components/arena/ToolsShell.svelte';
	import StatBlock from '$lib/components/eh/StatBlock.svelte';
	import Select from '$lib/components/eh/Select.svelte';
	import FilterChip from '$lib/components/eh/FilterChip.svelte';
	import {
		buildPlan,
		dayDetail,
		daysUntil,
		fmtPace,
		parseTime,
		trainingPaces,
		vdot,
		PHASE_DEFS,
		ZONE_INK,
		type RunDays,
		type ZoneKey
	} from '$lib/tools';

	let { data } = $props();
	const pf = data.prefill;

	// Target races come from the user's 관심대회 (favorites), upcoming only.
	const goalRaces = data.goalRaces;
	const hasGoals = goalRaces.length > 0;

	// fitness basis: signed-in user's recent record, else the design's sample.
	const recentDistKm = pf?.distKm ?? 21.0975;
	const recentTimeSec = pf?.timeSec ?? parseTime('1:42:15');

	// ── inputs ──
	let raceId = $state(goalRaces[0]?.id ?? ''); // nearest goal (sorted by date)
	let days = $state<RunDays>(5);
	let lenChoice = $state<number | null>(null);
	let focus = $state(0);

	const race = $derived(goalRaces.find((r) => r.id === raceId) ?? goalRaces[0]);
	const raceOptions = $derived(
		goalRaces.map((r) => ({
			value: r.id,
			label: `${r.name} · ${r.date.slice(5).replace('-', '.')}`
		}))
	);

	const daysOut = $derived(race ? daysUntil(race.date) : 0);
	const maxWeeks = $derived(Math.floor(daysOut / 7));
	// A 4-phase plan needs at least one week per phase; below that the race is too
	// imminent to periodize and we show a notice instead of a fabricated plan.
	const MIN_PLAN_WEEKS = 4;
	const canPlan = $derived(maxWeeks >= MIN_PLAN_WEEKS);
	// Offer only plan lengths that fit before race day; fall back to whatever fits.
	const lenOptions = $derived.by(() => {
		if (!canPlan) return [];
		const cand = [8, 12, 16, 18, 20].filter((w) => w <= maxWeeks);
		return cand.length ? cand : [maxWeeks];
	});
	const weeks = $derived(
		!canPlan
			? 0
			: lenChoice != null && lenOptions.includes(lenChoice)
				? lenChoice
				: (lenOptions.find((w) => w <= 16 && w >= 12) ?? lenOptions[lenOptions.length - 1])
	);

	// ── plan ──
	const v = $derived(vdot(recentDistKm, recentTimeSec));
	const paces = $derived(trainingPaces(v));
	const built = $derived(canPlan && race ? buildPlan(weeks, v, days, race.date, race.name) : null);
	const fIdx = $derived(built ? Math.min(focus, built.plan.length - 1) : 0);
	const fw = $derived(built ? built.plan[fIdx] : null);

	const fmtMonth = (d: Date) => `${d.getMonth() + 1}/${d.getDate()}`;
	const fmtKm = (km: number) => `${parseFloat(km.toFixed(1))}`;
</script>

<svelte:head>
	<title>트레이닝 플랜 — endurohub</title>
</svelte:head>

{#snippet sechead(title: string, aux: string)}
	<div class="sechead">
		<h2 class="sechead-title">{title}</h2>
		<span class="eh-micro sechead-aux">{aux}</span>
	</div>
{/snippet}

<ToolsShell currentPath={$page.url.pathname}>
<div class="page v-container">
	{#if !hasGoals}
		<!-- No upcoming 관심대회 to target — guide the user to register one -->
		<div class="empty-panel">
			<span class="eh-micro"><span class="acc">INPUT</span> · 플랜 구성</span>
			<h2 class="empty-title">목표 대회를 먼저 등록하세요</h2>
			{#if data.signedIn}
				<p class="empty-desc">
					관심대회로 등록한 다가오는 대회가 없습니다. 대회 카드의 하트를 눌러 목표 대회를
					추가하면 일정에 맞춘 트레이닝 플랜을 만들어 드립니다.
				</p>
				<a class="empty-cta" href="/races">대회 둘러보기 <span class="arrow">→</span></a>
			{:else}
				<p class="empty-desc">
					로그인하면 관심대회로 등록한 목표 대회에 맞춰 단계별 트레이닝 플랜을 만들어 드립니다.
				</p>
				<a class="empty-cta" href="/auth/login?next=/tools/training-plan"
					>로그인 <span class="arrow">→</span></a
				>
			{/if}
		</div>
	{:else}
		<div class="tool-layout">
			<!-- INPUT -->
			<div class="panel">
				<span class="eh-micro"><span class="acc">INPUT</span> · 플랜 구성</span>
				<Select label="목표 대회 (관심 대회 기반)" options={raceOptions} bind:value={raceId} />

				{#if canPlan}
					<div>
						<span class="eh-micro field-label">PLAN LENGTH</span>
						<div class="row">
							{#each lenOptions as w (w)}
								<FilterChip selected={weeks === w} onclick={() => (lenChoice = w)}>{w}주</FilterChip>
							{/each}
						</div>
					</div>

					<div>
						<span class="eh-micro field-label">RUN DAYS / WEEK</span>
						<div class="row">
							{#each [5, 6] as d (d)}
								<FilterChip selected={days === d} onclick={() => (days = d as RunDays)}>주 {d}일</FilterChip>
							{/each}
						</div>
					</div>
				{/if}

				<div class="panel-stats">
					<StatBlock label="D-Day" value={'D-' + daysOut} size="md" accent />
					<StatBlock label="현재 VDOT" value={v.toFixed(1)} size="md" />
				</div>
				{#if canPlan}
					<p class="src-note">
						VDOT {v.toFixed(1)} 기준 단계별 페이스가 적용됩니다. 4주마다 회복 주(volume −18%)가 자동
						배치됩니다.
					</p>
				{/if}
			</div>

			<!-- OUTPUT -->
			<div class="out">
			{#if built && fw}
				<div class="out-hero">
					<StatBlock label="총 볼륨" value={built.totalKm.toLocaleString()} unit="KM" size="xl" accent />
					<StatBlock label="피크 주차" value={built.peak.weekKm} unit="KM" size="lg" />
					<StatBlock label="최장 LSD" value={built.longMax} unit="KM" size="lg" />
					<StatBlock label="기간" value={weeks} unit="주" size="lg" />
				</div>

				<!-- periodization + weekly load -->
				<div>
					{@render sechead('주기화 · 주간 부하', `${built.raceName} 까지 ${weeks}주`)}
					<div class="phaseband">
						{#each PHASE_DEFS as ph, i (ph.name)}
							<div style="flex:{built.alloc[i]};background:{ph.color}">
								<span class="eh-data band-lbl" style="color:{ph.ink}">{ph.name} {built.alloc[i]}W</span>
							</div>
						{/each}
					</div>
					<div class="loadwrap">
						<div class="loadrow">
							{#each built.plan as w, i (w.wk)}
								{@const h = Math.max(6, Math.round((w.weekKm / built.peak.weekKm) * 116))}
								<button
									type="button"
									class="loadbar"
									class:on={i === fIdx}
									onclick={() => (focus = i)}
									title={`W${w.wk} · ${w.weekKm}km`}
								>
									<span class="cap" style="background:{w.ink}"></span>
									<span
										class="fill"
										style="height:{h}px;background:{w.color};opacity:{i === fIdx
											? 1
											: 0.78};border-top:2px solid {w.ink}"
									></span>
								</button>
							{/each}
						</div>
						<div class="weekaxis">
							{#each built.plan as w, i (w.wk)}
								<span class="eh-data" class:on={i === fIdx}>
									{i === fIdx || w.wk === 1 || w.wk === built.plan.length || w.wk % 4 === 0
										? 'W' + w.wk
										: '·'}
								</span>
							{/each}
						</div>
					</div>
				</div>

				<!-- focused week detail -->
				<div>
					{@render sechead(
						`WEEK ${fw.wk} 상세`,
						`${fmtMonth(fw.monday)} 주 · D-${(weeks - fw.wk + 1) * 7}`
					)}
					<div class="week-meta">
						<div class="week-tag-row">
							<span class="phase-tag eh-data" style="background:{fw.color};color:{fw.ink}">{fw.phase}</span>
							{#if fw.cutback}<span class="eh-micro cutback">회복 주</span>{/if}
						</div>
						<StatBlock label="주간 거리" value={fw.weekKm} unit="KM" size="lg" accent />
						<StatBlock label="러닝" value={fw.days.filter((d) => d.zone !== 'REST').length} unit="일" size="md" />
					</div>
					<div class="daygrid">
						{#each fw.days as d (d.dow)}
							{@const det = dayDetail(d.zone, fw.weekKm, paces, built.raceName)}
							<div class="daycell" class:rest={det.rest} class:race={det.race}>
								<span class="dn eh-data">{d.dow}</span>
								<span
									class="zlabel"
									style="color:{det.rest
										? 'var(--text-faint)'
										: det.race
											? 'var(--text-accent)'
											: det.zoneInk || 'var(--text-strong)'}">{det.label}</span
								>
								<span class="zsub">{det.sub}</span>
								{#if !det.rest}
									<span class="zspec">
										{#if det.race}
											{#if race?.distKm != null}
												<span class="zkm eh-data race-km">{fmtKm(race.distKm)}K</span>
											{/if}
										{:else}
											<span class="zkm eh-data">{det.km}K</span>
											<span class="zpace eh-data">{fmtPace(det.pace ?? 0)}</span>
										{/if}
									</span>
								{/if}
							</div>
						{/each}
					</div>
				</div>

				<!-- training paces -->
				<div>
					{@render sechead('트레이닝 페이스', `DANIELS · VDOT ${v.toFixed(1)}`)}
					<div class="paceref">
						{#each Object.entries(paces) as [z, p] (z)}
							<div>
								<div class="pace-head">
									<span class="pace-dot" style="background:{ZONE_INK[z as ZoneKey]}"></span>
									<span class="eh-micro pace-zone">{z} · {p.label}</span>
								</div>
								<div class="eh-data pace-val">{fmtPace(p.sec)}</div>
								<div class="eh-micro pace-hr">HR {p.hr}</div>
							</div>
						{/each}
					</div>
				</div>
			{:else}
				<div class="too-soon">
					{@render sechead('플랜 구성 불가', `D-${daysOut}`)}
					<p class="too-soon-desc">
						이 대회는 일정이 너무 임박해 단계별 트레이닝 플랜을 구성할 수 없습니다. 최소 {MIN_PLAN_WEEKS}주
						이상 여유가 있는 목표 대회를 선택해 주세요.
					</p>
				</div>
			{/if}
			</div>
		</div>
	{/if}
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
	.panel .row { display: flex; gap: 8px; flex-wrap: wrap; }
	.field-label { display: block; margin-bottom: 8px; }
	.panel-stats {
		display: flex;
		gap: 30px;
		flex-wrap: wrap;
		border-top: var(--border-hair);
		padding-top: 16px;
	}
	.src-note { margin: 0; font-size: 12px; color: var(--text-faint); line-height: 1.6; }

	.out { display: flex; flex-direction: column; gap: var(--sp-6); }
	.out-hero {
		border-top: var(--border-rule);
		padding-top: 16px;
		display: flex;
		gap: 48px;
		flex-wrap: wrap;
		align-items: flex-end;
	}

	/* section head */
	.sechead {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 16px;
		padding-bottom: 10px;
		border-bottom: var(--border-hair);
	}
	.sechead-title {
		margin: 0;
		font-size: var(--text-h3);
		font-weight: var(--w-strong);
		letter-spacing: var(--track-heading);
		color: var(--text-strong);
	}
	.sechead-aux { color: var(--text-faint); }

	/* phase band */
	.phaseband { display: flex; border: 1px solid var(--line); height: 30px; margin-top: 14px; }
	.phaseband > div {
		display: grid;
		place-items: center;
		min-width: 0;
		border-right: 1px solid var(--paper-0);
	}
	.phaseband > div:last-child { border-right: 0; }
	.band-lbl { font-size: 10.5px; font-weight: 800; letter-spacing: 0.07em; }
	.phase-tag {
		font-size: 10.5px;
		font-weight: 800;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		padding: 2px 7px;
		border-radius: var(--r-2);
	}

	/* weekly load chart */
	.loadwrap { border: 1px solid var(--line); padding: 16px 16px 12px; margin-top: 8px; }
	.loadrow { display: flex; align-items: flex-end; gap: 2px; height: 132px; }
	.loadbar {
		flex: 1;
		min-width: 0;
		align-self: stretch;
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
		cursor: pointer;
		padding: 0;
		border: 0;
		background: none;
	}
	.loadbar .fill { width: 100%; transition: opacity var(--dur-fast) var(--ease-out); }
	.loadbar:hover .fill { opacity: 1 !important; }
	.loadbar .cap { height: 3px; width: 100%; opacity: 0; transition: opacity var(--dur-fast) var(--ease-out); }
	.loadbar.on .cap, .loadbar:hover .cap { opacity: 1; }
	.weekaxis {
		display: flex;
		gap: 2px;
		margin-top: 7px;
		border-top: var(--border-hair);
		padding-top: 6px;
	}
	.weekaxis > span {
		flex: 1;
		min-width: 0;
		text-align: center;
		font-size: 9.5px;
		color: var(--text-faint);
		letter-spacing: 0.02em;
	}
	.weekaxis > span.on { color: var(--text-strong); font-weight: 700; }

	/* focused week */
	.week-meta {
		display: flex;
		align-items: flex-end;
		gap: 36px;
		flex-wrap: wrap;
		margin: 14px 0;
	}
	.week-tag-row { display: flex; align-items: center; gap: 10px; }
	.cutback { color: var(--caution); }

	.daygrid {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
		gap: 1px;
		background: var(--line);
		border: 1px solid var(--line);
	}
	.daycell {
		background: var(--paper-0);
		padding: 12px 10px;
		min-height: 112px;
		display: flex;
		flex-direction: column;
		gap: 5px;
	}
	.daycell.rest { background: var(--paper-50); }
	.daycell.race { background: var(--signal-100); }
	.daycell .dn { font-size: 10px; font-weight: 700; letter-spacing: 0.08em; color: var(--text-faint); }
	.daycell .zlabel { font-weight: 800; font-size: 14px; letter-spacing: -0.01em; line-height: 1.1; }
	.daycell .zsub { font-size: 11px; color: var(--text-muted); line-height: 1.35; }
	.daycell .zspec { margin-top: auto; display: flex; align-items: baseline; gap: 8px; }
	.daycell .zkm { font-weight: 700; font-size: 13px; }
	.daycell .race-km { color: var(--text-accent); }
	.daycell .zpace { font-size: 11.5px; color: var(--text-accent); font-weight: 700; }

	/* training paces */
	.paceref {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 1px;
		background: var(--line);
		border: 1px solid var(--line);
		margin-top: 14px;
	}
	.paceref > div { background: var(--paper-0); padding: 13px 14px; }
	.pace-head { display: flex; align-items: center; gap: 7px; margin-bottom: 6px; }
	.pace-dot { width: 9px; height: 9px; border-radius: 50%; }
	.pace-zone { color: var(--text-strong); }
	.pace-val { font-size: 19px; font-weight: 800; letter-spacing: -0.02em; }
	.pace-hr { color: var(--text-faint); margin-top: 2px; }

	@media (max-width: 768px) {
		.panel { padding: 18px; min-width: 0; }
		.out-hero { gap: 22px 28px; }

		/* day plan: 7-col grid → start-list rows */
		.daygrid { grid-template-columns: 1fr; gap: 0; }
		.daycell {
			flex-direction: row;
			align-items: center;
			min-height: 0;
			gap: 12px;
			padding: 11px 14px;
			border-bottom: 1px solid var(--line);
		}
		.daygrid .daycell:last-child { border-bottom: 0; }
		.daycell .dn { flex: 0 0 36px; }
		.daycell .zlabel { flex: 0 0 90px; font-size: 15px; }
		.daycell .zsub { display: block; flex: 1 1 auto; min-width: 0; font-size: 11.5px; }
		.daycell .zspec { margin-top: 0; flex: 0 0 auto; gap: 10px; align-items: baseline; }

		.paceref { grid-template-columns: repeat(3, minmax(0, 1fr)); }
		.paceref > div { padding: 11px 12px; }
		.pace-zone { white-space: normal; }
	}

	/* output notice — selected race too imminent to plan (defensive) */
	.too-soon { border: 1px solid var(--line); padding: var(--sp-6); background: var(--paper-0); }
	.too-soon-desc {
		margin: 14px 0 0;
		font-size: 13.5px;
		line-height: 1.7;
		color: var(--text-body);
		word-break: keep-all;
	}

	/* empty state — no upcoming 관심대회 to target */
	.empty-panel {
		border: 1px solid var(--ink-900);
		padding: var(--sp-10) var(--sp-8);
		background: var(--paper-0);
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: var(--sp-4);
		max-width: 560px;
	}
	.empty-title {
		margin: 0;
		font-size: var(--text-h3);
		font-weight: var(--w-strong);
		letter-spacing: var(--track-heading);
		color: var(--text-strong);
	}
	.empty-desc {
		margin: 0;
		font-size: 13.5px;
		line-height: 1.7;
		color: var(--text-body);
		word-break: keep-all;
	}
	.empty-cta {
		display: inline-flex;
		align-items: center;
		gap: 10px;
		margin-top: var(--sp-2);
		padding: 11px 18px;
		background: var(--ink-900);
		color: var(--paper-0);
		font-size: 13px;
		font-weight: 700;
		letter-spacing: -0.2px;
		text-decoration: none;
	}
	.empty-cta .arrow { color: var(--accent); }
</style>
