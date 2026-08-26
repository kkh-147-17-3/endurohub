import type { RequestHandler } from './$types';
import { apiFetch } from '$lib/api';
import { APP_URL } from '$lib/env';
import { SPORT_LANDINGS } from '$lib/seo/sport-landing';
import type { SitemapResponse } from '$lib/types';

export const GET: RequestHandler = async () => {
	const data = await apiFetch<SitemapResponse>('/sitemap/');
	const baseUrl = APP_URL.replace(/\/$/, '');

	const urls: string[] = [];

	// Static pages
	urls.push(entry(baseUrl, '/', 'daily', '1.0'));
	urls.push(entry(baseUrl, '/races', 'daily', '0.9'));
	urls.push(entry(baseUrl, '/calendar', 'daily', '0.8'));

	// Calendar monthly pages
	for (const cm of data.calendarMonths) {
		urls.push(entry(baseUrl, `/calendar?month=${cm.month}&year=${cm.year}`, 'weekly', '0.6'));
	}

	// Yearly race pages. These were missing entirely, so /races/year/{year} was
	// reachable only through the navbar and footer links.
	//
	// The year list is derived from calendarMonths rather than a raw year range:
	// that payload already holds only months with at least one race, so a year
	// appearing there is guaranteed to have races and therefore to answer 200.
	// /races/year/{year} 404s on an empty year (see the route's +page.server.ts),
	// and listing URLs that 404 — or thin pages that never get indexed — is the
	// exact problem the calendarMonths filter above was added to fix.
	const raceYears = [...new Set(data.calendarMonths.map((cm) => cm.year))].sort((a, b) => a - b);
	for (const year of raceYears) {
		urls.push(entry(baseUrl, `/races/year/${year}`, 'daily', '0.8'));
	}

	// Sport landing pages — these used to 301 to /races?sport=X and were excluded here
	// for that reason. They now answer 200 with their own content and self-canonical,
	// so they belong in the sitemap. Priority sits just under /races: they are the
	// entry point for sport keywords ("마라톤 대회 일정") and the second internal-link
	// path into race detail pages.
	for (const s of SPORT_LANDINGS) {
		urls.push(entry(baseUrl, s.path, 'daily', '0.9'));
	}

	// Tool pages
	urls.push(entry(baseUrl, '/tools', 'monthly', '0.8'));
	urls.push(entry(baseUrl, '/tools/pace-calculator', 'monthly', '0.8'));
	urls.push(entry(baseUrl, '/tools/training-plan', 'monthly', '0.8'));
	urls.push(entry(baseUrl, '/tools/vo2max', 'monthly', '0.8'));
	urls.push(entry(baseUrl, '/tools/race-predictor', 'monthly', '0.8'));
	urls.push(entry(baseUrl, '/running-terms', 'monthly', '0.7'));

	// Info pages
	urls.push(entry(baseUrl, '/about', 'monthly', '0.5'));
	// /privacy is excluded — the page sets <meta name="robots" content="noindex">,
	// so listing it in the sitemap would be contradictory.

	// Race detail pages
	for (const race of data.races) {
		urls.push(entry(baseUrl, `/races/${race.slug}`, 'weekly', '0.7', race.updatedAt));
	}

	// Community feed (/posts 301-redirects here, so list the canonical /community)
	urls.push(entry(baseUrl, '/community', 'daily', '0.8'));

	// Post detail pages
	for (const post of data.posts) {
		urls.push(entry(baseUrl, `/posts/${post.id}`, 'weekly', '0.6', post.updatedAt));
	}

	const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.join('\n')}
</urlset>`;

	return new Response(xml, {
		headers: {
			'Content-Type': 'application/xml',
			'Cache-Control': 'max-age=3600'
		}
	});
};

function entry(
	baseUrl: string,
	path: string,
	changefreq: string,
	priority: string,
	lastmod?: string
): string {
	// Race slugs are Hangul, so the raw path is not a valid <loc> — sitemaps must
	// carry RFC 3986 URLs. Resolving through WHATWG URL percent-encodes the path
	// with exactly the same rules SvelteKit's `url.pathname` uses to build the
	// page's <link rel="canonical">, so sitemap and canonical stay byte-identical;
	// emitting the raw form made Google treat them as two different URLs.
	const loc = new URL(path, `${baseUrl}/`).href;
	let xml = `  <url>\n    <loc>${escapeXml(loc)}</loc>`;
	const lastmodValue = formatLastmod(lastmod);
	if (lastmodValue) {
		xml += `\n    <lastmod>${lastmodValue}</lastmod>`;
	}
	xml += `\n    <changefreq>${changefreq}</changefreq>`;
	xml += `\n    <priority>${priority}</priority>`;
	xml += `\n  </url>`;
	return xml;
}

// Google Search Console rejects lastmod values with sub-second precision
// (e.g. "2026-06-27T12:34:56.789012Z"). Normalize to W3C date format (YYYY-MM-DD).
function formatLastmod(value?: string): string | null {
	if (!value) return null;
	const date = new Date(value);
	if (isNaN(date.getTime())) return null;
	return date.toISOString().slice(0, 10);
}

function escapeXml(str: string): string {
	return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
