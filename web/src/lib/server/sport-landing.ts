import { apiFetch } from '$lib/api';
import { getSportLanding } from '$lib/seo/sport-landing';
import type { RaceListResponse } from '$lib/types';

/**
 * 종목 랜딩 페이지(/running, /swimming, …)의 공통 load.
 *
 * 목록은 `/races` 와 같은 엔드포인트를 쓰되 첫 페이지만 가져온다. 랜딩 페이지는
 * 전체 목록을 대신하는 곳이 아니라 종목 허브이고, 더 보려는 사람은 `/races` 로
 * 넘긴다. 목록에 실리는 대회 상세 링크는 덤이 아니라 목적 중 하나다 — 대회
 * 상세 페이지로 가는 내부 링크 경로를 종목별로 하나씩 더 만들어 준다.
 */
export async function loadSportLanding(
	path: string,
	locals: App.Locals,
): Promise<{
	content: ReturnType<typeof getSportLanding>;
	races: RaceListResponse['data'];
	total: number;
	openTotal: number | null;
}> {
	const content = getSportLanding(path);
	const auth = {
		sessionId: locals.sessionId || undefined,
		authToken: locals.authToken || undefined,
		userAgent: locals.userAgent || undefined,
	};

	// 접수 중 집계는 부가 정보다. 실패해도 페이지 자체는 떠야 하므로 따로 삼킨다.
	const [upcoming, open] = await Promise.all([
		apiFetch<RaceListResponse>('/races/', auth, { sport: content.sport }),
		apiFetch<RaceListResponse>('/races/', auth, {
			sport: content.sport,
			status: 'registration_open',
		}).catch(() => null),
	]);

	return {
		content,
		races: upcoming.data,
		total: upcoming.meta.total,
		openTotal: open?.meta.total ?? null,
	};
}
