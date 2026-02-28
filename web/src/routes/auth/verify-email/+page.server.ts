import type { PageServerLoad, Actions } from './$types';
import { apiFetch, isApiError } from '$lib/api';
import { fail, redirect } from '@sveltejs/kit';
import type { EmailVerifyResponse, ApiErrors } from '$lib/types';

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
		const code = formData.get('code') as string;

		const result = await apiFetch<EmailVerifyResponse | ApiErrors>(
			'/auth/email/verify/',
			{
				method: 'POST',
				body: { code },
				authToken: locals.authToken,
			}
		);

		if (isApiError(result)) {
			return fail(400, { errors: result.errors });
		}

		redirect(303, '/');
	}
};
