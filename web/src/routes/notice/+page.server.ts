import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import type { NoticeCategory, NoticeListResponse } from './notices';

export const load: PageServerLoad = async ({ url }) => {
	const tab = (url.searchParams.get('tab') ?? 'all') as NoticeCategory | 'all';

	const validTabs = ['all', 'notice', 'racenews', 'event', 'urgent'] as const;
	const activeTab = validTabs.includes(tab as (typeof validTabs)[number]) ? tab : 'all';

	const resp = await apiFetch<NoticeListResponse>(
		'/notices/',
		{},
		{ tab: activeTab === 'all' ? undefined : activeTab }
	);

	return { notices: resp.data, counts: resp.counts, activeTab };
};
