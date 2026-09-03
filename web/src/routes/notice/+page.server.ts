import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import type { NoticeCategory, NoticeListResponse } from './notices';

const COFFEE_EVENT = {
	id: 0,
	href: '/notice/coffee-coupon-event',
	category: 'event' as const,
	categoryLabel: '이벤트',
	title: '스타벅스 카페 아메리카노 T 이벤트',
	date: '2026·09·03',
	views: 0,
	pinned: false,
	urgent: false
};

export const load: PageServerLoad = async ({ url }) => {
	const tab = (url.searchParams.get('tab') ?? 'all') as NoticeCategory | 'all';

	const validTabs = ['all', 'notice', 'racenews', 'event', 'urgent'] as const;
	const activeTab = validTabs.includes(tab as (typeof validTabs)[number]) ? tab : 'all';

	const resp = await apiFetch<NoticeListResponse>(
		'/notices/',
		{},
		{ tab: activeTab === 'all' ? undefined : activeTab }
	);

	const showCoffeeEvent = activeTab === 'all' || activeTab === 'event';
	const notices = showCoffeeEvent ? [COFFEE_EVENT, ...resp.data] : resp.data;
	const counts = {
		...resp.counts,
		all: resp.counts.all + 1,
		event: resp.counts.event + 1
	};

	return { notices, counts, activeTab };
};
