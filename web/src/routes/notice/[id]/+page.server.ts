import type { PageServerLoad } from './$types';
import { redirect } from '@sveltejs/kit';
import { apiFetch } from '$lib/api';
import type { NoticeDetailResponse } from '../notices';

export const load: PageServerLoad = async ({ params, locals }) => {
	const numeric = /^\d+$/.test(params.id);
	const resp = numeric
		? await apiFetch<NoticeDetailResponse>(`/notices/${Number(params.id)}/`, { authToken: locals.authToken })
		: await apiFetch<NoticeDetailResponse>(`/notices/by-slug/${encodeURIComponent(params.id)}/`, { authToken: locals.authToken });

	const canonicalPath = resp.notice.href ?? `/notice/${resp.notice.id}`;
	if (`/notice/${params.id}` !== canonicalPath) {
		redirect(301, canonicalPath);
	}

	return { notice: resp.notice, adjacent: resp.adjacent, event: resp.event };
};
