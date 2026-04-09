import posthog from 'posthog-js';

import { env as publicEnv } from '$env/dynamic/public';
import type { AuthUser } from '$lib/types';

type EventProperties = Record<string, string | number | boolean | null | undefined>;

const SESSION_COOKIE = 'ehub_sid';
const POSTHOG_KEY = publicEnv.PUBLIC_POSTHOG_KEY || '';
const POSTHOG_HOST = publicEnv.PUBLIC_POSTHOG_HOST || 'https://us.i.posthog.com';

let initialized = false;
let currentIdentifiedUserId = '';

function isBrowser() {
	return typeof window !== 'undefined';
}

function readCookie(name: string): string {
	if (!isBrowser()) return '';

	const prefix = `${name}=`;
	for (const part of document.cookie.split(';')) {
		const trimmed = part.trim();
		if (trimmed.startsWith(prefix)) {
			return decodeURIComponent(trimmed.slice(prefix.length));
		}
	}

	return '';
}

function getSessionId(): string {
	return readCookie(SESSION_COOKIE);
}

function getSuperProperties() {
	return {
		ehub_session_id: getSessionId(),
		is_logged_in: currentIdentifiedUserId !== '',
	};
}

function ensureInitialized() {
	if (!initialized) {
		initPostHog();
	}

	return initialized;
}

export function initPostHog() {
	if (!isBrowser() || initialized || !POSTHOG_KEY) {
		return false;
	}

	posthog.init(POSTHOG_KEY, {
		api_host: POSTHOG_HOST,
		defaults: '2026-01-30',
		autocapture: false,
		capture_pageview: false,
		capture_pageleave: true,
		loaded: (instance) => {
			instance.register(getSuperProperties());
		},
	});

	initialized = true;
	return true;
}

export function capturePostHogEvent(eventType: string, properties: EventProperties = {}) {
	if (!ensureInitialized()) return;

	posthog.register(getSuperProperties());
	posthog.capture(eventType, properties);
}

export function capturePostHogPageView(pathname: string, search = '', referrer = '') {
	if (!ensureInitialized()) return;

	const href = `${window.location.origin}${pathname}${search}`;
	const referrerDomain = referrer ? (() => {
		try {
			return new URL(referrer).hostname;
		} catch {
			return '';
		}
	})() : '';

	posthog.register(getSuperProperties());
	posthog.capture('$pageview', {
		page_path: pathname,
		page_search: search,
		page_url: href,
		referrer,
		referrer_domain: referrerDomain || undefined,
	});
}

export function syncPostHogUser(user: AuthUser | null) {
	if (!ensureInitialized()) return;

	if (user) {
		const nextUserId = String(user.id);
		posthog.register({
			...getSuperProperties(),
			is_logged_in: true,
		});
		if (currentIdentifiedUserId !== nextUserId) {
			posthog.identify(nextUserId, {
				email: user.email,
				nickname: user.nickname,
				email_verified: user.emailVerified,
				email_updates_opt_in: user.emailUpdatesOptIn,
			});
			currentIdentifiedUserId = nextUserId;
		}
		return;
	}

	if (currentIdentifiedUserId) {
		posthog.reset();
		currentIdentifiedUserId = '';
	}

	posthog.register(getSuperProperties());
}
