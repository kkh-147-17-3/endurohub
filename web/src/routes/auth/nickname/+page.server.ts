import type { PageServerLoad, Actions } from './$types';
import { apiFetch, isApiError } from '$lib/api';
import { fail, redirect } from '@sveltejs/kit';
import type { NicknameSetupResponse, ApiErrors } from '$lib/types';

export const load: PageServerLoad = async ({ locals }) => {
	if (!locals.authToken) {
		redirect(303, '/auth/login');
	}
	return {};
};

export const actions: Actions = {
	default: async ({ request, locals }) => {
		if (!locals.authToken) {
			redirect(303, '/auth/login');
		}

		const formData = await request.formData();
		const nickname = formData.get('nickname') as string;

		const result = await apiFetch<NicknameSetupResponse | ApiErrors>(
			'/auth/nickname/',
			{
				method: 'POST',
				body: { nickname },
				authToken: locals.authToken,
			}
		);

		if (isApiError(result)) {
			return fail(400, { errors: result.errors });
		}

		const data = result as NicknameSetupResponse;
		if (data.user.needsEmailVerification) {
			redirect(303, '/auth/verify-email');
		}

		redirect(303, '/');
	}
};
