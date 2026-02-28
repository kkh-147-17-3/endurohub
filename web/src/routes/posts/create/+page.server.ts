import type { PageServerLoad, Actions } from './$types';
import { apiFetch, isApiError } from '$lib/api';
import { fail, redirect } from '@sveltejs/kit';
import type { PostRacesResponse, PostCreateResponse, ApiErrors } from '$lib/types';

export const load: PageServerLoad = async () => {
	const data = await apiFetch<PostRacesResponse>('/posts/races/');
	return data;
};

export const actions: Actions = {
	default: async ({ request, locals }) => {
		const formData = await request.formData();
		const clientIp = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || '';

		// Build a new FormData to forward to Django API
		const apiFormData = new FormData();
		apiFormData.append('nickname', (formData.get('nickname') as string) || '');
		apiFormData.append('title', formData.get('title') as string);
		apiFormData.append('content', formData.get('content') as string);
		apiFormData.append('password', (formData.get('password') as string) || '');
		const category = formData.get('category') as string;
		if (category) apiFormData.append('category', category);

		// Race IDs (repeated key for DRF ListField)
		const raceIds = formData.getAll('race_ids');
		raceIds.forEach((id) => {
			apiFormData.append('race_ids', id as string);
		});

		// Image files (repeated key for DRF getlist)
		const images = formData.getAll('images');
		images.forEach((file) => {
			if (file instanceof File && file.size > 0) {
				apiFormData.append('images', file);
			}
		});

		const result = await apiFetch<PostCreateResponse | ApiErrors>(
			'/posts/',
			{ method: 'POST', body: apiFormData, clientIp, authToken: locals.authToken }
		);

		if (isApiError(result)) return fail(400, { errors: result.errors });

		const created = result as PostCreateResponse;
		redirect(303, `/posts/${created.post.id}`);
	}
};
