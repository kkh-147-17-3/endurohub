import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import type { HomeResponse } from '$lib/types';

let cachedData: HomeResponse | null = null;
let cachedAt = 0;
const CACHE_TTL = 60_000; // 1 minute

export const load: PageServerLoad = async () => {
	const now = Date.now();
	if (cachedData && now - cachedAt < CACHE_TTL) {
		return cachedData;
	}

	const data = await apiFetch<HomeResponse>('/home/');
	cachedData = data;
	cachedAt = now;
	return data;
};
