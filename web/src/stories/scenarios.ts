export type ComparisonVersion = 'before' | 'after';
export type Scenario = 'primitives' | 'cards' | 'single-sport' | 'home' | 'date-groups' | 'calendar-height' | 'calendar' | 'calendar-single' | 'calendar-open' | 'map';
export type PreviewViewport = 'mobile' | 'tablet' | 'desktop';

export const viewports: Record<PreviewViewport, { label: string; width: number }> = {
	mobile: { label: '모바일 390px', width: 390 },
	tablet: { label: '태블릿 768px', width: 768 },
	desktop: { label: '데스크톱 1100px', width: 1100 }
};

export const scenarios: Record<Scenario, { label: string; story: string; query: string; note: string }> = {
	'date-groups': { label: '일자별 그룹 목록', story: 'date-groups', query: '', note: '2027년 5월의 같은 36개 대회를 비교합니다. 변경 전은 각 행에 날짜가 반복되고, 변경 후는 날짜를 그룹 제목으로 한 번만 표시합니다. 대회명, 종목, 접수 상태와 마감일, 지역, 거리, 참가비는 유지합니다.' },
	'calendar-height': { label: '달력 높이 개선', story: 'calendar-height', query: '', note: '6주로 구성된 2027년 5월의 각 주에 다섯 종목, 6개 대회를 배치했습니다. 변경 전은 이번 높이 개선 직전의 달력이며, 양쪽 모두 현재 공통 스타일을 사용합니다. 날짜를 눌러 전체 대회 목록도 확인할 수 있습니다.' },
	primitives: { label: '종목 태그와 접수 상태', story: 'primitives', query: '', note: '텍스트로 이미 전달하는 종목과 상태 앞의 중복 점을 비교합니다.' },
	cards: { label: '대회 카드', story: 'cards', query: '', note: '같은 대회명, 날짜, 지역, 참가비로 카드의 정보 배치를 비교합니다.' },
	'single-sport': { label: '러닝 대회 목록', story: 'race-results', query: '?sport=running', note: '제목에 명시한 종목을 각 결과에서 반복하는지 확인합니다.' },
	home: { label: '홈 후기와 회원 기록', story: 'home', query: '', note: '후기의 작성 정보와 완주 기록의 대회명, 코스, 날짜를 비교합니다.' },
	calendar: { label: '여러 종목의 달력', story: 'calendar', query: '', note: '11월 8일에 다섯 종목과 여러 접수 상태가 함께 있는 경우입니다. 날짜를 눌러 목록도 확인할 수 있습니다.' },
	'calendar-single': { label: '러닝 필터 달력', story: 'calendar-single', query: '?sport=running', note: '러닝만 선택한 상태에서 반복 종목명과 날짜 칸을 비교합니다.' },
	'calendar-open': { label: '접수 중 필터 목록', story: 'calendar-open', query: '?status=registration_open&view=list', note: '접수 중 상태의 반복을 줄이면서 마감 임박과 남은 기간이 유지되는지 확인합니다.' },
	map: { label: '지역별 대회 지도', story: 'map', query: '?view=map', note: '지역별 종목 정보가 색상 없이도 구분되는지 확인합니다.' }
};

export function previewStoryId(scenario: Scenario, version: ComparisonVersion): string {
	return `design-preview--${scenarios[scenario].story}-${version}`;
}
