import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

// /posts is now the canonical community feed — redirect there,
// preserving all query params (page, category, search, sort).
export const load: PageServerLoad = async ({ url }) => {
	const dest = '/community' + (url.search || '');
	redirect(301, dest);
};
