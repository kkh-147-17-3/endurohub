import { ADMIN_SECRET } from '$lib/env';
import { apiFetch, type FetchOptions } from '$lib/api';

/**
 * Server-side admin API fetch. Sends the bearer token to Django's /api/v1/admin/* endpoints.
 * Use only in +page.server.ts / +server.ts — never expose ADMIN_SECRET to the browser.
 */
export async function adminApiFetch<T>(
	path: string,
	options: Omit<FetchOptions, 'authToken'> = {},
	params?: Parameters<typeof apiFetch>[2]
): Promise<T> {
	return apiFetch<T>(path, { ...options, authToken: ADMIN_SECRET }, params);
}

export interface AdminRaceListItem {
	id: number;
	slug: string;
	title: string;
	sport: string;
	sportLabel: string;
	raceDate: string | null;
	region: string | null;
	location: string | null;
	imageSrcThumb: string | null;
	isVerified: boolean;
}

export interface AdminRaceListResponse {
	races: AdminRaceListItem[];
	total: number;
	page: number;
	perPage: number;
}

export interface AdminImageItem {
	path: string;
	url: string;
}

export interface AdminImagesResponse {
	images: AdminImageItem[];
}
