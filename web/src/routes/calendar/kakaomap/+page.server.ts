import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import type { CalendarResponse } from '$lib/types';

export const load: PageServerLoad = async ({ url, locals }) => {
	const now = new Date();
	const year = url.searchParams.get('year') || String(now.getFullYear());
	const month = url.searchParams.get('month') || String(now.getMonth() + 1);
	const sport = url.searchParams.getAll('sport');

	// The map view shows every region for the month — region selection happens
	// by clicking on the map, so the `region` query param is intentionally not
	// forwarded to the API here.
	const params: Record<string, string | string[]> = { year, month };
	if (sport.length > 0) params.sport = sport;

	const data = await apiFetch<CalendarResponse>(
		'/races/calendar/',
		{ authToken: locals.authToken || undefined },
		params
	);
	return data;
};
