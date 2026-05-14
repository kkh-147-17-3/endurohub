import { error } from '@sveltejs/kit';
import { adminApiFetch } from '$lib/admin-api';
import type { Race } from '$lib/types';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params }) => {
	try {
		const race = await adminApiFetch<Race>(`/admin/races/${params.slug}/`);
		return { race };
	} catch (e) {
		throw error(404, '대회를 찾을 수 없습니다.');
	}
};
