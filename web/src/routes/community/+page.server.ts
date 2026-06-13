import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import type { PostListResponse } from '$lib/types';

export const load: PageServerLoad = async ({ url }) => {
	const params: Record<string, string> = {};
	const page = url.searchParams.get('page');
	if (page) params.page = page;
	const search = url.searchParams.get('search');
	if (search) params.search = search;
	const category = url.searchParams.get('category');
	if (category) params.category = category;
	const sort = url.searchParams.get('sort');
	if (sort) params.sort = sort;

	const data = await apiFetch<PostListResponse>('/posts/', {}, params);
	return data;
};
