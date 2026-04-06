import type { Handle } from '@sveltejs/kit';
import crypto from 'node:crypto';
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

const SESSION_COOKIE = 'ehub_sid';
const SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 365; // 1 year

const appHandle: Handle = async ({ event, resolve }) => {
	// Extract client IP from request headers for forwarding to Django API
	const forwardedFor = event.request.headers.get('x-forwarded-for');
	const realIp = event.request.headers.get('x-real-ip');
	event.locals.clientIp = forwardedFor?.split(',')[0]?.trim() || realIp || event.getClientAddress();

	// Extract auth token from cookie
	event.locals.authToken = event.cookies.get('auth_token') || '';

	// Extract session ID for forwarding to Django API
	event.locals.sessionId = event.cookies.get(SESSION_COOKIE) || '';

	// Ensure anonymous session ID exists for analytics
	if (!event.cookies.get(SESSION_COOKIE)) {
		event.cookies.set(SESSION_COOKIE, crypto.randomUUID(), {
			path: '/',
			httpOnly: false,
			secure: false,
			sameSite: 'lax',
			maxAge: SESSION_MAX_AGE_SECONDS,
		});
	}

	return resolve(event);
};

export const handle: Handle = env.SENTRY_DSN
	? sequence(Sentry.sentryHandle(), appHandle)
	: appHandle;

export const handleError = env.SENTRY_DSN
	? Sentry.handleErrorWithSentry()
	: undefined;
