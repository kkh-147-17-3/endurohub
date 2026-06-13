import type { Sport, RaceStatus } from '$lib/types';

/** DS sport keys (run/trail/ride/swim/tri) + their dot color + KO label. */
export type DsSport = 'run' | 'trail' | 'ride' | 'swim' | 'tri';

export const SPORT_META: Record<DsSport, { label: string; color: string; ko: string }> = {
	run: { label: 'RUN', color: 'var(--sport-run)', ko: '러닝' },
	trail: { label: 'TRAIL', color: 'var(--sport-trail)', ko: '트레일' },
	ride: { label: 'RIDE', color: 'var(--sport-ride)', ko: '사이클' },
	swim: { label: 'SWIM', color: 'var(--sport-swim)', ko: '수영' },
	tri: { label: 'TRI', color: 'var(--sport-tri)', ko: '철인3종' }
};

/** Map the app's Sport union onto the DS sport key. */
export const appSportToDs: Record<Sport, DsSport> = {
	running: 'run',
	trail_running: 'trail',
	cycling: 'ride',
	swimming: 'swim',
	triathlon: 'tri'
};

export function dsSport(sport: Sport): DsSport {
	return appSportToDs[sport] ?? 'run';
}

/** DS Badge status keys. */
export type DsBadgeStatus = 'open' | 'closing' | 'closed' | 'upcoming' | 'live';

export const BADGE_LABELS: Record<DsBadgeStatus, string> = {
	open: '접수 중',
	closing: '마감 임박',
	closed: '접수 마감',
	upcoming: '오픈 예정',
	live: 'LIVE'
};

/**
 * Map the app RaceStatus onto a DS badge status. When `daysToClose` is known
 * and small (≤7), an open registration becomes "closing" (마감 임박).
 */
export function dsBadgeStatus(status: RaceStatus, daysToClose?: number | null): DsBadgeStatus {
	switch (status) {
		case 'registration_open':
			return daysToClose != null && daysToClose >= 0 && daysToClose <= 7 ? 'closing' : 'open';
		case 'registration_closed':
			return 'closed';
		case 'finished':
			return 'closed';
		case 'upcoming':
		default:
			return 'upcoming';
	}
}
