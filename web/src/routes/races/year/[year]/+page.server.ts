import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import type { RaceYearlyResponse } from '$lib/types';

const cache = new Map<number, { data: RaceYearlyResponse; at: number }>();
const CACHE_TTL = 60_000; // 1 minute

export const load: PageServerLoad = async ({ params }) => {
	const year = parseInt(params.year);
	const now = Date.now();
	const cached = cache.get(year);
	if (cached && now - cached.at < CACHE_TTL) {
		return cached.data;
	}

	const data = await apiFetch<RaceYearlyResponse>(`/races/year/${year}/`);
	cache.set(year, { data, at: now });
	return data;
};
