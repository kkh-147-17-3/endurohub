import type { Race } from '$lib/types';
import {
	arenaDistLabel,
	arenaFeeRange,
	arenaFeeShort,
	arenaDday,
	arenaShortDate
} from '$lib/arena';
import { dsSport, dsBadgeStatus, type DsSport, type DsBadgeStatus } from './meta';
import type { Spec } from './EventCard.svelte';

export interface EventCardProps {
	sport: DsSport;
	title: string;
	date: string;
	location: string;
	status: DsBadgeStatus;
	specs: Spec[];
	href: string;
	note?: string;
}

/** Build full date label "2026.05.14" from a Race. */
function fullDate(race: Race): string {
	if (!race.raceDate) return '미정';
	const parts = race.raceDate.split('-');
	if (parts.length < 3) return race.raceDate;
	return `${parts[0]}.${parts[1]}.${parts[2]}`;
}

/**
 * Map a Race onto DS EventCard props. `withNote` includes the curation note
 * (used by row cards); `compactDate` uses the short MM.DD form.
 */
export function raceToEventCard(
	race: Race,
	opts: { compactDate?: boolean; note?: string } = {}
): EventCardProps {
	const { value: dday } = arenaDday(race);
	const { min, max } = arenaFeeRange(race);
	const status = dsBadgeStatus(race.status, race.daysUntilRegistrationEnd ?? null);

	const specs: Spec[] = [{ label: 'DIST', value: arenaDistLabel(race) }];
	if (min != null) {
		specs.push({
			label: 'FEE',
			value: max && max !== min ? `${arenaFeeShort(min)}~` : arenaFeeShort(min)
		});
	}
	if (status === 'open' || status === 'closing') {
		if (dday != null && dday >= 0) {
			specs.push({ label: 'ENTRY', value: `D-${dday}`, accent: true });
		}
	}

	return {
		sport: dsSport(race.sport),
		title: race.title,
		date: opts.compactDate ? arenaShortDate(race.raceDate) : fullDate(race),
		location: race.region || race.location || '',
		status,
		specs,
		href: `/races/${race.slug}`,
		note: opts.note
	};
}
