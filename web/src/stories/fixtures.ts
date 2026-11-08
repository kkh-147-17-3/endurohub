import type { HomeRaceRecord, HomeReview, Race, SportOption } from '$lib/types';

/** Fictional, fixed inputs shared by both versions. No live API data. */
export const comparisonDate = '2026-11-07T03:00:00Z';

export const sports: SportOption[] = [
	{ value: 'running', label: '러닝' },
	{ value: 'trail_running', label: '트레일' },
	{ value: 'cycling', label: '사이클' },
	{ value: 'swimming', label: '수영' },
	{ value: 'triathlon', label: '철인3종' }
];

function race(id: number, changes: Partial<Race>): Race {
	return {
		id, slug: `storybook-race-${id}`, title: '한강 가을 하프 마라톤', edition: null,
		sport: 'running', sportLabel: '러닝', raceDate: '2026-11-08', raceEndDate: null,
		startTime: '08:00', location: '여의도 한강공원', address: null,
		latitude: null, longitude: null, region: '서울',
		distances: [{ name: '하프', distanceMeter: 21097.5, fee: 45000 }, { name: '10K', distanceMeter: 10000, fee: 35000 }],
		registrationStart: '2026-10-01', registrationEnd: '2026-11-09', registrationPhases: null,
		entryFee: null, officialUrl: null, source: null, sourceUrl: null,
		status: 'registration_open', statusLabel: '접수 중', description: null,
		organizer: null, organizerContact: null, organizerEmail: null,
		imageSrc: null, imageSrcThumb: null, giveaways: null, courseImageSrcs: [], giveawayImageSrcs: [],
		viewCount: 120, daysUntilRace: 1, daysUntilRegistrationEnd: 2, isRegistrationOpen: true,
		recapUrl: null, aiSummary: null, url: `/races/storybook-race-${id}`, isFavorited: false,
		weatherForecast: null, courseSurface: null, courseDifficulty: null, aidStations: null,
		timingMethod: null, parking: null, createdAt: '2026-10-01T00:00:00Z', updatedAt: comparisonDate,
		...changes
	};
}

export const races: Race[] = [
	race(1, {}),
	race(2, {
		title: '북한산 능선 트레일 30K', sport: 'trail_running', sportLabel: '트레일', region: '경기',
		location: '북한산 탐방지원센터', status: 'registration_closed', statusLabel: '접수 마감',
		isRegistrationOpen: false, daysUntilRegistrationEnd: null,
		distances: [{ name: '30K', distanceMeter: 30000, fee: 80000 }]
	}),
	race(3, {
		title: '가을 산길 그란폰도', sport: 'cycling', sportLabel: '사이클', region: '강원',
		location: '춘천 의암호', status: 'upcoming', statusLabel: '접수 예정', isRegistrationOpen: false,
		daysUntilRegistrationEnd: null, distances: [{ name: '100K', distanceMeter: 100000, fee: 70000 }]
	}),
	race(4, {
		title: '바다 오픈워터 챌린지', sport: 'swimming', sportLabel: '수영', region: '부산',
		location: '송정해수욕장', daysUntilRegistrationEnd: 12,
		distances: [{ name: '3K', distanceMeter: 3000, fee: 60000 }]
	}),
	race(5, {
		title: '제주 철인3종 페스티벌', sport: 'triathlon', sportLabel: '철인3종', region: '제주',
		location: '서귀포', status: 'cancelled', statusLabel: '대회 취소', isRegistrationOpen: false,
		daysUntilRegistrationEnd: null, distances: [{ name: '올림픽', fee: 150000 }]
	}),
	race(6, { title: '서울공원 10K', daysUntilRegistrationEnd: 3, distances: [{ name: '10K', distanceMeter: 10000, fee: 30000 }] }),
	race(7, { title: '도심 달빛 하프 마라톤', raceDate: '2026-11-15', daysUntilRace: 8, daysUntilRegistrationEnd: 14 }),
	race(8, {
		title: '가을 숲길 트레일 20K', sport: 'trail_running', sportLabel: '트레일', region: '경기',
		raceDate: '2026-11-22', daysUntilRace: 15, daysUntilRegistrationEnd: 7,
		distances: [{ name: '20K', distanceMeter: 20000, fee: 55000 }]
	}),
	race(9, { title: '오늘의 한강 10K', raceDate: '2026-11-07', daysUntilRace: 0, status: 'upcoming', statusLabel: '개최 예정', isRegistrationOpen: false, daysUntilRegistrationEnd: null }),
	race(10, { title: '가을 첫 주 마라톤', raceDate: '2026-11-01', daysUntilRace: -6, status: 'finished', statusLabel: '종료', isRegistrationOpen: false, daysUntilRegistrationEnd: null })
];

export const runningRaces = races.filter((entry) => entry.sport === 'running');

export const calendarProps = {
	year: 2026,
	month: 11,
	startOfMonth: '2026-11-01',
	racesGrouped: races.reduce<Record<string, Race[]>>((grouped, entry) => {
		(grouped[entry.raceDate!] ??= []).push(entry);
		return grouped;
	}, {}),
	previousMonth: { year: 2026, month: 10 },
	nextMonth: { year: 2026, month: 12 },
	sports,
	regions: ['서울', '경기', '강원', '부산', '제주'],
	showDiscovery: true,
	basePath: '/calendar'
};

/** Six occupied week rows; the other comparison scenarios keep their original November fixtures. */
export const denseCalendarRaces: Race[] = [1, 2, 9, 16, 23, 30].flatMap((day, weekIndex) => {
	const raceDate = `2027-05-${String(day).padStart(2, '0')}`;
	return races.slice(0, 6).map((entry, index) => {
		const id = 100 + weekIndex * 10 + index;
		const registrationEnd = entry.status === 'registration_closed' ? '2026-11-06' : '2027-04-30';
		return {
			...entry,
			id,
			slug: `storybook-dense-race-${id}`,
			url: `/races/storybook-dense-race-${id}`,
			raceDate,
			daysUntilRace: Math.round((Date.parse(`${raceDate}T03:00:00Z`) - Date.parse(comparisonDate)) / 86_400_000),
			registrationStart: entry.status === 'upcoming' ? '2027-02-01' : '2026-10-01',
			registrationEnd,
			daysUntilRegistrationEnd: entry.isRegistrationOpen
				? Math.round((Date.parse(`${registrationEnd}T03:00:00Z`) - Date.parse(comparisonDate)) / 86_400_000)
				: null
		};
	});
});

export const denseCalendarProps = {
	...calendarProps,
	year: 2027,
	month: 5,
	startOfMonth: '2027-05-01',
	racesGrouped: denseCalendarRaces.reduce<Record<string, Race[]>>((grouped, entry) => {
		(grouped[entry.raceDate!] ??= []).push(entry);
		return grouped;
	}, {}),
	previousMonth: { year: 2027, month: 4 },
	nextMonth: { year: 2027, month: 6 }
};

const activityRace = (entry: Race) => ({
	id: entry.id, slug: entry.slug, title: entry.title, sport: entry.sport,
	sportLabel: entry.sportLabel, raceDate: entry.raceDate
});

export const reviews: HomeReview[] = [
	{
		id: 101, nickname: '한강러너', rating: 5,
		comment: '급수대 간격이 적절했고, 강변 코스라 초보 하프 참가자도 편하게 달릴 수 있었어요.',
		completionTime: '1:42:15', courseDifficulty: 'easy', operationSatisfaction: 5,
		recommendationTags: ['첫 하프', '기록 도전'], createdAt: '2026-11-06T09:00:00Z',
		createdAtFormatted: '2026.11.06', likeCount: 12, hasLiked: false, race: activityRace(races[0])
	},
	{
		id: 102, nickname: '숲길산책', rating: 4,
		comment: '후반 오르막은 힘들었지만 코스 안내와 응원이 좋아 완주할 수 있었습니다.',
		completionTime: '3:08:40', courseDifficulty: 'hard', operationSatisfaction: 4,
		recommendationTags: ['풍경'], createdAt: '2026-11-05T08:00:00Z',
		createdAtFormatted: '2026.11.05', likeCount: 7, hasLiked: false, race: activityRace(races[1])
	}
];

export const records: HomeRaceRecord[] = [
	{
		id: 201, nickname: '한강러너', sport: 'running', sportLabel: '러닝', courseCode: 'half',
		courseLabel: '하프', time: '1:42:15', metricLabel: '평균 페이스', metricValue: '4′51″ / km',
		date: '2026-11-06', durationSeconds: 6135, me: true, createdAt: '2026-11-06T10:00:00Z', race: activityRace(races[0])
	},
	{
		id: 202, nickname: '숲길산책', sport: 'trail_running', sportLabel: '트레일', courseCode: '30k',
		courseLabel: '30K', time: '3:08:40', metricLabel: '평균 페이스', metricValue: '6′17″ / km',
		date: '2026-11-05', durationSeconds: 11320, me: false, createdAt: '2026-11-05T10:00:00Z', race: activityRace(races[1])
	},
	{
		id: 203, nickname: '주말라이더', sport: 'cycling', sportLabel: '사이클', courseCode: '100k',
		courseLabel: '100K', time: '3:35:20', metricLabel: '평균 속도', metricValue: '27.9 km/h',
		date: '2026-11-04', durationSeconds: 12920, me: false, createdAt: '2026-11-04T10:00:00Z', race: activityRace(races[2])
	}
];
