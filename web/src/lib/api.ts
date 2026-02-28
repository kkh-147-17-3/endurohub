import { API_URL_INTERNAL } from '$lib/env';
import { error } from '@sveltejs/kit';
import type { ApiErrors } from '$lib/types';

/**
 * Build the full API URL for server-side fetches.
 * Always uses the internal Docker network URL (e.g. http://api:8000).
 */
function buildUrl(path: string, params?: Record<string, string | string[] | number | null | undefined>): string {
	const base = API_URL_INTERNAL.replace(/\/$/, '');
	const url = new URL(`${base}/api/v1${path}`);

	if (params) {
		for (const [key, value] of Object.entries(params)) {
			if (value === null || value === undefined || value === '') continue;
			if (Array.isArray(value)) {
				for (const v of value) {
					url.searchParams.append(key, v);
				}
			} else {
				url.searchParams.set(key, String(value));
			}
		}
	}

	return url.toString();
}

export interface FetchOptions {
	method?: string;
	body?: unknown;
	headers?: Record<string, string>;
	clientIp?: string;
	authToken?: string;
}

/**
 * Server-side API fetch wrapper.
 * Use this in +page.server.ts load() functions and form actions.
 *
 * - Automatically uses the internal API URL
 * - Forwards X-Forwarded-For header for IP-based features
 * - Handles JSON parsing and error responses
 */
export async function apiFetch<T>(
	path: string,
	options: FetchOptions = {},
	params?: Record<string, string | string[] | number | null | undefined>
): Promise<T> {
	const url = buildUrl(path, params);
	const headers: Record<string, string> = {
		'Accept': 'application/json',
		...options.headers
	};

	if (options.clientIp) {
		headers['X-Forwarded-For'] = options.clientIp;
	}

	if (options.authToken) {
		headers['Authorization'] = `Bearer ${options.authToken}`;
	}

	const fetchOptions: RequestInit = {
		method: options.method || 'GET',
		headers
	};

	if (options.body !== undefined) {
		if (options.body instanceof FormData) {
			// Let the browser set Content-Type with boundary for multipart
			fetchOptions.body = options.body;
		} else {
			headers['Content-Type'] = 'application/json';
			fetchOptions.body = JSON.stringify(options.body);
		}
	}

	const response = await fetch(url, fetchOptions);

	if (!response.ok) {
		if (response.status === 404) {
			error(404, { message: 'Not found.' });
		}

		// Try to parse error response body
		try {
			const errorBody = await response.json();
			return errorBody as T;
		} catch {
			error(response.status, { message: `API error: ${response.status}` });
		}
	}

	return response.json() as Promise<T>;
}

/**
 * Check if a response is an API error (has errors field).
 */
export function isApiError(response: unknown): response is ApiErrors {
	return (
		typeof response === 'object' &&
		response !== null &&
		'errors' in response &&
		typeof (response as ApiErrors).errors === 'object'
	);
}

