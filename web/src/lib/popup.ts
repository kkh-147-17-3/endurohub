// 팝업 배너(이벤트 배너) — 관리자(django admin)의 "팝업 배너"에서 관리한다.
// 같은 페이로드를 팝업 모달과 공지 상세 상단 히어로가 함께 쓴다.

export interface EventStep {
	order: number;
	title: string;
	description: string;
}

export interface EventBanner {
	id: number;
	/** 내용이 바뀌면 값이 바뀐다 — "다시 보지 않기" 저장 키에 섞어 쓴다. */
	version: number;
	placement: 'home' | 'all';
	dismissDays: number;
	noticeId: number | null;
	/** CTA 링크. 비어 있으면 버튼을 렌더하지 않는다. */
	targetUrl: string;

	tag: string;
	headline: string;
	headlineAccent: string;
	subtitle: string;

	metaPeriod: string;
	metaWinners: string;
	showDday: boolean;
	/** 마감까지 남은 일수. 종료일이 없으면 null. */
	dday: number | null;
	isLive: boolean;

	prizeImage: string;
	prizeNote: string;
	prizeName: string;
	prizeCount: string;

	ctaLabel: string;

	finePeriod: string;
	fineAnnounce: string;
	fineNote: string;

	steps: EventStep[];
}

export interface PopupActiveResponse {
	popup: EventBanner | null;
}

/** 배너 내용이 수정되면 키가 바뀌므로 닫아 둔 사람에게도 다시 뜬다. */
function dismissKey(banner: EventBanner): string {
	return `eh_popup_${banner.id}_${banner.version}`;
}

/** "다시 보지 않기" 기간이 아직 남아 있는가. */
export function isDismissed(banner: EventBanner): boolean {
	if (typeof localStorage === 'undefined') return false;
	try {
		const until = localStorage.getItem(dismissKey(banner));
		if (!until) return false;
		return Date.now() < Number(until);
	} catch {
		return false;
	}
}

/** 관리자가 지정한 일수만큼 숨긴다. */
export function dismissFor(banner: EventBanner, days: number): void {
	if (typeof localStorage === 'undefined') return;
	try {
		const until = Date.now() + Math.max(1, days) * 24 * 60 * 60 * 1000;
		localStorage.setItem(dismissKey(banner), String(until));
	} catch {
		// 시크릿 모드 등에서 localStorage 가 막혀 있으면 그냥 매번 뜬다.
	}
}

/** 헤드라인을 강조 단어 기준으로 쪼갠다 — {@html} 없이 <em> 을 넣기 위해. */
export function splitAccent(
	headline: string,
	accent: string
): { text: string; accent: boolean }[] {
	if (!accent || !headline.includes(accent)) return [{ text: headline, accent: false }];
	const out: { text: string; accent: boolean }[] = [];
	for (const chunk of headline.split(accent)) {
		out.push({ text: chunk, accent: false });
		out.push({ text: accent, accent: true });
	}
	out.pop(); // split 은 항상 조각이 하나 더 많다
	return out.filter((p) => p.text.length > 0);
}

/** "D-15" / "D-DAY" — 표시할 게 없으면 빈 문자열. */
export function ddayLabel(banner: EventBanner): string {
	if (!banner.showDday || banner.dday === null || banner.dday < 0) return '';
	return banner.dday === 0 ? 'D-DAY' : `D-${banner.dday}`;
}
