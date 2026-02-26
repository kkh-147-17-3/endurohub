import type { ApiErrors } from '$lib/types';

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

/**
 * Client-side API fetch wrapper.
 * Use this in Svelte components for client-side interactions (likes, etc.).
 * Routes through nginx proxy at /api.
 */
export async function clientApiFetch<T>(
	path: string,
	options: {
		method?: string;
		body?: unknown;
	} = {}
): Promise<T> {
	const headers: Record<string, string> = {
		'Accept': 'application/json'
	};

	const fetchOptions: RequestInit = {
		method: options.method || 'GET',
		headers
	};

	if (options.body !== undefined) {
		if (options.body instanceof FormData) {
			fetchOptions.body = options.body;
		} else {
			headers['Content-Type'] = 'application/json';
			fetchOptions.body = JSON.stringify(options.body);
		}
	}

	const response = await fetch(`/api/v1${path}`, fetchOptions);
	return response.json() as Promise<T>;
}
