<script lang="ts">
	import type { Race, Sport } from '$lib/types';
	import { track } from '$lib/analytics';
	import { arenaDday, arenaDdayLabel, arenaDistLabel } from '$lib/arena';

	let { races, month }: { races: Race[]; month: number } = $props();

	// ── 17 시도 canonical list ────────────────────────────────────────
	type Sido =
		| '서울' | '부산' | '대구' | '인천' | '광주' | '대전' | '울산'
		| '세종' | '경기' | '강원' | '충북' | '충남' | '전북' | '전남'
		| '경북' | '경남' | '제주';

	// ── Tile cartogram (col, row) — clean 4-column grid approximating Korea ─
	//    인천 서울 경기 강원
	//    충남 세종 충북 경북
	//    전북 대전 대구 울산
	//    전남 광주 경남 부산
	//    제주
	const CARTO: [Sido, number, number][] = [
		['인천', 1, 1], ['서울', 2, 1], ['경기', 3, 1], ['강원', 4, 1],
		['충남', 1, 2], ['세종', 2, 2], ['충북', 3, 2], ['경북', 4, 2],
		['전북', 1, 3], ['대전', 2, 3], ['대구', 3, 3], ['울산', 4, 3],
		['전남', 1, 4], ['광주', 2, 4], ['경남', 3, 4], ['부산', 4, 4],
		['제주', 1, 5]
	];

	const SPORT_CSS: Record<Sport, string> = {
		running: 'var(--sport-run)',
		trail_running: 'var(--sport-trail)',
		cycling: 'var(--sport-ride)',
		swimming: 'var(--sport-swim)',
		triathlon: 'var(--sport-tri)'
	};
	const SPORT_ORDER: Sport[] = ['running', 'trail_running', 'cycling', 'swimming', 'triathlon'];

	function normaliseSido(region: string): Sido | null {
		const r = region.trim();
		const found = CARTO.find(([s]) => r === s || r.startsWith(s) || r.includes(s));
		return found ? found[0] : null;
	}

	const racesBySido = $derived.by(() => {
		const m = new Map<Sido, Race[]>();
		for (const r of races) {
			if (!r.region) continue;
			const key = normaliseSido(r.region);
			if (!key) continue;
			const list = m.get(key) ?? [];
			list.push(r);
			m.set(key, list);
		}
		return m;
	});

	function byDate(a: Race, b: Race): number {
		return (a.raceDate || '').localeCompare(b.raceDate || '');
	}

	type SidoStat = { code: Sido; races: Race[]; count: number; col: number; row: number };

	const sidoStats = $derived.by<SidoStat[]>(() =>
		CARTO.map(([code, col, row]) => {
			const list = [...(racesBySido.get(code) ?? [])].sort(byDate);
			return { code, races: list, count: list.length, col, row };
		})
	);

	const maxN = $derived(Math.max(1, ...sidoStats.map((s) => s.count)));

	// ── Selection (always one region selected — defaults to the busiest) ──
	let selected = $state<Sido | null>(null);
	const defaultSido = $derived.by<Sido>(() => {
		const busiest = [...sidoStats].sort((a, b) => b.count - a.count)[0];
		return busiest && busiest.count > 0 ? busiest.code : '서울';
	});
	const activeSido = $derived(selected ?? defaultSido);
	const activeStat = $derived(sidoStats.find((s) => s.code === activeSido) ?? null);
	const panelRaces = $derived(activeStat?.races ?? []);

	function selectSido(code: Sido) {
		selected = code;
		track('calendar_map_region', { region: code });
	}

	// ── Density heat (relative to the busiest region, per design) ─────────
	function heatLevel(n: number): number {
		if (n === 0) return 0;
		if (n >= maxN * 0.66) return 3;
		if (n >= maxN * 0.33) return 2;
		return 1;
	}

	function sportsIn(list: Race[]): Sport[] {
		const seen = new Set<Sport>();
		for (const r of list) seen.add(r.sport);
		return SPORT_ORDER.filter((s) => seen.has(s));
	}

	// ── Per-race status helpers ──────────────────────────────────────────
	type RaceState = { label: string; closed: boolean; urgent: boolean };
	function raceState(race: Race): RaceState {
		const label = arenaDdayLabel(race);
		const closed = race.status === 'finished' || label === '마감';
		return {
			label: race.status === 'finished' ? '종료' : label,
			closed,
			urgent: !closed && arenaDday(race).urgent
		};
	}
	function shortDate(d: string | null): string {
		if (!d) return '—';
		const p = d.split('-');
		return p.length >= 3 ? `${p[1]}.${p[2]}` : d;
	}
</script>

<div class="mapwrap">
	<!-- ── tile cartogram ──────────────────────────────────────────── -->
	<div>
		<div class="eh-micro carto-cap">REGION DENSITY · 시·도별 대회 수</div>
		<div class="carto" role="group" aria-label="시·도별 타일 지도">
			{#each sidoStats as stat (stat.code)}
				{@const heat = heatLevel(stat.count)}
				{@const dots = sportsIn(stat.races)}
				<button
					class="tile heat{heat}"
					class:zero={stat.count === 0}
					class:sel={activeSido === stat.code}
					style="grid-column: {stat.col}; grid-row: {stat.row};"
					onclick={() => stat.count > 0 && selectSido(stat.code)}
					disabled={stat.count === 0}
					aria-pressed={activeSido === stat.code}
					aria-label="{stat.code} 대회 {stat.count}개{stat.count > 0 ? ' — 목록 보기' : ''}"
				>
					<span class="rg">{stat.code}</span>
					<span class="dots" aria-hidden="true">
						{#each dots as s}
							<span class="v-dot" style:background={SPORT_CSS[s]}></span>
						{/each}
					</span>
					<span class="ct eh-data">{stat.count}</span>
				</button>
			{/each}
		</div>
	</div>

	<!-- ── selected region list ────────────────────────────────────── -->
	<div>
		<div class="v-sechead">
			<div class="sechead-row">
				<h2 class="sechead-title">{activeSido}</h2>
				<span class="eh-micro eh-data">{panelRaces.length} RACES · {month}월</span>
			</div>
		</div>
		<div class="v-table region-list">
			{#if panelRaces.length === 0}
				<div class="region-empty">{month}월에는 {activeSido} 지역 대회가 없습니다.</div>
			{:else}
				{#each panelRaces as r (r.id)}
					{@const st = raceState(r)}
					<a class="v-trow click" class:is-closed={st.closed} href={r.url}>
						<span class="rl-date eh-data">{shortDate(r.raceDate)}</span>
						<span class="rl-name">
							<span class="v-dot" style:background={SPORT_CSS[r.sport]}></span>
							<span class="rl-title">{r.title}</span>
						</span>
						<span class="rl-stat eh-data" class:urgent={st.urgent} class:closed={st.closed}>
							{st.label}
						</span>
					</a>
				{/each}
			{/if}
		</div>
	</div>
</div>

<style>
	/* ── map (tile cartogram) — per design v2/Home.html ── */
	.mapwrap {
		display: grid;
		grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr);
		gap: var(--sp-8);
		align-items: start;
	}

	.carto-cap {
		margin-bottom: 10px;
		color: var(--text-muted);
	}

	.carto {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 6px;
	}

	.tile {
		aspect-ratio: 1;
		border: 1px solid var(--line);
		background: var(--paper-0);
		padding: 10px;
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		text-align: left;
		border-radius: var(--r-0);
		min-width: 0;
		cursor: pointer;
		transition: border-color var(--dur-fast) var(--ease-out);
	}
	.tile:not(.zero):hover {
		border-color: var(--ink-900);
	}
	.tile:not(.zero):focus-visible {
		outline: none;
		box-shadow: var(--focus-ring);
	}
	.tile.sel {
		border-color: var(--ink-900);
		box-shadow: inset 0 0 0 1px var(--ink-900);
	}
	.tile.zero {
		background: var(--paper-50);
		cursor: default;
	}

	.tile .rg {
		font-size: 12px;
		font-weight: 700;
		color: var(--text-strong);
	}
	.tile.zero .rg {
		color: var(--ink-300);
	}
	.tile .ct {
		font-size: 26px;
		font-weight: 800;
		letter-spacing: -0.03em;
		color: var(--text-strong);
		line-height: 1;
	}
	.tile.zero .ct {
		color: var(--ink-300);
	}
	.tile .dots {
		display: flex;
		gap: 3px;
		flex-wrap: wrap;
	}
	.tile .dots .v-dot {
		width: 6px;
		height: 6px;
	}

	.tile.heat1 {
		background: var(--signal-100);
	}
	.tile.heat2 {
		background: var(--signal-200);
	}
	.tile.heat3 {
		background: var(--signal-600);
		border-color: var(--signal-700);
	}
	.tile.heat3 .rg,
	.tile.heat3 .ct {
		color: #fff;
	}

	.v-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex: none;
		display: inline-block;
	}

	/* ── selected region list ── */
	.v-sechead {
		padding-bottom: 12px;
		border-bottom: var(--border-rule);
	}
	.sechead-row {
		display: flex;
		align-items: baseline;
		gap: 12px;
	}
	.sechead-title {
		font-size: var(--text-h2);
		font-weight: 800;
		letter-spacing: var(--track-heading);
		color: var(--text-strong);
		margin: 0;
	}
	.sechead-row .eh-micro {
		color: var(--text-faint);
	}

	.v-table.region-list {
		border: 1px solid var(--line);
		border-top: 0;
		background: var(--paper-0);
		margin-top: 14px;
	}
	.region-list .v-trow {
		display: grid;
		grid-template-columns: 56px 1fr auto;
		gap: 12px;
		align-items: center;
		padding: 12px 16px;
		border-bottom: 1px solid var(--line);
		text-decoration: none;
		color: inherit;
		transition: background var(--dur-fast) var(--ease-out);
	}
	.region-list .v-trow:last-child {
		border-bottom: 0;
	}
	.region-list .v-trow:hover {
		background: var(--paper-50);
	}
	.rl-date {
		font-weight: 600;
		color: var(--text-strong);
	}
	.rl-name {
		display: flex;
		align-items: center;
		gap: 8px;
		min-width: 0;
	}
	.rl-title {
		font-weight: 600;
		color: var(--text-strong);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.rl-stat {
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.04em;
		color: var(--text-accent);
		white-space: nowrap;
	}
	.rl-stat.urgent {
		color: var(--danger);
	}
	.rl-stat.closed {
		color: var(--text-faint);
		font-weight: 600;
	}
	.v-trow.is-closed .rl-title {
		color: var(--text-muted);
	}
	.v-trow.is-closed .v-dot {
		opacity: 0.45;
	}
	.region-empty {
		padding: 28px 18px;
		color: var(--text-faint);
		font-size: 14px;
	}

	@media (max-width: 768px) {
		.mapwrap {
			grid-template-columns: 1fr;
		}
	}
</style>
