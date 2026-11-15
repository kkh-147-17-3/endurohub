/** The stored, decoded slug is the identity shared by redirects and SEO metadata. */
export function raceCanonicalPath(slug: string): string {
	return `/races/${encodeURIComponent(slug)}`;
}

export function raceCanonicalUrl(appUrl: string, slug: string): string {
	return new URL(raceCanonicalPath(slug), `${appUrl.replace(/\/$/, '')}/`).href;
}
