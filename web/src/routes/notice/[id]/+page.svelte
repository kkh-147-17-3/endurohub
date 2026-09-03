<script lang="ts">
	import type { NoticeDetail, NoticeCategory } from '../notices';
	import { CAT_LABEL } from '../notices';
	import EventBanner from '$lib/components/EventBanner.svelte';

	let { data } = $props();

	const notice = $derived<NoticeDetail>(data.notice);
	const adjacent = $derived(data.adjacent);
	// 이벤트 공지에 배너가 붙어 있으면 본문 위에 히어로로 펼친다 — 팝업 모달과
	// 같은 데이터(django admin > 팝업 배너)를 쓴다.
	const event = $derived(data.event);

	const catLabel = $derived(CAT_LABEL[notice.category as NoticeCategory]);
</script>

<svelte:head>
	<title>{notice.title} · 공지사항 · ENDUROHUB</title>
	<meta name="description" content={notice.title} />
</svelte:head>

<div class="detail-page">
	<div class="wrap">

		<!-- Breadcrumb -->
		<nav class="crumb" aria-label="이동 경로">
			<a href="/notice">공지사항</a>
			<span aria-hidden="true">›</span>
			<span class="crumb-cur">{catLabel}</span>
			<a href="/notice" class="crumb-back">← 목록</a>
		</nav>

		<!-- Article header -->
		<header class="notice-hd">
			<div class="hd-tags">
				<span class="cat-tag cat-tag--{notice.category}">{catLabel}</span>
			</div>
			<h1>{notice.title}</h1>
			<div class="meta eh-data">
				<span><b>{notice.author ?? 'ENDUROHUB 운영팀'}</b></span>
				<span>게시 {notice.date}</span>
				<span>조회 {notice.views.toLocaleString('ko-KR')}</span>
			</div>
		</header>

		<!-- Event hero (관리자에서 배너를 연결한 이벤트 공지만) -->
		{#if event}
			<div class="event-hero">
				<EventBanner banner={event} variant="page" />
			</div>
		{/if}

		<!-- Article body (sanitized HTML from the backend) -->
		<article class="md">
			{#if notice.content && notice.content.trim().length > 0}
				{@html notice.content}
			{:else}
				<p class="md-empty">본문 내용이 없습니다.</p>
			{/if}
		</article>

		<!-- Attachments (optional) -->
		{#if notice.attachments && notice.attachments.length > 0}
			<div class="att">
				<div class="att-label eh-micro">첨부파일 · {notice.attachments.length}</div>
				{#each notice.attachments as [filename, size] (filename)}
					<div class="att-row">
						<span class="att-icon" aria-hidden="true">◫</span>
						<span class="att-name">{filename}</span>
						<span class="att-size eh-data">{size}</span>
						<span class="att-dl" aria-label="다운로드">↓</span>
					</div>
				{/each}
			</div>
		{/if}

		<!-- Prev / Next navigation -->
		{#if adjacent.prev || adjacent.next}
			<nav class="pn" aria-label="이전·다음 공지">
				{#if adjacent.prev}
					<a href={adjacent.prev.href ?? `/notice/${adjacent.prev.id}`}>
						<span class="dir">이전 글</span>
						<span class="t">{adjacent.prev.title}</span>
						<span class="d eh-data">{adjacent.prev.date.slice(5)}</span>
					</a>
				{/if}
				{#if adjacent.next}
					<a href={adjacent.next.href ?? `/notice/${adjacent.next.id}`}>
						<span class="dir">다음 글</span>
						<span class="t">{adjacent.next.title}</span>
						<span class="d eh-data">{adjacent.next.date.slice(5)}</span>
					</a>
				{/if}
			</nav>
		{/if}

		<!-- Back to list -->
		<div class="back-row">
			<a href="/notice" class="btn-outline">목록으로</a>
		</div>

	</div>
</div>

<style>
	.detail-page {
		padding: 0 var(--sp-6) var(--sp-16);
	}
	.wrap {
		max-width: 860px;
		margin: 0 auto;
	}

	/* ---- Breadcrumb ---- */
	.crumb {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 14px 0;
		font-size: 12.5px;
		color: var(--text-faint);
		flex-wrap: wrap;
	}
	.crumb a {
		color: var(--text-muted);
		text-decoration: none;
	}
	.crumb a:hover {
		color: var(--text-strong);
		text-decoration: underline;
		text-underline-offset: 3px;
	}
	.crumb-cur {
		color: var(--text-muted);
	}
	.crumb-back {
		margin-left: auto;
		font-weight: 600;
	}

	/* ---- Category tag (DS soft-filled status badge) ---- */
	.cat-tag {
		display: inline-flex;
		align-items: center;
		height: 24px;
		padding: 0 9px;
		font-size: 12px;
		font-weight: 600;
		border-radius: var(--r-2);
		white-space: nowrap;
	}
	.cat-tag--urgent { color: var(--danger); background: var(--danger-bg); }
	.cat-tag--notice { color: var(--ink-500); background: var(--paper-100); }
	.cat-tag--racenews { color: var(--info); background: var(--info-bg); }
	.cat-tag--event { color: var(--positive); background: var(--positive-bg); }

	/* ---- Article header ---- */
	.notice-hd {
		padding: 32px 0 22px;
		border-bottom: var(--border-rule);
	}
	.hd-tags {
		display: flex;
		align-items: center;
		gap: 8px;
		flex-wrap: wrap;
	}
	.notice-hd h1 {
		margin: 14px 0 0;
		font-size: clamp(23px, 3vw, 32px);
		font-weight: var(--w-display);
		letter-spacing: var(--track-display);
		line-height: 1.25;
		color: var(--text-strong);
		text-wrap: pretty;
	}
	.notice-hd .meta {
		display: flex;
		gap: 14px;
		margin-top: 16px;
		font-size: 12.5px;
		color: var(--text-faint);
		flex-wrap: wrap;
	}
	.notice-hd .meta b {
		color: var(--text-muted);
		font-weight: 600;
	}

	/* ---- Event hero ---- */
	.event-hero {
		margin-top: 28px;
		border: 1px solid var(--ink-900);
	}

	/* ---- Markdown body ---- */
	.md {
		padding: 30px 0 0;
		font-size: 15.5px;
		line-height: 1.78;
		color: var(--text-strong);
		max-width: 720px;
	}
	.md :global(> * + *) {
		margin-top: 16px;
	}
	.md :global(h2) {
		margin-top: 40px;
		padding-top: 12px;
		border-top: var(--border-rule);
		font-size: 19px;
		font-weight: var(--w-strong);
		letter-spacing: var(--track-heading);
		line-height: 1.3;
		color: var(--text-strong);
	}
	.md :global(h3) {
		margin-top: 30px;
		font-size: 16.5px;
		font-weight: 700;
		letter-spacing: var(--track-heading);
		color: var(--text-strong);
	}
	.md :global(strong) {
		font-weight: 700;
	}
	.md :global(ul),
	.md :global(ol) {
		padding-left: 22px;
	}
	.md :global(li + li) {
		margin-top: 7px;
	}
	.md :global(li::marker) {
		color: var(--text-faint);
		font-weight: 700;
	}
	.md :global(blockquote) {
		border-left: 2px solid var(--ink-900);
		background: var(--paper-50);
		padding: 13px 18px;
		color: var(--text-muted);
		font-size: 0.95em;
	}
	.md :global(table) {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.92em;
	}
	.md :global(th) {
		border-top: var(--border-rule);
		border-bottom: var(--border-hair);
		text-align: left;
		padding: 9px 10px;
		font-size: var(--text-micro);
		font-weight: var(--w-strong);
		letter-spacing: var(--track-micro);
		text-transform: uppercase;
		color: var(--text-muted);
	}
	.md :global(td) {
		border-bottom: var(--border-hair);
		padding: 9px 10px;
		font-variant-numeric: tabular-nums;
	}
	.md :global(td.kv-k) {
		font-weight: 600;
		color: var(--text-muted);
		white-space: nowrap;
	}
	.md-empty {
		color: var(--text-faint);
	}

	/* ---- Attachments ---- */
	.att {
		margin-top: 32px;
		padding: 16px 18px;
		border: var(--border-hair);
		background: var(--paper-50);
	}
	.att-label {
		color: var(--text-faint);
		margin-bottom: 12px;
	}
	.att-row {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 8px 12px;
		background: var(--paper-0);
		border: var(--border-hair);
		font-size: 13px;
	}
	.att-row + .att-row {
		margin-top: 8px;
	}
	.att-icon { color: var(--accent); }
	.att-name { flex: 1; color: var(--text-body); }
	.att-size { color: var(--text-faint); }
	.att-dl { color: var(--text-muted); cursor: pointer; }
	.att-dl:hover { color: var(--accent); }

	/* ---- Prev / Next ---- */
	.pn {
		margin-top: 44px;
		border-top: var(--border-rule);
	}
	.pn a {
		display: grid;
		grid-template-columns: 64px 1fr auto;
		gap: 14px;
		align-items: baseline;
		padding: 14px 4px;
		border-bottom: var(--border-hair);
		text-decoration: none;
		color: inherit;
		font-size: 14px;
		transition: background var(--dur-fast) var(--ease-out);
	}
	.pn a:hover {
		background: var(--paper-50);
	}
	.pn a:hover .t {
		text-decoration: underline;
		text-underline-offset: 3px;
	}
	.pn .dir {
		font-size: var(--text-micro);
		font-weight: var(--w-strong);
		letter-spacing: var(--track-micro);
		text-transform: uppercase;
		color: var(--text-faint);
	}
	.pn .t {
		font-weight: 600;
		color: var(--text-strong);
		min-width: 0;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.pn .d {
		font-size: 12px;
		color: var(--text-faint);
		white-space: nowrap;
	}

	/* ---- Back to list ---- */
	.back-row {
		display: flex;
		justify-content: center;
		margin-top: 28px;
	}
	.btn-outline {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		height: 40px;
		padding: 0 22px;
		border: 1px solid var(--ink-900);
		border-radius: var(--r-2);
		background: var(--paper-0);
		color: var(--text-strong);
		font-size: 14px;
		font-weight: 600;
		text-decoration: none;
		transition: background var(--dur-fast) var(--ease-out);
	}
	.btn-outline:hover {
		background: var(--paper-50);
	}

	/* ---- Responsive ---- */
	@media (max-width: 640px) {
		.detail-page {
			padding: 0 var(--sp-4) var(--sp-12);
		}
		.pn a {
			grid-template-columns: 56px 1fr;
		}
		.pn .d {
			display: none;
		}
	}
</style>
