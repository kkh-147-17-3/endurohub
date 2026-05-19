import type { Handle } from '@sveltejs/kit';
import crypto from 'node:crypto';
import * as Sentry from '@sentry/sveltekit';
import { env } from '$env/dynamic/private';
import { sequence } from '@sveltejs/kit/hooks';
import { ADMIN_SECRET } from '$lib/env';

if (env.SENTRY_DSN) {
	Sentry.init({
		dsn: env.SENTRY_DSN,
		tracesSampleRate: 0.1,
		profilesSampleRate: 0.1,
	});
}

const SESSION_COOKIE = 'ehub_sid';
const SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 365; // 1 year

function safeClientAddress(event: Parameters<Handle>[0]['event']): string {
	try {
		return event.getClientAddress();
	} catch {
		return '127.0.0.1';
	}
}

const appHandle: Handle = async ({ event, resolve }) => {
	// Extract client IP from request headers for forwarding to Django API
	const forwardedFor = event.request.headers.get('x-forwarded-for');
	const realIp = event.request.headers.get('x-real-ip');
	event.locals.clientIp = forwardedFor?.split(',')[0]?.trim() || realIp || safeClientAddress(event);

	// Forward the original User-Agent to the API so server-side analytics can
	// distinguish crawlers (the API otherwise only sees the SSR fetch's UA).
	event.locals.userAgent = event.request.headers.get('user-agent') || '';

	// Extract auth token from cookie
	event.locals.authToken = event.cookies.get('auth_token') || '';

	const adminToken = event.cookies.get('admin_token') || '';
	event.locals.isAdmin = !!(ADMIN_SECRET && adminToken && adminToken === ADMIN_SECRET);

	// Ensure anonymous session ID exists for analytics, and forward it to Django API
	// on the same request (Set-Cookie reaches the browser only after the response,
	// so we must populate locals.sessionId synchronously when minting a new ID).
	let sessionId = event.cookies.get(SESSION_COOKIE);
	if (!sessionId) {
		sessionId = crypto.randomUUID();
		event.cookies.set(SESSION_COOKIE, sessionId, {
			path: '/',
			httpOnly: false,
			secure: false,
			sameSite: 'lax',
			maxAge: SESSION_MAX_AGE_SECONDS,
		});
	}
	event.locals.sessionId = sessionId;

	return resolve(event);
};

export const handle: Handle = env.SENTRY_DSN
	? sequence(Sentry.sentryHandle(), appHandle)
	: appHandle;

export const handleError = env.SENTRY_DSN
	? Sentry.handleErrorWithSentry()
	: undefined;
