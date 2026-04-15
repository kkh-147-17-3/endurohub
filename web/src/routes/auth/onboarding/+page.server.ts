import type { PageServerLoad, Actions } from './$types';
import { apiFetch, isApiError } from '$lib/api';
import { fail, redirect } from '@sveltejs/kit';
import type { OnboardingResponse, ApiErrors } from '$lib/types';

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
		const sportsRaw = formData.get('preferred_sports') as string;
		const regionsRaw = formData.get('preferred_regions') as string;

		const preferredSports = sportsRaw ? sportsRaw.split(',').filter(Boolean) : [];
		const preferredRegions = regionsRaw ? regionsRaw.split(',').filter(Boolean) : [];

		const result = await apiFetch<OnboardingResponse | ApiErrors>(
			'/auth/onboarding/',
			{
				method: 'POST',
				body: {
					preferred_sports: preferredSports,
					preferred_regions: preferredRegions,
				},
				authToken: locals.authToken,
			}
		);

		if (isApiError(result)) {
			return fail(400, { errors: result.errors });
		}

		redirect(303, '/');
	}
};
