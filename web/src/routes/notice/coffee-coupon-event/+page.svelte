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
		content="리뷰와 참가 기록을 남기고 스타벅스 카페 아메리카노 T를 받아보세요."
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
			<h1 id="participation-title">현재 나의 참여 현황을 확인하세요.</h1>
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

	.participation h1 {
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
	}

	.condition strong {
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

		.participation {
			grid-template-columns: 1fr;
			margin: var(--sp-5) var(--sp-4) 0;
			padding: 24px 20px;
		}
	}

	@media (min-width: 641px) and (max-width: 900px) {
		.participation {
			grid-template-columns: 1fr;
		}
	}
</style>
