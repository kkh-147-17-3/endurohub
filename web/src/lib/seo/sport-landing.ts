import type { Sport } from '$lib/types';

/**
 * 종목별 랜딩 페이지(/running, /swimming, …)의 고정 콘텐츠.
 *
 * 이 페이지들은 원래 `/races?sport=X` 로 301 리다이렉트되던 경로였다. 그런데
 * 착지점인 facet URL 의 canonical 은 `/races` 라서, "마라톤 대회 일정" 같은
 * 종목 키워드가 전부 `/races` 한 장으로 흡수되고 정작 그 facet URL 들은
 * 색인되지 않은 채 크롤 예산만 소모했다. 그래서 리다이렉트를 걷어내고
 * self-canonical 랜딩 페이지로 만든다.
 *
 * 랜딩 페이지가 대회 목록만 나열하면 `/races` 와 사실상 같은 페이지가 되어
 * 똑같이 "크롤링됨 - 현재 색인 생성되지 않음" 으로 떨어진다. 그래서 종목마다
 * 시즌·거리·준비물·FAQ 를 다르게 채워 각 페이지가 독립적으로 읽히게 한다.
 */

export interface SportFaq {
	q: string;
	a: string;
}

export interface SportDistance {
	/** 종목/코스 이름 (예: '하프') */
	label: string;
	/** 거리 표기 (예: '21.0975km') */
	spec: string;
	note: string;
}

export interface SportRelatedLink {
	href: string;
	label: string;
	desc: string;
}

export interface SportLandingContent {
	/** 라우트 경로 (canonical 과 동일) */
	path: string;
	/** API 의 sport 필터 값 */
	sport: Sport;
	/** 사람이 읽는 종목명 */
	label: string;
	h1: string;
	/** {year} 는 렌더 시점의 연도로 치환된다. */
	metaTitle: string;
	metaDescription: string;
	ogImage: string;
	/** 첫 문단 — 이 종목의 국내 대회 판을 한 문단으로 */
	lede: string;
	/** 시즌 분포 한 줄 */
	season: string;
	distances: SportDistance[];
	/** 요강에서 먼저 확인해야 하는 항목 */
	checklist: string[];
	faqs: SportFaq[];
	related: SportRelatedLink[];
}

const TOOL_PACE: SportRelatedLink = {
	href: '/tools/pace-calculator',
	label: '페이스 계산기',
	desc: '목표 시간에서 구간별 페이스를 역산',
};
const TOOL_PREDICT: SportRelatedLink = {
	href: '/tools/race-predictor',
	label: '기록 예측기',
	desc: '최근 기록으로 다른 거리의 예상 기록 산출',
};
const TOOL_PLAN: SportRelatedLink = {
	href: '/tools/training-plan',
	label: '훈련 플랜',
	desc: '목표 대회까지 남은 주차를 단계별로 구성',
};
const TOOL_VO2: SportRelatedLink = {
	href: '/tools/vo2max',
	label: 'VO₂max 계산기',
	desc: '기록으로 유산소 능력 추정',
};
const LINK_CALENDAR: SportRelatedLink = {
	href: '/calendar',
	label: '대회 캘린더',
	desc: '월별로 펼쳐 보는 전체 대회 일정',
};
const LINK_TERMS: SportRelatedLink = {
	href: '/running-terms',
	label: '러닝 용어 사전',
	desc: '페이스 · LSD · 인터벌 · 컷오프 등 용어 정리',
};

export const SPORT_LANDINGS: SportLandingContent[] = [
	{
		path: '/running',
		sport: 'running',
		label: '마라톤',
		h1: '국내 마라톤 대회 일정',
		metaTitle: '마라톤 대회 일정 {year} — 국내 풀·하프·10K 접수 정보',
		metaDescription:
			'{year}년 국내 마라톤 대회 일정을 한곳에서. 5K·10K·하프·풀코스 종목과 접수 시작·마감일, 참가비를 대회별로 정리했습니다.',
		ogImage: '/images/og-running.png',
		lede: '국내 마라톤 대회는 봄(3~4월)과 가을(9~11월)에 가장 촘촘하게 열립니다. 같은 대회라도 5km·10km·하프·풀코스로 종목이 나뉘고, 접수는 보통 대회일 2~3개월 전에 열려 인기 대회는 오픈 며칠 만에 마감되기도 합니다. 엔듀로허브는 대회별 접수 시작·마감일과 종목별 참가비를 모아 갱신합니다.',
		season: '봄(3~4월)과 가을(9~11월)에 집중되고, 한여름에는 야간 대회가 늘어납니다.',
		distances: [
			{ label: '5K', spec: '5km', note: '첫 대회로 가장 많이 선택하는 거리' },
			{ label: '10K', spec: '10km', note: '참가 인원이 가장 많은 대중적인 거리' },
			{ label: '하프', spec: '21.0975km', note: '풀코스 전 단계. 12~16주 준비를 권장' },
			{ label: '풀코스', spec: '42.195km', note: '표준 마라톤 거리. 컷오프는 5시간 안팎이 일반적' },
			{ label: '울트라', spec: '50km 이상', note: '표준 거리가 없고 대회마다 코스가 다름' },
		],
		checklist: [
			'접수 마감일과 정원 소진 여부',
			'기록칩(넷타임) 측정 여부',
			'종목별 컷오프 시간',
			'배번 수령 방법 — 사전 수령인지 당일인지',
			'물품보관소·셔틀버스 운영',
		],
		faqs: [
			{
				q: '마라톤 대회 접수는 언제 시작하나요?',
				a: '대부분 대회일 2~3개월 전에 열립니다. 참가 정원이 정해져 있어 인기 대회는 며칠 만에 마감되므로, 관심 대회의 접수 시작일을 미리 확인해 두는 편이 안전합니다.',
			},
			{
				q: '첫 마라톤은 어떤 거리로 시작하는 게 좋나요?',
				a: '쉬지 않고 30분 정도 달릴 수 있다면 10km가 무난합니다. 달리기를 막 시작했다면 5km부터 참가해 출발 혼잡·급수대 이용 같은 대회 흐름에 먼저 익숙해지는 것을 권합니다.',
			},
			{
				q: '참가비는 보통 얼마인가요?',
				a: '국내 대회 기준 5~10km는 3만원 안팎, 하프·풀코스는 4~7만원대가 일반적입니다. 기념품 구성과 기록 측정 여부에 따라 달라지므로 대회별 상세 페이지에서 확인하세요.',
			},
			{
				q: '기록은 어떻게 측정되나요?',
				a: '규모가 있는 대회는 배번에 부착된 기록칩으로 측정합니다. 출발 매트를 통과한 시점부터 재는 넷타임과 출발 신호 기준의 그로스타임이 함께 제공되는 경우가 많습니다.',
			},
		],
		related: [TOOL_PACE, TOOL_PREDICT, TOOL_PLAN, LINK_CALENDAR],
	},
	{
		path: '/swimming',
		sport: 'swimming',
		label: '수영',
		h1: '국내 수영 대회 일정',
		metaTitle: '수영 대회 일정 {year} — 오픈워터·경영 대회 접수 정보',
		metaDescription:
			'{year}년 국내 수영 대회 일정을 한곳에서. 바다·호수 오픈워터와 실내 경영 대회의 접수 기간, 거리별 종목과 참가비를 정리했습니다.',
		ogImage: '/images/og-swimming.png',
		lede: '국내 수영 대회는 실내 수영장에서 열리는 경영 대회와, 바다·호수·강에서 열리는 오픈워터로 나뉩니다. 야외 대회는 수온이 오르는 6~9월에 몰려 있고 1.5km·3km·5km 구성이 일반적입니다. 오픈워터는 벽도 레인도 없어, 같은 거리라도 실내 기록보다 느려지는 것이 정상입니다.',
		season: '오픈워터는 수온이 오르는 6~9월에 집중되고, 실내 경영 대회는 연중 열립니다.',
		distances: [
			{ label: '1.5K', spec: '1.5km', note: '오픈워터 입문 거리. 철인3종 표준 코스의 수영 구간과 동일' },
			{ label: '3K', spec: '3km', note: '실내에서 3km를 쉬지 않고 헤엄칠 수 있으면 도전 가능' },
			{ label: '5K', spec: '5km', note: '장거리 오픈워터. 조류·파도 대응 경험이 필요' },
		],
		checklist: [
			'수온과 웻슈트 착용 허용/의무 여부',
			'조류·시야 등 코스 특성',
			'안전요원·구간 부표 운영',
			'컷오프 시간',
			'수영 실력 증빙(완영 기록) 요구 여부',
		],
		faqs: [
			{
				q: '오픈워터는 수영장과 무엇이 다른가요?',
				a: '벽과 레인이 없어 방향을 스스로 잡아야 하고(사이팅), 파도·조류·수온·시야가 매번 다릅니다. 같은 거리라도 실내 기록보다 느려지는 것이 일반적입니다.',
			},
			{
				q: '웻슈트를 반드시 입어야 하나요?',
				a: '대회 규정과 수온에 따라 다릅니다. 수온이 낮으면 착용을 의무화하고, 반대로 수온이 높으면 금지하는 대회도 있으므로 요강을 반드시 확인하세요.',
			},
			{
				q: '입문 거리는 어느 정도가 좋나요?',
				a: '실내에서 1,500m를 쉬지 않고 완영할 수 있다면 1.5km 오픈워터를 권합니다. 그 전이라면 실내 경영 대회로 먼저 경험을 쌓는 편이 안전합니다.',
			},
		],
		related: [LINK_CALENDAR, TOOL_PLAN, LINK_TERMS],
	},
	{
		path: '/cycling',
		sport: 'cycling',
		label: '자전거',
		h1: '국내 자전거 대회 일정',
		metaTitle: '자전거 대회 일정 {year} — 그란폰도·업힐 대회 접수 정보',
		metaDescription:
			'{year}년 국내 자전거 대회 일정을 한곳에서. 그란폰도·메디오폰도·업힐 대회의 접수 기간과 코스 거리, 참가비를 정리했습니다.',
		ogImage: '/images/og-cycling.png',
		lede: '국내 자전거 대회는 순위를 다투는 경기보다, 정해진 코스를 제한 시간 안에 완주하는 그란폰도·랠리 형식이 주를 이룹니다. 4~10월에 열리고 100km 안팎의 메디오와 150km 이상의 그란폰도로 나뉘는 경우가 많습니다. 업힐 대회는 거리가 짧은 대신 경사와 누적 상승고도가 난이도를 결정합니다.',
		season: '4~10월에 집중되며, 한여름에는 이른 아침 출발이나 고지대 코스가 많습니다.',
		distances: [
			{ label: '메디오폰도', spec: '60~110km', note: '하루 라이딩 경험이 있으면 완주할 만한 구간' },
			{ label: '그란폰도', spec: '130~200km', note: '보급과 페이스 배분이 중요해지는 장거리' },
			{ label: '업힐', spec: '5~20km', note: '거리는 짧고 경사·상승고도로 난이도가 갈림' },
		],
		checklist: [
			'구간별 컷오프와 관문 통과 시간',
			'누적 상승고도',
			'보급소 간격과 제공 품목',
			'헬멧 착용·차량 통제 등 안전 규정',
			'완주 인증 방식(기록칩·체크포인트)',
		],
		faqs: [
			{
				q: '입문자는 어느 거리부터 시작하면 되나요?',
				a: '평지 기준 60~80km를 쉬지 않고 탈 수 있다면 메디오폰도부터 시작하는 것이 무난합니다. 코스의 누적 상승고도를 함께 확인하면 체감 난이도를 가늠하기 좋습니다.',
			},
			{
				q: '헬멧은 필수인가요?',
				a: '국내 대회는 사실상 모두 헬멧 착용을 의무로 하며, 미착용 시 출발이 제한됩니다. 대회에 따라 자전거 정비 상태를 사전 점검하기도 합니다.',
			},
			{
				q: '그란폰도는 순위 경쟁인가요?',
				a: '대회마다 다릅니다. 완주 중심으로 운영하면서 특정 업힐 구간의 기록만 따로 집계하는 방식이 흔합니다. 요강의 기록 집계 방식을 확인하세요.',
			},
		],
		related: [LINK_CALENDAR, TOOL_PLAN, LINK_TERMS],
	},
	{
		path: '/triathlon',
		sport: 'triathlon',
		label: '철인3종',
		h1: '국내 철인3종 대회 일정',
		metaTitle: '철인3종 대회 일정 {year} — 스프린트·올림픽·하프 접수 정보',
		metaDescription:
			'{year}년 국내 철인3종 대회 일정을 한곳에서. 스프린트·올림픽(표준)·하프·풀 코스의 접수 기간과 구간별 거리, 참가비를 정리했습니다.',
		ogImage: '/images/og-triathlon.png',
		lede: '철인3종은 수영·사이클·달리기를 쉬지 않고 이어 치르는 종목입니다. 국내 대회는 수온이 오르는 5~9월에 집중되고, 거리 구성에 따라 스프린트·올림픽(표준)·하프·풀로 나뉩니다. 세 종목 기록만큼이나 종목 사이 전환구간(트랜지션) 운영이 총 기록에 크게 작용합니다.',
		season: '수온이 오르는 5~9월에 집중됩니다.',
		distances: [
			{ label: '스프린트', spec: '수영 750m · 사이클 20km · 달리기 5km', note: '입문자용 표준 구성' },
			{ label: '올림픽(표준)', spec: '1.5km · 40km · 10km', note: '국내 대회에서 가장 흔한 구성' },
			{ label: '하프', spec: '1.9km · 90km · 21.1km', note: '보급·페이스 전략이 필요한 장거리' },
			{ label: '풀', spec: '3.8km · 180km · 42.2km', note: '하루 종일 이어지는 최장 구성' },
		],
		checklist: [
			'수온과 웻슈트 규정',
			'트랜지션 구역 반입 물품과 배치 규칙',
			'드래프팅 허용 여부',
			'구간별 컷오프',
			'자전거 검차 일정',
		],
		faqs: [
			{
				q: '어떤 거리로 시작해야 하나요?',
				a: '수영 750m를 쉬지 않고 할 수 있다면 스프린트가 적당합니다. 세 종목을 이어서 치르는 감각과 트랜지션 흐름을 먼저 익히는 것이 거리보다 중요합니다.',
			},
			{
				q: '어떤 장비가 필요한가요?',
				a: '자전거와 헬멧, 수경이 기본이고 수온에 따라 웻슈트가 필요합니다. 입문 단계에서는 보유한 로드바이크나 하이브리드로도 참가할 수 있는 대회가 많습니다.',
			},
			{
				q: '드래프팅이 허용되나요?',
				a: '국내 동호인 대회는 대부분 드래프팅(앞 선수 뒤에 붙어 주행)을 금지하며, 앞 선수와 일정 간격을 유지해야 합니다. 위반 시 페널티가 부과됩니다.',
			},
		],
		related: [LINK_CALENDAR, TOOL_PACE, TOOL_PLAN],
	},
	{
		path: '/trail-running',
		sport: 'trail_running',
		label: '트레일러닝',
		h1: '국내 트레일러닝 대회 일정',
		metaTitle: '트레일러닝 대회 일정 {year} — 국내 트레일런·울트라 접수 정보',
		metaDescription:
			'{year}년 국내 트레일러닝 대회 일정을 한곳에서. 거리별 코스와 누적 상승고도, 접수 기간과 참가비, 필수 장비 확인 사항을 정리했습니다.',
		ogImage: '/images/og-trail-running.png',
		lede: '트레일러닝은 산길·임도처럼 포장되지 않은 코스를 달리는 종목입니다. 같은 거리라도 누적 상승고도(D+)에 따라 체감 난이도가 크게 달라지기 때문에, 거리보다 고도와 컷오프를 먼저 확인해야 합니다. 국내 대회는 봄과 가을에 몰려 있고, 대부분 필수 장비 검사를 거쳐 출발합니다.',
		season: '봄(4~6월)과 가을(9~11월)에 집중됩니다.',
		distances: [
			{ label: '입문', spec: '10~20km', note: '등산 경험이 있으면 도전할 만한 구간' },
			{ label: '중거리', spec: '25~35km', note: '보급과 페이스 배분이 필요해지는 지점' },
			{ label: '울트라', spec: '50km 내외', note: '울트라 입문. 야간 구간이 포함되기도 함' },
			{ label: '장거리 울트라', spec: '100km 이상', note: '수면·보급 전략까지 필요한 장거리' },
		],
		checklist: [
			'누적 상승고도(D+)',
			'구간별 컷오프와 관문 위치',
			'필수 장비 목록과 출발 전 검사 여부',
			'보급소 간격과 드롭백 운영',
			'야간 구간 포함 여부',
		],
		faqs: [
			{
				q: '필수 장비가 따로 있나요?',
				a: '대부분의 대회가 물통·헤드램프·방수 재킷·휴대전화·비상식량 등을 필수 장비로 지정하고 출발 전에 확인합니다. 대회마다 목록이 다르므로 요강을 반드시 확인하세요.',
			},
			{
				q: '도로 마라톤과 무엇이 다른가요?',
				a: '오르막에서는 걷는 것이 정상이고, 내리막과 기술 구간에서 시간이 갈립니다. 같은 거리라도 도로 마라톤보다 훨씬 오래 걸리므로 페이스가 아니라 소요 시간으로 계획을 세웁니다.',
			},
			{
				q: '어느 거리부터 시작하는 게 좋나요?',
				a: '10km 로드를 무리 없이 달리고 등산 경험이 있다면 10~20km 구간을 권합니다. 누적 상승고도가 1,000m를 넘는 코스는 같은 거리라도 훨씬 어렵습니다.',
			},
		],
		related: [LINK_CALENDAR, TOOL_PACE, TOOL_VO2],
	},
];

const BY_PATH = new Map(SPORT_LANDINGS.map((c) => [c.path, c]));
const BY_SPORT = new Map(SPORT_LANDINGS.map((c) => [c.sport, c]));

export function getSportLanding(path: string): SportLandingContent {
	const found = BY_PATH.get(path);
	if (!found) throw new Error(`Unknown sport landing path: ${path}`);
	return found;
}

/**
 * 종목 링크는 facet URL(`/races?sport=X`)이 아니라 랜딩 페이지를 가리켜야 한다.
 * facet URL 은 noindex 라 링크 가치가 그대로 흘러가지 못하고, 랜딩 페이지가
 * 바로 그 종목 키워드를 받도록 만든 곳이다. 알 수 없는 종목이면 전체 목록으로.
 */
export function sportLandingPath(sport: Sport): string {
	return BY_SPORT.get(sport)?.path ?? '/races';
}

/** {year} 자리표시자를 실제 연도로 치환한다. */
export function withYear(text: string, year: number): string {
	return text.replaceAll('{year}', String(year));
}
