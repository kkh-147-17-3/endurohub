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

export const POST: RequestHandler = async ({ params, request, cookies }) => {
	requireAdmin(cookies);
	// Forward multipart body as-is.
	const incoming = await request.formData();
	const res = await fetch(`${apiBase()}/admin/races/${params.slug}/images/`, {
		method: 'POST',
		headers: {
			'Authorization': `Bearer ${ADMIN_SECRET}`,
			'Accept': 'application/json',
		},
		body: incoming,
	});
	const data = await res.json();
	return json(data, { status: res.status });
};

export const DELETE: RequestHandler = async ({ params, url, cookies }) => {
	requireAdmin(cookies);
	const kind = url.searchParams.get('kind') || '';
	const path = url.searchParams.get('path') || '';
	const target = `${apiBase()}/admin/races/${params.slug}/images/?kind=${encodeURIComponent(kind)}&path=${encodeURIComponent(path)}`;
	const res = await fetch(target, {
		method: 'DELETE',
		headers: {
			'Authorization': `Bearer ${ADMIN_SECRET}`,
			'Accept': 'application/json',
		},
	});
	const data = await res.json();
	return json(data, { status: res.status });
};

export const PUT: RequestHandler = async ({ params, request, cookies }) => {
	requireAdmin(cookies);
	const body = await request.text();
	const res = await fetch(`${apiBase()}/admin/races/${params.slug}/images/`, {
		method: 'PUT',
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
