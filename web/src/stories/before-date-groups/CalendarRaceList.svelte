<script lang="ts">
	import type { Race } from '$lib/types';
	import { kstTodayStr } from '$lib/date';
	import { arenaFeeRange, arenaFeeShort } from '$lib/arena';
	import { dsBadgeStatus, dsSport, SPORT_META, type DsBadgeStatus } from '$lib/components/eh/meta';
	import SportTag from '$lib/components/eh/SportTag.svelte';
	import Badge from '$lib/components/eh/Badge.svelte';

	let {
		rows,
		noHead = false,
		showSport = true,
		showRegistrationStatus = true
	}: {
		rows: Race[];
		noHead?: boolean;
		showSport?: boolean;
		showRegistrationStatus?: boolean;
	} = $props();
	const today = $derived(kstTodayStr());
	const weekdays = ['일', '월', '화', '수', '목', '금', '토'];

	function shortDate(race: Race): string {
		if (!race.raceDate) return '일정 확인 필요';
		const [year, month, day] = race.raceDate.split('-').map(Number);
		return `${month}.${String(day).padStart(2, '0')} (${weekdays[new Date(year, month - 1, day).getDay()]})`;
	}

	function distanceLabel(race: Race): string {
		const labels = (race.distances ?? []).map((distance) => {
			if (distance.name?.trim()) return distance.name.trim();
			if (distance.distanceMeter != null && distance.distanceMeter > 0) {
				return `${Number((distance.distanceMeter / 1000).toFixed(2))}km`;
			}
			return '';
		}).filter(Boolean);
		return [...new Set(labels)].join(' · ') || '확인 필요';
	}

	function feeLabel(race: Race): string {
		const { min, max } = arenaFeeRange(race);
		if (race.distances?.some((distance) => distance.fee === 0)) {
			return max != null ? `무료~${arenaFeeShort(max)}` : '무료';
		}
		if (min != null) return `${arenaFeeShort(min)}${max != null && max > min ? '~' : ''}`;
		return '확인 필요';
	}

	function badgeStatus(race: Race): DsBadgeStatus {
		// An explicit cancellation must never be replaced by today's live badge.
		if (race.status === 'cancelled') return dsBadgeStatus(race.status);
		if (race.raceDate === today && (race.status === 'registration_open' || race.status === 'upcoming')) {
			return 'live';
		}
		return dsBadgeStatus(race.status, race.daysUntilRegistrationEnd);
	}
</script>

<div class="race-list" class:nohead={noHead} class:without-sport={!showSport}>
	{#if !noHead}
		<div class="race-head" aria-hidden="true">
			<span>날짜</span>{#if showSport}<span>종목</span>{/if}<span>대회명</span>
			<span>지역</span><span>거리</span><span>참가비</span><span class="status-heading">{showRegistrationStatus ? '접수 상태' : '마감'}</span>
		</div>
	{/if}
	{#each rows as race (race.id)}
		{@const status = badgeStatus(race)}
		<a class="race-row" href={`/races/${encodeURIComponent(race.slug)}`} title={race.title}>
			{#if !noHead}
				<time class="row-date eh-data" datetime={race.raceDate ?? undefined}>{shortDate(race)}</time>
			{/if}
			{#if showSport}<span class="row-sport"><SportTag sport={dsSport(race.sport)}>{SPORT_META[dsSport(race.sport)].ko}</SportTag></span>{/if}
			<span class="row-name">{race.title}</span>
			<span class="row-details">
				<span class="row-region"><span class="detail-label">지역</span>{race.region?.trim() || '확인 필요'}</span>
				<span class="row-distance eh-data"><span class="detail-label">거리</span>{distanceLabel(race)}</span>
				<span class="row-fee eh-data"><span class="detail-label">참가비</span>{feeLabel(race)}</span>
			</span>
			<span class="row-status">
				{#if showRegistrationStatus || status !== 'open'}
				<Badge {status}>
					{#if race.status === 'cancelled'}대회 취소
					{:else if status === 'live'}오늘 개최
					{:else if race.status === 'finished'}종료
					{:else if status === 'closing'}마감 임박
					{:else if status === 'open'}접수 중
					{:else if status === 'upcoming'}오픈 예정
					{:else}접수 마감{/if}
				</Badge>
				{/if}
				{#if race.status === 'registration_open' && race.daysUntilRegistrationEnd != null && race.daysUntilRegistrationEnd >= 0}
					<span class="row-deadline eh-data">접수 마감 D-{race.daysUntilRegistrationEnd}</span>
				{/if}
			</span>
		</a>
	{/each}
</div>

<style>
	.race-list {
		border: 1px solid var(--line);
		background: var(--paper-0);
	}
	.race-list.nohead { border: 0; }
	.race-head,
	.race-row {
		display: grid;
		grid-template-columns: 74px 62px minmax(0, 1fr) 44px 84px 70px 104px;
		align-items: center;
		gap: 12px;
		padding: 14px 18px;
	}
	.nohead .race-row {
		grid-template-columns: 62px minmax(0, 1fr) 44px 84px 70px 104px;
	}
	.without-sport .race-head,
	.without-sport .race-row {
		grid-template-columns: 74px minmax(0, 1fr) 44px 84px 70px 104px;
	}
	.nohead.without-sport .race-row {
		grid-template-columns: minmax(0, 1fr) 44px 84px 70px 104px;
	}
	.race-head {
		border-bottom: var(--border-rule);
		color: var(--text-muted);
		font-size: var(--text-micro);
		font-weight: var(--w-strong);
	}
	.race-row {
		border-bottom: 1px solid var(--line);
		color: var(--text-body);
		font-size: var(--text-body-sm);
		line-height: 1.5;
		text-decoration: none;
		transition: background var(--dur-fast) var(--ease-out);
	}
	.race-row:last-child { border-bottom: 0; }
	.race-row:hover { background: var(--paper-50); }
	.race-row:focus-visible { outline: 2px solid var(--accent-strong); outline-offset: -2px; }
	.row-date { color: var(--text-strong); font-size: 12px; font-weight: var(--w-strong); }
	.row-sport { min-width: 0; }
	.row-name {
		min-width: 0;
		display: -webkit-box;
		-webkit-box-orient: vertical;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		overflow: hidden;
		overflow-wrap: anywhere;
		color: var(--text-strong);
		font-weight: var(--w-strong);
	}
	.row-details { display: contents; }
	.row-region,
	.row-distance,
	.row-fee { min-width: 0; color: var(--text-muted); overflow-wrap: anywhere; font-size: var(--text-caption); }
	.detail-label { display: none; }
	.row-status { display: flex; flex-direction: column; align-items: flex-end; gap: 5px; }
	.status-heading { text-align: right; }
	.row-deadline { color: var(--text-accent); font-size: 11px; white-space: nowrap; }
	@media (max-width: 768px) {
		.race-head { display: none; }
		.race-row,
		.nohead .race-row,
		.without-sport .race-row,
		.nohead.without-sport .race-row {
			grid-template-columns: minmax(0, 1fr) auto;
			grid-template-areas: 'date status' 'sport status' 'name name' 'details details';
			align-items: start;
			gap: 6px 12px;
			padding: 16px;
		}
		.nohead .race-row { grid-template-areas: 'sport status' 'name name' 'details details'; }
		.without-sport .race-row { grid-template-areas: 'date status' 'name name' 'details details'; }
		.nohead.without-sport .race-row { grid-template-areas: 'status status' 'name name' 'details details'; }
		.row-date { grid-area: date; color: var(--text-muted); }
		.row-sport { grid-area: sport; }
		.row-name { grid-area: name; margin-top: 2px; font-size: 15px; line-height: 1.5; }
		.row-status { grid-area: status; }
		.row-details { grid-area: details; display: flex; flex-wrap: wrap; gap: 5px 14px; margin-top: 4px; }
		.row-region,
		.row-distance,
		.row-fee { display: inline; max-width: 100%; font-size: var(--text-caption); }
		.detail-label { display: inline; margin-right: 5px; color: var(--text-faint); font-size: 11px; }
	}
</style>
