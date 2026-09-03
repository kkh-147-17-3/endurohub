import type { PageServerLoad } from './$types';
import { error } from '@sveltejs/kit';
import { apiFetch } from '$lib/api';
import { kstTodayStr } from '$lib/date';
import type { RaceYearlyResponse } from '$lib/types';

const cache = new Map<number, { data: RaceYearlyResponse; at: number }>();
const CACHE_TTL = 60_000; // 1 minute

export const load: PageServerLoad = async ({ params, locals }) => {
	// 숫자 접두사만 읽는 parseInt는 /2026foo, /+2026, /02026 같은 서로 다른
	// 경로를 모두 같은 데이터로 200 응답하게 만든다. 정규화된 4자리 연도만 허용한다.
	if (!/^[1-9]\d{3}$/.test(params.year)) {
		error(404, '유효하지 않은 연도입니다.');
	}
	const year = Number(params.year);
	const now = Date.now();
	const canUseSharedCache = !locals.authToken;
	const cached = cache.get(year);
	if (canUseSharedCache && cached && now - cached.at < CACHE_TTL) {
		return cached.data;
	}

	const data = await apiFetch<RaceYearlyResponse>(`/races/year/${year}/`, {
		authToken: locals.authToken || undefined,
	});

	// 대회가 한 건도 없는 연도는 404. 이 라우트는 어떤 숫자든 200 을 돌려주기 때문에
	// /races/year/2031, /2036, /2019 처럼 데이터가 없는 연도가 본문 460자짜리 페이지로
	// 응답하고 있었다. Search Console 에서 17개 연도가 "크롤링됨 - 현재 색인 생성되지
	// 않음" 에 쌓인 원인이다. 소프트 404 는 사이트 전체 품질 신호를 깎는다.
	//
	// 올해만 예외로 둔다. 상단 내비게이션이 /races/year/{올해} 를 가리키는데, 새해가
	// 바뀐 직후 그 해 대회가 아직 수집되지 않았을 때 주 메뉴가 404 로 떨어지면 안 된다.
	const currentYear = Number(kstTodayStr().slice(0, 4));
	if (!data.totalCount && year !== currentYear) {
		error(404, `${year}년에 등록된 대회가 없습니다.`);
	}

	if (canUseSharedCache) {
		cache.set(year, { data, at: now });
	}
	return data;
};
