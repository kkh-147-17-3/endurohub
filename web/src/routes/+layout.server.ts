import type { LayoutServerLoad } from './$types';
import {
	APP_NAME,
	APP_URL,
	KAKAO_JAVASCRIPT_KEY,
	NAVER_MAP_CLIENT_ID,
	GOOGLE_ANALYTICS_ID,
	FEEDBACK_FORM_URL,
	ADMIN_SECRET
} from '$lib/env';
import { apiFetch } from '$lib/api';
import type { MeResponse, AuthUser } from '$lib/types';

export const load: LayoutServerLoad = async ({ cookies, locals }) => {
	const adminToken = cookies.get('admin_token') || '';
	const isAdmin = !!(ADMIN_SECRET && adminToken && adminToken === ADMIN_SECRET);

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

	return {
		appName: APP_NAME,
		appUrl: APP_URL,
		currentYear: new Date().getFullYear(),
		kakaoJsKey: KAKAO_JAVASCRIPT_KEY,
		naverMapClientId: NAVER_MAP_CLIENT_ID,
		googleAnalyticsId: GOOGLE_ANALYTICS_ID,
		feedbackFormUrl: FEEDBACK_FORM_URL,
		isAdmin,
		user
	};
};
