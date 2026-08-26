<!--
  EventBanner — 관리자에서 관리하는 이벤트 배너 본문.

  두 곳에서 같은 데이터를 쓴다:
    variant="popup" — 팝업 모달 (640 세로 배너)
    variant="page"  — 공지 상세 상단 히어로 (잉크 블록 + 경품 2단)

  내용·게시기간은 django admin 의 "팝업 배너"에서 편집한다.
-->
<script lang="ts">
	import { splitAccent, ddayLabel, type EventBanner } from '$lib/popup';

	interface Props {
		banner: EventBanner;
		variant?: 'popup' | 'page';
		/** 헤드라인 요소의 id — 모달의 aria-labelledby 로 물린다. */
		headlineId?: string;
		/** CTA 클릭 시(링크 이동 전) 호출 — 팝업 닫기 등에 쓴다. */
		onCta?: () => void;
	}

	let { banner, variant = 'popup', headlineId, onCta }: Props = $props();

	const parts = $derived(splitAccent(banner.headline, banner.headlineAccent));
	const dday = $derived(ddayLabel(banner));
	const hasPrize = $derived(!!(banner.prizeImage || banner.prizeName || banner.prizeCount));
	const hasMeta = $derived(!!(banner.metaPeriod || banner.metaWinners || dday));
	const hasFine = $derived(!!(banner.finePeriod || banner.fineAnnounce || banner.fineNote));
	const hasCta = $derived(!!(banner.targetUrl && banner.ctaLabel));
</script>

<div class="evb evb--{variant}" class:evb--solo={!hasPrize}>
	<!-- ── 잉크 헤드라인 블록 ── -->
	<header class="evb-top">
		{#if banner.tag}<span class="evb-tag">{banner.tag}</span>{/if}

		<svelte:element this={variant === 'popup' ? 'h2' : 'p'} class="evb-h" id={headlineId}>
			{#each parts as p, i (i)}{#if p.accent}<em>{p.text}</em>{:else}{p.text}{/if}{/each}
		</svelte:element>

		{#if banner.subtitle}<p class="evb-sub">{banner.subtitle}</p>{/if}

		{#if hasMeta}
			<div class="evb-meta eh-data">
				{#if banner.metaPeriod}
					<div><span class="k">기간</span><span class="v">{banner.metaPeriod}</span></div>
				{/if}
				{#if banner.metaWinners}
					<div><span class="k">당첨</span><span class="v">{banner.metaWinners}</span></div>
				{/if}
				{#if dday}
					<div><span class="k">마감까지</span><span class="v acc">{dday}</span></div>
				{/if}
			</div>
		{/if}
	</header>

	<!-- ── 경품 ── -->
	{#if hasPrize}
		<section class="evb-prize">
			<div class="ph">
				<span class="eh-micro">경품</span>
				{#if banner.prizeNote}<span class="eh-micro note">{banner.prizeNote}</span>{/if}
			</div>
			<div class="pfig">
				{#if banner.prizeImage}
					<img src={banner.prizeImage} alt={banner.prizeName || '경품 이미지'} loading="lazy" />
				{/if}
			</div>
			{#if banner.prizeName || banner.prizeCount}
				<div class="pfoot">
					<b>{banner.prizeName}</b>
					{#if banner.prizeCount}<span class="q eh-data">{banner.prizeCount}</span>{/if}
				</div>
			{/if}
		</section>
	{/if}

	<!-- ── 참여 방법 ── -->
	{#if banner.steps.length > 0}
		<section class="evb-steps">
			{#each banner.steps as step, i (step.order + '-' + i)}
				<div class="r">
					<span class="n eh-data">{String(step.order).padStart(2, '0')}</span>
					<span class="t">{step.title}</span>
					{#if step.description}<p class="d">{step.description}</p>{/if}
				</div>
			{/each}
		</section>
	{/if}

	<!-- ── CTA ── -->
	{#if hasCta}
		<a class="evb-cta" href={banner.targetUrl} onclick={() => onCta?.()}>
			{banner.ctaLabel} <span class="arr">→</span>
		</a>
	{/if}

	<!-- ── 하단 세부 안내 ── -->
	{#if hasFine}
		<footer class="evb-fine">
			{#if banner.finePeriod}
				<div class="r"><span class="k">기간</span><span class="eh-data"><b>{banner.finePeriod}</b></span></div>
			{/if}
			{#if banner.fineAnnounce}
				<div class="r"><span class="k">발표</span><span class="eh-data">{banner.fineAnnounce}</span></div>
			{/if}
			{#if banner.fineNote}
				<div class="r"><span class="k">유의</span><span>{banner.fineNote}</span></div>
			{/if}
			<div class="evb-mark">
				<span class="wm">ENDURO<span class="s">/</span>HUB</span>
				<span class="eh-micro note">대회 큐레이션</span>
			</div>
		</footer>
	{/if}
</div>

<style>
	.evb {
		background: var(--paper-0);
		display: flex;
		flex-direction: column;
	}

	/* ── 잉크 헤드라인 블록 ── */
	.evb-top {
		background: var(--bg-inverse);
		color: var(--text-inverse);
		padding: 34px 34px 0;
	}
	.evb-tag {
		display: inline-flex;
		align-items: center;
		height: 26px;
		padding: 0 10px;
		border: 1px solid var(--signal-600);
		border-radius: var(--r-2);
		font-size: var(--text-micro);
		font-weight: var(--w-strong);
		letter-spacing: 0.02em;
		color: var(--signal-200);
	}
	.evb-h {
		margin: 20px 0 0;
		font-size: clamp(30px, 5.6vw, 46px);
		font-weight: var(--w-display);
		letter-spacing: -0.042em;
		line-height: 0.99;
		color: var(--text-inverse);
		white-space: pre-line;
		text-wrap: balance;
	}
	.evb-h :global(em) {
		font-style: normal;
		color: var(--signal-600);
	}
	.evb-sub {
		margin: 16px 0 0;
		font-size: 15.5px;
		line-height: 1.62;
		color: var(--ink-300);
		max-width: 36ch;
		text-wrap: pretty;
	}
	.evb-meta {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(0, 1fr));
		margin-top: 26px;
		border-top: 1px solid rgba(128, 128, 128, 0.35);
	}
	.evb-meta > div {
		padding: 14px 0 20px 16px;
		border-left: 1px solid rgba(128, 128, 128, 0.35);
	}
	.evb-meta > div:first-child {
		border-left: 0;
		padding-left: 0;
	}
	.evb-meta .k {
		display: block;
		font-size: 11px;
		font-weight: var(--w-strong);
		letter-spacing: 0.02em;
		color: var(--ink-300);
	}
	.evb-meta .v {
		display: block;
		margin-top: 6px;
		font-size: 21px;
		font-weight: var(--w-display);
		letter-spacing: -0.03em;
		color: var(--text-inverse);
	}
	.evb-meta .v.acc {
		color: var(--signal-600);
	}

	/* ── 경품 ── */
	.evb-prize {
		border-top: 1px solid var(--ink-900);
		background: var(--paper-0);
		display: flex;
		flex-direction: column;
	}
	.evb-prize .ph {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 16px;
		padding: 12px 34px;
		border-bottom: var(--border-hair);
		color: var(--text-strong);
	}
	.evb-prize .pfig {
		position: relative;
		flex: 1;
		min-height: 200px;
		background: var(--paper-50);
		border-bottom: var(--border-hair);
	}
	.evb-prize .pfig img {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: contain;
		padding: 16px;
	}
	.evb-prize .pfoot {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 16px;
		padding: 14px 34px 18px;
	}
	.evb-prize .pfoot b {
		font-size: 19px;
		font-weight: var(--w-heading);
		letter-spacing: var(--track-heading);
		color: var(--text-strong);
	}
	.evb-prize .pfoot .q {
		font-size: 20px;
		font-weight: var(--w-display);
		letter-spacing: -0.03em;
		color: var(--text-accent);
		white-space: nowrap;
	}

	/* ── 참여 방법 ── */
	.evb-steps {
		border-top: var(--border-rule);
		background: var(--paper-0);
	}
	.evb-steps .r {
		display: grid;
		grid-template-columns: 74px 1fr;
		align-items: baseline;
		gap: 0 4px;
		padding: 18px 34px 20px;
		border-bottom: var(--border-hair);
	}
	.evb-steps .r:last-child {
		border-bottom: 0;
	}
	.evb-steps .n {
		font-size: 32px;
		font-weight: var(--w-display);
		letter-spacing: -0.045em;
		line-height: 1;
		color: var(--accent);
		font-variant-numeric: tabular-nums;
	}
	.evb-steps .t {
		font-size: 18px;
		font-weight: var(--w-heading);
		letter-spacing: var(--track-heading);
		color: var(--text-strong);
	}
	.evb-steps .d {
		grid-column: 2;
		margin: 6px 0 0;
		font-size: 14.5px;
		line-height: 1.6;
		color: var(--text-muted);
		text-wrap: pretty;
	}

	/* ── CTA ── */
	.evb-cta {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 10px;
		height: 66px;
		background: var(--accent);
		color: #fff;
		text-decoration: none;
		font-size: 20px;
		font-weight: 700;
		letter-spacing: var(--track-heading);
		border-top: 1px solid var(--ink-900);
		transition: background var(--dur-fast) var(--ease-out);
	}
	.evb-cta:hover {
		background: var(--accent-strong);
		color: #fff;
	}
	.evb-cta:active {
		transform: translateY(1px);
	}
	.evb-cta .arr {
		font-weight: 400;
	}

	/* ── 하단 세부 안내 ── */
	.evb-fine {
		background: var(--paper-50);
		border-top: 1px solid var(--ink-900);
		padding: 16px 34px 20px;
	}
	.evb-fine .r {
		display: grid;
		grid-template-columns: 64px 1fr;
		gap: 14px;
		padding: 6px 0;
		font-size: 13px;
		line-height: 1.55;
		color: var(--text-muted);
	}
	.evb-fine .r + .r {
		border-top: var(--border-hair);
	}
	.evb-fine .k {
		font-size: var(--text-micro);
		font-weight: var(--w-strong);
		letter-spacing: 0.02em;
		color: var(--text-faint);
		padding-top: 2px;
	}
	.evb-fine b {
		color: var(--text-body);
		font-weight: 600;
	}
	.evb-mark {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 16px;
		margin-top: 14px;
		padding-top: 12px;
		border-top: var(--border-hair);
	}
	.evb-mark .wm {
		font-size: 14px;
		font-weight: 900;
		letter-spacing: -0.02em;
		color: var(--text-strong);
	}
	.evb-mark .wm .s {
		color: var(--accent);
	}
	.note {
		color: var(--text-faint);
	}

	/* ─────────────────────────────────────────────────────────
	   variant="page" — 공지 상세 히어로. 잉크 블록과 경품을 2단으로
	   펼치고, 참여 방법은 3단 그리드로 눕힌다.
	   ───────────────────────────────────────────────────────── */
	@media (min-width: 861px) {
		.evb--page {
			display: grid;
			grid-template-columns: 1.06fr 0.94fr;
		}
		/* 경품이 없으면 오른쪽 칸이 빈다 — 한 단으로 되돌린다. */
		.evb--page.evb--solo {
			grid-template-columns: 1fr;
		}
		.evb--page .evb-prize {
			border-top: 0;
			border-left: 1px solid var(--ink-900);
			background: var(--paper-50);
		}
		.evb--page .evb-prize .ph,
		.evb--page .evb-prize .pfoot {
			background: var(--paper-0);
			padding-left: 22px;
			padding-right: 22px;
		}
		.evb--page .evb-prize .pfoot {
			border-top: var(--border-hair);
		}
		.evb--page .evb-steps,
		.evb--page .evb-cta,
		.evb--page .evb-fine {
			grid-column: 1 / -1;
		}
		.evb--page .evb-steps {
			display: grid;
			grid-template-columns: repeat(3, 1fr);
			border-top: 1px solid var(--ink-900);
		}
		.evb--page .evb-steps .r {
			display: block;
			padding: 20px 22px 24px;
			border-bottom: 0;
			border-left: var(--border-hair);
		}
		.evb--page .evb-steps .r:first-child {
			border-left: 0;
		}
		.evb--page .evb-steps .n {
			display: block;
			font-size: 34px;
		}
		.evb--page .evb-steps .t {
			display: block;
			margin-top: 10px;
		}
	}

	/* ─────────────────────────────────────────────────────────
	   variant="popup" — 모달이 테두리를 갖고 있으므로 배너는 테두리 없이
	   모달 폭을 꽉 채운다.
	   ───────────────────────────────────────────────────────── */
	.evb--popup {
		border: 0;
	}
	.evb--popup .evb-top {
		padding-top: 38px;
	}
	.evb--popup .evb-h {
		font-size: clamp(32px, 7vw, 48px);
	}

	@media (max-width: 700px) {
		.evb-top {
			padding: 28px 22px 0;
		}
		.evb-prize .ph,
		.evb-prize .pfoot,
		.evb-steps .r,
		.evb-fine {
			padding-left: 22px;
			padding-right: 22px;
		}
		.evb-steps .r {
			grid-template-columns: 56px 1fr;
		}
		.evb-cta {
			height: 60px;
			font-size: 17px;
		}
		.evb-prize .pfig {
			min-height: 170px;
		}
	}
</style>
