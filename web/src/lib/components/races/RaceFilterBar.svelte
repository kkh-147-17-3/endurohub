<script lang="ts">
	import { goto } from '$app/navigation';
	import FilterChip from '$lib/components/eh/FilterChip.svelte';
	import Select from '$lib/components/eh/Select.svelte';
	import { SPORT_META, appSportToDs } from '$lib/components/eh/meta';
	import type { SportOption, DistanceCategory } from '$lib/types';

	interface Applied {
		sport: string[];
		region: string[];
		status: string[];
		name: string | null;
		distanceCategory: string[];
		monthFrom: string;
		monthTo: string | null;
	}

	let {
		filters,
		applied,
		total = 0,
		title = '전체 대회'
	}: {
		filters: {
			regions: string[];
			sports: SportOption[];
			distanceCategories: Record<string, DistanceCategory[]>;
		};
		applied: Applied;
		total?: number;
		title?: string;
	} = $props();

	const STATUSES = [
		{ value: 'registration_open', label: '접수 중' },
		{ value: 'closing_soon', label: '마감 임박' },
		{ value: 'upcoming', label: '예정' },
		{ value: 'registration_closed', label: '접수 마감' }
	] as const;

	// ── Current month (server defaults month_from to this when absent) ────────
	const now = new Date();
	const curY = now.getFullYear();
	const curM = now.getMonth() + 1;
	const currentMonth = `${curY}-${String(curM).padStart(2, '0')}`;

	// ── Selections derive straight from the URL (server `applied`) ────────────
	let sportSel = $derived(applied.sport ?? []);
	let regionSel = $derived(applied.region ?? []);
	let statusSel = $derived(applied.status ?? []);
	let distSel = $derived(applied.distanceCategory ?? []);
	let monthFrom = $derived(applied.monthFrom || currentMonth);
	let monthTo = $derived(applied.monthTo ?? null);

	// 거리 카테고리는 종목이 정확히 1개일 때만 의미가 있다 (백엔드 규칙과 동일).
	let availableDist = $derived(sportSel.length === 1 ? (filters.distanceCategories[sportSel[0]] ?? []) : []);

	let monthActive = $derived(monthFrom !== currentMonth || monthTo != null);
	let activeCount = $derived(
		sportSel.length + regionSel.length + statusSel.length + distSel.length + (monthActive ? 1 : 0) + (applied.name ? 1 : 0)
	);

	// Name input — local draft synced to the applied value on navigation.
	let nameDraft = $state('');
	$effect(() => {
		nameDraft = applied.name ?? '';
	});

	// ── URL building ──────────────────────────────────────────────────────────
	type Over = Partial<{
		sport: string[];
		region: string[];
		status: string[];
		distance_category: string[];
		name: string;
		month_from: string;
		month_to: string | null;
	}>;

	function buildParams(over: Over = {}): URLSearchParams {
		const sport = over.sport ?? sportSel;
		const region = over.region ?? regionSel;
		const status = over.status ?? statusSel;
		const name = over.name !== undefined ? over.name : (applied.name ?? '');
		let dist = over.distance_category ?? distSel;
		const mFrom = over.month_from !== undefined ? over.month_from : monthFrom;
		const mTo = over.month_to !== undefined ? over.month_to : monthTo;

		if (sport.length !== 1) dist = []; // distance only valid for a single sport

		const sp = new URLSearchParams();
		for (const s of sport) sp.append('sport', s);
		for (const r of region) sp.append('region', r);
		for (const s of status) sp.append('status', s);
		if (name) sp.set('name', name);
		for (const d of dist) sp.append('distance_category', d);
		if (mFrom && mFrom !== currentMonth) sp.set('month_from', mFrom);
		if (mTo) sp.set('month_to', mTo);
		return sp;
	}

	function apply(over: Over = {}) {
		const qs = buildParams(over).toString();
		goto(qs ? `/races?${qs}` : '/races', { noScroll: true, keepFocus: true });
	}

	function toggle(list: string[], v: string): string[] {
		return list.includes(v) ? list.filter((x) => x !== v) : [...list, v];
	}

	function submitName(e: Event) {
		e.preventDefault();
		apply({ name: nameDraft.trim() || '' });
	}

	function resetAll() {
		goto('/races', { noScroll: true });
	}

	// ── Month presets ─────────────────────────────────────────────────────────
	function addMonths(n: number): string {
		const d = new Date(curY, curM - 1 + n, 1);
		return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
	}
	const PRESETS = [
		{ label: '3개월', from: currentMonth, to: addMonths(2) },
		{ label: '6개월', from: currentMonth, to: addMonths(5) },
		{ label: '올해', from: `${curY}-01`, to: `${curY}-12` },
		{ label: '내년', from: `${curY + 1}-01`, to: `${curY + 1}-12` },
		{ label: '전체', from: `${curY}-01`, to: '' }
	];
	function presetActive(p: { from: string; to: string }): boolean {
		return p.from === monthFrom && p.to === (monthTo ?? '');
	}

	function genMonths(): { value: string; label: string }[] {
		const out: { value: string; label: string }[] = [];
		for (let y = curY; y <= curY + 1; y++) {
			for (let m = 1; m <= 12; m++) {
				const ym = `${y}-${String(m).padStart(2, '0')}`;
				out.push({ value: ym, label: `${y}.${String(m).padStart(2, '0')}` });
			}
		}
		return out;
	}
	const monthOptions = genMonths();
	const monthToOptions = [{ value: '', label: '제한 없음' }, ...monthOptions];

	function fmtMonth(ym: string): string {
		const [y, m] = ym.split('-');
		return `${y}.${m}`;
	}
	function monthRangeLabel(): string {
		const f = monthFrom !== currentMonth ? fmtMonth(monthFrom) : '';
		const t = monthTo ? fmtMonth(monthTo) : '';
		if (f && t) return `${f} ~ ${t}`;
		if (f) return `${f} ~`;
		if (t) return `~ ${t}`;
		return '전체 기간';
	}

	// ── Label helpers for active chips / dropdown buttons ─────────────────────
	function sportLabel(v: string): string {
		return filters.sports.find((s) => s.value === v)?.label ?? v;
	}
	function statusLabel(v: string): string {
		return STATUSES.find((s) => s.value === v)?.label ?? v;
	}
	function distLabel(v: string): string {
		for (const cats of Object.values(filters.distanceCategories)) {
			const f = cats.find((c) => c.value === v);
			if (f) return f.label;
		}
		return v;
	}

	// ── <details> popover: close when clicking outside ────────────────────────
	function closeOutside(node: HTMLDetailsElement) {
		function onDown(e: Event) {
			if (node.open && !node.contains(e.target as Node)) node.open = false;
		}
		document.addEventListener('pointerdown', onDown, true);
		return {
			destroy() {
				document.removeEventListener('pointerdown', onDown, true);
			}
		};
	}
</script>

<section class="filterbar" aria-label="대회 필터">
	<div class="fb-head">
		<span class="eh-micro"><span class="acc">SEARCH</span> · {title}</span>
		<span class="eh-micro eh-data fb-count">{total.toLocaleString()} RACES</span>
	</div>

	<div class="fb-row">
		<div class="fb-drops">
			<!-- 종목 -->
			<details class="fdrop" use:closeOutside>
				<summary class="fdrop__btn" class:on={sportSel.length > 0}>
					종목{#if sportSel.length}<span class="fdrop__n">{sportSel.length}</span>{/if}
					<svg class="fdrop__chev" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6" /></svg>
				</summary>
				<div class="fdrop__panel">
					<div class="fdrop__chips">
						{#each filters.sports as s (s.value)}
							<FilterChip
								selected={sportSel.includes(s.value)}
								dotColor={SPORT_META[appSportToDs[s.value]].color}
								onclick={() => apply({ sport: toggle(sportSel, s.value) })}
							>{s.label}</FilterChip>
						{/each}
					</div>
				</div>
			</details>

			<!-- 지역 -->
			<details class="fdrop" use:closeOutside>
				<summary class="fdrop__btn" class:on={regionSel.length > 0}>
					지역{#if regionSel.length}<span class="fdrop__n">{regionSel.length}</span>{/if}
					<svg class="fdrop__chev" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6" /></svg>
				</summary>
				<div class="fdrop__panel fdrop__panel--wide">
					<div class="fdrop__chips">
						{#each filters.regions as r (r)}
							<FilterChip
								selected={regionSel.includes(r)}
								onclick={() => apply({ region: toggle(regionSel, r) })}
							>{r}</FilterChip>
						{/each}
					</div>
				</div>
			</details>

			<!-- 상태 -->
			<details class="fdrop" use:closeOutside>
				<summary class="fdrop__btn" class:on={statusSel.length > 0}>
					상태{#if statusSel.length}<span class="fdrop__n">{statusSel.length}</span>{/if}
					<svg class="fdrop__chev" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6" /></svg>
				</summary>
				<div class="fdrop__panel">
					<div class="fdrop__chips">
						{#each STATUSES as s (s.value)}
							<FilterChip
								selected={statusSel.includes(s.value)}
								onclick={() => apply({ status: toggle(statusSel, s.value) })}
							>{s.label}</FilterChip>
						{/each}
					</div>
				</div>
			</details>

			<!-- 거리 (종목 1개 선택 시) -->
			<details class="fdrop" use:closeOutside>
				<summary class="fdrop__btn" class:on={distSel.length > 0} class:disabled={availableDist.length === 0}>
					거리{#if distSel.length}<span class="fdrop__n">{distSel.length}</span>{/if}
					<svg class="fdrop__chev" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6" /></svg>
				</summary>
				<div class="fdrop__panel">
					{#if availableDist.length === 0}
						<p class="fdrop__hint">종목을 하나만 선택하면 거리로 좁힐 수 있습니다.</p>
					{:else}
						<div class="fdrop__chips">
							{#each availableDist as c (c.value)}
								<FilterChip
									selected={distSel.includes(c.value)}
									onclick={() => apply({ distance_category: toggle(distSel, c.value) })}
								>{c.label}</FilterChip>
							{/each}
						</div>
					{/if}
				</div>
			</details>

			<!-- 개최월 -->
			<details class="fdrop" use:closeOutside>
				<summary class="fdrop__btn" class:on={monthActive}>
					개최월
					<svg class="fdrop__chev" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6" /></svg>
				</summary>
				<div class="fdrop__panel fdrop__panel--wide">
					<div class="fdrop__chips">
						{#each PRESETS as p (p.label)}
							<FilterChip selected={presetActive(p)} onclick={() => apply({ month_from: p.from, month_to: p.to || null })}>{p.label}</FilterChip>
						{/each}
					</div>
					<div class="fdrop__range">
						<Select
							label="시작"
							options={monthOptions}
							value={monthFrom}
							onchange={(e) => apply({ month_from: (e.target as HTMLSelectElement).value })}
						/>
						<span class="fdrop__tilde">~</span>
						<Select
							label="종료"
							options={monthToOptions}
							value={monthTo ?? ''}
							onchange={(e) => apply({ month_to: (e.target as HTMLSelectElement).value || null })}
						/>
					</div>
				</div>
			</details>
		</div>

		<form class="fb-search" onsubmit={submitName} role="search">
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg>
			<input type="search" bind:value={nameDraft} placeholder="대회명 검색" aria-label="대회명 검색" />
		</form>
	</div>

	{#if activeCount > 0}
		<div class="fb-active">
			{#each sportSel as v (v)}
				<button type="button" class="achip" onclick={() => apply({ sport: toggle(sportSel, v) })}>{sportLabel(v)}<span class="x">×</span></button>
			{/each}
			{#each regionSel as v (v)}
				<button type="button" class="achip" onclick={() => apply({ region: toggle(regionSel, v) })}>{v}<span class="x">×</span></button>
			{/each}
			{#each statusSel as v (v)}
				<button type="button" class="achip" onclick={() => apply({ status: toggle(statusSel, v) })}>{statusLabel(v)}<span class="x">×</span></button>
			{/each}
			{#each distSel as v (v)}
				<button type="button" class="achip" onclick={() => apply({ distance_category: toggle(distSel, v) })}>{distLabel(v)}<span class="x">×</span></button>
			{/each}
			{#if monthActive}
				<button type="button" class="achip" onclick={() => apply({ month_from: currentMonth, month_to: null })}>{monthRangeLabel()}<span class="x">×</span></button>
			{/if}
			{#if applied.name}
				<button type="button" class="achip" onclick={() => apply({ name: '' })}>“{applied.name}”<span class="x">×</span></button>
			{/if}
			<button type="button" class="fb-clear" onclick={resetAll}>모두 지우기 ↺</button>
		</div>
	{/if}
</section>

<style>
	.filterbar {
		margin-bottom: var(--sp-5);
	}

	/* ── Head ─────────────────────────────────────────────────────────────── */
	.fb-head {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 12px;
		border-top: var(--border-rule);
		padding-top: 12px;
		margin-bottom: 14px;
	}
	.fb-head .acc {
		color: var(--accent);
		font-weight: 700;
	}
	.fb-count {
		color: var(--text-faint);
		white-space: nowrap;
	}

	/* ── Filter row ───────────────────────────────────────────────────────── */
	.fb-row {
		display: flex;
		align-items: center;
		gap: var(--sp-4);
		flex-wrap: wrap;
		padding-bottom: 14px;
		border-bottom: var(--border-hair);
	}
	.fb-drops {
		display: flex;
		gap: 6px;
		flex-wrap: wrap;
		min-width: 0;
	}

	/* dropdown */
	.fdrop {
		position: relative;
	}
	.fdrop__btn {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		height: 34px;
		padding: 0 12px;
		border: 1px solid var(--line);
		background: var(--paper-0);
		color: var(--text-body);
		font-family: var(--font-sans);
		font-size: 13px;
		font-weight: 600;
		cursor: pointer;
		user-select: none;
		list-style: none;
		white-space: nowrap;
		transition: border-color var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
	}
	.fdrop__btn::-webkit-details-marker {
		display: none;
	}
	.fdrop__btn:hover {
		border-color: var(--ink-900);
		color: var(--text-strong);
	}
	.fdrop__btn.on {
		border-color: var(--ink-900);
		color: var(--text-strong);
	}
	.fdrop__btn.disabled {
		color: var(--text-faint);
	}
	.fdrop[open] .fdrop__chev {
		transform: rotate(180deg);
	}
	.fdrop__chev {
		color: var(--ink-500);
		transition: transform var(--dur-fast) var(--ease-out);
	}
	.fdrop__n {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 16px;
		height: 16px;
		padding: 0 4px;
		background: var(--accent);
		color: var(--paper-0);
		font-size: 11px;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}

	.fdrop__panel {
		position: absolute;
		z-index: 30;
		top: calc(100% + 4px);
		left: 0;
		width: max-content;
		max-width: min(320px, 86vw);
		padding: 14px;
		background: var(--surface-card);
		border: 1px solid var(--ink-900);
		box-shadow: 4px 4px 0 0 rgba(16, 19, 18, 0.08);
	}
	.fdrop__panel--wide {
		max-width: min(420px, 90vw);
	}
	.fdrop__chips {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
	}
	.fdrop__hint {
		margin: 0;
		font-size: 12px;
		color: var(--text-muted);
		line-height: 1.5;
	}
	.fdrop__range {
		display: flex;
		align-items: flex-end;
		gap: 8px;
		margin-top: 12px;
		padding-top: 12px;
		border-top: 1px solid var(--line);
	}
	.fdrop__range :global(.eh-select-wrap) {
		flex: 1;
		min-width: 0;
	}
	.fdrop__tilde {
		padding-bottom: 8px;
		color: var(--text-faint);
	}

	/* ── Name search ──────────────────────────────────────────────────────── */
	.fb-search {
		display: flex;
		align-items: center;
		gap: 8px;
		height: 34px;
		padding: 0 12px;
		margin-left: auto;
		border: 1px solid var(--line);
		background: var(--paper-0);
		color: var(--ink-500);
		min-width: 0;
	}
	.fb-search:focus-within {
		border-color: var(--ink-900);
	}
	.fb-search input {
		border: 0;
		background: transparent;
		outline: none;
		font-family: var(--font-sans);
		font-size: 13px;
		color: var(--text-strong);
		width: 160px;
		min-width: 0;
	}
	.fb-search input::placeholder {
		color: var(--text-faint);
	}

	/* ── Active chips ─────────────────────────────────────────────────────── */
	.fb-active {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 6px;
		padding-top: 14px;
	}
	.achip {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		height: 28px;
		padding: 0 8px 0 10px;
		border: 1px solid var(--ink-900);
		background: var(--ink-900);
		color: var(--paper-0);
		font-family: var(--font-sans);
		font-size: 12px;
		font-weight: 600;
		cursor: pointer;
	}
	.achip:hover {
		background: var(--ink-700);
		border-color: var(--ink-700);
	}
	.achip .x {
		font-size: 15px;
		line-height: 1;
		opacity: 0.7;
		transform: translateY(-1px);
	}
	.achip:hover .x {
		opacity: 1;
	}
	.fb-clear {
		margin-left: auto;
		background: transparent;
		border: 0;
		padding: 4px 0;
		font-family: var(--font-sans);
		font-size: 12px;
		font-weight: 600;
		color: var(--text-muted);
		cursor: pointer;
	}
	.fb-clear:hover {
		color: var(--accent-strong);
	}

	@media (max-width: 768px) {
		.fb-search {
			margin-left: 0;
			flex: 1;
		}
		.fb-search input {
			width: 100%;
		}
		.fb-clear {
			margin-left: 0;
		}
	}
</style>
