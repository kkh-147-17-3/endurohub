import assert from 'node:assert/strict';
import { before, after, test } from 'node:test';
import { TOOL_PAGES } from '../src/lib/seo/tool-pages.ts';
import { startToolsServer } from './support/tools-server.mjs';

let server;
before(async () => { server = await startToolsServer(); });
after(async () => { await server?.close(); });

async function getPage(path, token) {
    const response = await fetch(`${server.baseUrl}${path}`, { headers: token ? { cookie: `auth_token=${token}` } : {} });
    assert.equal(response.status, 200, path);
    return response.text();
}
const headOf = (html) => html.split('</head>')[0];
const textOf = (html) => html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/g, '').replace(/<[^>]+>/g, ' ');

test('all four tools serve unique, public SSR metadata, headings, guide and related links', async () => {
    server.requests.length = 0;
    for (const tool of TOOL_PAGES) {
        const html = await getPage(tool.path);
        const head = headOf(html);
        assert.equal([...head.matchAll(/<title>/g)].length, 1, tool.path);
        assert.ok(head.includes(tool.title), tool.path);
        assert.equal([...head.matchAll(/name="description"/g)].length, 1, tool.path);
        assert.ok(head.includes(tool.description), tool.path);
        assert.equal([...html.matchAll(/<h1(?:\s|>)/g)].length, 1, tool.path);
        assert.ok(html.includes(tool.h1), tool.path);
        assert.ok(head.includes(`href="https://www.endurohub.kr${tool.path}"`));
        for (const question of tool.faqs) assert.ok(html.includes(question.question), question.question);
        for (const link of tool.related) assert.ok(html.includes(`href="${link.href}"`), link.href);
    }
    assert.equal(server.requests.some(({ path }) => path.includes('/me/')), false);
});

test('anonymous training page contains the full public example without requiring sign-in', async () => {
    const text = textOf(await getPage('/tools/training-plan'));
    assert.ok(text.includes('공개 예시'));
    assert.ok(text.includes('가상 풀코스 마라톤'));
    assert.ok(text.includes('1:42:15'));
    for (const phase of ['BASE', 'BUILD', 'PEAK', 'TAPER']) assert.ok(text.includes(phase));
    assert.ok(text.includes('16'));
    assert.equal(text.includes('춘천 마라톤'), false);
});

test('signed-in calculators use the saved record without leaking it into search metadata', async () => {
    const pace = await getPage('/tools/pace-calculator', 'personal');
    assert.ok(pace.includes('50:00'));
    assert.ok(textOf(pace).includes('12.0'));
    assert.equal(headOf(pace).includes('test@example.invalid'), false);
    const predictor = await getPage('/tools/race-predictor', 'personal');
    assert.ok(textOf(predictor).includes('1:50:19'));
    assert.ok(textOf(predictor).includes('3:50:01'));
    assert.equal(textOf(predictor).includes('춘천 마라톤'), false);
    const vdot = textOf(await getPage('/tools/vo2max', 'personal'));
    assert.ok(vdot.includes('40.0'));
    assert.equal(vdot.includes('상위 5%'), false);
    assert.equal(vdot.includes('등급 (동연령)'), false);
});

test('saved marathon goals remain available and unrelated or cancelled goals are excluded', async () => {
    const html = await getPage('/tools/training-plan', 'personal');
    const text = textOf(html);
    assert.ok(text.includes('내 관심 풀코스 테스트 대회'));
    assert.ok(text.includes('50:00'));
    assert.equal(text.includes('취소 후보'), false);
    assert.equal(text.includes('자전거 후보'), false);
    assert.equal(text.includes('하프 후보'), false);
    assert.equal(headOf(html).includes('내 관심 풀코스 테스트 대회'), false);
});

test('signed-in visitors without usable data and API failures can still view the labeled public example', async () => {
    for (const token of ['empty', 'failed']) {
        const text = textOf(await getPage('/tools/training-plan', token));
        assert.ok(text.includes('공개 예시'), token);
        assert.ok(text.includes('가상 풀코스 마라톤'), token);
        assert.ok(text.includes('1:42:15'), token);
    }
});

test('a saved record outside the VDOT formula uses an explicitly labeled sample basis', async () => {
    const text = textOf(await getPage('/tools/training-plan', 'slow'));
    assert.ok(text.includes('내 관심 풀코스 테스트 대회'));
    assert.ok(text.includes('계산 기준 · 예시 기록'));
    assert.ok(text.includes('1:42:15'));
    assert.equal(text.includes('NaN'), false);
});
