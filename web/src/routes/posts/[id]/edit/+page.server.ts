import type { PageServerLoad, Actions } from './$types';
import { apiFetch, isApiError } from '$lib/api';
import { error, fail, redirect } from '@sveltejs/kit';
import type { VerifyPasswordResponse, PostUpdateResponse, PostRacesResponse, ApiErrors } from '$lib/types';

export const load: PageServerLoad = async ({ params, url }) => {
	const editToken = url.searchParams.get('token');
	if (!editToken) {
		redirect(303, `/posts/${params.id}`);
	}

	// Fetch post detail and available races in parallel
	const [postData, racesData] = await Promise.all([
		apiFetch<{ post: import('$lib/types').Post }>(`/posts/${params.id}/`),
		apiFetch<PostRacesResponse>('/posts/races/')
	]);

	return {
		post: postData.post,
		races: racesData.races,
		editToken
	};
};

export const actions: Actions = {
	default: async ({ params, request, locals }) => {
		const formData = await request.formData();
		const editToken = formData.get('edit_token') as string;

		// Build FormData to forward to Django API
		const apiFormData = new FormData();
		apiFormData.append('nickname', (formData.get('nickname') as string) || '');
		apiFormData.append('title', formData.get('title') as string);
		apiFormData.append('content', formData.get('content') as string);
		apiFormData.append('edit_token', editToken);
		const category = formData.get('category') as string;
		if (category) apiFormData.append('category', category);

		// Race IDs (repeated key for DRF ListField)
		const raceIds = formData.getAll('race_ids');
		raceIds.forEach((id) => {
			apiFormData.append('race_ids', id as string);
		});

		// Existing images (repeated key for DRF ListField)
		const existingImages = formData.getAll('existing_images');
		existingImages.forEach((path) => {
			apiFormData.append('existing_images', path as string);
		});

		// New image files (repeated key for DRF getlist)
		const images = formData.getAll('images');
		images.forEach((file) => {
			if (file instanceof File && file.size > 0) {
				apiFormData.append('images', file);
			}
		});

		const result = await apiFetch<PostUpdateResponse | ApiErrors>(
			`/posts/${params.id}/`,
			{ method: 'PUT', body: apiFormData, authToken: locals.authToken }
		);

		if (isApiError(result)) return fail(400, { errors: result.errors });

		redirect(303, `/posts/${params.id}`);
	}
};
