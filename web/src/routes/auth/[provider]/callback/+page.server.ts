import type { PageServerLoad } from './$types';
import { redirect } from '@sveltejs/kit';
import { apiFetch } from '$lib/api';
import { APP_URL } from '$lib/env';
import type { OAuthCallbackResponse, OAuthPendingResponse } from '$lib/types';

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

	const appUrl = APP_URL.replace(/\/$/, '') || url.origin;
	const redirectUri = `${appUrl}/auth/${provider}/callback`;

	try {
		const body: Record<string, string> = { code, redirect_uri: redirectUri };
		if (state) {
			body.state = state;
		}

		const result = await apiFetch<OAuthCallbackResponse | OAuthPendingResponse | { error: string }>(
			`/auth/${provider}/callback/`,
			{ method: 'POST', body }
		);

		if ('error' in result) {
			return { error: (result as { error: string }).error };
		}

		if ('pendingToken' in result) {
			// Parked login — no session until the code checks out, including any
			// session this browser was still carrying.
			cookies.delete('auth_token', { path: '/' });
			cookies.set('pending_social_token', result.pendingToken, {
				path: '/',
				httpOnly: true,
				secure: url.protocol === 'https:',
				sameSite: 'lax',
				maxAge: 60 * 30, // 30 minutes
			});
			// Only a prefill for the verification step — the code decides, not the provider.
			if (result.email) {
				cookies.set('pending_social_email', result.email, {
					path: '/',
					httpOnly: true,
					secure: url.protocol === 'https:',
					sameSite: 'lax',
					maxAge: 60 * 30,
				});
			} else {
				cookies.delete('pending_social_email', { path: '/' });
			}
			redirect(303, '/auth/onboarding');
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
		cookies.delete('pending_social_token', { path: '/' });
		cookies.delete('pending_social_email', { path: '/' });

		// Bridge a one-shot login event to the client (redirects happen server-side,
		// so the browser can't fire it directly). The layout reads + clears this.
		cookies.set('eh_evt', `login:${provider}`, {
			path: '/',
			httpOnly: false,
			secure: url.protocol === 'https:',
			sameSite: 'lax',
			maxAge: 60,
		});

		// Any incomplete signup state funnels into the unified onboarding flow.
		if (
			data.user.needsNickname ||
			data.user.needsEmailVerification ||
			data.user.needsOnboarding ||
			!data.user.emailVerified
		) {
			redirect(303, '/auth/onboarding');
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
