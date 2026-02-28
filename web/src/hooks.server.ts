import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
	// Extract client IP from request headers for forwarding to Django API
	const forwardedFor = event.request.headers.get('x-forwarded-for');
	const realIp = event.request.headers.get('x-real-ip');
	event.locals.clientIp = forwardedFor?.split(',')[0]?.trim() || realIp || event.getClientAddress();

	// Extract auth token from cookie
	event.locals.authToken = event.cookies.get('auth_token') || '';

	return resolve(event);
};
