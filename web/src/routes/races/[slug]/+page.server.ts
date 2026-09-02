import type { PageServerLoad, Actions } from './$types';
import { apiFetch, isApiError } from '$lib/api';
import { fail, redirect } from '@sveltejs/kit';
import type { RaceDetailResponse, ReviewCreateResponse, ApiErrors } from '$lib/types';

export const load: PageServerLoad = async ({ params, locals }) => {
	const data = await apiFetch<RaceDetailResponse>(`/races/${params.slug}/`, {
		clientIp: locals.clientIp,
		authToken: locals.authToken || undefined,
		sessionId: locals.sessionId || undefined,
		userAgent: locals.userAgent || undefined,
	});

	// ID로 접근한 경우 slug URL로 301 리다이렉트 (SEO)
	if (/^\d+$/.test(params.slug) && data.race?.slug) {
		redirect(301, `/races/${encodeURIComponent(data.race.slug)}`);
	}

	return data;
};

export const actions: Actions = {
	review: async ({ params, request, locals }) => {
		if (!locals.authToken) {
			return fail(401, { errors: { review: ['로그인 후 리뷰를 작성해주세요.'] } });
		}
		const formData = await request.formData();

		const recommendationTags = formData.getAll('recommendation_tags') as string[];
		const operationSat = formData.get('operation_satisfaction');

		const body: Record<string, unknown> = {
			rating: Number(formData.get('rating')),
			comment: formData.get('comment') as string,
			completion_time: (formData.get('completion_time') as string) || null,
			course_difficulty: (formData.get('course_difficulty') as string) || null,
			operation_satisfaction: operationSat ? Number(operationSat) : null,
			recommendation_tags: recommendationTags.length > 0 ? recommendationTags : null,
		};

		const result = await apiFetch<ReviewCreateResponse | ApiErrors>(
			`/races/${params.slug}/reviews/`,
			{
				method: 'POST',
				body,
				clientIp: locals.clientIp,
				authToken: locals.authToken,
				sessionId: locals.sessionId,
				userAgent: locals.userAgent,
			}
		);

		if (isApiError(result)) {
			return fail(400, { errors: result.errors });
		}
		if (!('success' in result) || !result.success) {
			return fail(400, { errors: { review: ['리뷰를 등록하지 못했습니다. 다시 시도해주세요.'] } });
		}

		return { success: true, message: result.message };
	}
};
