import type { LayoutServerLoad } from './$types';
import {
	APP_NAME,
	APP_URL,
	KAKAO_JAVASCRIPT_KEY,
	NAVER_MAP_CLIENT_ID,
	GOOGLE_ANALYTICS_ID,
	FEEDBACK_FORM_URL,
} from '$lib/env';
import { apiFetch } from '$lib/api';
import type { MeResponse, AuthUser } from '$lib/types';
import type { PopupActiveResponse, EventBanner } from '$lib/popup';

export const load: LayoutServerLoad = async ({ locals }) => {
	const { isAdmin } = locals;

	let user: AuthUser | null = null;
	if (locals.authToken) {
		try {
			const meData = await apiFetch<MeResponse>('/auth/me/', {
				authToken: locals.authToken
			});
			user = meData.user;
		} catch {
			// Token invalid or expired - ignore
		}
	}

	// 게시기간 안인 팝업 배너 (django admin > 팝업 배너). 백엔드에서 60초 캐시하고
	// 관리자 저장 시 즉시 무효화되므로 전 페이지 로드에서 불러도 부담이 없다.
	// 실패해도 페이지는 그대로 떠야 하므로 조용히 넘긴다.
	let popup: EventBanner | null = null;
	try {
		const resp = await apiFetch<PopupActiveResponse>('/popups/active/');
		popup = resp.popup;
	} catch {
		// 팝업은 부가 요소 — 조회 실패가 페이지를 막지 않는다.
	}

	return {
		appName: APP_NAME,
		appUrl: APP_URL,
		currentYear: new Date().getFullYear(),
		kakaoJsKey: KAKAO_JAVASCRIPT_KEY,
		naverMapClientId: NAVER_MAP_CLIENT_ID,
		googleAnalyticsId: GOOGLE_ANALYTICS_ID,
		feedbackFormUrl: FEEDBACK_FORM_URL,
		isAdmin,
		user,
		popup
	};
};
