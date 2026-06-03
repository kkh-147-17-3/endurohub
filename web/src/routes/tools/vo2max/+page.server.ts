import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import { pickRunningRecordPrefill } from '$lib/tools';
import type { RaceRecordListResponse } from '$lib/types';

// Prefill the tool with the user's most recent running/trail race record, when signed in.
export const load: PageServerLoad = async ({ locals }) => {
	if (!locals.authToken) return { prefill: null };
	try {
		const res = await apiFetch<RaceRecordListResponse>('/me/records/', {
			authToken: locals.authToken
		});
		return { prefill: pickRunningRecordPrefill(res.records ?? []) };
	} catch {
		return { prefill: null };
	}
};
