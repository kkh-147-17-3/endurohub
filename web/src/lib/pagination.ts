import type { PaginatedResponse } from './types';

/**
 * API 기본 페이지 크기. api/core/pagination.py 의 StandardPagination.page_size
 * 와 일치해야 한다. 프론트에서 per_page 를 지정해 호출하지 않는 목록 엔드포인트는
 * 모두 이 크기로 페이지네이션된다.
 */
export const DEFAULT_PAGE_SIZE = 20;

export interface PaginationInfo {
	currentPage: number;
	lastPage: number;
	from: number;
	to: number;
	total: number;
	hasPrevious: boolean;
	hasNext: boolean;
}

/**
 * DRF 스타일 페이지네이션 응답(count/next/previous/results)에서 UI 렌더링에
 * 필요한 페이지 상태를 도출한다. currentPage 는 URL 의 page 파라미터에서
 * 가져온다(목록 페이지는 goto/href 로 page 파라미터를 바꾸므로 URL 이 기준).
 */
export function getPaginationInfo(
	paginated: Pick<PaginatedResponse<unknown>, 'count' | 'next' | 'previous'>,
	currentPage: number,
	pageSize: number = DEFAULT_PAGE_SIZE
): PaginationInfo {
	const total = paginated.count;
	const lastPage = Math.max(1, Math.ceil(total / pageSize));
	const from = total === 0 ? 0 : (currentPage - 1) * pageSize + 1;
	const to = Math.min(currentPage * pageSize, total);
	return {
		currentPage,
		lastPage,
		from,
		to,
		total,
		hasPrevious: paginated.previous !== null,
		hasNext: paginated.next !== null
	};
}

/** URL 검색 파라미터에서 현재 페이지 번호를 뽑는다. 없으면 1. */
export function currentPageFromUrl(url: URL): number {
	const page = Number(url.searchParams.get('page'));
	return Number.isInteger(page) && page > 0 ? page : 1;
}
