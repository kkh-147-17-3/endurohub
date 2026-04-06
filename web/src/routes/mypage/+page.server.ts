import type { Actions, PageServerLoad } from './$types';
import { apiFetch, isApiError } from '$lib/api';
import { fail, redirect } from '@sveltejs/kit';
import type { ApiErrors, MeResponse, ProfileUpdateResponse } from '$lib/types';

function parseCheckboxValue(value: FormDataEntryValue | null): boolean {
	return value === 'on' || value === 'true' || value === '1';
}

export const load: PageServerLoad = async ({ locals }) => {
	if (!locals.authToken) {
		redirect(303, '/auth/login');
	}

	const result = await apiFetch<MeResponse>('/auth/me/', {
		authToken: locals.authToken
	});

	if (!result.user) {
		redirect(303, '/auth/login');
	}

	return {
		user: result.user
	};
};

export const actions: Actions = {
	default: async ({ request, locals }) => {
		if (!locals.authToken) {
			redirect(303, '/auth/login');
		}

		const formData = await request.formData();
		const emailUpdatesOptIn = parseCheckboxValue(formData.get('email_updates_opt_in'));

		const result = await apiFetch<ProfileUpdateResponse | ApiErrors>('/auth/preferences/', {
			method: 'POST',
			body: { email_updates_opt_in: emailUpdatesOptIn },
			authToken: locals.authToken
		});

		if (isApiError(result)) {
			return fail(400, { errors: result.errors, emailUpdatesOptIn });
		}

		return {
			successMessage: result.message,
			emailUpdatesOptIn: result.user.emailUpdatesOptIn,
			user: result.user
		};
	}
};
