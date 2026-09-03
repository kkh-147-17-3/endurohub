import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';

export interface EventCondition {
	completed: boolean;
	count: number;
}

export interface CoffeeEventStatus {
	period: { startsAt: string; endsAt: string };
	review: EventCondition;
	record: EventCondition;
	completed: boolean;
}

export const load: PageServerLoad = async ({ locals }) => {
	// This custom page still belongs to the notice system, so loading it records
	// a view just like the numeric /notice/[id] detail route does.
	await apiFetch('/notices/by-slug/coffee-coupon-event/');

	if (!locals.authToken) return { participation: null };

	try {
		const participation = await apiFetch<CoffeeEventStatus>(
			'/rewards/coffee-coupon-event/status/',
			{ authToken: locals.authToken }
		);
		return { participation };
	} catch {
		return { participation: null };
	}
};
