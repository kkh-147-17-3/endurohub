import assert from 'node:assert/strict';
import test from 'node:test';
import { readCalendarFilters, calendarFilterParams, matchesCalendarFilters, raceSearchHref } from '../src/lib/calendar-filters.ts';

const sports = ['running', 'cycling'];
const empty = readCalendarFilters(new URLSearchParams(), sports);
const race = { title: '2026 Enduro 하프마라톤', sport: 'running', region: '서울', status: 'registration_open' };

test('shared filter URLs restore valid selections without accepting unknown sports or views', () => {
	const filters = readCalendarFilters(new URLSearchParams('sport=running&sport=unknown&sport=running&region=서울&name=+Enduro+&status=registration_open&view=list'), sports);
	assert.deepEqual(filters, { sports: ['running'], regions: ['서울'], name: 'Enduro', openOnly: true, view: 'list' });
	assert.equal(readCalendarFilters(new URLSearchParams('view=unknown'), sports).view, 'cal');
});

test('all four discovery conditions combine and cancelled races never match open-only', () => {
	const filters = { ...empty, sports: ['running'], regions: ['서울'], name: 'enduro', openOnly: true };
	assert.equal(matchesCalendarFilters(race, filters), true);
	for (const changes of [{ sport: 'cycling' }, { region: '경기' }, { title: '다른 대회' }, { status: 'cancelled' }]) {
		assert.equal(matchesCalendarFilters({ ...race, ...changes }, filters), false);
	}
});

test('month navigation, refresh and clearing filters retain the selected calendar date and view', () => {
	const current = new URLSearchParams('year=2027&month=2&name=old&region=경기&status=registration_open');
	const changed = calendarFilterParams(current, { ...empty, name: '한강', view: 'list' });
	assert.equal(changed.get('year'), '2027');
	assert.equal(changed.get('month'), '2');
	assert.equal(changed.has('region'), false);
	assert.equal(changed.has('status'), false);
	assert.equal(readCalendarFilters(changed, sports).name, '한강');
	assert.equal(readCalendarFilters(changed, sports).view, 'list');
});

test('advanced search carries discovery conditions without restricting to a calendar month or view', () => {
	const href = raceSearchHref({ ...empty, name: '한강 & 서울', regions: ['서울'], openOnly: true, view: 'map' });
	const url = new URL(href, 'https://example.com');
	assert.equal(url.pathname, '/races');
	assert.equal(url.searchParams.get('name'), '한강 & 서울');
	assert.equal(url.searchParams.get('region'), '서울');
	assert.equal(url.searchParams.get('status'), 'registration_open');
	assert.equal(url.searchParams.has('view'), false);
	assert.equal(url.searchParams.has('month'), false);
});
