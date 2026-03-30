import type { Handle } from '@sveltejs/kit';
import * as Sentry from '@sentry/sveltekit';
import { env } from '$env/dynamic/private';
import { sequence } from '@sveltejs/kit/hooks';

if (env.SENTRY_DSN) {
	Sentry.init({
		dsn: env.SENTRY_DSN,
		tracesSampleRate: 0.1,
		profilesSampleRate: 0.1,
	});
}

const appHandle: Handle = async ({ event, resolve }) => {
	// Extract client IP from request headers for forwarding to Django API
	const forwardedFor = event.request.headers.get('x-forwarded-for');
	const realIp = event.request.headers.get('x-real-ip');
	event.locals.clientIp = forwardedFor?.split(',')[0]?.trim() || realIp || event.getClientAddress();

	// Extract auth token from cookie
	event.locals.authToken = event.cookies.get('auth_token') || '';

	return resolve(event);
};

export const handle: Handle = env.SENTRY_DSN
	? sequence(Sentry.sentryHandle(), appHandle)
	: appHandle;

export const handleError = env.SENTRY_DSN
	? Sentry.handleErrorWithSentry()
	: undefined;
