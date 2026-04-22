import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import type { CalendarResponse } from '$lib/types';

export const load: PageServerLoad = async ({ url, locals }) => {
	const now = new Date();
	const year = url.searchParams.get('year') || String(now.getFullYear());
	const month = url.searchParams.get('month') || String(now.getMonth() + 1);
	const sport = url.searchParams.get('sport');

	const params: Record<string, string> = { year, month };
	if (sport) params.sport = sport;

	const data = await apiFetch<CalendarResponse>(
		'/races/calendar/',
		{ authToken: locals.authToken || undefined },
		params
	);
	return data;
};
