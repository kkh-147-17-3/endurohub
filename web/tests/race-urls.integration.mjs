import assert from 'node:assert/strict';
import { before, after, test } from 'node:test';
import { startToolsServer } from './support/tools-server.mjs';

const slug = '2026-화순-테스트마라톤';
const title = '2026 화순 테스트마라톤';
const path = `/races/${encodeURIComponent(slug)}`;
const canonical = `https://www.endurohub.kr${path}`;
const race = {
    id: 87, slug, title, sport: 'running', sportLabel: '마라톤',
    raceDate: '2027-12-01', raceEndDate: null, startTime: '09:00:00',
    location: '공식 대회장', address: null, region: '전남',
    latitude: null, longitude: null, status: 'upcoming', statusLabel: '개최 예정',
    daysUntilRace: 365, daysUntilRegistrationEnd: null,
    distances: [{ name: '10km', distanceMeter: 10000, fee: 30000 }],
    description: '참가자가 확인할 공식 안내를 제공하는 주소 통합 검증용 대회입니다.',
    organizer: '테스트 주최자', officialUrl: 'https://example.org/',
    registrationStart: null, registrationEnd: null, registrationPhases: [],
    courseImageSrcs: [], giveawayImageSrcs: [],
    createdAt: '2026-11-15T00:00:00Z', updatedAt: '2026-11-15T00:00:00Z',
    isFavorited: false, isVerified: false, viewCount: 0,
};
let server;
before(async () => {
    server = await startToolsServer({ respond(req, res, { path: requestPath }) {
        if (requestPath === '/api/v1/sitemap/') {
            res.end(JSON.stringify({ races: [race], posts: [], notices: [], calendarMonths: [] }));
            return true;
        }
        if (!requestPath.startsWith('/api/v1/races/')) return false;
        // Django decodes the path once. Retain this boundary to exercise the
        // second decoding that legacy, double-encoded public URLs depend on.
        const identifier = decodeURIComponent(requestPath.slice('/api/v1/races/'.length, -1));
        if (identifier === 'temporarily-unavailable') {
            res.writeHead(503).end(JSON.stringify({ detail: 'Service unavailable' }));
        } else if ([slug, '87', 'previous-slug'].includes(identifier)) {
            res.end(JSON.stringify({ race, relatedRaces: [], relatedPosts: [], reviews: [],
                reviewStats: { count: 0, average: 0 }, hasReviewed: false, seasonRecords: [] }));
        } else {
            res.writeHead(404).end(JSON.stringify({ detail: 'Not found' }));
        }
        return true;
    } });
});
after(async () => { await server?.close(); });

function headOf(html) { return html.split('</head>')[0]; }
function assertCanonical(html) {
    const head = headOf(html);
    const links = [...head.matchAll(/<link\b[^>]*rel="canonical"[^>]*>/g)];
    assert.equal(links.length, 1);
    assert.ok(links[0][0].includes(`href="${canonical}"`));
    assert.match(head, new RegExp(`property="og:url" content="${canonical}"`));
    assert.equal(/name="robots"[^>]*content="[^"]*noindex/.test(head), false);
    const schemas = [...head.matchAll(/<script type="application\/ld\+json">([^<]*)<\/script>/g)]
        .map((match) => JSON.parse(match[1]));
    assert.equal(schemas.find((schema) => schema['@type'] === 'SportsEvent').url, canonical);
    assert.equal(schemas.find((schema) => schema['@type'] === 'BreadcrumbList').itemListElement.at(-1).item, canonical);
}

test('representative race has one canonical shared by metadata, schema and sitemap', async () => {
    const response = await fetch(`${server.baseUrl}${path}`);
    assert.equal(response.status, 200);
    const html = await response.text();
    assert.ok(html.includes(title));
    assertCanonical(html);
    const sitemap = await (await fetch(`${server.baseUrl}/sitemap.xml`)).text();
    assert.ok(sitemap.includes(`<loc>${canonical}</loc>`));
    assert.equal(sitemap.includes('/races/87'), false);
    assert.equal(sitemap.includes('/races/previous-slug'), false);
});

test('old ID, renamed slug and encoding variants each redirect once to the same race', async () => {
    const variants = [
        '/races/87', '/races/previous-slug',
        `/races/${encodeURIComponent(encodeURIComponent(slug))}`,
        path.replace(/%[\dA-F]{2}/g, (escape) => escape.toLowerCase()),
        path.replace('2026', '%32%30%32%36'),
    ];
    for (const variant of variants) {
        const alias = await fetch(`${server.baseUrl}${variant}`, { redirect: 'manual' });
        assert.equal(alias.status, 301, variant);
        assert.equal(alias.headers.get('location'), path, variant);
        const target = await fetch(`${server.baseUrl}${alias.headers.get('location')}`, { redirect: 'manual' });
        assert.equal(target.status, 200, variant);
        const html = await target.text();
        assert.ok(html.includes(title));
        assertCanonical(html);
    }
});

test('ignored and tracking query parameters keep the clean representative canonical', async () => {
    const response = await fetch(`${server.baseUrl}${path}?utm_source=test&page=2&region=seoul`);
    assert.equal(response.status, 200);
    assertCanonical(await response.text());
});

test('missing races remain 404 and do not redirect to another race or the home page', async () => {
    const response = await fetch(`${server.baseUrl}/races/never-existed`, { redirect: 'manual' });
    assert.equal(response.status, 404);
    assert.equal(response.headers.get('location'), null);
    assert.equal((await response.text()).includes(`<h1>${title}</h1>`), false);
});

test('upstream outages remain temporary errors without a false redirect or deletion', async () => {
    const response = await fetch(`${server.baseUrl}/races/temporarily-unavailable`, { redirect: 'manual' });
    assert.equal(response.status, 502);
    assert.equal(response.headers.get('location'), null);
});
