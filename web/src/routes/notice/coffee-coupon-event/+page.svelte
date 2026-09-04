<script lang="ts">
	import { onDestroy } from 'svelte';
	import { page } from '$app/stores';

	interface CoffeeEventStatus {
		period: { startsAt: string; endsAt: string };
		review: { completed: boolean; count: number };
		record: { completed: boolean; count: number };
		completed: boolean;
	}

	let { data } = $props();
	const participation = $derived<CoffeeEventStatus | null>(data.participation);
	const loginHref = $derived(`/auth/login?redirect=${encodeURIComponent($page.url.pathname)}`);

	let frameHeight = $state(900);
	let frame: HTMLIFrameElement;
	let observer: ResizeObserver | undefined;

	function syncHeight(frame: HTMLIFrameElement) {
		observer?.disconnect();

		const doc = frame.contentDocument;
		if (!doc) return;

		const update = () => {
			frameHeight = Math.max(doc.documentElement.scrollHeight, doc.body.scrollHeight);
		};

		update();
		observer = new ResizeObserver(update);
		observer.observe(doc.documentElement);
	}

	onDestroy(() => observer?.disconnect());
</script>

<svelte:head>
	<title>스타벅스 카페 아메리카노 T 이벤트 · ENDUROHUB</title>
	<meta
		name="description"
		content="9월 30일까지 참가한 대회의 리뷰와 본인 기록을 남기면 자동 응모됩니다. 조건을 완료한 회원 중 20명을 추첨해 스타벅스 카페 아메리카노 T를 드립니다."
	/>
</svelte:head>

<div class="event-page">
	<nav class="crumb" aria-label="이동 경로">
		<a href="/notice">공지사항</a>
		<span aria-hidden="true">›</span>
		<a href="/notice?tab=event">이벤트</a>
		<span aria-hidden="true">›</span>
		<span class="current">커피 쿠폰 이벤트</span>
	</nav>

	<section class="event-overview" aria-labelledby="event-title">
		<div class="event-overview-copy">
			<p class="section-label">9월 회원 이벤트</p>
			<h1 id="event-title">리뷰와 기록을 남기면<br />자동으로 응모됩니다.</h1>
			<p class="event-lede">
				종목과 관계없이 실제 참가한 대회의 리뷰 1개와 본인 기록 1개를 등록해 주세요.
				두 조건을 완료한 회원 중 20명을 추첨해 스타벅스 카페 아메리카노 T 모바일
				상품권을 드립니다.
			</p>
			<dl class="event-facts">
				<div>
					<dt>참여 기간</dt>
					<dd><time datetime="2026-09-03">2026.09.03</time>–<time datetime="2026-09-30">09.30</time></dd>
				</div>
				<div>
					<dt>당첨 혜택</dt>
					<dd>커피 쿠폰 · 20명</dd>
				</div>
				<div>
					<dt>응모 방식</dt>
					<dd>조건 완료 시 자동 응모</dd>
				</div>
			</dl>
		</div>

		<div class="event-how">
			<h2>참여 방법</h2>
			<ol>
				<li>
					<span class="step-number" aria-hidden="true">1</span>
					<div>
						<strong>참가한 대회의 리뷰 열기</strong>
						<p>대회 상세 페이지에서 회원 계정으로 리뷰 작성 버튼을 누릅니다.</p>
					</div>
				</li>
				<li>
					<span class="step-number" aria-hidden="true">2</span>
					<div>
						<strong>종목과 완주 시간 함께 입력</strong>
						<p>리뷰 폼에서 참가 종목과 실제 완주 시간을 입력하면 본인 기록도 함께 등록됩니다.</p>
					</div>
				</li>
			</ol>
			<p class="event-note">
				두 조건을 9월 30일까지 완료하면 회원당 1회 자동 응모됩니다. 이미 리뷰를 작성했다면
				해당 대회의 시즌 타임라인에서 완주 기록만 추가해 주세요.
			</p>
		</div>
	</section>

	<iframe
		bind:this={frame}
		src="/coffee-coupon-event.html"
		title="스타벅스 카페 아메리카노 T 이벤트"
		style:height="{frameHeight}px"
		onload={() => syncHeight(frame)}
	></iframe>

	<section class="participation" aria-labelledby="participation-title">
		<div class="participation-copy">
			<p class="section-label">내 참여 현황</p>
			<h2 id="participation-title">현재 나의 참여 현황을 확인하세요.</h2>
			<p>2026년 9월 3일부터 9월 30일까지 등록한 리뷰와 대회 기록을 확인합니다.</p>
		</div>

		{#if participation}
			<div class="condition-list">
				<div class:done={participation.review.completed} class="condition">
					<span class="condition-mark" aria-hidden="true">
						{#if participation.review.completed}
							<svg viewBox="0 0 16 16"><path d="m3.5 8.2 3 3 6-6.4" /></svg>
						{:else}1{/if}
					</span>
					<div>
						<strong>대회 리뷰</strong>
						<span>{participation.review.completed ? `${participation.review.count}개 작성 완료` : '아직 작성하지 않았어요'}</span>
					</div>
				</div>
				<div class:done={participation.record.completed} class="condition">
					<span class="condition-mark" aria-hidden="true">
						{#if participation.record.completed}
							<svg viewBox="0 0 16 16"><path d="m3.5 8.2 3 3 6-6.4" /></svg>
						{:else}2{/if}
					</span>
					<div>
						<strong>대회 기록</strong>
						<span>{participation.record.completed ? `${participation.record.count}개 등록 완료` : '아직 등록하지 않았어요'}</span>
					</div>
				</div>
				<p class:complete={participation.completed} class="result" role="status">
					{participation.completed ? '응모 조건을 모두 완료했어요.' : '두 조건을 모두 완료하면 자동으로 응모돼요.'}
				</p>
			</div>
		{:else}
			<div class="login-prompt">
				<p>로그인하면 내 리뷰와 대회 기록을 바로 확인할 수 있어요.</p>
				<a href={loginHref}>로그인하고 확인하기</a>
			</div>
		{/if}
	</section>
</div>

<style>
	.event-page {
		max-width: 1440px;
		margin: 0 auto;
		padding: var(--sp-5) var(--sp-6) var(--sp-12);
	}

	.crumb {
		display: flex;
		align-items: center;
		gap: var(--sp-2);
		max-width: 1280px;
		margin: 0 auto var(--sp-4);
		color: var(--text-faint);
		font-size: 12px;
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

	.event-overview {
		display: grid;
		grid-template-columns: minmax(0, 1.25fr) minmax(360px, 0.75fr);
		gap: clamp(32px, 6vw, 88px);
		max-width: 1280px;
		margin: 0 auto var(--sp-6);
		padding: clamp(28px, 4vw, 48px) 0;
		border-top: 2px solid var(--ink-900);
		border-bottom: var(--border-hair);
	}

	.event-overview h1 {
		margin: 0;
		color: var(--text-strong);
		font-size: clamp(30px, 4vw, 52px);
		letter-spacing: -0.045em;
		line-height: 1.08;
	}

	.event-lede {
		max-width: 46em;
		margin: 20px 0 0;
		color: var(--text-muted);
		font-size: 15px;
		line-height: 1.75;
	}

	.event-facts {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		margin: 28px 0 0;
		border-top: var(--border-hair);
	}

	.event-facts > div {
		padding: 16px 14px 0 0;
	}

	.event-facts dt {
		color: var(--text-faint);
		font-size: 11px;
		font-weight: 700;
	}

	.event-facts dd {
		margin: 5px 0 0;
		color: var(--text-strong);
		font-family: var(--font-mono);
		font-size: 13px;
		font-weight: 650;
		line-height: 1.5;
	}

	.event-how {
		align-self: end;
	}

	.event-how h2 {
		margin: 0;
		color: var(--text-strong);
		font-size: 18px;
		letter-spacing: -0.025em;
	}

	.event-how ol {
		margin: 14px 0 0;
		padding: 0;
		list-style: none;
		border-top: 2px solid var(--ink-900);
	}

	.event-how li {
		display: grid;
		grid-template-columns: 30px 1fr;
		gap: 14px;
		padding: 16px 0;
		border-bottom: var(--border-hair);
	}

	.step-number {
		display: inline-flex;
		width: 26px;
		height: 26px;
		align-items: center;
		justify-content: center;
		border: 1px solid var(--ink-300);
		border-radius: 50%;
		color: var(--text-faint);
		font-family: var(--font-mono);
		font-size: 11px;
		font-weight: 800;
	}

	.event-how strong {
		display: block;
		color: var(--text-strong);
		font-size: 14px;
	}

	.event-how li p {
		margin: 4px 0 0;
		color: var(--text-muted);
		font-size: 13px;
		line-height: 1.55;
	}

	.event-note {
		margin: 14px 0 0;
		color: var(--accent-strong);
		font-size: 12px;
		font-weight: 700;
		line-height: 1.55;
	}

	.participation {
		display: grid;
		grid-template-columns: minmax(0, 0.85fr) minmax(420px, 1.15fr);
		gap: clamp(32px, 6vw, 88px);
		max-width: 1280px;
		margin: var(--sp-6) auto 0;
		padding: clamp(28px, 4vw, 48px);
		border: 1px solid var(--ink-900);
		background: var(--paper-0);
	}

	.section-label {
		margin: 0 0 10px;
		color: var(--accent);
		font-size: 12px;
		font-weight: 700;
	}

	.participation h2 {
		margin: 0;
		color: var(--text-strong);
		font-size: clamp(26px, 3vw, 40px);
		letter-spacing: -0.04em;
		line-height: 1.15;
	}

	.participation-copy > p:last-child {
		max-width: 34em;
		margin: 16px 0 0;
		color: var(--text-muted);
		font-size: 14px;
		line-height: 1.65;
	}

	.condition-list {
		border-top: 2px solid var(--ink-900);
	}

	.condition {
		display: grid;
		grid-template-columns: 34px 1fr;
		gap: 14px;
		align-items: center;
		padding: 18px 0;
		border-bottom: var(--border-hair);
	}

	.condition-mark {
		display: inline-flex;
		width: 28px;
		height: 28px;
		align-items: center;
		justify-content: center;
		box-sizing: border-box;
		border: 1px solid var(--ink-300);
		border-radius: 50%;
		color: var(--text-faint);
		font-family: var(--font-mono);
		font-size: 12px;
		font-weight: 800;
		line-height: 1;
		font-variant-numeric: tabular-nums;
	}

	.condition-mark svg {
		display: block;
		width: 15px;
		height: 15px;
		fill: none;
		stroke: currentColor;
		stroke-width: 2;
		stroke-linecap: round;
		stroke-linejoin: round;
	}

	.condition.done .condition-mark {
		border-color: var(--positive);
		color: var(--positive);
		background: var(--positive-bg);
	}

	.condition strong {
		display: block;
		color: var(--text-strong);
		font-size: 15px;
	}

	.condition div span {
		margin-top: 3px;
		color: var(--text-muted);
		font-size: 13px;
	}

	.result {
		margin: 18px 0 0;
		color: var(--text-muted);
		font-size: 14px;
		font-weight: 650;
	}

	.result.complete {
		color: var(--positive);
	}

	.login-prompt {
		align-self: center;
		padding: 24px;
		background: var(--paper-50);
	}

	.login-prompt p {
		margin: 0 0 18px;
		color: var(--text-muted);
		font-size: 14px;
	}

	.login-prompt a {
		display: inline-flex;
		min-height: 42px;
		align-items: center;
		padding: 0 18px;
		background: var(--ink-900);
		color: var(--paper-0);
		font-size: 13px;
		font-weight: 700;
		text-decoration: none;
	}

	.current {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	iframe {
		display: block;
		width: 100%;
		min-height: 900px;
		border: 0;
		background: white;
	}

	@media (max-width: 640px) {
		.event-page {
			padding: var(--sp-3) 0 var(--sp-8);
		}

		.crumb {
			padding: 0 var(--sp-4);
		}

		.event-overview {
			grid-template-columns: 1fr;
			gap: var(--sp-8);
			margin: 0 var(--sp-4) var(--sp-5);
			padding: 28px 0;
		}

		.event-facts {
			grid-template-columns: 1fr;
		}

		.event-facts > div {
			display: grid;
			grid-template-columns: 90px 1fr;
			gap: 12px;
			padding: 12px 0;
			border-bottom: var(--border-hair);
		}

		.event-facts dd {
			margin: 0;
		}

		.participation {
			grid-template-columns: 1fr;
			margin: var(--sp-5) var(--sp-4) 0;
			padding: 24px 20px;
		}
	}

	@media (min-width: 641px) and (max-width: 900px) {
		.event-overview,
		.participation {
			grid-template-columns: 1fr;
		}
	}
</style>
