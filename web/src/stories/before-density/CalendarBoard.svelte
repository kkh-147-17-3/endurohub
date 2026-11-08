<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { calendarFilterParams, matchesCalendarFilters, readCalendarFilters, type CalendarFilters, type CalendarView } from '$lib/calendar-filters';
	import { kstTodayStr } from '$lib/date';
	import type { Race, Sport, SportOption } from '$lib/types';
	import CalendarRaceList from '$lib/components/calendar/CalendarRaceList.svelte';
	import CalendarDiscovery from '$lib/components/calendar/CalendarDiscovery.svelte';
	import StatBlock from '$lib/components/eh/StatBlock.svelte';
	import IconButton from '$lib/components/eh/IconButton.svelte';
	import FilterChip from '$lib/components/eh/FilterChip.svelte';
	import { dsSport, SPORT_META } from '$lib/components/eh/meta';
	import RegionCartogram from '$lib/components/calendar/RegionCartogram.svelte';

	let {
		year,
		month,
		startOfMonth,
		racesGrouped,
		previousMonth,
		nextMonth,
		sports,
		regions = [],
		showDiscovery = false,
		basePath = '/',
		initialView = 'cal'
	}: {
		year: number;
		month: number;
		startOfMonth: string;
		racesGrouped: Record<string, Race[]>;
		previousMonth: { year: number; month: number } | null;
		nextMonth: { year: number; month: number } | null;
		sports: SportOption[];
		regions?: string[];
		showDiscovery?: boolean;
		basePath?: string;
		initialView?: CalendarView;
	} = $props();

	// ── Calendar geometry ──────────────────────────────────────────
	const firstDayOfMonth = $derived(new Date(startOfMonth).getDay()); // 0 = Sun
	const daysInMonth = $derived(new Date(year, month, 0).getDate());
	const prevDaysInMonth = $derived(new Date(year, month - 1, 0).getDate());
	const todayStr = $derived(kstTodayStr());
	const todayDay = $derived(
		((): number | null => {
			const p = todayStr.split('-');
			if (Number(p[0]) === year && Number(p[1]) === month) return Number(p[2]);
			return null;
		})()
	);

	const DOW_EN = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
	const DOW_KO = ['일', '월', '화', '수', '목', '금', '토'];
	function dowKo(day: number): string {
		return DOW_KO[new Date(year, month - 1, day).getDay()];
	}

	const MAX_PER_CELL = 4;

	// month cells incl. leading/trailing out-of-month days (prototype `.cell.out`)
	type Cell = { out: boolean; d: number };
	const weeks = $derived(
		((): Cell[][] => {
			const cells: Cell[] = [];
			for (let i = 0; i < firstDayOfMonth; i++)
				cells.push({ out: true, d: prevDaysInMonth - firstDayOfMonth + 1 + i });
			for (let d = 1; d <= daysInMonth; d++) cells.push({ out: false, d });
			let nx = 1;
			while (cells.length % 7 !== 0) cells.push({ out: true, d: nx++ });
			const w: Cell[][] = [];
			for (let i = 0; i < cells.length; i += 7) w.push(cells.slice(i, i + 7));
			return w;
		})()
	);

	// ── Races ──────────────────────────────────────────────────────
	const allRaces = $derived(Object.values(racesGrouped).flat());

	const allRacesByDay = $derived(
		((): Record<number, Race[]> => {
			const out: Record<number, Race[]> = {};
			for (const [dateStr, list] of Object.entries(racesGrouped)) {
				const d = Number(dateStr.split('-')[2]);
				if (!isNaN(d)) out[d] = (out[d] ?? []).concat(list);
			}
			return out;
		})()
	);

	function dayOf(r: Race): number {
		return Number((r.raceDate ?? '').split('-')[2]) || 0;
	}

	// URL-backed discovery controls survive reloads, sharing and month changes.
	const sportValues = $derived(sports.map((s) => s.value));
	const filters = $derived(readCalendarFilters(page.url.searchParams, sportValues, initialView));
	const selected = $derived(filters.sports);
	const view = $derived(filters.view);
	const hasFilters = $derived(!!filters.name || filters.regions.length > 0 || filters.openOnly || selected.length > 0);

	function applyFilters(changes: Partial<CalendarFilters>) {
		selDay = null;
		const params = calendarFilterParams(page.url.searchParams, { ...filters, ...changes });
		goto(`${basePath}${params.size ? `?${params}` : ''}`, { noScroll: true, keepFocus: true });
	}

	function toggleSport(v: string) {
		const sports = selected.includes(v) ? selected.filter((sport) => sport !== v) : [...selected, v];
		applyFilters({ sports: sports.length === sportValues.length ? [] : sports });
	}

	const sportCounts = $derived(
		((): Record<string, number> => {
			const c: Record<string, number> = {};
			for (const r of allRaces) c[r.sport] = (c[r.sport] ?? 0) + 1;
			return c;
		})()
	);

	function inFilter(r: Race): boolean {
		return matchesCalendarFilters(r, filters);
	}
	const filteredRaces = $derived(allRaces.filter(inFilter));
	const showSport = $derived(selected.length !== 1);
	function dayRaces(day: number): Race[] {
		return (allRacesByDay[day] ?? []).filter(inFilter);
	}

	function daySports(races: Race[]): { label: string; shortLabel: string; count: number }[] {
		const counts = new Map<Sport, number>();
		for (const race of races) counts.set(race.sport, (counts.get(race.sport) ?? 0) + 1);
		return [...counts].map(([sport, count]) => {
			const label = SPORT_META[dsSport(sport)].ko;
			return { label, shortLabel: sport === 'triathlon' ? '철인' : label, count };
		});
	}

	function dayStatusSummary(races: Race[]): string {
		const counts = new Map<string, number>();
		for (const race of races) counts.set(race.statusLabel, (counts.get(race.statusLabel) ?? 0) + 1);
		return [...counts].map(([label, count]) => `${label} ${count}개`).join(', ');
	}

	// Prototype chip order + labels (run → trail → cycle → swim → tri),
	// shown regardless of the API's own label/order, filtered to supported sports.
	const SPORT_CHIPS = [
		{ value: 'running', label: '러닝' },
		{ value: 'trail_running', label: '트레일' },
		{ value: 'cycling', label: '사이클' },
		{ value: 'swimming', label: '수영' },
		{ value: 'triathlon', label: '철인3종' }
	];
	const sportChips = $derived(SPORT_CHIPS.filter((c) => sportValues.includes(c.value as Sport)));

	// ── Header stats (reflect the active sport filter) ─────────────
	const openCount = $derived(filteredRaces.filter((r) => r.status === 'registration_open').length);
	const todayCount = $derived(todayDay != null ? dayRaces(todayDay).filter((race) => race.status !== 'cancelled').length : 0);

	// ── Per-race helpers ───────────────────────────────────────────
	function ddayOf(r: Race): number | null {
		return r.status === 'cancelled' ? null : r.daysUntilRegistrationEnd ?? null;
	}
	function isOpen(r: Race): boolean {
		return r.status === 'registration_open';
	}
	function isClosedish(r: Race): boolean {
		return r.status === 'cancelled' || r.status === 'finished' || r.status === 'registration_closed';
	}
	function isToday(r: Race): boolean {
		return todayDay != null && dayOf(r) === todayDay;
	}

	// ── View + selection state ─────────────────────────────────────
	let selDay = $state<number | null>(null);
	let dayTrigger: HTMLElement | null = null;

	function openDay(day: number, trigger: HTMLElement) {
		if (dayRaces(day).length === 0) return;
		dayTrigger = trigger;
		selDay = day;
	}
	function closeDay() {
		selDay = null;
	}

	// Native modal dialogs keep keyboard focus inside and make the page inert.
	// The action also cleans up when filtering or navigation removes the dialog.
	function dayDialog(node: HTMLDialogElement) {
		const trigger = dayTrigger;
		const previousOverflow = document.body.style.overflow;
		function keepFocusInside(event: KeyboardEvent) {
			if (event.key !== 'Tab' || event.ctrlKey || event.metaKey || event.altKey || !node.open) return;
			const controls = [...node.querySelectorAll<HTMLElement>('a[href], button, input, select, textarea, [tabindex]')]
				.filter((element) => element.tabIndex >= 0 && !element.matches(':disabled') && element.getClientRects().length > 0);
			const first = controls[0];
			const last = controls.at(-1);
			if (!first || !last) return;
			const active = document.activeElement;
			if (!node.contains(active) || active === node) {
				event.preventDefault();
				first.focus();
			} else if (event.shiftKey && active === first) {
				event.preventDefault();
				last.focus();
			} else if (!event.shiftKey && active === last) {
				event.preventDefault();
				first.focus();
			}
		}
		document.body.style.overflow = 'hidden';
		node.showModal();
		node.querySelector<HTMLButtonElement>('.day-close')?.focus({ preventScroll: true });
		document.addEventListener('keydown', keepFocusInside, true);
		return {
			destroy() {
				document.removeEventListener('keydown', keepFocusInside, true);
				if (node.open) node.close();
				document.body.style.overflow = previousOverflow;
				if (trigger?.isConnected && !trigger.matches(':disabled')) {
					trigger.focus({ preventScroll: true });
				}
				dayTrigger = null;
			}
		};
	}
	$effect(() => {
		if (selDay !== null && (view !== 'cal' || dayRaces(selDay).length === 0)) closeDay();
	});

	// ── Month nav ──────────────────────────────────────────────────
	function buildMonthUrl(y: number, m: number): string {
		const p = calendarFilterParams(page.url.searchParams, filters);
		p.set('year', String(y));
		p.set('month', String(m));
		return `${basePath}?${p.toString()}`;
	}
	const prevHref = $derived(
		previousMonth ? buildMonthUrl(previousMonth.year, previousMonth.month) : null
	);
	const nextHref = $derived(
		nextMonth ? buildMonthUrl(nextMonth.year, nextMonth.month) : null
	);

	// ── List ordering (date, then today → open → other) ────────────
	const listRaces = $derived(
		[...filteredRaces].sort((a, b) => {
			const rank = (r: Race) => (isToday(r) ? 0 : isOpen(r) ? 1 : 2);
			return dayOf(a) - dayOf(b) || rank(a) - rank(b);
		})
	);


	// ── Mobile (agenda swaps in for the calendar grid) ─────────────
	let isMobile = $state(false);
	onMount(() => {
		const mq = window.matchMedia('(max-width: 768px)');
		const apply = () => (isMobile = mq.matches);
		apply();
		mq.addEventListener('change', apply);
		return () => mq.removeEventListener('change', apply);
	});

</script>

{#snippet listTable(rows: Race[], noHead: boolean)}
	<CalendarRaceList {rows} {noHead} {showSport} showRegistrationStatus={!filters.openOnly} />
{/snippet}

<div class="v-container cal-page" class:with-discovery={showDiscovery} data-screen-label="홈 · 캘린더">
	{#if showDiscovery}<CalendarDiscovery {month} {filters} {regions} onapply={applyFilters} />{/if}
	<!-- ═══ page header ═══════════════════════════════════════════ -->
	<div class="hd">
		<div class="eh-micro">전국 5종목</div>
		<div class="hd-month">
			<h1 class="eh-data">{month}월</h1>
			<span class="yr eh-data">{year}</span>
			<div class="hd-nav" data-sveltekit-noscroll>
				{#if prevHref}
					<IconButton label="이전 달" variant="outline" href={prevHref}>
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6" /></svg>
					</IconButton>
				{/if}
				{#if nextHref}
					<IconButton label="다음 달" variant="outline" href={nextHref}>
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6" /></svg>
					</IconButton>
				{/if}
			</div>
		</div>
		<div class="hd-stats">
			<StatBlock label="대회" value={filteredRaces.length} size="md" />
			<button class="open-stat" type="button" aria-label={`접수 중 대회 ${openCount}개${filters.openOnly ? ', 필터 해제' : '만 보기'}`} aria-pressed={filters.openOnly} onclick={() => applyFilters({ openOnly: !filters.openOnly })}>
				<StatBlock label="접수 중" value={openCount} size="md" accent />
			</button>
			<StatBlock label="오늘 개최" value={todayCount} size="md" />
		</div>
	</div>

	<!-- ═══ toolbar (segmented view switch + sport chips) ═════════ -->
	<div class="toolbar">
		<div class="views" role="group" aria-label="대회 보기 방식">
			<button aria-pressed={view === 'cal'} class:on={view === 'cal'} onclick={() => applyFilters({ view: 'cal' })}>캘린더</button>
			<button aria-pressed={view === 'list'} class:on={view === 'list'} onclick={() => applyFilters({ view: 'list' })}>리스트</button>
			<button aria-pressed={view === 'map'} class:on={view === 'map'} onclick={() => applyFilters({ view: 'map' })}>지도</button>
		</div>
		<div class="chips-row">
			<FilterChip selected={selected.length === 0} onclick={() => applyFilters({ sports: [] })}>전체 종목</FilterChip>
			{#each sportChips as s (s.value)}
				<FilterChip
					selected={selected.includes(s.value)}
					count={sportCounts[s.value] ?? 0}
					onclick={() => toggleSport(s.value)}>{s.label}</FilterChip
				>
			{/each}
		</div>
	</div>
	{#if hasFilters && !showDiscovery}
		<div class="filter-summary">
			{#if filters.name || filters.regions.length}
				<p class="applied-filters" role="status">
					{#if filters.name}<span>대회명 “{filters.name}”</span>{/if}
					{#if filters.regions.length}<span>지역 {filters.regions.join(', ')}</span>{/if}
				</p>
			{/if}
			<button type="button" onclick={() => applyFilters({ name: '', regions: [], sports: [], openOnly: false })}>조건 초기화</button>
		</div>
	{/if}
	{#if filteredRaces.length === 0}
		<div class="empty-state">
			<p>{hasFilters ? '선택한 조건에 맞는 대회가 없습니다.' : '이 달에 등록된 대회가 없습니다.'}</p>
			{#if hasFilters}<button type="button" onclick={() => applyFilters({ name: '', regions: [], sports: [], openOnly: false })}>조건 초기화하고 다시 보기</button>{/if}
		</div>
	{/if}

	<!-- ═══ CALENDAR (desktop) / AGENDA (mobile) ═════════════════ -->
	{#if view === 'cal'}
		{#if isMobile}
			<!-- mobile: mini month grid → opens day modal on tap -->
			<div class="mcal">
				<div class="mcal-dow">
					{#each DOW_KO as d}<span>{d}</span>{/each}
				</div>
				{#each weeks as week, wi (wi)}
					<div class="mcal-week">
						{#each week as c, ci (ci)}
							{@const evs = c.out ? [] : dayRaces(c.d)}
							{@const dayOpenCount = evs.filter(isOpen).length}
							{@const wknd = ci === 0 || ci === 6}
							<button
								type="button"
								class="mcell"
								class:out={c.out}
								class:wknd={wknd && !c.out}
								class:today={!c.out && c.d === todayDay}
								class:sel={!c.out && evs.length > 0 && c.d === selDay}
								disabled={c.out || evs.length === 0}
								aria-label={evs.length > 0 ? `${month}월 ${c.d}일 대회 ${evs.length}개, ${daySports(evs).map((sport) => `${sport.label} ${sport.count}개`).join(', ')}, ${dayStatusSummary(evs)}` : undefined}
								aria-haspopup="dialog"
								onclick={(e) => !c.out && openDay(c.d, e.currentTarget)}
							>
								<span class="n eh-data">{c.d}</span>
								{#if evs.length > 0}
									<span class="day-sports" aria-hidden="true">
										{#if showSport}
											{#each daySports(evs) as sport (sport.label)}
												<span>{sport.shortLabel} <b class="eh-data">{sport.count}</b></span>
											{/each}
										{:else}
											<span class="eh-data">{evs.length}개</span>
										{/if}
										{#if dayOpenCount > 0 && dayOpenCount < evs.length}
											<span class="day-open">접수 <b class="eh-data">{dayOpenCount}</b></span>
										{/if}
									</span>
								{/if}
							</button>
						{/each}
					</div>
				{/each}
			</div>

		{:else}
			<div class="cal">
				<div class="cal-dow">
					{#each DOW_EN as d}<span>{d}</span>{/each}
				</div>
				{#each weeks as week, wi (wi)}
					<div class="cal-week">
						{#each week as c, ci (ci)}
							{@const evs = c.out ? [] : dayRaces(c.d)}
							{@const wknd = ci === 0 || ci === 6}
							<div
								class="cell"
								class:out={c.out}
								class:wknd={wknd && !c.out}
								class:emph={wknd && !c.out}
								class:has={evs.length > 0}
								class:sel={selDay === c.d && !c.out}
							>
								{#if evs.length > 0}
									<button
										type="button"
										class="cell-open d-num eh-data"
										aria-label={`${month}월 ${c.d}일 대회 ${evs.length}개 보기`}
										aria-haspopup="dialog"
										onclick={(e) => openDay(c.d, e.currentTarget)}
									>
										{c.d}
										{#if c.d === todayDay}<span class="today-pin">TODAY</span>{/if}
									</button>
								{:else}
									<span class="d-num eh-data">
										{c.d}
										{#if !c.out && c.d === todayDay}<span class="today-pin">TODAY</span>{/if}
									</span>
								{/if}
								{#each evs.slice(0, MAX_PER_CELL) as r (r.id)}
									<a class="ev" class:dim={isClosedish(r)} href={`/races/${encodeURIComponent(r.slug)}`}>
										{#if showSport}<span class="ev-sport">{SPORT_META[dsSport(r.sport)].ko}</span>{/if}
										<span class="nm">{r.title}</span>
										{#if r.status === 'cancelled'}
											<span class="dd" style="color:var(--danger)">취소</span>
										{:else if isToday(r) && !isClosedish(r)}
											<span class="dd" style="color:var(--ink-900)">오늘</span>
										{:else if isOpen(r) && ddayOf(r) != null && ddayOf(r)! >= 0}
											<span class="dd eh-data">D-{ddayOf(r)}</span>
										{/if}
									</a>
								{/each}
								{#if evs.length > MAX_PER_CELL}
									<button
										type="button"
										class="more eh-data"
										aria-label={`${month}월 ${c.d}일 대회 ${evs.length}개 모두 보기`}
										aria-haspopup="dialog"
										onclick={(e) => openDay(c.d, e.currentTarget)}
									>
										+{evs.length - MAX_PER_CELL} 더보기
									</button>
								{/if}
							</div>
						{/each}
					</div>
				{/each}
			</div>
		{/if}

		{#if listRaces.length > 0}
			<!-- Native disclosure keeps every race link in the server HTML, including
			     busy days and the compact mobile calendar, without requiring a click to fetch it. -->
			<details class="month-list">
				<summary>{month}월 전체 대회 목록 <span class="eh-data">{listRaces.length}개</span></summary>
				{@render listTable(listRaces, false)}
			</details>
		{/if}

		<!-- day modal -->
		{#if selDay !== null && dayRaces(selDay).length > 0}
			{@const rows = dayRaces(selDay)}
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<dialog
				class="v-scrim"
				use:dayDialog
				aria-modal="true"
				aria-label={`${month}월 ${selDay}일 대회`}
				oncancel={(e) => { e.preventDefault(); closeDay(); }}
				onclick={(e) => { if (e.target === e.currentTarget) closeDay(); }}
			>
				<div class="v-modal day-modal">
					<div class="daypanel-head">
						<b class="eh-data">{month}.{String(selDay).padStart(2, '0')}</b>
						<span class="eh-micro">{dowKo(selDay)}요일</span>
						<span class="eh-micro">{rows.length}개 대회</span>
						<button type="button" class="day-close" onclick={closeDay}>닫기 ×</button>
					</div>
					<div class="day-scroll">
						{@render listTable(rows, true)}
					</div>
				</div>
			</dialog>
		{/if}
	{/if}

	<!-- ═══ LIST ═════════════════════════════════════════════════ -->
	{#if view === 'list'}
		{#if listRaces.length > 0}
			{@render listTable(listRaces, false)}
		{/if}
	{/if}

	<!-- ═══ MAP (tile cartogram) ═════════════════════════════════ -->
	{#if view === 'map'}
		<div style="margin-top: var(--sp-6);">
			<RegionCartogram races={filteredRaces} {month} {showSport} />
		</div>
	{/if}
</div>

<style>
	.cal-page {
		padding-top: var(--sp-2);
		padding-bottom: var(--sp-20);
	}

	/* ── page header ── */
	.hd {
		padding: 40px 0 0;
	}
	.with-discovery .hd { padding-top: var(--sp-5); }
	.with-discovery .hd-month h1 { font-size: clamp(38px, 4.5vw, 56px); }
	.with-discovery .hd-stats { margin-top: var(--sp-3); }
	.open-stat { border: 0; padding: 0; background: transparent; text-align: left; cursor: pointer; }
	.open-stat:hover { text-decoration: underline; text-underline-offset: 4px; }
	.open-stat:focus-visible, .views button:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
	.filter-summary { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: var(--sp-2); padding: 12px 0; font-size: var(--text-caption); color: var(--text-muted); }
	.applied-filters { display: flex; flex-wrap: wrap; gap: 6px 16px; margin: 0; }
	.filter-summary button, .empty-state button { min-height: 40px; padding: 4px 8px; background: transparent; border: 1px solid var(--line); color: var(--text-accent); font: inherit; cursor: pointer; }
	.hd-month {
		display: flex;
		align-items: baseline;
		gap: 18px;
		flex-wrap: wrap;
		margin-top: 10px;
	}
	.hd-month h1 {
		font-size: clamp(44px, 6vw, 72px);
		font-weight: var(--w-display);
		letter-spacing: var(--track-display);
		line-height: var(--leading-display);
		color: var(--text-strong);
		white-space: nowrap;
		margin: 0;
	}
	.hd-month .yr {
		font-size: var(--text-h3);
		font-weight: 600;
		color: var(--text-faint);
		letter-spacing: 0.02em;
	}
	.hd-nav {
		display: flex;
		gap: 2px;
		margin-left: auto;
	}
	.hd-stats {
		display: flex;
		gap: 36px;
		margin-top: 20px;
		flex-wrap: wrap;
	}

	/* ── toolbar ── */
	.toolbar {
		display: flex;
		align-items: center;
		gap: var(--sp-4);
		margin-top: 26px;
		padding: 14px 0;
		border-top: var(--border-rule);
		border-bottom: var(--border-hair);
		flex-wrap: wrap;
	}
	.views {
		display: flex;
		border: 1px solid var(--line);
		border-radius: var(--r-1);
		overflow: hidden;
	}
	.views button {
		padding: 8px 18px;
		border: 0;
		background: var(--paper-0);
		font-family: var(--font-sans);
		font-size: 13px;
		font-weight: 600;
		color: var(--text-muted);
		border-right: 1px solid var(--line);
		white-space: nowrap;
		transition:
			background var(--dur-fast) var(--ease-out),
			color var(--dur-fast) var(--ease-out);
	}
	.views button:last-child {
		border-right: 0;
	}
	.views button.on {
		background: var(--ink-900);
		color: var(--paper-0);
	}
	.chips-row {
		display: flex;
		gap: 6px;
		flex-wrap: nowrap;
		flex: 1 1 auto;
		min-width: 0;
		overflow-x: auto;
		scrollbar-width: none;
		-webkit-overflow-scrolling: touch;
	}
	.chips-row::-webkit-scrollbar {
		display: none;
	}
	.chips-row :global(.eh-chip) {
		flex: 0 0 auto;
	}

	/* ── calendar grid ── */
	.cal {
		border: 1px solid var(--line);
		border-top: 0;
		background: var(--paper-0);
		margin-top: 0;
	}
	.cal-dow {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
		border-bottom: var(--border-rule);
	}
	.cal-dow span {
		padding: 9px 10px;
		font-size: var(--text-micro);
		font-weight: var(--w-strong);
		letter-spacing: var(--track-micro);
		color: var(--text-muted);
		border-right: 1px solid var(--line);
	}
	.cal-dow span:last-child {
		border-right: 0;
	}
	.cal-dow span:first-child {
		color: var(--danger);
	}
	.cal-week {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
	}
	.cell {
		position: relative;
		min-height: 118px;
		padding: 8px 8px 10px;
		border-right: 1px solid var(--line);
		border-bottom: 1px solid var(--line);
		display: flex;
		flex-direction: column;
		gap: 6px;
		background: var(--paper-0);
		cursor: default;
		min-width: 0;
		text-align: left;
	}
	.cell:last-child {
		border-right: 0;
	}
	.cal-week:last-child .cell {
		border-bottom: 0;
	}
	.cell.out {
		background: var(--paper-50);
	}
	.cell.wknd.emph {
		background: var(--paper-50);
	}
	.cell.has {
		cursor: pointer;
	}
	.cell.has:hover {
		background: var(--accent-tint);
	}
	.cell.sel {
		box-shadow: inset 0 0 0 2px var(--ink-900);
	}
	.cell-open {
		background: none;
		border: 0;
		padding: 0;
		width: fit-content;
		font-family: inherit;
		cursor: pointer;
	}
	.cell-open::after {
		content: '';
		position: absolute;
		inset: 0;
	}
	.cell-open:focus-visible {
		outline: none;
	}
	.cell-open:focus-visible::after {
		outline: 2px solid var(--ink-900);
		outline-offset: -2px;
	}
	.d-num {
		font-size: 13px;
		font-weight: 700;
		color: var(--text-strong);
		display: flex;
		align-items: center;
		gap: 6px;
	}
	.cell.out .d-num {
		color: var(--ink-300);
	}
	.cell:first-child .d-num {
		color: var(--danger);
	}
	.cell.out:first-child .d-num {
		color: var(--ink-300);
	}
	.d-num .today-pin {
		background: var(--accent);
		color: #fff;
		font-size: 9px;
		font-weight: 700;
		letter-spacing: 0.08em;
		padding: 2px 5px;
		border-radius: var(--r-2);
	}
	.ev {
		position: relative;
		z-index: 1;
		display: flex;
		align-items: center;
		gap: 5px;
		font-size: 11.5px;
		line-height: 1.25;
		min-width: 0;
		text-decoration: none;
	}
	.ev:hover .nm {
		text-decoration: underline;
	}
	.ev:focus-visible,
	.more:focus-visible,
	.month-list summary:focus-visible {
		outline: 2px solid var(--ink-900);
		outline-offset: 2px;
	}
	.ev-sport {
		flex: none;
		font-size: 10px;
		color: var(--text-muted);
	}
	.ev .nm {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		font-weight: 500;
		color: var(--text-body);
	}
	.ev.dim .nm {
		color: var(--ink-300);
	}
	.ev .dd {
		font-size: 10px;
		font-weight: 700;
		color: var(--text-accent);
		flex: none;
	}
	.more {
		position: relative;
		z-index: 1;
		align-self: flex-start;
		background: none;
		border: 0;
		padding: 0;
		font-family: inherit;
		cursor: pointer;
		font-size: 10.5px;
		font-weight: 600;
		letter-spacing: 0.06em;
		color: var(--text-faint);
		margin-top: auto;
	}
	.cell.has:hover .more {
		color: var(--text-accent);
	}
	.month-list {
		margin-top: var(--sp-5);
		border: 1px solid var(--line);
		background: var(--paper-0);
	}
	.month-list summary {
		padding: 14px 16px;
		font-size: 13px;
		font-weight: 600;
		cursor: pointer;
	}
	.month-list summary span {
		margin-left: 8px;
		color: var(--text-muted);
	}
	/* ── day modal ── */
	.v-scrim {
		position: fixed;
		inset: 0;
		width: 100%;
		height: 100%;
		max-width: none;
		max-height: none;
		margin: 0;
		border: 0;
		box-sizing: border-box;
		overflow: hidden;
		color: inherit;
		z-index: 200;
		background: rgba(16, 19, 18, 0.45);
		display: grid;
		place-items: center;
		padding: var(--sp-5);
		animation: v-fade var(--dur-base) var(--ease-out);
	}
	.v-scrim::backdrop { background: transparent; }
	.v-modal {
		background: var(--paper-0);
		border: 1px solid var(--ink-900);
		border-radius: var(--r-0);
		box-shadow: var(--shadow-pop);
		width: 100%;
		position: relative;
		animation: v-rise var(--dur-base) var(--ease-out);
	}
	.day-modal {
		max-width: 860px;
		border-top: var(--border-rule);
	}
	.daypanel-head {
		display: flex;
		align-items: center;
		gap: 14px;
		padding: 18px 20px 12px;
	}
	.daypanel-head b {
		font-size: 22px;
		font-weight: 800;
		color: var(--text-strong);
	}
	.day-close {
		margin-left: auto;
		background: none;
		border: 0;
		padding: 4px 6px;
		font-family: var(--font-sans);
		font-size: 13px;
		font-weight: 600;
		color: var(--text-muted);
		cursor: pointer;
	}
	.day-close:hover {
		color: var(--text-strong);
	}
	.day-close:focus-visible { outline: 2px solid var(--accent-strong); outline-offset: 2px; }
	.day-scroll {
		max-height: min(60vh, 520px);
		overflow-y: auto;
	}
	@keyframes v-fade {
		from {
			opacity: 0;
		}
	}
	@keyframes v-rise {
		from {
			opacity: 0;
			transform: translateY(8px);
		}
	}
	@keyframes v-sheet-up {
		from {
			transform: translateY(100%);
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.v-scrim,
		.v-modal {
			animation: none;
		}
	}

	/* ── mobile: mini month grid ── */
	.mcal {
		border: 1px solid var(--line);
		border-top: 0;
		background: var(--paper-0);
	}
	.mcal-dow {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
		border-bottom: var(--border-rule);
	}
	.mcal-dow span {
		padding: 8px 0;
		text-align: center;
		font-size: 10px;
		font-weight: var(--w-strong);
		letter-spacing: var(--track-micro);
		color: var(--text-muted);
	}
	.mcal-dow span:first-child {
		color: var(--danger);
	}
	.mcal-week {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
	}
	.mcell {
		border: 0;
		border-right: 1px solid var(--line);
		border-bottom: 1px solid var(--line);
		background: var(--paper-0);
		border-radius: 0;
		min-height: 52px;
		padding: 8px 2px 7px;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 5px;
		min-width: 0;
		cursor: pointer;
	}
	.mcell:last-child {
		border-right: 0;
	}
	.mcal-week:last-child .mcell {
		border-bottom: 0;
	}
	.mcell.out,
	.mcell.wknd {
		background: var(--paper-50);
	}
	.mcell:disabled {
		cursor: default;
	}
	.mcell .n {
		font-size: 14px;
		font-weight: 700;
		color: var(--text-strong);
		line-height: 1;
	}
	.mcell:disabled .n {
		color: var(--ink-300);
		font-weight: 500;
	}
	.mcell.today .n {
		color: var(--text-accent);
	}
	.mcell.today .n::after {
		content: '';
		display: block;
		height: 2px;
		background: var(--accent);
		margin-top: 2px;
	}
	.mcell.sel {
		box-shadow: inset 0 0 0 2px var(--ink-900);
	}
	.mcell .day-sports {
		display: flex;
		flex-direction: column;
		gap: 2px;
		align-items: center;
		max-width: 100%;
		font-size: 9px;
		color: var(--text-muted);
		line-height: 1.3;
	}
	.day-sports > span {
		white-space: nowrap;
	}
	.day-sports b {
		font-weight: 700;
	}
	.day-open {
		margin-top: 2px;
		color: var(--text-strong);
	}


	.empty-state {
		padding: var(--sp-12) 0;
		text-align: center;
		color: var(--text-muted);
		font-size: 14px;
	}

	/* ── responsive ── */
	@media (max-width: 768px) {
		.hd {
			padding-top: 22px;
		}
		.hd-stats {
			gap: 22px;
		}

		/* day modal → bottom sheet */
		.v-scrim {
			place-items: end center;
			padding: 0;
		}
		.day-modal {
			max-width: 100%;
			border-left: 0;
			border-right: 0;
			border-bottom: 0;
			border-top: var(--border-rule);
			border-radius: var(--r-3) var(--r-3) 0 0;
			max-height: 85vh;
			display: flex;
			flex-direction: column;
			animation: v-sheet-up var(--dur-base) var(--ease-out);
		}
		/* grabber handle */
		.day-modal::before {
			content: '';
			width: 36px;
			height: 4px;
			border-radius: 999px;
			background: var(--line);
			margin: 8px auto 0;
			flex: none;
		}
		.daypanel-head {
			padding-top: 12px;
		}
		.day-scroll {
			max-height: none;
			flex: 1 1 auto;
			overflow-y: auto;
			overscroll-behavior: contain;
			padding-bottom: env(safe-area-inset-bottom);
		}
	}
</style>
