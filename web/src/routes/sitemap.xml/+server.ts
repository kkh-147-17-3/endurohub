import type { RequestHandler } from './$types';
import { apiFetch } from '$lib/api';
import { APP_URL } from '$lib/env';
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

	// Sport category pages
	urls.push(entry(baseUrl, '/running', 'daily', '0.8'));
	urls.push(entry(baseUrl, '/swimming', 'daily', '0.8'));
	urls.push(entry(baseUrl, '/cycling', 'daily', '0.8'));
	urls.push(entry(baseUrl, '/triathlon', 'daily', '0.8'));
	urls.push(entry(baseUrl, '/trail-running', 'daily', '0.8'));

	// Tool pages
	urls.push(entry(baseUrl, '/tools', 'monthly', '0.8'));
	urls.push(entry(baseUrl, '/tools/pace-calculator', 'monthly', '0.8'));
	urls.push(entry(baseUrl, '/tools/training-plan', 'monthly', '0.8'));
	urls.push(entry(baseUrl, '/tools/vo2max', 'monthly', '0.8'));
	urls.push(entry(baseUrl, '/tools/race-predictor', 'monthly', '0.8'));
	urls.push(entry(baseUrl, '/running-terms', 'monthly', '0.7'));

	// Info pages
	urls.push(entry(baseUrl, '/about', 'monthly', '0.5'));
	urls.push(entry(baseUrl, '/privacy', 'monthly', '0.3'));

	// Race detail pages
	for (const race of data.races) {
		urls.push(entry(baseUrl, `/races/${race.slug}`, 'weekly', '0.7', race.updatedAt));
	}

	// Posts list
	urls.push(entry(baseUrl, '/posts', 'daily', '0.8'));

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
	const loc = `${baseUrl}${path}`;
	let xml = `  <url>\n    <loc>${escapeXml(loc)}</loc>`;
	if (lastmod) {
		xml += `\n    <lastmod>${lastmod}</lastmod>`;
	}
	xml += `\n    <changefreq>${changefreq}</changefreq>`;
	xml += `\n    <priority>${priority}</priority>`;
	xml += `\n  </url>`;
	return xml;
}

function escapeXml(str: string): string {
	return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
