import type { PageServerLoad, Actions } from './$types';
import { apiFetch, isApiError } from '$lib/api';
import { fail, redirect } from '@sveltejs/kit';
import type {
	PostDetailResponse, ApiErrors,
	CommentCreateResponse, CommentUpdateResponse, CommentDeleteResponse,
	LikeToggleResponse, PostDeleteResponse, VerifyPasswordResponse
} from '$lib/types';

export const load: PageServerLoad = async ({ params, request, locals }) => {
	const clientIp = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || '';
	const data = await apiFetch<PostDetailResponse>(`/posts/${params.id}/`, {
		clientIp,
		authToken: locals.authToken,
	});
	return data;
};

export const actions: Actions = {
	comment: async ({ params, request, locals }) => {
		const formData = await request.formData();
		const clientIp = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || '';
		const body = {
			nickname: (formData.get('nickname') as string) || '익명',
			content: formData.get('content') as string,
			password: (formData.get('password') as string) || '',
			parent_id: formData.get('parent_id') ? Number(formData.get('parent_id')) : null,
		};

		const result = await apiFetch<CommentCreateResponse | ApiErrors>(
			`/posts/${params.id}/comments/`,
			{ method: 'POST', body, clientIp, authToken: locals.authToken }
		);

		if (isApiError(result)) return fail(400, { errors: result.errors });
		return { success: true, comment: (result as CommentCreateResponse).comment };
	},

	updateComment: async ({ params, request, locals }) => {
		const formData = await request.formData();
		const commentId = formData.get('comment_id') as string;
		const body = {
			content: formData.get('content') as string,
			password: (formData.get('password') as string) || '',
		};

		const result = await apiFetch<CommentUpdateResponse | ApiErrors>(
			`/posts/${params.id}/comments/${commentId}/`,
			{ method: 'PUT', body, authToken: locals.authToken }
		);

		if (isApiError(result)) return fail(400, { errors: result.errors });
		return { success: true, comment: (result as CommentUpdateResponse).comment };
	},

	deleteComment: async ({ params, request, locals }) => {
		const formData = await request.formData();
		const commentId = formData.get('comment_id') as string;
		const body = { password: (formData.get('password') as string) || '' };

		const result = await apiFetch<CommentDeleteResponse | ApiErrors>(
			`/posts/${params.id}/comments/${commentId}/`,
			{ method: 'DELETE', body, authToken: locals.authToken }
		);

		if (isApiError(result)) return fail(400, { errors: result.errors });
		return { success: true };
	},

	like: async ({ params, request }) => {
		const clientIp = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || '';

		const result = await apiFetch<LikeToggleResponse>(
			`/posts/${params.id}/like/`,
			{ method: 'POST', clientIp }
		);

		return result;
	},

	delete: async ({ params, request, locals }) => {
		const formData = await request.formData();
		const body = { password: (formData.get('password') as string) || '' };

		const result = await apiFetch<PostDeleteResponse | ApiErrors>(
			`/posts/${params.id}/`,
			{ method: 'DELETE', body, authToken: locals.authToken }
		);

		if (isApiError(result)) return fail(400, { errors: result.errors });
		redirect(303, '/posts');
	},

	verifyEdit: async ({ params, request, locals }) => {
		const formData = await request.formData();
		const body = { password: (formData.get('password') as string) || '' };

		const result = await apiFetch<VerifyPasswordResponse | ApiErrors>(
			`/posts/${params.id}/verify-password/`,
			{ method: 'POST', body, authToken: locals.authToken }
		);

		if (isApiError(result)) return fail(400, { errors: result.errors });

		const verified = result as VerifyPasswordResponse;
		redirect(303, `/posts/${params.id}/edit?token=${verified.editToken}`);
	}
};
