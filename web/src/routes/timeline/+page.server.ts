import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import { kstTodayStr } from '$lib/date';
import type { Race } from '$lib/types';

/** Race rows from /me/season/ carry a flat participation/result overlay. */
interface SeasonResponse {
	year: number;
	races: Race[];
	stats: unknown;
}

export const load: PageServerLoad = async ({ locals, url }) => {
	const isAuthed = !!locals.authToken;
	const seasonToday = kstTodayStr();
	const currentYear = Number(seasonToday.slice(0, 4));
	const requestedYear = Number(url.searchParams.get('year'));
	const year = Number.isInteger(requestedYear) && requestedYear >= 2000 && requestedYear <= currentYear
		? requestedYear
		: currentYear;

	let races: Race[] = [];

	// Only authenticated users have a season. Guests (and authed users with an
	// empty season) get a CTA empty-state instead of a sample — no fallback fetch.
	if (isAuthed) {
		try {
			const data = await apiFetch<SeasonResponse>(
				'/me/season/',
				{ authToken: locals.authToken },
				{ year },
			);
			races = data.races ?? [];
		} catch {
			races = [];
		}
	}

	return {
		races,
		isAuthed,
		seasonYear: year,
		currentYear,
		seasonToday,
	};
};
