import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import type { RaceYearlyResponse } from '$lib/types';

const cache = new Map<number, { data: RaceYearlyResponse; at: number }>();
const CACHE_TTL = 60_000; // 1 minute

export const load: PageServerLoad = async ({ params, locals }) => {
	const year = parseInt(params.year);
	const now = Date.now();
	const canUseSharedCache = !locals.authToken;
	const cached = cache.get(year);
	if (canUseSharedCache && cached && now - cached.at < CACHE_TTL) {
		return cached.data;
	}

	const data = await apiFetch<RaceYearlyResponse>(`/races/year/${year}/`, {
		authToken: locals.authToken || undefined,
	});
	if (canUseSharedCache) {
		cache.set(year, { data, at: now });
	}
	return data;
};
