import type { PageServerLoad, Actions } from './$types';
import { apiFetch, isApiError } from '$lib/api';
import { fail, redirect } from '@sveltejs/kit';
import type {
	ApiErrors,
	RaceDetailResponse,
	ReviewCreateResponse,
	ReviewRaceRecordPayload,
} from '$lib/types';

export const load: PageServerLoad = async ({ params, locals }) => {
	const data = await apiFetch<RaceDetailResponse>(`/races/${params.slug}/`, {
		clientIp: locals.clientIp,
		authToken: locals.authToken || undefined,
		sessionId: locals.sessionId || undefined,
		userAgent: locals.userAgent || undefined,
	});

	// 숫자 ID, 이중 인코딩 등 canonical slug가 아닌 별칭 URL을 하나로 통합한다.
	if (data.race?.slug && params.slug !== data.race.slug) {
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
		const raceRecord: ReviewRaceRecordPayload = {
			course_code: String(formData.get('course_code') ?? '').trim(),
			hours: Number(formData.get('hours') ?? 0),
			minutes: Number(formData.get('minutes') ?? 0),
			seconds: Number(formData.get('seconds') ?? 0),
		};

		const body: Record<string, unknown> = {
			rating: Number(formData.get('rating')),
			comment: formData.get('comment') as string,
			course_difficulty: (formData.get('course_difficulty') as string) || null,
			operation_satisfaction: operationSat ? Number(operationSat) : null,
			recommendation_tags: recommendationTags.length > 0 ? recommendationTags : null,
			race_record: raceRecord,
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

		return {
			success: true,
			message: result.message || '리뷰와 참가 기록이 등록되었습니다.',
		};
	}
};
