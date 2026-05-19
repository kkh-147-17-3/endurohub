import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import type { RaceListResponse } from '$lib/types';

export const load: PageServerLoad = async ({ url, locals }) => {
	const params: Record<string, string | string[]> = {};

	const sport = url.searchParams.getAll('sport');
	if (sport.length > 0) params.sport = sport;

	const region = url.searchParams.getAll('region');
	if (region.length > 0) params.region = region;

	const status = url.searchParams.getAll('status');
	if (status.length > 0) params.status = status;

	const name = url.searchParams.get('name');
	if (name) params.name = name;

	const search = url.searchParams.get('search');
	if (search) params.name = search;

	const distanceCategory = url.searchParams.getAll('distance_category');
	if (distanceCategory.length > 0) params.distance_category = distanceCategory;

	const monthFrom = url.searchParams.get('month_from');
	if (monthFrom) params.month_from = monthFrom;

	const monthTo = url.searchParams.get('month_to');
	if (monthTo) params.month_to = monthTo;

	const page = url.searchParams.get('page');
	if (page) params.page = page;

	const data = await apiFetch<RaceListResponse>('/races/', {
		sessionId: locals.sessionId || undefined,
		authToken: locals.authToken || undefined,
		userAgent: locals.userAgent || undefined,
	}, params);
	return { ...data };
};
