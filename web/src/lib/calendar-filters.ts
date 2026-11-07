import type { Race } from './types';

export type CalendarView = 'cal' | 'list' | 'map';

export interface CalendarFilters {
	sports: string[];
	regions: string[];
	name: string;
	openOnly: boolean;
	view: CalendarView;
}

export function readCalendarFilters(
	params: URLSearchParams,
	availableSports: string[],
	defaultView: CalendarView = 'cal'
): CalendarFilters {
	const view = params.get('view');
	return {
		sports: [...new Set(params.getAll('sport').filter((sport) => availableSports.includes(sport)))],
		regions: [...new Set(params.getAll('region').filter(Boolean))],
		name: (params.get('name') ?? '').trim(),
		openOnly: params.getAll('status').includes('registration_open'),
		view: view === 'cal' || view === 'list' || view === 'map' ? view : defaultView
	};
}

/** Keep the date and other navigation parameters when changing discovery controls. */
export function calendarFilterParams(
	current: URLSearchParams,
	filters: CalendarFilters
): URLSearchParams {
	const params = new URLSearchParams(current);
	for (const key of ['sport', 'region', 'name', 'status', 'view']) params.delete(key);
	for (const sport of filters.sports) params.append('sport', sport);
	for (const region of filters.regions) params.append('region', region);
	if (filters.name.trim()) params.set('name', filters.name.trim());
	if (filters.openOnly) params.set('status', 'registration_open');
	if (filters.view !== 'cal') params.set('view', filters.view);
	return params;
}

export function matchesCalendarFilters(race: Race, filters: CalendarFilters): boolean {
	return (
		(filters.sports.length === 0 || filters.sports.includes(race.sport)) &&
		(filters.regions.length === 0 || filters.regions.includes(race.region ?? '')) &&
		(!filters.name || race.title.normalize('NFKC').toLocaleLowerCase('ko').includes(
			filters.name.normalize('NFKC').toLocaleLowerCase('ko')
		)) &&
		(!filters.openOnly || race.status === 'registration_open')
	);
}

export function raceSearchHref(filters: CalendarFilters): string {
	const params = calendarFilterParams(new URLSearchParams(), { ...filters, view: 'cal' });
	return `/races${params.size ? `?${params}` : ''}`;
}
