import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import type { HomeResponse } from '$lib/types';

export const load: PageServerLoad = async () => {
	const data = await apiFetch<HomeResponse>('/home/');
	return data;
};
