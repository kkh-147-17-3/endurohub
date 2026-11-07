export interface ToolPage {
	slug: string;
	path: string;
	title: string;
	description: string;
	h1: string;
	intro: string;
	useCases: readonly string[];
	steps: readonly string[];
	method: { explanation: string; formulas: readonly string[] };
	assumptions: readonly string[];
	faqs: readonly { question: string; answer: string }[];
	related: readonly { href: string; label: string; description: string }[];
}

/** Public descriptions of the calculations actually provided by the running tools. */
export const TOOL_PAGES: readonly ToolPage[] = [
	{
		slug: 'pace-calculator', path: '/tools/pace-calculator',
		title: '마라톤 페이스 계산기 — 5km·10km·하프·풀 목표 시간 | 엔듀로허브',
		description: '5km·10km·하프·풀코스 거리와 목표 완주 시간으로 km당 페이스, 평균 속도, 주요 구간 통과 시간을 계산하세요. 계산 방법과 일정한 페이스의 가정도 확인할 수 있습니다.',
		h1: '마라톤 페이스 계산기',
		intro: '달릴 거리와 목표 완주 시간을 선택하면 km당 페이스와 평균 속도, 주요 구간의 예상 통과 시간을 확인할 수 있습니다.',
		useCases: ['10km 50분 목표의 km당 페이스 확인', '하프·풀코스 목표 시간의 구간 통과 시간 비교'],
		steps: [
			'5K·10K·하프·풀코스 중 달릴 거리를 선택합니다.',
			'목표 완주 시간을 시:분:초 또는 분:초로 입력합니다. 10km 50분은 50:00으로 입력합니다.',
			'km당 페이스와 평균 속도를 확인하고, 표에서 주요 지점까지의 누적 통과 시간을 읽습니다.',
		],
		method: {
			explanation: '완주 시간을 거리로 나누어 일정한 페이스를 구합니다. 예를 들어 10km를 50분에 달리는 경우 페이스는 5분/km, 평균 속도는 12km/h입니다.',
			formulas: ['페이스(초/km) = 완주 시간(초) ÷ 거리(km)', '속도(km/h) = 거리(km) ÷ 완주 시간(시간)', '구간 통과 시간 = 페이스(초/km) × 누적 거리(km)'],
		},
		assumptions: [
			'처음부터 끝까지 같은 페이스로 달리는 단순 환산입니다. 코스 경사·혼잡·급수 정차 등은 반영하지 않습니다.',
			'표는 5km 단위 주요 지점과 하프·풀코스 지점 중 선택한 거리 이내의 누적 시간을 표시합니다.',
		],
		faqs: [
			{ question: '하프와 풀코스의 기준 거리는 얼마인가요?', answer: '이 계산기는 하프 21.0975km, 풀코스 42.195km를 사용합니다. 5K와 10K는 각각 5km와 10km입니다.' },
			{ question: '표의 시간은 구간별 시간인가요?', answer: '출발부터 해당 거리까지의 누적 시간입니다. 10km 행은 직전 지점부터 걸린 시간이 아니라 출발 후 10km까지의 통과 시간입니다.' },
			{ question: '로그인해야 계산할 수 있나요?', answer: '직접 거리와 시간을 입력하는 계산은 로그인 없이 사용할 수 있습니다. 로그인한 회원은 저장한 러닝·트레일 기록이 있으면 입력에 활용할 수 있습니다.' },
		],
		related: [
			{ href: '/tools/race-predictor', label: '대회 기록 예측', description: '최근 기록으로 다른 거리의 예상 기록 비교' },
			{ href: '/running', label: '마라톤 대회 일정', description: '5km·10km·하프·풀코스 대회 찾기' },
			{ href: '/running-terms', label: '러닝 용어 사전', description: '페이스·넷타임·컷오프 등 용어 확인' },
		],
	},
	{
		slug: 'vo2max', path: '/tools/vo2max',
		title: 'VDOT 계산기 — 러닝 기록의 수행 지수와 동등 기록 | 엔듀로허브',
		description: '5km·10km·하프·풀코스 기록으로 VDOT와 같은 지수의 거리별 동등 기록을 비교하세요. 실제 측정 VO₂max와의 차이, 기록 기반 계산식과 가정을 함께 설명합니다.',
		h1: '러닝 VDOT 계산기와 동등 기록 비교',
		intro: '최근 달린 거리와 기록으로 VDOT 근사값을 계산하고, 같은 지수에 해당하는 다른 거리의 동등 기록을 비교합니다.',
		useCases: ['최근 5km·10km 기록으로 VDOT 비교', '같은 VDOT에 해당하는 하프·풀코스 기록 살펴보기'],
		steps: [
			'기준으로 사용할 러닝 거리와 완주 기록을 입력합니다.',
			'기록 기반으로 계산한 VDOT 값을 확인합니다.',
			'같은 지수를 사용한 거리별 동등 기록을 비교합니다.',
		],
		method: {
			explanation: 'Daniels·Gilbert VDOT 근사식에 거리와 완주 시간을 넣습니다. 거리별 동등 기록은 각 거리에서 같은 VDOT가 되는 시간을 역으로 찾는 방식입니다.',
			formulas: ['t = 완주 시간(분), v = 거리(m) ÷ t', '산소 비용 근사값 = -4.6 + 0.182258v + 0.000104v²', 'VDOT = 산소 비용 근사값 ÷ (0.8 + 0.1894393e^(-0.012778t) + 0.2989558e^(-0.1932605t))'],
		},
		assumptions: [
			'VDOT는 러닝 기록에서 계산하는 참고 지표입니다. 호흡가스를 측정한 VO₂max 값과 동일한 측정 결과가 아닙니다.',
			'코스 경사·날씨·피로·거리 측정 오차와 개인별 달리기 효율은 따로 입력받지 않습니다.',
			'동등 기록은 계산상 같은 지수가 되는 값입니다. 연령별 순위나 개인별 훈련 강도·실제 완주 가능성을 판정하지 않습니다.',
		],
		faqs: [
			{ question: 'VO₂max를 직접 측정하는 계산기인가요?', answer: '러닝 기록으로 VDOT 근사값을 계산하는 도구입니다. 실제 산소 섭취량을 측정하는 검사나 기기의 실측 기능은 제공하지 않습니다.' },
			{ question: '동등 기록은 다음 대회에서 낼 수 있는 기록인가요?', answer: '같은 VDOT를 만드는 수학적 환산값입니다. 거리별 준비 경험과 당일 조건은 평가하지 않으므로 실제 결과를 보장하지 않습니다.' },
			{ question: '연령별 상위 몇 퍼센트인지 알 수 있나요?', answer: '이 도구는 연령·성별과 비교 모집단을 입력받지 않으므로 백분위나 동연령 순위를 계산하지 않습니다.' },
		],
		related: [
			{ href: '/tools/pace-calculator', label: '페이스 계산기', description: '거리와 목표 시간으로 일정한 페이스 환산' },
			{ href: '/tools/race-predictor', label: '대회 기록 예측', description: 'Riegel 모델의 거리별 예상 기록과 비교' },
			{ href: '/running-terms', label: '러닝 용어 사전', description: 'VDOT·페이스 등 러닝 용어 확인' },
		],
	},
	{
		slug: 'race-predictor', path: '/tools/race-predictor',
		title: '마라톤 기록 예측기 — 10km·하프·풀 예상 기록 | 엔듀로허브',
		description: '최근 5km·10km·하프·풀코스 기록을 Riegel 모델로 환산해 거리별 예상 완주 시간과 평균 페이스를 비교하세요. 지수 1.06의 계산 방식과 예측의 한계를 설명합니다.',
		h1: '마라톤 대회 기록 예측기',
		intro: '최근 달린 거리와 기록을 기준으로 5km·10km·하프·풀코스의 예상 완주 시간과 평균 페이스를 비교합니다.',
		useCases: ['10km 기록을 기준으로 하프 예상 기록 비교', '하프 기록을 기준으로 풀코스 목표 검토'],
		steps: [
			'최근 기록의 기준 거리와 완주 시간을 입력합니다.',
			'거리별 표에서 예상 기록과 평균 페이스를 확인합니다.',
			'기준 기록의 코스와 목표 대회의 조건 차이를 함께 고려해 결과를 참고합니다.',
		],
		method: {
			explanation: 'Riegel 모델의 지수를 1.06으로 고정해 기준 거리의 완주 시간을 다른 거리로 환산합니다. 기준 거리와 같은 행은 입력 기록과 같은 값입니다.',
			formulas: ['예상 시간 T₂ = 기준 시간 T₁ × (목표 거리 D₂ ÷ 기준 거리 D₁)^1.06'],
		},
		assumptions: [
			'입력 기록과 비슷한 달리기 상태·코스 조건을 가정한 수학적 환산입니다. 코스 경사·날씨·보급·개인별 지구력은 따로 입력받지 않습니다.',
			'짧은 거리 기록만으로 장거리 준비 상태를 확인할 수는 없습니다. 실제 완주 기록을 보장하는 값이 아닙니다.',
		],
		faqs: [
			{ question: '목표 시간을 직접 달성할 수 있다는 뜻인가요?', answer: '입력한 기록을 다른 거리로 환산한 예상값입니다. 목표 거리의 훈련 경험이나 당일 조건은 확인하지 않으므로 달성 여부를 판정하지 않습니다.' },
			{ question: '페이스 계산기와 어떤 차이가 있나요?', answer: '페이스 계산기는 선택한 거리와 목표 시간을 단순히 나눕니다. 기록 예측기는 Riegel 모델을 이용해 거리가 바뀔 때 예상 완주 시간도 함께 바꿉니다.' },
			{ question: '어떤 거리의 기록을 비교할 수 있나요?', answer: '현재 화면에서는 5km, 10km, 하프 21.0975km, 풀코스 42.195km를 비교합니다.' },
		],
		related: [
			{ href: '/tools/pace-calculator', label: '페이스 계산기', description: '예상 기록의 주요 구간 통과 시간 확인' },
			{ href: '/running', label: '마라톤 대회 일정', description: '비교한 거리의 실제 대회 찾기' },
			{ href: '/tools/vo2max', label: 'VDOT 계산기', description: '같은 기록으로 VDOT 참고값 확인' },
		],
	},
	{
		slug: 'training-plan', path: '/tools/training-plan',
		title: '풀코스 마라톤 훈련 플랜 — 16주 공개 예시와 주차별 구성 | 엔듀로허브',
		description: '로그인 없이 16주 풀코스 마라톤 참고 플랜을 살펴보세요. BASE·BUILD·PEAK·TAPER의 구성과 상대 부하를 확인하고, 로그인 후 풀코스를 제공하는 관심 대회 일정으로 주차를 구성할 수 있습니다.',
		h1: '풀코스 마라톤 훈련 플랜과 16주 예시',
		intro: '가상의 풀코스 목표를 사용한 16주 공개 예시를 살펴보세요. 로그인한 회원은 풀코스를 제공하는 러닝 관심 대회 일정으로 주차별 참고 구성을 볼 수 있습니다.',
		useCases: ['16주 마라톤 플랜의 네 단계 구성 살펴보기', '관심 대회까지 남은 기간에 따른 주차 구성 비교'],
		steps: [
			'공개 예시에서는 가상의 목표와 16주 구성을 확인합니다.',
			'로그인 후 풀코스를 제공하는 러닝 대회를 관심 목록에 추가하면, 조건에 맞는 대회가 목표 후보로 표시됩니다.',
			'목표 대회까지 남은 기간 안에서 구성을 선택하고 단계별 주차와 참고 내용을 살펴봅니다.',
		],
		method: {
			explanation: '이 서비스의 규칙에 따라 전체 기간을 BASE·BUILD·PEAK·TAPER로 나누어 주차와 상대 부하를 보여줍니다. 부하는 예시 플랜의 최대 주차를 100으로 한 비교값이며 일별 거리나 페이스 처방이 아닙니다.',
			formulas: ['전체 기간 → BASE / BUILD / PEAK / TAPER'],
		},
		assumptions: [
			'공개 예시는 실제 대회 일정이나 회원의 개인 훈련 계획을 뜻하지 않습니다.',
			'현재 훈련량·회복 상태·목표 거리별 준비 경험을 평가하지 않습니다. 주차별 단계의 구성 방식을 살펴보는 참고 자료입니다.',
			'개인 목표 목록은 개최일까지 한 달 이상 남고 취소·종료되지 않은 러닝 관심 대회 중 풀코스 42.195km를 제공하는 대회로 구성됩니다.',
		],
		faqs: [
			{ question: '로그인 없이도 플랜을 볼 수 있나요?', answer: '가상의 목표를 사용한 16주 공개 예시를 볼 수 있습니다. 실제 관심 대회를 목표로 선택하려면 로그인이 필요합니다.' },
			{ question: '관심 대회가 목표 목록에 보이지 않아요.', answer: '풀코스 42.195km를 제공하고 개최일까지 한 달 이상 남은 러닝 관심 대회가 대상입니다. 취소·종료된 대회나 하프만 제공하는 대회, 트레일 등 다른 종목은 목표 후보에 포함되지 않습니다.' },
			{ question: '목표 거리에 맞춘 개인별 훈련 처방인가요?', answer: '대회까지 남은 기간을 바탕으로 규칙에 따라 구성하는 참고 플랜입니다. 현재 훈련량이나 거리별 준비 상태를 평가한 개인별 처방 기능은 제공하지 않습니다.' },
		],
		related: [
			{ href: '/running', label: '목표 마라톤 대회 찾기', description: '다가오는 대회와 접수 정보 확인' },
			{ href: '/tools/pace-calculator', label: '페이스 계산기', description: '거리와 목표 시간으로 페이스 환산' },
			{ href: '/running-terms', label: '러닝 용어 사전', description: '베이스·테이퍼 등 용어 확인' },
		],
	},
];

export function getToolPage(path: string): ToolPage | undefined {
	return TOOL_PAGES.find((tool) => tool.path === path);
}
