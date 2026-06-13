<script lang="ts">
	import EventCard from './EventCard.svelte';
	import Badge from './Badge.svelte';
	import SportTag from './SportTag.svelte';
	import { raceToEventCard } from './race';
	import { dsSport, dsBadgeStatus } from './meta';
	import { arenaDday, arenaFeeRange, arenaFeeShort } from '$lib/arena';
	import type { Race } from '$lib/types';

	let { races }: { races: Race[] } = $props();

	// ── Row helpers (PC table layout) ─────────────────────────────────────────
	const DOW = ['일', '월', '화', '수', '목', '금', '토'];
	function rowDate(d: string | null): string {
		if (!d) return '미정';
		const p = d.split('-');
		if (p.length < 3) return d;
		return `${Number(p[1])}.${p[2]}`;
	}
	function weekdayKo(d: string | null): string {
		if (!d) return '';
		const dt = new Date(`${d}T00:00:00`);
		return Number.isNaN(dt.getTime()) ? '' : DOW[dt.getDay()];
	}

	// 참가비 — 모든 결과 행에 노출. 범위면 최저가에 ~ 표기.
	function feeLabel(race: Race): string {
		const { min, max } = arenaFeeRange(race);
		if (min == null) return '—';
		return max != null && max !== min ? `${arenaFeeShort(min)}~` : arenaFeeShort(min);
	}
</script>

<!-- PC: hairline table — 일정 · 종목 · 대회명 · 참가비 · 상태 -->
<div class="v-pc">
	<div class="v-table rowlist">
		{#each races as race (race.slug)}
			{@const status = dsBadgeStatus(race.status, race.daysUntilRegistrationEnd ?? null)}
			{@const dday = arenaDday(race).value}
			<a class="v-trow click" href={`/races/${race.slug}`}>
				<span class="eh-data trow-date">{rowDate(race.raceDate)}<span class="trow-dow"> {weekdayKo(race.raceDate)}</span></span>
				<span class="trow-sport"><SportTag sport={dsSport(race.sport)} /></span>
				<span class="trow-name">{race.title}</span>
				<span class="eh-data trow-fee">{feeLabel(race)}</span>
				<span class="trow-badge">
					{#if status === 'open'}
						<Badge status="open"><span class="eh-data">접수 중{dday != null && dday >= 0 ? ` D-${dday}` : ''}</span></Badge>
					{:else if status === 'closing'}
						<Badge status="closing"><span class="eh-data">마감 임박{dday != null && dday >= 0 ? ` D-${dday}` : ''}</span></Badge>
					{:else if status === 'upcoming'}
						<Badge status="upcoming" />
					{:else}
						<Badge status="closed" />
					{/if}
				</span>
			</a>
		{/each}
	</div>
</div>

<!-- Mobile: cards — EventCard specs already carry 종목 + 거리 + 참가비 -->
<div class="v-mob">
	<div class="grid">
		{#each races as race (race.slug)}
			{@const c = raceToEventCard(race)}
			<EventCard
				sport={c.sport}
				title={c.title}
				date={c.date}
				location={c.location}
				status={c.status}
				specs={c.specs}
				href={c.href}
			/>
		{/each}
	</div>
</div>

<style>
	/* ── PC table (RowList) ───────────────────────────────────────────────── */
	.rowlist .v-trow {
		grid-template-columns: 92px 96px 1fr 92px 132px;
		gap: 14px;
		text-decoration: none;
		color: var(--text-strong);
	}
	.trow-date {
		font-weight: 600;
		color: var(--text-strong);
		white-space: nowrap;
	}
	.trow-dow {
		color: var(--text-muted);
	}
	.trow-sport {
		min-width: 0;
	}
	.trow-name {
		font-weight: 600;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.trow-fee {
		color: var(--text-muted);
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
	}
	.trow-badge {
		justify-self: end;
	}

	/* ── Mobile cards ─────────────────────────────────────────────────────── */
	.grid {
		display: grid;
		grid-template-columns: 1fr;
		gap: var(--sp-3);
		align-items: stretch;
	}
	@media (min-width: 560px) {
		.grid {
			grid-template-columns: repeat(2, 1fr);
		}
	}
	.grid :global(.eh-event__title) {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
		min-height: 2.4em;
	}
</style>
