import { error, json } from '@sveltejs/kit';
import { ADMIN_SECRET, API_URL_INTERNAL } from '$lib/env';
import type { RequestHandler } from './$types';

function requireAdmin(cookies: { get(name: string): string | undefined }) {
	const token = cookies.get('admin_token') || '';
	if (!ADMIN_SECRET || token !== ADMIN_SECRET) {
		throw error(403, 'Forbidden');
	}
}

const apiBase = () => `${API_URL_INTERNAL.replace(/\/$/, '')}/api/v1`;

export const PATCH: RequestHandler = async ({ params, request, cookies }) => {
	requireAdmin(cookies);
	const body = await request.text();
	const res = await fetch(`${apiBase()}/admin/races/${params.slug}/`, {
		method: 'PATCH',
		headers: {
			'Authorization': `Bearer ${ADMIN_SECRET}`,
			'Content-Type': 'application/json',
			'Accept': 'application/json',
		},
		body,
	});
	const data = await res.json();
	return json(data, { status: res.status });
};
