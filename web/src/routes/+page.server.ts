import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import { kstTodayStr } from '$lib/date';
import type { CalendarResponse } from '$lib/types';

export const load: PageServerLoad = async ({ url, locals }) => {
	const [todayYear, todayMonth] = kstTodayStr().split('-').map(Number);

	// 홈의 월 이동은 같은 라우트에서 처리한다. /calendar로 넘기면 홈 히어로가
	// 사라지므로 쿼리를 보존한 채 이 페이지의 캘린더 데이터만 다시 불러온다.
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
