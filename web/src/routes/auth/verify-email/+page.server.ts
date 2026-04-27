import type { PageServerLoad, Actions } from './$types';
import { apiFetch, isApiError } from '$lib/api';
import { fail, redirect } from '@sveltejs/kit';
import type {
	EmailVerifyResponse,
	PendingEmailVerifyResponse,
	ApiErrors,
	MeResponse,
} from '$lib/types';

function parseCheckboxValue(value: FormDataEntryValue | null): boolean {
	return value === 'on' || value === 'true' || value === '1';
}

export const load: PageServerLoad = async ({ locals, cookies }) => {
	const hasPendingSocialLogin = !!cookies.get('pending_social_token');

	let tokenIsValid = false;
	if (locals.authToken) {
		try {
			const me = await apiFetch<MeResponse>('/auth/me/', { authToken: locals.authToken });
			tokenIsValid = !!me.user;
		} catch {
			tokenIsValid = false;
		}
		if (!tokenIsValid) {
			cookies.delete('auth_token', { path: '/' });
			locals.authToken = '';
		}
	}

	if (!tokenIsValid && !hasPendingSocialLogin) {
		redirect(303, '/auth/login?next=/auth/verify-email');
	}

	return { hasPendingSocialLogin };
};

export const actions: Actions = {
	send: async ({ request, locals, cookies }) => {
		const pendingSocialToken = cookies.get('pending_social_token') || '';
		if (!locals.authToken && !pendingSocialToken) {
			redirect(303, '/auth/login');
		}

		const formData = await request.formData();
		const email = (formData.get('email') as string) || '';
		const emailUpdatesOptIn = parseCheckboxValue(formData.get('email_updates_opt_in'));

		const result = locals.authToken
			? await apiFetch<{ success: boolean; message: string } | ApiErrors | { error: string }>(
				'/auth/email/send/',
				{
					method: 'POST',
					body: { email },
					authToken: locals.authToken,
				}
			)
			: await apiFetch<{ success: boolean; message: string } | ApiErrors | { error: string }>(
				'/auth/pending/email/send/',
				{
					method: 'POST',
					body: { email, pending_token: pendingSocialToken },
				}
			);

		if (isApiError(result)) {
			return fail(400, { sendErrors: result.errors, email, emailUpdatesOptIn });
		}
		if ('error' in result) {
			return fail(400, { sendErrors: { email: [result.error] }, email, emailUpdatesOptIn });
		}

		return {
			sendMessage: result.message,
			email,
			emailUpdatesOptIn,
		};
	},
	verify: async ({ request, locals, cookies, url }) => {
		const pendingSocialToken = cookies.get('pending_social_token') || '';
		if (!locals.authToken && !pendingSocialToken) {
			redirect(303, '/auth/login');
		}

		const formData = await request.formData();
		const code = formData.get('code') as string;
		const email = (formData.get('email') as string) || '';
		const emailUpdatesOptIn = parseCheckboxValue(formData.get('email_updates_opt_in'));

		const result = locals.authToken
			? await apiFetch<EmailVerifyResponse | ApiErrors | { error: string }>(
				'/auth/email/verify/',
				{
					method: 'POST',
					body: { code, email_updates_opt_in: emailUpdatesOptIn },
					authToken: locals.authToken,
				}
			)
			: await apiFetch<PendingEmailVerifyResponse | ApiErrors | { error: string }>(
				'/auth/pending/email/verify/',
				{
					method: 'POST',
					body: {
						code,
						pending_token: pendingSocialToken,
						email_updates_opt_in: emailUpdatesOptIn,
					},
				}
			);

		if (isApiError(result)) {
			return fail(400, { errors: result.errors, email, emailUpdatesOptIn });
		}
		if ('error' in result) {
			return fail(400, { errors: { code: [result.error] }, email, emailUpdatesOptIn });
		}

		if ('token' in result) {
			cookies.set('auth_token', result.token, {
				path: '/',
				httpOnly: true,
				secure: url.protocol === 'https:',
				sameSite: 'lax',
				maxAge: 60 * 60 * 24 * 7,
			});
			cookies.delete('pending_social_token', { path: '/' });

			if (result.user.needsNickname) {
				redirect(303, '/auth/nickname');
			}
			if (result.user.needsOnboarding) {
				redirect(303, '/auth/onboarding');
			}
		}

		// Check onboarding for authenticated user flow (non-pending)
		if ('user' in result && result.user.needsOnboarding) {
			redirect(303, '/auth/onboarding');
		}

		redirect(303, '/');
	}
};
