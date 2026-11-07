import assert from 'node:assert/strict';
import test from 'node:test';
import { TOOL_PAGES, getToolPage } from '../src/lib/seo/tool-pages.ts';

test('each public tool resolves to a distinct search title, description and primary heading', () => {
	const paths = ['/tools/pace-calculator', '/tools/vo2max', '/tools/race-predictor', '/tools/training-plan'];
	for (const path of paths) {
		const page = getToolPage(path);
		assert.ok(page, path);
		assert.equal(page.path, path);
		assert.ok(page.title.includes('엔듀로허브'));
		for (const key of ['title', 'description', 'h1', 'intro']) assert.ok(page[key].trim().length > 0, `${path}: ${key}`);
	}
	for (const key of ['title', 'description', 'h1']) assert.equal(new Set(TOOL_PAGES.map(page => page[key])).size, paths.length);
	assert.equal(getToolPage('/tools'), undefined);
	assert.equal(getToolPage('/tools/unknown'), undefined);
});

test('tool guides carry public usage, calculation assumptions, FAQs and crawlable next steps', () => {
	for (const tool of TOOL_PAGES) {
		assert.ok(tool.useCases.length > 0);
		assert.ok(tool.steps.length > 1);
		assert.ok(tool.method.explanation && tool.method.formulas.length > 0);
		assert.ok(tool.assumptions.length > 0);
		assert.ok(tool.faqs.every(faq => faq.question.trim() && faq.answer.trim()));
		assert.ok(tool.related.some(link => link.href === '/running' || link.href === '/running-terms'));
		assert.ok(tool.related.every(link => link.href.startsWith('/') && link.href !== tool.path && link.label && link.description));
	}
});

test('VDOT and training descriptions preserve the public output boundaries', () => {
	const vdot = getToolPage('/tools/vo2max');
	assert.match(vdot.description, /동등 기록/);
	assert.match(vdot.assumptions.join(' '), /VO₂max/);
	assert.match(vdot.faqs.map(faq => faq.answer).join(' '), /백분위.*계산하지/);
	const plan = getToolPage('/tools/training-plan');
	assert.match(plan.description, /풀코스/);
	assert.match(plan.intro, /가상/);
	assert.match(plan.assumptions.join(' '), /42\.195/);
	assert.match(plan.method.explanation, /일별 거리나 페이스 처방이 아닙니다/);
});
