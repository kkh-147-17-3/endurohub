import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import type { Race } from '$lib/types';

/** Race rows from /me/season/ carry a flat participation/result overlay. */
interface SeasonResponse {
	year: number;
	races: Race[];
	stats: unknown;
}

export const load: PageServerLoad = async ({ locals }) => {
	const isAuthed = !!locals.authToken;
	const year = new Date().getFullYear();

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
	};
};
