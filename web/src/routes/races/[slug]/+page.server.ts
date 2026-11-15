import type { PageServerLoad, Actions } from './$types';
import { apiFetch, isApiError } from '$lib/api';
import { error, fail, redirect } from '@sveltejs/kit';
import { raceCanonicalPath } from '$lib/seo/race-url';
import type {
	ApiErrors,
	RaceDetailResponse,
	ReviewCreateResponse,
	ReviewRaceRecordPayload,
} from '$lib/types';

export const load: PageServerLoad = async ({ params, locals, url }) => {
	const data = await apiFetch<RaceDetailResponse>(`/races/${params.slug}/`, {
		clientIp: locals.clientIp,
		authToken: locals.authToken || undefined,
		sessionId: locals.sessionId || undefined,
		userAgent: locals.userAgent || undefined,
	});
	if (!data.race || typeof data.race.slug !== 'string' || !data.race.slug) {
		// A temporary upstream error must not invent a canonical destination or
		// look like a deleted race to a crawler.
		error(502, { message: '대회 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.' });
	}

	// Resolve identity first, then use the stored slug for every URL signal.
	// Comparing the encoded pathname also folds lowercase/unreserved percent
	// escapes into the same address used by the sitemap and structured data.
	const canonicalRacePath = raceCanonicalPath(data.race.slug);
	if (url.pathname !== canonicalRacePath) {
		redirect(301, canonicalRacePath);
	}

	return { ...data, canonicalRacePath };
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
			is_public: formData.get('is_public') === 'true',
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
