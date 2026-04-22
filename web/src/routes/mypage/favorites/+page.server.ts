import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import { redirect } from '@sveltejs/kit';
import type { PaginatedResponse, Race } from '$lib/types';

export const load: PageServerLoad = async ({ url, locals }) => {
	if (!locals.authToken) {
		redirect(303, '/auth/login?next=/mypage/favorites');
	}

	const params: Record<string, string> = {};
	const page = url.searchParams.get('page');
	if (page) params.page = page;

	const data = await apiFetch<PaginatedResponse<Race>>(
		'/me/favorites/races/',
		{ authToken: locals.authToken },
		params
	);

	return { ...data };
};
