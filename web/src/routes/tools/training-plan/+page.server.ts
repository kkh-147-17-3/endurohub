import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import { favoriteRacesToGoals, pickRunningRecordPrefill } from '$lib/tools';
import type { PaginatedResponse, Race, RaceRecordListResponse } from '$lib/types';

// Prefill the tool with the user's most recent running/trail race record, and
// load the season's target-race options from their 관심대회 (favorite races),
// keeping only races that haven't finished yet. Both require sign-in.
export const load: PageServerLoad = async ({ locals }) => {
	if (!locals.authToken) return { prefill: null, goalRaces: [], signedIn: false };

	const [prefill, goalRaces] = await Promise.all([
		apiFetch<RaceRecordListResponse>('/me/records/', { authToken: locals.authToken })
			.then((res) => pickRunningRecordPrefill(res.records ?? []))
			.catch(() => null),
		apiFetch<PaginatedResponse<Race>>(
			'/me/favorites/races/',
			{ authToken: locals.authToken },
			{ per_page: '100' }
		)
			.then((res) => favoriteRacesToGoals(res.data ?? []))
			.catch(() => [])
	]);

	return { prefill, goalRaces, signedIn: true };
};
