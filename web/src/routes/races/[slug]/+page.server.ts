import type { PageServerLoad, Actions } from './$types';
import { apiFetch, isApiError } from '$lib/api';
import { fail, redirect } from '@sveltejs/kit';
import type { RaceDetailResponse, ReviewCreateResponse, ApiErrors } from '$lib/types';

export const load: PageServerLoad = async ({ params, request }) => {
	const clientIp = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || '';
	const data = await apiFetch<RaceDetailResponse>(`/races/${params.slug}/`, { clientIp });

	// ID로 접근한 경우 slug URL로 301 리다이렉트 (SEO)
	if (/^\d+$/.test(params.slug) && data.race?.slug) {
		redirect(301, `/races/${data.race.slug}`);
	}

	return data;
};

export const actions: Actions = {
	review: async ({ params, request }) => {
		const formData = await request.formData();
		const clientIp = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || '';

		const body = {
			rating: Number(formData.get('rating')),
			comment: formData.get('comment') as string,
			nickname: (formData.get('nickname') as string) || '익명',
		};

		const result = await apiFetch<ReviewCreateResponse | ApiErrors>(
			`/races/${params.slug}/reviews/`,
			{ method: 'POST', body, clientIp }
		);

		if (isApiError(result)) {
			return fail(400, { errors: result.errors });
		}

		return { success: true, message: result.message };
	}
};
