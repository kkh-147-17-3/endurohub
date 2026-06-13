/* ENDUROHUB — 러닝 용어 사전 데이터
   62개 용어 · 5개 카테고리 · 초성 / A-Z / 숫자 그룹.
   Ported from the Claude Design v2 handoff (data/terms.js).
   cat: train(훈련) · race(대회) · body(신체·체력) · gear(장비) · fuel(영양) */

export type GlossaryCategory = 'train' | 'race' | 'body' | 'gear' | 'fuel';

export interface GlossaryCat {
    id: GlossaryCategory | 'all';
    ko: string;
    en: string;
}

export interface GlossaryTerm {
    cat: GlossaryCategory;
    ko: string;
    en: string;
    short: string;
    def: string;
}

export interface GlossaryGroup {
    key: string;
    terms: GlossaryTerm[];
}

export const glossaryCats: GlossaryCat[] = [
    { id: 'all', ko: '전체', en: 'ALL' },
    { id: 'train', ko: '훈련', en: 'TRAINING' },
    { id: 'race', ko: '대회', en: 'RACE' },
    { id: 'body', ko: '신체·체력', en: 'BODY' },
    { id: 'gear', ko: '장비', en: 'GEAR' },
    { id: 'fuel', ko: '영양', en: 'FUEL' },
];

export const categoryLabels: Record<GlossaryCategory, string> = {
    train: '훈련',
    race: '대회',
    body: '신체·체력',
    gear: '장비',
    fuel: '영양',
};

export const glossaryGroups: GlossaryGroup[] = [
    {
        key: 'ㄱ',
        terms: [
            {
                cat: 'train',
                ko: '교차훈련',
                en: 'Cross Training',
                short: '달리기 외 보조 운동',
                def: '달리기 부하를 줄이면서 심폐 능력을 유지하기 위해 수영·자전거·로잉 등 비충격 운동으로 대체하는 훈련입니다. 부상 회복기나 고강도 주간 사이 회복일에 주로 배치합니다.',
            },
            {
                cat: 'body',
                ko: '과훈련 증후군',
                en: 'Overtraining Syndrome',
                short: '과도한 훈련으로 인한 만성 피로 상태',
                def: '회복이 부하를 따라가지 못해 나타나는 만성 피로 상태입니다. 안정시심박수 상승, 수면 장애, 기록 정체가 신호이며 해법은 더 많은 훈련이 아니라 휴식입니다.',
            },
            {
                cat: 'body',
                ko: '글리코겐',
                en: 'Glycogen',
                short: '근육과 간에 저장된 탄수화물 에너지',
                def: "탄수화물이 근육과 간에 저장된 형태로, 중·고강도 달리기의 주 연료입니다. 저장량이 한정적이어서 고갈되면 '벽'을 만나게 됩니다.",
            },
        ],
    },
    {
        key: 'ㄴ',
        terms: [
            {
                cat: 'race',
                ko: '네거티브 스플릿',
                en: 'Negative Split',
                short: '후반부를 전반부보다 빠르게 달리는 전략',
                def: '후반부를 전반부보다 빠르게 달리는 페이스 전략입니다. 초반 오버페이스를 막아 마라톤에서 가장 안정적으로 좋은 기록을 내는 방법으로 꼽힙니다.',
            },
            {
                cat: 'race',
                ko: '넷 타임 / 그로스 타임',
                en: 'Net / Gross Time',
                short: '실제 달린 시간 vs 총 경과 시간',
                def: '넷(net)은 출발선을 통과한 순간부터의 실제 기록, 그로스(gross)는 총성이 울린 시점부터의 기록입니다. 공식 순위는 보통 그로스, 개인 기록은 넷으로 판단합니다.',
            },
        ],
    },
    {
        key: 'ㄹ',
        terms: [
            {
                cat: 'train',
                ko: '롱런',
                en: 'Long Run',
                short: '주간 최장거리 달리기',
                def: '주간 훈련 중 가장 긴 거리를 편안한 페이스로 달리는 세션입니다. 모세혈관 밀도와 지방 대사 능력을 키우는 지구력 훈련의 핵심입니다.',
            },
            {
                cat: 'train',
                ko: '레이스 페이스',
                en: 'Race Pace',
                short: '목표 대회 완주 페이스',
                def: '목표 대회를 완주하려는 목표 페이스입니다. 훈련에서 이 페이스 구간을 반복해 몸에 각인시킵니다.',
            },
            {
                cat: 'train',
                ko: '리커버리 런',
                en: 'Recovery Run',
                short: '회복을 위한 가벼운 달리기',
                def: '고강도 세션 다음 날 매우 느리게 달려 혈류를 늘리고 회복을 돕는 짧은 달리기입니다. 기록이 아니라 회복이 목적이므로 페이스를 의식하지 않습니다.',
            },
            {
                cat: 'body',
                ko: '러너스 니',
                en: "Runner's Knee",
                short: '슬개대퇴 통증 증후군',
                def: '무릎 앞쪽 슬개골 주변 통증을 통칭합니다. 주행거리 급증, 약한 둔근, 내리막 부하가 주원인이며 보강 운동과 거리 조절로 관리합니다.',
            },
            {
                cat: 'gear',
                ko: '러닝 조끼 / 하이드레이션 팩',
                en: 'Hydration Vest',
                short: '물과 보급품을 넣는 러닝용 가방',
                def: '물·보급품·여벌 장비를 몸에 밀착해 휴대하는 러닝용 가방입니다. 장거리·트레일에서 보급소 간격이 길 때 필수입니다.',
            },
            {
                cat: 'fuel',
                ko: '러너스 스토마크',
                en: "Runner's Stomach",
                short: '달리기 중 위장 장애',
                def: '달리기 중 진동과 혈류 재분배로 생기는 복통·메스꺼움·급한 변의 등 위장 장애입니다. 출발 전 식사 타이밍과 보급 종류 조절로 줄일 수 있습니다.',
            },
        ],
    },
    {
        key: 'ㅂ',
        terms: [
            {
                cat: 'train',
                ko: '베이스 빌딩',
                en: 'Base Building',
                short: '유산소 기초 체력 구축 단계',
                def: '본격 훈련에 앞서 낮은 강도로 주간 거리를 쌓아 유산소 기초를 다지는 단계입니다. 이후 고강도 훈련을 감당할 토대를 만듭니다.',
            },
            {
                cat: 'train',
                ko: '브릭 훈련',
                en: 'Brick Training',
                short: '두 종목을 연이어 하는 복합 훈련',
                def: '자전거 직후 달리기처럼 두 종목을 쉬지 않고 이어 하는 복합 훈련입니다. 철인3종에서 전환 구간의 다리 감각에 적응하기 위해 합니다.',
            },
            {
                cat: 'race',
                ko: '벽',
                en: 'The Wall / Bonking',
                short: '글리코겐 고갈로 인한 급격한 체력 저하',
                def: "글리코겐이 고갈되며 갑자기 다리가 멈추듯 페이스가 무너지는 현상입니다. 마라톤 30km 부근에서 흔하며 사전 카보로딩과 레이스 중 보급으로 늦춥니다.",
            },
            {
                cat: 'race',
                ko: '배번',
                en: 'Bib Number',
                short: '레이스 참가 번호표',
                def: '참가자에게 부여되는 번호표로, 기록 측정 칩이 부착되는 경우가 많습니다. 가슴 정면에 잘 보이게 부착해야 사진·계측에 반영됩니다.',
            },
        ],
    },
    {
        key: 'ㅅ',
        terms: [
            {
                cat: 'train',
                ko: '스트라이드',
                en: 'Strides',
                short: '짧은 가속 달리기',
                def: '20~30초간 매끄럽게 가속했다 푸는 짧은 질주를 반복하는 훈련입니다. 신경근 협응과 달리기 폼을 다듬으며 레이스 전 워밍업으로도 씁니다.',
            },
            {
                cat: 'body',
                ko: '심박 존',
                en: 'Heart Rate Zone',
                short: '심박수 기반 훈련 강도 구간',
                def: '최대심박수 대비 비율로 나눈 훈련 강도 구간입니다. 존을 기준으로 회복·지구력·역치·VO₂max 훈련의 강도를 객관적으로 관리합니다.',
            },
            {
                cat: 'body',
                ko: '신 스플린트',
                en: 'Shin Splints',
                short: '정강이 통증',
                def: '정강이 안쪽을 따라 생기는 통증으로, 주행거리 급증이나 딱딱한 노면이 주원인입니다. 휴식과 점진적 부하 증가로 회복합니다.',
            },
            {
                cat: 'fuel',
                ko: '수분 보충',
                en: 'Hydration',
                short: '운동 중/후 수분 섭취',
                def: '운동 전·중·후 손실되는 수분을 보충하는 것입니다. 장시간 운동에서는 물만으로는 부족해 전해질을 함께 섭취해야 합니다.',
            },
        ],
    },
    {
        key: 'ㅇ',
        terms: [
            {
                cat: 'train',
                ko: '인터벌',
                en: 'Interval Training',
                short: '고강도 반복 훈련',
                def: 'VO₂max 부근의 고강도 구간과 회복 구간을 번갈아 반복하는 훈련입니다. 짧은 시간에 심폐 능력을 끌어올리지만 부상 위험이 커 빈도를 제한합니다.',
            },
            {
                cat: 'train',
                ko: '이지런',
                en: 'Easy Run',
                short: '편안한 회복 달리기',
                def: '대화가 가능한 편안한 강도로 달리는 회복·기초 지구력 달리기입니다. 전체 주간 거리의 대부분을 차지해야 하는 토대 훈련입니다.',
            },
            {
                cat: 'train',
                ko: '워밍업 / 쿨다운',
                en: 'Warm-up / Cool-down',
                short: '운동 전후 준비 및 정리 운동',
                def: '본운동 전 몸을 데우고(워밍업) 후에 서서히 진정시키는(쿨다운) 과정입니다. 부상 예방과 회복을 돕습니다.',
            },
            {
                cat: 'train',
                ko: '야소 800',
                en: 'Yasso 800s',
                short: '마라톤 기록 예측 훈련법',
                def: '800m를 목표 마라톤 기록의 분·초와 같은 시간에 달리는 인터벌로, 완주 기록을 가늠하는 훈련법입니다. 예: 3분 30초에 10회면 마라톤 3시간 30분.',
            },
            {
                cat: 'race',
                ko: '이븐 스플릿',
                en: 'Even Split',
                short: '전후반을 같은 페이스로 달리는 전략',
                def: '전반부와 후반부를 같은 페이스로 균등하게 달리는 전략입니다. 페이스 관리가 잘 된 안정적인 레이스의 지표로 봅니다.',
            },
            {
                cat: 'race',
                ko: '에이드 스테이션',
                en: 'Aid Station',
                short: '급수/급식 지점',
                def: '코스 곳곳에 설치된 급수·급식 지점입니다. 물·이온음료·간식이 제공되며 보급 계획의 기준점이 됩니다.',
            },
            {
                cat: 'race',
                ko: '웨이브 스타트',
                en: 'Wave Start',
                short: '시차를 두고 그룹별 출발',
                def: '참가자가 많을 때 기록대별 그룹을 시차를 두고 출발시키는 방식입니다. 초반 혼잡을 줄여 안전과 페이스 유지에 유리합니다.',
            },
            {
                cat: 'race',
                ko: '엑스포',
                en: 'Race Expo',
                short: '대회 전 참가자 등록 행사',
                def: '대회 전 배번·기념품을 수령하고 용품을 둘러보는 등록 행사입니다. 보통 대회 1~2일 전 개최됩니다.',
            },
            {
                cat: 'race',
                ko: '울트라마라톤',
                en: 'Ultra Marathon',
                short: '42.195km 이상의 초장거리 대회',
                def: '42.195km를 넘는 모든 초장거리 대회를 통칭합니다. 50km·100km·100마일 등이 대표적이며 보급·페이스 전략이 기록을 좌우합니다.',
            },
            {
                cat: 'body',
                ko: '유산소',
                en: 'Aerobic',
                short: '산소를 사용하는 에너지 시스템',
                def: '산소를 이용해 지방·탄수화물을 천천히 연소하는 에너지 시스템입니다. 장거리 지구력의 바탕이 되는 영역입니다.',
            },
            {
                cat: 'body',
                ko: '안정시심박수',
                en: 'Resting HR',
                short: '휴식 중 심박수',
                def: '완전한 휴식 상태에서 측정한 분당 심박수입니다. 며칠간 평소보다 높게 지속되면 피로·과훈련의 신호일 수 있습니다.',
            },
            {
                cat: 'gear',
                ko: '안티 차핑',
                en: 'Anti-Chafe',
                short: '피부 쓸림 방지 제품',
                def: '허벅지 안쪽·겨드랑이 등 반복 마찰로 살이 쓸리는 것을 막는 윤활 제품입니다. 장거리에서 바르지 않으면 통증으로 페이스가 무너질 수 있습니다.',
            },
            {
                cat: 'fuel',
                ko: '에너지젤',
                en: 'Energy Gel',
                short: '레이스 중 탄수화물 보충제',
                def: '레이스 중 빠르게 흡수되는 농축 탄수화물 보충제입니다. 보통 30~45분 간격으로 섭취해 글리코겐 고갈을 늦춥니다.',
            },
        ],
    },
    {
        key: 'ㅈ',
        terms: [
            {
                cat: 'train',
                ko: '주기화',
                en: 'Periodization',
                short: '체계적 훈련 단계 구분',
                def: '훈련을 베이스·빌드·피크·테이퍼 등 단계로 나눠 강도와 양을 계획적으로 조절하는 방법입니다. 목표 대회에 컨디션을 맞추는 설계도입니다.',
            },
            {
                cat: 'body',
                ko: '젖산역치',
                en: 'Lactate Threshold',
                short: '젖산이 급격히 쌓이기 시작하는 운동 강도',
                def: '젖산이 제거 속도보다 빠르게 쌓이기 시작하는 운동 강도입니다. 이 지점을 끌어올리는 것이 마라톤 기록 향상의 핵심입니다.',
            },
            {
                cat: 'body',
                ko: '족저근막염',
                en: 'Plantar Fasciitis',
                short: '발바닥 통증을 일으키는 흔한 부상',
                def: '발바닥 근막에 생기는 염증으로 아침 첫 발걸음의 통증이 특징입니다. 종아리·발바닥 유연성 부족과 과사용이 원인입니다.',
            },
            {
                cat: 'fuel',
                ko: '전해질',
                en: 'Electrolytes',
                short: '땀으로 손실되는 필수 미네랄',
                def: '땀으로 빠져나가는 나트륨·칼륨 등 미네랄입니다. 장시간 운동에서 부족하면 경련과 저나트륨혈증 위험이 있어 보충이 필요합니다.',
            },
        ],
    },
    {
        key: 'ㅊ',
        terms: [
            {
                cat: 'body',
                ko: '최대심박수',
                en: 'Max HR',
                short: '운동 중 도달할 수 있는 최대 심박수',
                def: '운동 중 도달할 수 있는 분당 최대 심박수입니다. 심박 존 설정의 기준값이며 실측이 공식 추정치보다 정확합니다.',
            },
        ],
    },
    {
        key: 'ㅋ',
        terms: [
            {
                cat: 'race',
                ko: '컷오프 타임',
                en: 'Cut-off Time',
                short: '제한 시간',
                def: '특정 지점이나 결승선을 통과해야 하는 제한 시간입니다. 초과하면 기록이 인정되지 않거나 중도 회수됩니다.',
            },
            {
                cat: 'race',
                ko: '코스 레코드',
                en: 'Course Record / CR',
                short: '특정 대회 코스 최고 기록',
                def: '해당 대회 코스에서 세워진 역대 최고 기록입니다. 코스 난이도를 가늠하는 지표가 되기도 합니다.',
            },
            {
                cat: 'body',
                ko: '케이던스 / 피치',
                en: 'Cadence',
                short: '분당 걸음 수',
                def: '1분당 걸음 수입니다. 보통 170~190spm가 효율 구간으로 여겨지며 보폭과 함께 페이스를 결정합니다.',
            },
            {
                cat: 'gear',
                ko: '카본 플레이트 슈즈',
                en: 'Carbon Plate Shoes',
                short: '탄소 섬유판이 내장된 레이싱 슈즈',
                def: '밑창에 탄소섬유판을 넣어 추진력을 높인 레이싱화입니다. 에너지 손실을 줄여 기록 단축에 기여하지만 가격과 내구성에서 손해를 봅니다.',
            },
            {
                cat: 'gear',
                ko: '컴프레션 웨어',
                en: 'Compression Wear',
                short: '착압 기능 스포츠 의류',
                def: '근육을 압박해 진동을 줄이고 회복을 돕는다고 알려진 착압 의류입니다. 효과는 개인차가 있으며 회복용으로 선호됩니다.',
            },
            {
                cat: 'fuel',
                ko: '카보로딩',
                en: 'Carb Loading',
                short: '대회 전 탄수화물 저장량 극대화',
                def: "대회 며칠 전부터 탄수화물 섭취를 늘려 글리코겐 저장량을 극대화하는 식이 전략입니다. 후반 '벽'을 늦추는 데 목적이 있습니다.",
            },
            {
                cat: 'fuel',
                ko: '카페인',
                en: 'Caffeine',
                short: '합법적 퍼포먼스 향상 보조제',
                def: '각성과 피로 인지를 낮춰 지구력에 도움을 주는 합법적 보조제입니다. 레이스 1시간 전 섭취가 일반적이며 위장 반응은 개인차가 큽니다.',
            },
        ],
    },
    {
        key: 'ㅌ',
        terms: [
            {
                cat: 'train',
                ko: '템포런',
                en: 'Tempo Run',
                short: '젖산역치 페이스 달리기',
                def: "젖산역치 부근의 '편안하게 힘든' 페이스를 일정 시간 유지하는 훈련입니다. 역치를 끌어올려 더 빠른 페이스를 오래 버티게 합니다.",
            },
            {
                cat: 'train',
                ko: '테이퍼',
                en: 'Taper',
                short: '대회 전 훈련량 감소 기간',
                def: '대회 1~3주 전 훈련량을 줄여 누적 피로를 빼고 컨디션을 끌어올리는 기간입니다. 강도는 유지하되 양만 줄이는 것이 핵심입니다.',
            },
        ],
    },
    {
        key: 'ㅍ',
        terms: [
            {
                cat: 'train',
                ko: '파틀렉',
                en: 'Fartlek',
                short: '자유로운 속도 변화 훈련',
                def: "정해진 구간 없이 지형·기분에 따라 자유롭게 속도를 바꾸는 스웨덴식 '스피드 플레이' 훈련입니다. 인터벌보다 유연해 즐겁게 강도를 넣을 수 있습니다.",
            },
            {
                cat: 'race',
                ko: '페이서 / 토끼',
                en: 'Pacer',
                short: '목표 기록 완주를 도와주는 주자',
                def: '목표 기록 완주를 돕기 위해 일정한 페이스로 달리는 주자입니다. 풍선이나 깃발로 목표 시간을 표시해 따라가게 합니다.',
            },
            {
                cat: 'body',
                ko: '프로네이션',
                en: 'Pronation',
                short: '발의 안쪽 회전 움직임',
                def: '착지 시 발이 안쪽으로 회전하며 충격을 흡수하는 자연스러운 움직임입니다. 과도하거나 부족하면 부상 위험이 커져 신발 선택에 영향을 줍니다.',
            },
            {
                cat: 'gear',
                ko: '폼롤러',
                en: 'Foam Roller',
                short: '근막 이완용 원통형 도구',
                def: '원통형 도구로 근막을 눌러 풀어 뭉친 근육을 이완하는 셀프 마사지 기구입니다. 회복과 가동범위 유지에 씁니다.',
            },
        ],
    },
    {
        key: 'ㅎ',
        terms: [
            {
                cat: 'train',
                ko: '힐 트레이닝',
                en: 'Hill Training',
                short: '오르막 반복 훈련',
                def: "오르막을 반복해 오르며 근력과 파워를 키우는 훈련입니다. '저충격 스피드 훈련'으로 불리며 폼 개선에도 도움이 됩니다.",
            },
            {
                cat: 'gear',
                ko: '헤드램프',
                en: 'Headlamp',
                short: '야간/새벽 달리기용 머리 조명',
                def: '야간·새벽·트레일 달리기에서 시야를 확보하는 머리 착용 조명입니다. 밝기(루멘)와 배터리 지속시간, 예비 배터리가 선택 기준입니다.',
            },
        ],
    },
    {
        key: 'A-Z',
        terms: [
            {
                cat: 'train',
                ko: 'LSD',
                en: 'Long Slow Distance',
                short: '장거리 저강도 달리기',
                def: '낮은 강도로 오래 달리는 장거리 지구력 훈련입니다. 지방 대사와 모세혈관을 발달시키는 베이스 훈련의 대표 격입니다.',
            },
            {
                cat: 'race',
                ko: 'DNS',
                en: 'Did Not Start',
                short: '출발하지 않음',
                def: '신청했으나 출발하지 않은 상태입니다. 부상·컨디션 난조로 레이스를 시작조차 하지 않은 경우입니다.',
            },
            {
                cat: 'race',
                ko: 'DNF',
                en: 'Did Not Finish',
                short: '완주하지 못함',
                def: '출발했으나 완주하지 못한 상태입니다. 컷오프 초과, 부상, 기권 등이 원인이며 무리한 완주보다 현명한 판단일 때도 있습니다.',
            },
            {
                cat: 'race',
                ko: 'PB / PR',
                en: 'Personal Best / Record',
                short: '개인 최고 기록',
                def: '같은 거리에서 자신이 세운 가장 빠른 기록입니다. 대회의 가장 보편적인 개인 목표입니다.',
            },
            {
                cat: 'race',
                ko: 'BQ',
                en: 'Boston Qualifier',
                short: '보스턴 마라톤 자격 기록',
                def: '보스턴 마라톤 출전 자격 기준 기록입니다. 연령·성별별 기준을 충족해야 신청 자격이 주어집니다.',
            },
            {
                cat: 'body',
                ko: 'VO₂max',
                en: '최대산소섭취량',
                short: '유산소 능력의 지표',
                def: '체중 1kg당 1분에 소비할 수 있는 최대 산소량으로, 유산소 능력의 상한을 나타내는 지표입니다. 훈련으로 높일 수 있으나 한계가 있습니다.',
            },
            {
                cat: 'body',
                ko: 'IT밴드 증후군',
                en: 'ITBS',
                short: '무릎 바깥쪽 통증',
                def: '허벅지 바깥쪽 장경인대가 무릎 바깥과 마찰해 생기는 통증입니다. 주행거리 급증과 약한 둔근이 원인으로 꼽힙니다.',
            },
            {
                cat: 'body',
                ko: 'DOMS',
                en: '지연성 근육통',
                short: '운동 후 24~72시간 뒤 근육통',
                def: '운동 24~72시간 뒤 나타나는 지연성 근육통입니다. 익숙지 않은 부하나 내리막 후 흔하며 보통 며칠 내 회복됩니다.',
            },
            {
                cat: 'gear',
                ko: 'GPS 워치',
                en: 'GPS Watch',
                short: 'GPS 기반 러닝 시계',
                def: '위성 신호로 거리·페이스·경로를 기록하는 러닝 시계입니다. 심박·고도·케이던스 등 훈련 데이터 관리의 중심 장비입니다.',
            },
        ],
    },
    {
        key: '0-9',
        terms: [
            {
                cat: 'train',
                ko: '10% 룰',
                en: '10% Rule',
                short: '주간 훈련량 증가 제한 원칙',
                def: '주간 주행거리를 한 번에 10% 넘게 늘리지 말라는 부상 예방 원칙입니다. 점진적 부하 증가로 몸이 적응할 시간을 줍니다.',
            },
        ],
    },
];

/* Flat list with group key — for counting / filtering / SEO. */
export const glossaryTerms: (GlossaryTerm & { group: string })[] = glossaryGroups.flatMap((g) =>
    g.terms.map((t) => ({ ...t, group: g.key }))
);
