import type { PageServerLoad } from './$types';
import { redirect } from '@sveltejs/kit';
import { apiFetch } from '$lib/api';
import { kstTodayStr } from '$lib/date';
import type { CalendarResponse } from '$lib/types';

export const load: PageServerLoad = async ({ url, locals }) => {
	const [todayYear, todayMonth] = kstTodayStr().split('-').map(Number);
	const rawYear = url.searchParams.get('year');
	const rawMonth = url.searchParams.get('month');
	const year = rawYear ?? String(todayYear);
	const month = rawMonth ?? String(todayMonth);
	const sport = url.searchParams.getAll('sport');
	const region = url.searchParams.getAll('region');

	// 필터 없는 현재 월은 /calendar 하나로 합친다. year/month 중 하나만 명시한
	// 경우도 실제 콘텐츠가 같으므로 동일하게 정규화한다.
	const hasExplicitDate = rawYear !== null || rawMonth !== null;
	if (
		hasExplicitDate &&
		year === String(todayYear) &&
		month === String(todayMonth) &&
		sport.length === 0 &&
		region.length === 0
	) {
		redirect(301, '/calendar');
	}

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
