import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';
import { djangoAdminNextUrl } from '$lib/server/admin-login';

const LOGIN = '/admin/login';

/** Use locals.isAdmin from hooks — not `await parent()`, so guards are not stale under SvelteKit layout load caching. */
export const load: LayoutServerLoad = async ({ locals, url }) => {
	const path = url.pathname;

	if (path === LOGIN || path.startsWith(`${LOGIN}/`)) {
		if (locals.isAdmin) {
			redirect(303, djangoAdminNextUrl(url));
		}
	}

	if (!locals.isAdmin) {
		const nextPath = djangoAdminNextUrl(url);
		redirect(303, `/dj-admin/login/?next=${encodeURIComponent(nextPath)}`);
	}
	return {};
};
