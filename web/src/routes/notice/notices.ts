import type { EventBanner } from '$lib/popup';

// Types and constants for the notice pages. Data is served by the Django
// backend at /api/v1/notices/ — see +page.server.ts for the fetches.

export type NoticeCategory = 'urgent' | 'notice' | 'racenews' | 'event';

export const CAT_LABEL: Record<NoticeCategory, string> = {
  urgent:   '긴급',
  notice:   '공지',
  racenews: '대회소식',
  event:    '이벤트',
};

/** A notice row as returned by the list endpoint. */
export interface NoticeListItem {
  id: number;
  /** 정적 이벤트처럼 숫자 상세 페이지가 아닌 경로로 연결할 때 사용한다. */
  href?: string;
  category: NoticeCategory;
  categoryLabel: string;
  title: string;
  date: string;          // "YYYY·MM·DD"
  views: number;
  pinned: boolean;
  urgent: boolean;
}
// Note: the API camelCases responses, so `category_label` arrives as `categoryLabel`.

/** A notice as returned by the detail endpoint. */
export interface NoticeDetail extends NoticeListItem {
  content: string;       // sanitized HTML
  author: string;
  attachments: [string, string][] | null;  // [filename, size]
  relatedRace: string;
}

/** Minimal shape for prev/next navigation. */
export interface AdjacentNotice {
  id: number;
  href?: string;
  title: string;
  date: string;
}

export interface NoticeCounts {
  all: number;
  notice: number;
  racenews: number;
  event: number;
  urgent: number;
}

export interface NoticeListResponse {
  data: NoticeListItem[];
  counts: NoticeCounts;
}

export interface NoticeDetailResponse {
  notice: NoticeDetail;
  adjacent: { prev: AdjacentNotice | null; next: AdjacentNotice | null };
  /** 이 공지에 연결된 이벤트 배너 (django admin > 팝업 배너). 없으면 null. */
  event: EventBanner | null;
}
