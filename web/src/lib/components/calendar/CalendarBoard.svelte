<script lang="ts">
	import { onMount } from 'svelte';
	import { kstTodayStr } from '$lib/date';
	import type { Race, Sport, SportOption } from '$lib/types';
	import { arenaDistLabel, arenaMinFee, arenaFeeShort } from '$lib/arena';
	import { dsSport } from '$lib/components/eh/meta';
	import SportTag from '$lib/components/eh/SportTag.svelte';
	import Badge from '$lib/components/eh/Badge.svelte';
	import StatBlock from '$lib/components/eh/StatBlock.svelte';
	import IconButton from '$lib/components/eh/IconButton.svelte';
	import FilterChip from '$lib/components/eh/FilterChip.svelte';
	import RegionCartogram from './RegionCartogram.svelte';

	type ViewId = 'cal' | 'list' | 'map';

	let {
		year,
		month,
		startOfMonth,
		racesGrouped,
		previousMonth,
		nextMonth,
		sports,
		sportFilter = [],
		basePath = '/',
		initialView = 'cal'
	}: {
		year: number;
		month: number;
		startOfMonth: string;
		racesGrouped: Record<string, Race[]>;
		previousMonth: { year: number; month: number };
		nextMonth: { year: number; month: number };
		sports: SportOption[];
		sportFilter?: string[];
		basePath?: string;
		initialView?: ViewId;
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

	// ── Sport multi-select (prototype: all on by default, toggle) ───
	const sportValues = $derived(sports.map((s) => s.value));
	let selectedSports = $state<string[] | null>(null);
	const selected = $derived(selectedSports ?? sportValues);

	function toggleSport(v: string) {
		const cur = selected;
		if (cur.includes(v)) {
			selectedSports = cur.length === 1 ? sportValues : cur.filter((x) => x !== v);
		} else {
			selectedSports = [...cur, v];
		}
	}

	const sportCounts = $derived(
		((): Record<string, number> => {
			const c: Record<string, number> = {};
			for (const r of allRaces) c[r.sport] = (c[r.sport] ?? 0) + 1;
			return c;
		})()
	);

	function inFilter(r: Race): boolean {
		return selected.includes(r.sport);
	}
	const filteredRaces = $derived(allRaces.filter(inFilter));
	function dayRaces(day: number): Race[] {
		return (allRacesByDay[day] ?? []).filter(inFilter);
	}

	const sportDotColor: Record<string, string> = {
		running: 'var(--sport-run)',
		trail_running: 'var(--sport-trail)',
		cycling: 'var(--sport-ride)',
		swimming: 'var(--sport-swim)',
		triathlon: 'var(--sport-tri)'
	};

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
	const todayCount = $derived(todayDay != null ? dayRaces(todayDay).length : 0);

	// ── Per-race helpers ───────────────────────────────────────────
	function ddayOf(r: Race): number | null {
		return r.daysUntilRegistrationEnd ?? null;
	}
	function isOpen(r: Race): boolean {
		return r.status === 'registration_open';
	}
	function isClosedish(r: Race): boolean {
		return r.status === 'finished' || r.status === 'registration_closed';
	}
	function isToday(r: Race): boolean {
		return todayDay != null && dayOf(r) === todayDay;
	}

	// ── View + selection state ─────────────────────────────────────
	let view = $state<ViewId>(initialView);
	let selDay = $state<number | null>(null);

	function openDay(day: number) {
		if (dayRaces(day).length > 0) selDay = selDay === day ? null : day;
	}
	function onKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') selDay = null;
	}

	// Lock background scroll while the day modal / bottom sheet is open.
	$effect(() => {
		if (selDay === null) return;
		const prev = document.body.style.overflow;
		document.body.style.overflow = 'hidden';
		return () => {
			document.body.style.overflow = prev;
		};
	});

	// ── Month nav ──────────────────────────────────────────────────
	function buildMonthUrl(y: number, m: number): string {
		const p = new URLSearchParams();
		p.set('year', String(y));
		p.set('month', String(m));
		for (const s of sportFilter) p.append('sport', s);
		return `${basePath}?${p.toString()}`;
	}
	const prevHref = $derived(buildMonthUrl(previousMonth.year, previousMonth.month));
	const nextHref = $derived(buildMonthUrl(nextMonth.year, nextMonth.month));

	// ── List ordering (date, then today → open → other) ────────────
	const listRaces = $derived(
		[...filteredRaces].sort((a, b) => {
			const rank = (r: Race) => (isToday(r) ? 0 : isOpen(r) ? 1 : 2);
			return dayOf(a) - dayOf(b) || rank(a) - rank(b);
		})
	);

	function feeLabel(r: Race): string {
		const min = arenaMinFee(r);
		return min != null ? arenaFeeShort(min) : '—';
	}
	function dsBadge(r: Race): 'open' | 'closing' | 'live' | 'closed' {
		if (isToday(r) && !isClosedish(r)) return 'live';
		if (isOpen(r)) {
			const d = ddayOf(r);
			return d != null && d >= 0 && d <= 3 ? 'closing' : 'open';
		}
		return 'closed';
	}

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

<svelte:window onkeydown={onKeydown} />

{#snippet listTable(rows: Race[], noHead: boolean)}
	<div class="v-table lv" class:nohead={noHead}>
		{#if !noHead}
			<div class="v-thead">
				<span>DATE</span><span>SPORT</span><span>RACE</span>
				<span class="hide-m">REGION</span><span class="hide-m">DIST</span>
				<span class="hide-m">FEE</span><span>STATUS</span>
			</div>
		{/if}
		{#each rows as r (r.id)}
			{@const d = dayOf(r)}
			<a class="v-trow click" href={`/races/${r.slug}`}>
				<span class="dt eh-data"
					>{month}.{String(d).padStart(2, '0')}<span class="dw">{dowKo(d)}</span></span
				>
				<span class="v-pc"><SportTag sport={dsSport(r.sport)} /></span>
				<span class="nm">{r.title}</span>
				<span class="mut hide-m">{r.region ?? ''}</span>
				<span class="mut hide-m eh-data">{arenaDistLabel(r)}</span>
				<span class="mut hide-m eh-data">{feeLabel(r)}</span>
				<span>
					<Badge status={dsBadge(r)}>
						{#if dsBadge(r) === 'open'}<span class="eh-data"
								>접수 중{#if ddayOf(r) != null && ddayOf(r)! >= 0}
									D-{ddayOf(r)}{/if}</span
							>
						{:else if dsBadge(r) === 'closing'}<span class="eh-data"
								>마감 임박{#if ddayOf(r) != null && ddayOf(r)! >= 0}
									D-{ddayOf(r)}{/if}</span
							>
						{:else if dsBadge(r) === 'live'}오늘 개최
						{:else}접수 마감{/if}
					</Badge>
				</span>
			</a>
		{/each}
	</div>
{/snippet}

<div class="v-container cal-page" data-screen-label="홈 · 캘린더">
	<!-- ═══ page header ═══════════════════════════════════════════ -->
	<div class="hd">
		<div class="eh-micro home-kicker">
			<span class="acc">RACE CALENDAR</span> · {year} · 전국 5종목
		</div>
		<div class="hd-month">
			<h1 class="eh-data">{month}월</h1>
			<span class="yr eh-data">{year}</span>
			<div class="hd-nav">
				<IconButton label="이전 달" variant="outline" href={prevHref}>
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6" /></svg>
				</IconButton>
				<IconButton label="다음 달" variant="outline" href={nextHref}>
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6" /></svg>
				</IconButton>
			</div>
		</div>
		<div class="hd-stats">
			<StatBlock label="대회" value={filteredRaces.length} size="md" />
			<StatBlock label="접수 중" value={openCount} size="md" accent />
			<StatBlock label="오늘 개최" value={todayCount} size="md" />
		</div>
	</div>

	<!-- ═══ toolbar (segmented view switch + sport chips) ═════════ -->
	<div class="toolbar">
		<div class="views" role="tablist">
			<button class:on={view === 'cal'} onclick={() => { view = 'cal'; selDay = null; }}>캘린더</button>
			<button class:on={view === 'list'} onclick={() => { view = 'list'; selDay = null; }}>리스트</button>
			<button class:on={view === 'map'} onclick={() => { view = 'map'; selDay = null; }}>지도</button>
		</div>
		<div class="chips-row">
			{#each sportChips as s (s.value)}
				<FilterChip
					selected={selected.includes(s.value)}
					dotColor={sportDotColor[s.value]}
					count={sportCounts[s.value] ?? 0}
					onclick={() => toggleSport(s.value)}>{s.label}</FilterChip
				>
			{/each}
		</div>
	</div>

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
							{@const wknd = ci === 0 || ci === 6}
							<button
								type="button"
								class="mcell"
								class:out={c.out}
								class:wknd={wknd && !c.out}
								class:today={!c.out && c.d === todayDay}
								class:sel={!c.out && evs.length > 0 && c.d === selDay}
								disabled={c.out || evs.length === 0}
								aria-label={evs.length > 0 ? `${month}월 ${c.d}일 대회 ${evs.length}개` : undefined}
								onclick={() => !c.out && openDay(c.d)}
							>
								<span class="n eh-data">{c.d}</span>
								<span class="dots">
									{#each evs.slice(0, 4) as r (r.id)}
										<span
											class="v-dot"
											style:background={sportDotColor[r.sport]}
											style:opacity={isClosedish(r) ? 0.35 : 1}
										></span>
									{/each}
									{#if evs.length > 4}<span class="more-n eh-data">+{evs.length - 4}</span>{/if}
								</span>
							</button>
						{/each}
					</div>
				{/each}
			</div>

			{#if filteredRaces.length === 0}
				<p class="empty-state">이 달에는 해당하는 대회가 없습니다.</p>
			{/if}
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
							<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
							<div
								class="cell"
								class:out={c.out}
								class:wknd={wknd && !c.out}
								class:emph={wknd && !c.out}
								class:has={evs.length > 0}
								class:sel={selDay === c.d && !c.out}
								role={evs.length > 0 ? 'button' : undefined}
								tabindex={evs.length > 0 ? 0 : undefined}
								aria-label={evs.length > 0 ? `${month}월 ${c.d}일 대회 ${evs.length}개` : undefined}
								onclick={() => !c.out && openDay(c.d)}
								onkeydown={(e) => {
									if (!c.out && evs.length > 0 && (e.key === 'Enter' || e.key === ' ')) {
										e.preventDefault();
										openDay(c.d);
									}
								}}
							>
								<span class="d-num eh-data">
									{c.d}
									{#if !c.out && c.d === todayDay}<span class="today-pin">TODAY</span>{/if}
								</span>
								{#each evs.slice(0, MAX_PER_CELL) as r (r.id)}
									<span class="ev" class:dim={isClosedish(r)}>
										<span class="v-dot" style:background={sportDotColor[r.sport]}></span>
										<span class="nm">{r.title}</span>
										{#if isToday(r) && !isClosedish(r)}
											<span class="dd" style="color:var(--ink-900)">오늘</span>
										{:else if isOpen(r) && ddayOf(r) != null && ddayOf(r)! >= 0}
											<span class="dd eh-data">D-{ddayOf(r)}</span>
										{/if}
									</span>
								{/each}
								{#if evs.length > MAX_PER_CELL}
									<span class="more eh-data">+{evs.length - MAX_PER_CELL} 더보기</span>
								{/if}
							</div>
						{/each}
					</div>
				{/each}
			</div>
		{/if}

		<!-- day modal -->
		{#if selDay !== null && dayRaces(selDay).length > 0}
			{@const rows = dayRaces(selDay)}
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div class="v-scrim" onclick={() => (selDay = null)}>
				<div
					class="v-modal day-modal"
					role="dialog"
					aria-modal="true"
					tabindex="-1"
					aria-label={`${month}월 ${selDay}일 대회`}
					onclick={(e) => e.stopPropagation()}
				>
					<div class="daypanel-head">
						<b class="eh-data">{month}.{String(selDay).padStart(2, '0')}</b>
						<span class="eh-micro">{dowKo(selDay)}요일 · {rows.length}개 대회</span>
						<button type="button" class="day-close" onclick={() => (selDay = null)}>닫기 ×</button>
					</div>
					<div class="day-scroll">
						{@render listTable(rows, true)}
					</div>
				</div>
			</div>
		{/if}
	{/if}

	<!-- ═══ LIST ═════════════════════════════════════════════════ -->
	{#if view === 'list'}
		{#if listRaces.length === 0}
			<p class="empty-state">이 달에는 해당하는 대회가 없습니다.</p>
		{:else}
			{@render listTable(listRaces, false)}
		{/if}
	{/if}

	<!-- ═══ MAP (tile cartogram) ═════════════════════════════════ -->
	{#if view === 'map'}
		<div style="margin-top: var(--sp-6);">
			<RegionCartogram races={filteredRaces} {month} />
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
	.home-kicker .acc {
		color: var(--text-accent);
	}
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
		display: flex;
		align-items: center;
		gap: 5px;
		font-size: 11.5px;
		line-height: 1.25;
		min-width: 0;
	}
	.ev .v-dot {
		width: 6px;
		height: 6px;
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
		font-size: 10.5px;
		font-weight: 600;
		letter-spacing: 0.06em;
		color: var(--text-faint);
		margin-top: auto;
	}
	.cell.has:hover .more {
		color: var(--text-accent);
	}
	.v-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex: none;
		display: inline-block;
	}

	/* ── day modal ── */
	.v-scrim {
		position: fixed;
		inset: 0;
		z-index: 200;
		background: rgba(16, 19, 18, 0.45);
		display: grid;
		place-items: center;
		padding: var(--sp-5);
		animation: v-fade var(--dur-base) var(--ease-out);
	}
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

	/* ── list / table ── */
	.v-table {
		border: 1px solid var(--line);
		background: var(--paper-0);
	}
	.v-table.lv {
		border-top: 0;
	}
	.v-table.nohead {
		border: 0;
	}
	.v-thead {
		display: grid;
		align-items: center;
		padding: 10px 18px;
		border-bottom: var(--border-rule);
		font-size: var(--text-micro);
		font-weight: var(--w-strong);
		letter-spacing: var(--track-micro);
		text-transform: uppercase;
		color: var(--text-muted);
	}
	.v-trow {
		display: grid;
		align-items: center;
		padding: 13px 18px;
		border-bottom: 1px solid var(--line);
		font-size: var(--text-body-sm);
		color: inherit;
		text-decoration: none;
		transition: background var(--dur-fast) var(--ease-out);
	}
	.v-trow:last-child {
		border-bottom: 0;
	}
	.v-trow.click {
		cursor: pointer;
	}
	.v-trow.click:hover {
		background: var(--paper-50);
	}
	.lv .v-thead,
	.lv .v-trow {
		grid-template-columns: 76px 92px 1fr 110px 110px 80px 130px;
		gap: 14px;
	}
	.lv .dt {
		font-weight: 600;
		color: var(--text-strong);
	}
	.lv .dt .dw {
		color: var(--text-faint);
		font-weight: 500;
		margin-left: 4px;
	}
	.lv .nm {
		font-weight: 600;
		color: var(--text-strong);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.lv .mut {
		color: var(--text-muted);
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
	.mcell .dots {
		display: flex;
		gap: 3px;
		justify-content: center;
		align-items: center;
		min-height: 6px;
		flex-wrap: wrap;
		max-width: 100%;
	}
	.mcell .dots .v-dot {
		width: 6px;
		height: 6px;
		flex: none;
	}
	.mcell .more-n {
		font-size: 9px;
		font-weight: 700;
		color: var(--text-faint);
		line-height: 6px;
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
		.lv .v-thead {
			display: none;
		}
		.lv .v-trow {
			grid-template-columns: 60px 1fr auto;
			gap: 10px;
		}
		.lv .hide-m {
			display: none;
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
