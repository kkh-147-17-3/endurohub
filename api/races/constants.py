SPORT_LABELS = {
    'running': '마라톤',
    'swimming': '수영',
    'cycling': '자전거',
    'triathlon': '철인3종',
    'trail_running': '트레일러닝',
}

STATUS_LABELS = {
    'upcoming': '예정',
    'registration_open': '접수중',
    'registration_closed': '접수마감',
    'finished': '종료',
}

SPORTS = [
    {'value': k, 'label': v}
    for k, v in SPORT_LABELS.items()
]

REGIONS = [
    '서울', '경기', '인천', '부산', '대구', '광주', '대전', '울산', '세종',
    '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주',
]

DISTANCE_CATEGORIES = {
    'running': [
        {'value': 'short', 'label': '10km 이하', 'type': 'range', 'min': 0, 'max': 10},
        {'value': 'half', 'label': '하프', 'type': 'range', 'min': 20, 'max': 22},
        {'value': 'full', 'label': '풀코스', 'type': 'range', 'min': 40, 'max': 43},
        {'value': 'ultra', 'label': '울트라', 'type': 'range', 'min': 50, 'max': 999},
        {'value': 'special', 'label': '특별종목', 'type': 'non_numeric'},
    ],
    'trail_running': [
        {'value': 'short', 'label': '20km 이하', 'type': 'range', 'min': 0, 'max': 20},
        {'value': 'middle', 'label': '21~50km', 'type': 'range', 'min': 21, 'max': 50},
        {'value': 'ultra', 'label': '울트라', 'type': 'range', 'min': 51, 'max': 999},
    ],
    'cycling': [
        {'value': 'mtb', 'label': 'MTB', 'type': 'keyword', 'keyword': 'MTB'},
        {'value': 'road', 'label': '로드', 'type': 'keyword', 'keyword': '로드'},
        {'value': 'granfondo', 'label': '그란폰도', 'type': 'keyword', 'keyword': '그란폰도'},
        {'value': 'mediofondo', 'label': '메디오폰도', 'type': 'keyword', 'keyword': '메디오폰도'},
    ],
    'triathlon': [
        {'value': 'half', 'label': '70.3 (하프)', 'type': 'keyword', 'keyword': '70.3'},
        {'value': 'full', 'label': '풀코스', 'type': 'keyword', 'keyword': '풀코스'},
    ],
    'swimming': [
        {'value': 'short', 'label': '1.5km 이하', 'type': 'range_m', 'min': 0, 'max': 1500},
        {'value': 'long', 'label': '1.5km 초과', 'type': 'range_m', 'min': 1501, 'max': 99999},
    ],
}
