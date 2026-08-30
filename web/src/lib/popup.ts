// 팝업 배너(이벤트 배너) — 관리자(django admin)의 "팝업 배너"에서 관리한다.
// 내용은 이미지 한 장이고, 같은 페이로드를 팝업 모달과 공지 상세 상단
// 히어로가 함께 쓴다.

export interface EventBanner {
	id: number;
	/** 내용이 바뀌면 값이 바뀐다 — "다시 보지 않기" 저장 키에 섞어 쓴다. */
	version: number;
	placement: 'home' | 'all';
	dismissDays: number;
	noticeId: number | null;
	isLive: boolean;

	/** 배너 이미지 URL. 비어 있으면 띄울 내용이 없다. */
	image: string;
	imageAlt: string;
	/** 원본 크기 — <img width height> 로 자리를 미리 잡는다. */
	imageWidth: number | null;
	imageHeight: number | null;

	/** 이동 링크. 비어 있으면 이미지·버튼 모두 링크가 되지 않는다. */
	targetUrl: string;
	/** 버튼 문구. 비어 있으면 버튼 없이 이미지만 눌러 이동한다. */
	ctaLabel: string;
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
