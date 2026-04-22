import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import type { HomeResponse, RecommendationsResponse } from '$lib/types';

let cachedData: Omit<HomeResponse, 'recommendations'> | null = null;
let cachedAt = 0;
const CACHE_TTL = 60_000; // 1 minute

export const load: PageServerLoad = async ({ locals }) => {
	const now = Date.now();

	// Home data: shared cache only for anonymous users (isFavorited varies per user).
	const canUseSharedCache = !locals.authToken;
	const homePromise = (canUseSharedCache && cachedData && now - cachedAt < CACHE_TTL)
		? Promise.resolve(cachedData)
		: apiFetch<Omit<HomeResponse, 'recommendations'>>('/home/', {
			authToken: locals.authToken || undefined,
		}).then((data) => {
			if (canUseSharedCache) {
				cachedData = data;
				cachedAt = Date.now();
			}
			return data;
		});

	// Recommendations: per-user/session (no client-side cache, Django caches)
	const recsPromise = apiFetch<RecommendationsResponse>(
		'/races/recommendations/',
		{
			authToken: locals.authToken || undefined,
			sessionId: locals.sessionId || undefined,
		},
	).catch(() => null);

	const [home, recommendations] = await Promise.all([homePromise, recsPromise]);

	return {
		...home,
		recommendations,
	};
};
