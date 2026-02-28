import type { Actions } from './$types';
import { redirect } from '@sveltejs/kit';

export const actions: Actions = {
	default: async ({ cookies }) => {
		cookies.delete('auth_token', { path: '/' });
		redirect(303, '/');
	}
};
