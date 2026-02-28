import type { PageServerLoad } from './$types';
import { redirect } from '@sveltejs/kit';
import { apiFetch } from '$lib/api';
import type { OAuthCallbackResponse } from '$lib/types';

export const load: PageServerLoad = async ({ params, url, cookies }) => {
	const { provider } = params;
	const code = url.searchParams.get('code');
	const state = url.searchParams.get('state');
	const error = url.searchParams.get('error');

	if (error) {
		return { error: '소셜 로그인이 취소되었습니다.' };
	}

	if (!code) {
		return { error: '인증 코드가 없습니다.' };
	}

	const appUrl = url.origin;
	const redirectUri = `${appUrl}/auth/${provider}/callback`;

	try {
		const body: Record<string, string> = { code, redirect_uri: redirectUri };
		if (state) {
			body.state = state;
		}

		const result = await apiFetch<OAuthCallbackResponse | { error: string }>(
			`/auth/${provider}/callback/`,
			{ method: 'POST', body }
		);

		if ('error' in result) {
			return { error: (result as { error: string }).error };
		}

		const data = result as OAuthCallbackResponse;

		// Set auth token as HttpOnly cookie
		cookies.set('auth_token', data.token, {
			path: '/',
			httpOnly: true,
			secure: url.protocol === 'https:',
			sameSite: 'lax',
			maxAge: 60 * 60 * 24 * 7, // 7 days
		});

		// Redirect based on user state
		if (data.user.needsNickname) {
			redirect(303, '/auth/nickname');
		}
		if (data.user.needsEmailVerification) {
			redirect(303, '/auth/verify-email');
		}

		redirect(303, '/');
	} catch (err) {
		// Check if it's a redirect (thrown by SvelteKit's redirect())
		if (err && typeof err === 'object' && 'status' in err) {
			throw err;
		}
		return { error: '로그인 처리 중 오류가 발생했습니다.' };
	}
};
