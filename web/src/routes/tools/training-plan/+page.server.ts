import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import { favoriteRacesToGoals, pickRunningRecordPrefill } from '$lib/tools';
import { kstTodayStr } from '$lib/date';
import { createPublicTrainingExample, supportsMarathonPlan } from '$lib/tools/public-training-example';
import type { PaginatedResponse, Race, RaceRecordListResponse } from '$lib/types';

// Personal targets are saved road races offering a full marathon. Other
// visitors can explore the fictional model without any account requests.
export const load: PageServerLoad = async ({ locals }) => {
	// The same serialized date anchors SSR and hydration; anonymous visitors need
	// no private endpoints to explore the fictional example.
	const publicExample = createPublicTrainingExample(kstTodayStr());
	if (!locals.authToken) return { prefill: null, goalRaces: [], signedIn: false, publicExample };

	const [prefill, goalRaces] = await Promise.all([
		apiFetch<RaceRecordListResponse>('/me/records/', { authToken: locals.authToken })
			.then((res) => pickRunningRecordPrefill(res.records ?? []))
			.catch(() => null),
		apiFetch<PaginatedResponse<Race>>(
			'/me/favorites/races/',
			{ authToken: locals.authToken },
			{ per_page: '100' }
		)
			.then((res) => favoriteRacesToGoals((res.results ?? []).filter(supportsMarathonPlan)))
			.catch(() => [])
	]);

	return { prefill, goalRaces, signedIn: true, publicExample };
};
