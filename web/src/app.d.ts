/// <reference types="@sveltejs/kit" />

declare module '*.otf' {
	const url: string;
	export default url;
}

declare module '*.ttf' {
	const url: string;
	export default url;
}

declare global {
	function gtag(...args: unknown[]): void;
	interface Window {
		dataLayer: unknown[];
		gtag: (...args: unknown[]) => void;
	}

	namespace App {
		interface Error {
			message: string;
			code?: string;
		}
		interface Locals {
			clientIp: string;
			authToken: string;
			sessionId: string;
		}
		interface PageData {
			appName: string;
			appUrl: string;
			currentYear: number;
			kakaoJsKey: string;
			naverMapClientId: string;
			googleAnalyticsId: string;
			feedbackFormUrl: string;
			user: import('$lib/types').AuthUser | null;
		}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};
