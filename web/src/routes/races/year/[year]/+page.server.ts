import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import type { RaceYearlyResponse } from '$lib/types';

export const load: PageServerLoad = async ({ params }) => {
	const year = parseInt(params.year);
	const data = await apiFetch<RaceYearlyResponse>(`/races/year/${year}/`);
	return data;
};
