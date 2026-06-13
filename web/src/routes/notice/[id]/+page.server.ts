import type { PageServerLoad } from './$types';
import { error } from '@sveltejs/kit';
import { apiFetch } from '$lib/api';
import type { NoticeDetailResponse } from '../notices';

export const load: PageServerLoad = async ({ params }) => {
	const id = parseInt(params.id, 10);
	if (isNaN(id)) error(404, { message: '공지사항을 찾을 수 없습니다.' });

	const resp = await apiFetch<NoticeDetailResponse>(`/notices/${id}/`);

	return { notice: resp.notice, adjacent: resp.adjacent };
};
