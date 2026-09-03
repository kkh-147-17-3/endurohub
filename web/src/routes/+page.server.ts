import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import { kstTodayStr } from '$lib/date';
import { redirect } from '@sveltejs/kit';
import type { CalendarResponse } from '$lib/types';

export const load: PageServerLoad = async ({ url, locals }) => {
	const [todayYear, todayMonth] = kstTodayStr().split('-').map(Number);

	// Calendar navigation used to live at /?year=&month=, duplicating the dedicated
	// /calendar route. Permanently move those legacy URLs while preserving filters.
	if (['year', 'month', 'sport', 'region'].some((key) => url.searchParams.has(key))) {
		const year = url.searchParams.get('year') ?? String(todayYear);
		const month = url.searchParams.get('month') ?? String(todayMonth);
		if (
			year === String(todayYear) &&
			month === String(todayMonth) &&
			!url.searchParams.has('sport') &&
			!url.searchParams.has('region')
		) {
			redirect(301, '/calendar');
		}
		redirect(301, `/calendar${url.search}`);
	}

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
