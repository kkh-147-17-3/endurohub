<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import type { NoticeListItem, NoticeCategory } from './notices';
	import { CAT_LABEL } from './notices';

	let { data } = $props();

	// Tabs definition
	// Tabs mirror the design: 전체 / 공지 / 대회소식 / 이벤트 (urgent items surface
	// in the pinned block and under 전체, so no separate 긴급 tab).
	const tabDefs: { id: string; label: string }[] = [
		{ id: 'all',      label: '전체' },
		{ id: 'notice',   label: '공지' },
		{ id: 'racenews', label: '대회소식' },
		{ id: 'event',    label: '이벤트' },
	];

	function setTab(id: string) {
		const params = new URLSearchParams($page.url.searchParams);
		if (id === 'all') {
			params.delete('tab');
		} else {
			params.set('tab', id);
		}
		const qs = params.toString();
		goto(`/notice${qs ? '?' + qs : ''}`, { replaceState: true });
	}

	// Pinned notices (shown only on "all" tab)
	const pinned = $derived(
		data.activeTab === 'all' ? data.notices.filter((n: NoticeListItem) => n.pinned) : []
	);
	// Main list (pinned excluded when pinned block is shown)
	const list = $derived(
		data.activeTab === 'all'
			? data.notices.filter((n: NoticeListItem) => !n.pinned)
			: data.notices
	);
</script>

<svelte:head>
	<title>공지사항 · ENDUROHUB</title>
	<meta name="description" content="엔듀로허브 공지사항 — 운영 안내, 대회 소식, 이벤트를 확인하세요." />
</svelte:head>

<div class="notice-wrap">
	<!-- Page header -->
	<div class="page-hd">
		<div class="page-kicker eh-micro"><span class="acc">NOTICE</span> · 운영 / 대회 소식</div>
		<h1 class="page-title eh-h1">공지사항</h1>
	</div>

	<!-- Pinned block (all-tab only) -->
	{#if pinned.length > 0}
		<div class="pinned-block" aria-label="고정 공지">
			{#each pinned as n (n.id)}
				<a class="pinned-row" href={n.href ?? `/notice/${n.id}`}>
					<span class="cat-tag cat-tag--{n.category}">{CAT_LABEL[n.category as NoticeCategory]}</span>
					<span class="pinned-ttl">{n.title}</span>
					<span class="pinned-date eh-micro eh-data">{n.date.slice(5)}</span>
				</a>
			{/each}
		</div>
	{/if}

	<!-- Tab bar -->
	<div class="tab-bar" role="tablist">
		{#each tabDefs as t (t.id)}
			<button
				type="button"
				role="tab"
				aria-selected={data.activeTab === t.id}
				class="tab-btn"
				class:tab-btn--on={data.activeTab === t.id}
				onclick={() => setTab(t.id)}
			>
				{t.label}
				<span class="tab-count eh-data">
					{data.counts[t.id as keyof typeof data.counts]}
				</span>
			</button>
		{/each}
	</div>

	<!-- Notice list -->
	{#if list.length === 0 && pinned.length === 0}
		<div class="empty-state">
			<span class="eh-micro">NO NOTICES</span>
			<p>등록된 공지사항이 없습니다.</p>
		</div>
	{:else if list.length === 0}
		<!-- Only pinned, no regular items — nothing extra to show -->
	{:else}
		<div class="notice-list">
			{#each list as n (n.id)}
				<a class="nrow" href={n.href ?? `/notice/${n.id}`}>
					<span class="cat-tag cat-tag--{n.category}">{CAT_LABEL[n.category as NoticeCategory]}</span>
					<span class="nrow-ttl">{n.title}</span>
					<span class="nrow-date eh-data">{n.date}</span>
					<span class="nrow-views eh-data">{n.views.toLocaleString('ko-KR')}</span>
				</a>
			{/each}
		</div>
	{/if}
</div>

<style>
	.notice-wrap {
		max-width: 860px;
		margin: 0 auto;
		padding: var(--sp-10) var(--sp-6) var(--sp-16);
	}

	@media (max-width: 640px) {
		.notice-wrap {
			padding: var(--sp-6) var(--sp-4) var(--sp-12);
		}
	}

	/* ---- Page header ---- */
	.page-hd {
		padding-bottom: var(--sp-6);
	}
	.page-kicker {
		margin-bottom: var(--sp-2);
		color: var(--text-muted);
	}
	.page-kicker .acc {
		color: var(--accent);
	}
	.page-title {
		margin: 0;
	}

	/* ---- Pinned block ---- */
	.pinned-block {
		border: var(--border-rule);
		margin-bottom: var(--sp-6);
	}
	.pinned-row {
		display: grid;
		grid-template-columns: auto 1fr auto;
		gap: var(--sp-3);
		align-items: center;
		padding: var(--sp-4) var(--sp-5);
		border-bottom: var(--border-hair);
		text-decoration: none;
		color: inherit;
		transition: background var(--dur-fast) var(--ease-out);
		cursor: pointer;
	}
	.pinned-row:last-child {
		border-bottom: 0;
	}
	.pinned-row:hover {
		background: var(--paper-50);
	}
	.pinned-ttl {
		font-weight: 700;
		font-size: 15px;
		color: var(--text-strong);
		min-width: 0;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.pinned-row:hover .pinned-ttl {
		text-decoration: underline;
		text-underline-offset: 3px;
	}
	.pinned-date {
		color: var(--text-faint);
		white-space: nowrap;
	}

	/* ---- Category tag (DS soft-filled status badge) ---- */
	.cat-tag {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		height: 24px;
		padding: 0 9px;
		font-family: var(--font-sans);
		font-size: 12px;
		font-weight: 600;
		letter-spacing: 0;
		border-radius: var(--r-2);
		white-space: nowrap;
	}
	/* urgent: soft danger */
	.cat-tag--urgent {
		color: var(--danger);
		background: var(--danger-bg);
	}
	/* notice: closed (neutral) */
	.cat-tag--notice {
		color: var(--ink-500);
		background: var(--paper-100);
	}
	/* racenews: upcoming (blue) */
	.cat-tag--racenews {
		color: var(--info);
		background: var(--info-bg);
	}
	/* event: open (green) */
	.cat-tag--event {
		color: var(--positive);
		background: var(--positive-bg);
	}

	/* ---- Tab bar ---- */
	.tab-bar {
		display: flex;
		gap: 0;
		border-bottom: var(--border-hair);
		margin-bottom: 0;
	}
	.tab-btn {
		display: flex;
		align-items: baseline;
		gap: var(--sp-1);
		padding: var(--sp-3) var(--sp-4);
		background: transparent;
		border: none;
		border-bottom: 2px solid transparent;
		margin-bottom: -1px;
		font-family: var(--font-mono);
		font-size: 13px;
		font-weight: 400;
		color: var(--text-muted);
		cursor: pointer;
		transition: color var(--dur-fast) var(--ease-out),
		            border-color var(--dur-fast) var(--ease-out);
		white-space: nowrap;
	}
	.tab-btn:hover {
		color: var(--text-strong);
	}
	.tab-btn--on {
		color: var(--text-strong);
		font-weight: 700;
		border-bottom-color: var(--accent);
	}
	.tab-count {
		font-size: 10px;
		color: var(--text-faint);
	}

	/* ---- Notice rows ---- */
	.notice-list {
		display: flex;
		flex-direction: column;
		margin-top: var(--sp-2);
	}
	.nrow {
		display: grid;
		grid-template-columns: 88px 1fr 90px 70px;
		gap: var(--sp-3);
		align-items: center;
		padding: var(--sp-4) var(--sp-1);
		border-bottom: var(--border-hair);
		text-decoration: none;
		color: inherit;
		transition: background var(--dur-fast) var(--ease-out);
		cursor: pointer;
	}
	.nrow:hover {
		background: var(--paper-50);
	}
	.nrow-ttl {
		font-weight: 600;
		font-size: 14.5px;
		color: var(--text-strong);
		min-width: 0;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.nrow:hover .nrow-ttl {
		text-decoration: underline;
		text-underline-offset: 3px;
	}
	.nrow-date {
		font-size: 13px;
		color: var(--text-muted);
		text-align: right;
		white-space: nowrap;
	}
	.nrow-views {
		font-size: 12px;
		color: var(--text-faint);
		text-align: right;
	}

	/* ---- Empty state ---- */
	.empty-state {
		border: var(--border-hair);
		padding: var(--sp-12) var(--sp-6);
		text-align: center;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--sp-3);
		color: var(--text-muted);
		margin-top: var(--sp-6);
	}
	.empty-state p {
		margin: 0;
		font-size: var(--text-body-sm);
	}

	/* ---- Responsive ---- */
	@media (max-width: 640px) {
		.nrow {
			grid-template-columns: auto 1fr;
			row-gap: var(--sp-1);
		}
		.nrow-date,
		.nrow-views {
			display: none;
		}
		.pinned-row {
			grid-template-columns: auto 1fr;
		}
		.pinned-date {
			display: none;
		}
	}
</style>
