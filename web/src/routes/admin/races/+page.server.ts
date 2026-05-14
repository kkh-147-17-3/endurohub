import { adminApiFetch, type AdminRaceListResponse } from '$lib/admin-api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ url }) => {
	const q = url.searchParams.get('q') || '';
	const page = Math.max(1, parseInt(url.searchParams.get('page') || '1', 10) || 1);
	const data = await adminApiFetch<AdminRaceListResponse>('/admin/races/', {}, {
		q,
		page,
		per_page: 50,
	});
	return {
		races: data.races,
		total: data.total,
		page: data.page,
		perPage: data.perPage,
		q,
	};
};
