/**
 * Open-redirect safe return URL for post-login navigation (admin area only).
 */
export function getSafeAdminRedirect(raw: string | null | undefined): string | null {
	if (raw == null || raw === '') return null;
	if (!raw.startsWith('/') || raw.startsWith('//')) return null;
	if (!raw.startsWith('/admin')) return null;
	// 다시 로그인 페이지로 돌아오는 것만 차단 (django next 로 사용)
	if (
		raw === '/admin/login' ||
		raw.startsWith('/admin/login?') ||
		raw.startsWith('/admin/login/')
	) {
		return null;
	}
	return raw;
}

/**
 * Django Admin 로그인 후 `?next=`에 넣을 경로 (현재 요청 URL 기준).
 */
export function djangoAdminNextUrl(url: URL): string {
	if (url.pathname === '/admin/login' || url.pathname.startsWith('/admin/login/')) {
		const inner = url.searchParams.get('redirect');
		if (inner) {
			const s = getSafeAdminRedirect(inner);
			if (s) return s;
		}
		return '/admin/races';
	}
	const combined = url.pathname + url.search;
	return getSafeAdminRedirect(combined) ?? '/admin/races';
}
