import assert from 'node:assert/strict';
import { test } from 'node:test';
import { raceCanonicalPath, raceCanonicalUrl } from '../src/lib/seo/race-url.ts';

test('race URL identity is built from the decoded stored slug using one encoding', () => {
    const slug = '2026-화순고인돌마라톤';
    const path = `/races/${encodeURIComponent(slug)}`;
    assert.equal(raceCanonicalPath(slug), path);
    assert.equal(raceCanonicalUrl('https://www.endurohub.kr/', slug), `https://www.endurohub.kr${path}`);
    assert.equal(new URL(path, 'https://www.endurohub.kr').href, raceCanonicalUrl('https://www.endurohub.kr', slug));
    assert.equal(decodeURIComponent(new URL(raceCanonicalUrl('https://www.endurohub.kr', slug)).pathname), `/races/${slug}`);
});

test('different events keep distinct canonical URLs', () => {
    assert.notEqual(raceCanonicalPath('제1회-테스트런'), raceCanonicalPath('제2회-테스트런'));
});
