import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import { kstTodayStr } from '$lib/date';
import type { CalendarResponse } from '$lib/types';

export const load: PageServerLoad = async ({ url, locals }) => {
	const [todayYear, todayMonth] = kstTodayStr().split('-').map(Number);
	const year = url.searchParams.get('year') || String(todayYear);
	const month = url.searchParams.get('month') || String(todayMonth);
	const sport = url.searchParams.getAll('sport');
	const region = url.searchParams.getAll('region');

	const params: Record<string, string | string[]> = { year, month };
	if (sport.length > 0) params.sport = sport;
	if (region.length > 0) params.region = region;

	const data = await apiFetch<CalendarResponse>(
		'/races/calendar/',
		{ authToken: locals.authToken || undefined },
		params
	);
	return data;
};
