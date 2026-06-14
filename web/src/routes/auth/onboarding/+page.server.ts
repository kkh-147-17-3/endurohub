import type { PageServerLoad, Actions } from './$types';
import { apiFetch, isApiError } from '$lib/api';
import { fail, redirect } from '@sveltejs/kit';
import type {
	AuthUser,
	MeResponse,
	EmailVerifyResponse,
	PendingEmailVerifyResponse,
	NicknameSetupResponse,
	OnboardingResponse,
	RaceRecordListResponse,
	ApiErrors,
} from '$lib/types';

function parseCheckboxValue(value: FormDataEntryValue | null): boolean {
	return value === 'on' || value === 'true' || value === '1';
}

/** A user has finished onboarding once email is verified, nickname is set, and preferences saved. */
function isFullyOnboarded(user: AuthUser | null): boolean {
	return !!user && user.emailVerified && !!user.nickname && user.onboardingCompleted;
}

export const load: PageServerLoad = async ({ locals, cookies }) => {
	const hasPendingSocialLogin = !!cookies.get('pending_social_token');

	let user: AuthUser | null = null;
	if (locals.authToken) {
		try {
			const me = await apiFetch<MeResponse>('/auth/me/', { authToken: locals.authToken });
			user = me.user;
		} catch {
			user = null;
		}
		if (!user) {
			cookies.delete('auth_token', { path: '/' });
			locals.authToken = '';
		}
	}

	if (!user && !hasPendingSocialLogin) {
		redirect(303, '/auth/login?next=/auth/onboarding');
	}

	if (isFullyOnboarded(user)) {
		redirect(303, '/');
	}

	let records: RaceRecordListResponse['records'] = [];
	if (user) {
		try {
			const res = await apiFetch<RaceRecordListResponse>('/me/records/', {
				authToken: locals.authToken,
			});
			records = res.records ?? [];
		} catch {
			records = [];
		}
	}

	// Decide where the flow should open based on what's still missing.
	let startStep = 0; // 0 EMAIL · 1 NICKNAME · 2 SPORT · 3 REGION · 4 RECORDS
	if (user) {
		if (!user.emailVerified) startStep = 0;
		else if (!user.nickname) startStep = 1;
		else startStep = 2;
	}

	return { user, hasPendingSocialLogin, records, startStep };
};

export const actions: Actions = {
	// STEP 01 — send a verification code to the entered email.
	sendEmail: async ({ request, locals, cookies }) => {
		const pendingToken = cookies.get('pending_social_token') || '';
		if (!locals.authToken && !pendingToken) {
			redirect(303, '/auth/login');
		}

		const formData = await request.formData();
		const email = ((formData.get('email') as string) || '').trim();

		const result = locals.authToken
			? await apiFetch<{ success: boolean; message: string } | ApiErrors | { error: string }>(
					'/auth/email/send/',
					{ method: 'POST', body: { email }, authToken: locals.authToken }
				)
			: await apiFetch<{ success: boolean; message: string } | ApiErrors | { error: string }>(
					'/auth/pending/email/send/',
					{ method: 'POST', body: { email, pending_token: pendingToken } }
				);

		if (isApiError(result)) {
			return fail(400, { action: 'sendEmail', sendErrors: result.errors });
		}
		if ('error' in result) {
			return fail(400, { action: 'sendEmail', sendErrors: { email: [result.error] } });
		}
		return { action: 'sendEmail', sendMessage: result.message };
	},

	// STEP 01 — verify the 6-digit code. On the pending-social path this also creates the account.
	verifyEmail: async ({ request, locals, cookies, url }) => {
		const pendingToken = cookies.get('pending_social_token') || '';
		if (!locals.authToken && !pendingToken) {
			redirect(303, '/auth/login');
		}

		const formData = await request.formData();
		const code = ((formData.get('code') as string) || '').trim();
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
						body: { code, pending_token: pendingToken, email_updates_opt_in: emailUpdatesOptIn },
					}
				);

		if (isApiError(result)) {
			return fail(400, { action: 'verifyEmail', verifyErrors: result.errors });
		}
		if ('error' in result) {
			return fail(400, { action: 'verifyEmail', verifyErrors: { code: [result.error] } });
		}

		// Pending-social verification returns a fresh token — persist it as the auth cookie.
		if ('token' in result) {
			cookies.set('auth_token', result.token, {
				path: '/',
				httpOnly: true,
				secure: url.protocol === 'https:',
				sameSite: 'lax',
				maxAge: 60 * 60 * 24 * 7,
			});
			cookies.delete('pending_social_token', { path: '/' });
		}

		return { action: 'verifyEmail', user: result.user };
	},

	// STEP 02 — set the community nickname.
	setNickname: async ({ request, locals }) => {
		if (!locals.authToken) {
			redirect(303, '/auth/login');
		}

		const formData = await request.formData();
		const nickname = ((formData.get('nickname') as string) || '').trim();

		const result = await apiFetch<NicknameSetupResponse | ApiErrors>('/auth/nickname/', {
			method: 'POST',
			body: { nickname },
			authToken: locals.authToken,
		});

		if (isApiError(result)) {
			return fail(400, { action: 'setNickname', nicknameErrors: result.errors });
		}
		return { action: 'setNickname', user: result.user };
	},

	// STEPS 03–05 — persist sports/regions, save the collected records, and finish onboarding.
	complete: async ({ request, locals, cookies, url }) => {
		if (!locals.authToken) {
			redirect(303, '/auth/login');
		}

		const formData = await request.formData();
		const sportsRaw = (formData.get('preferred_sports') as string) || '';
		const regionsRaw = (formData.get('preferred_regions') as string) || '';
		const recordsRaw = (formData.get('records') as string) || '';

		const preferredSports = sportsRaw ? sportsRaw.split(',').filter(Boolean) : [];
		const preferredRegions = regionsRaw ? regionsRaw.split(',').filter(Boolean) : [];

		let records: unknown[] = [];
		if (recordsRaw) {
			try {
				const parsed = JSON.parse(recordsRaw);
				if (Array.isArray(parsed)) records = parsed;
			} catch {
				records = [];
			}
		}

		// Save race records first (best-effort — a record failure must not block onboarding).
		if (records.length > 0) {
			try {
				await apiFetch<RaceRecordListResponse | ApiErrors>('/me/records/', {
					method: 'POST',
					body: records,
					authToken: locals.authToken,
				});
			} catch {
				// Ignore — onboarding can complete even if record persistence hiccups.
			}
		}

		const result = await apiFetch<OnboardingResponse | ApiErrors>('/auth/onboarding/', {
			method: 'POST',
			body: { preferred_sports: preferredSports, preferred_regions: preferredRegions },
			authToken: locals.authToken,
		});

		if (isApiError(result)) {
			return fail(400, { action: 'complete', errors: result.errors });
		}

		// Bridge a one-shot sign_up event to the client (fired by the layout after
		// the client navigates away from onboarding).
		cookies.set('eh_evt', 'signup', {
			path: '/',
			httpOnly: false,
			secure: url.protocol === 'https:',
			sameSite: 'lax',
			maxAge: 60,
		});

		return { action: 'complete', user: result.user, done: true };
	},
};
