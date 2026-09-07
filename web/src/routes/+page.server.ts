import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import { kstTodayStr } from '$lib/date';
import type { CalendarResponse, HomeCommunityResponse } from '$lib/types';

const EMPTY_COMMUNITY: HomeCommunityResponse = {
	recentReviews: [],
	recentRecords: []
};

function normalizeCommunity(value: unknown): HomeCommunityResponse {
	if (!value || typeof value !== 'object') return EMPTY_COMMUNITY;
	const data = value as Partial<HomeCommunityResponse>;
	return {
		recentReviews: Array.isArray(data.recentReviews) ? data.recentReviews : [],
		recentRecords: Array.isArray(data.recentRecords) ? data.recentRecords : []
	};
}

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

	const communityRequest = apiFetch<HomeCommunityResponse>('/home/community/', {
		clientIp: locals.clientIp,
		authToken: locals.authToken || undefined,
		sessionId: locals.sessionId || undefined,
		userAgent: locals.userAgent || undefined
	})
		.then(normalizeCommunity)
		.catch(() => EMPTY_COMMUNITY);

	const [calendar, community] = await Promise.all([
		apiFetch<CalendarResponse>(
			'/races/calendar/',
			{ authToken: locals.authToken || undefined },
			params
		),
		communityRequest
	]);

	return { ...calendar, ...community };
};
