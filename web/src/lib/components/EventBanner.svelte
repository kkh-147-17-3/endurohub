<!--
  EventBanner — 관리자에서 관리하는 이벤트 배너 본문.

  내용은 이미지 한 장이다. 디자인은 이미지 안에서 끝나고, 여기서 하는 일은
  이미지를 링크로 감싸고 그 아래 CTA 버튼을 붙이는 것뿐이다.

  두 곳에서 같은 데이터를 쓴다:
    variant="popup" — 팝업 모달 (640 폭)
    variant="page"  — 공지 상세 상단 히어로

  내용·게시기간은 django admin 의 "팝업 배너"에서 편집한다.
-->
<script lang="ts">
	import { page } from '$app/stores';
	import type { EventBanner } from '$lib/popup';

	interface Props {
		banner: EventBanner;
		variant?: 'popup' | 'page';
		/** CTA(이미지·버튼) 클릭 시 링크 이동 전에 호출 — 팝업 닫기 등에 쓴다. */
		onCta?: () => void;
	}

	let { banner, variant = 'popup', onCta }: Props = $props();

	// 지금 보고 있는 페이지를 가리키는 링크는 링크가 아니다 — 공지 상세에 붙은
	// 히어로의 CTA 가 그 공지 자신을 가리키는(cta_url 을 비운) 경우가 그렇다.
	const isSelf = $derived(banner.targetUrl === $page.url.pathname);
	const hasLink = $derived(!!banner.targetUrl && !isSelf);
	const hasButton = $derived(hasLink && !!banner.ctaLabel);

	// 공지 상세는 본문 폭이 이미지 원본보다 넓을 수 있다 — 원본 폭을 넘겨
	// 늘리면 흐려지므로 거기서 멈춘다. 모달은 폭이 640 으로 고정이라 그냥 채운다.
	const maxWidth = $derived(
		variant === 'page' && banner.imageWidth ? `${banner.imageWidth}px` : undefined
	);
</script>

<div class="evb evb--{variant}" style:max-width={maxWidth}>
	{#if banner.image}
		{#if hasLink}
			<a class="evb-fig" href={banner.targetUrl} onclick={() => onCta?.()}>
				<img
					src={banner.image}
					alt={banner.imageAlt}
					width={banner.imageWidth ?? undefined}
					height={banner.imageHeight ?? undefined}
				/>
			</a>
		{:else}
			<div class="evb-fig">
				<img
					src={banner.image}
					alt={banner.imageAlt}
					width={banner.imageWidth ?? undefined}
					height={banner.imageHeight ?? undefined}
				/>
			</div>
		{/if}
	{/if}

	{#if hasButton}
		<a class="evb-cta" href={banner.targetUrl} onclick={() => onCta?.()}>
			{banner.ctaLabel} <span class="arr">→</span>
		</a>
	{/if}
</div>

<style>
	.evb {
		background: var(--paper-0);
		display: flex;
		flex-direction: column;
	}

	/* ── 이미지 ──
	   width/height 속성이 내려오면 브라우저가 비율만큼 자리를 먼저 잡는다.
	   아래 CSS 는 그 자리를 컨테이너 폭에 맞춰 늘였다 줄일 뿐이다. */
	.evb-fig {
		display: block;
		background: var(--paper-50);
	}
	.evb-fig img {
		display: block;
		width: 100%;
		height: auto;
	}
	a.evb-fig:active {
		opacity: 0.9;
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

	/* ── variant="page" — 공지 상세 히어로.
	   원본 폭에서 멈추므로(위 maxWidth) 남는 자리는 가운데로 모은다. ── */
	.evb--page {
		margin-inline: auto;
	}

	@media (max-width: 700px) {
		.evb-cta {
			height: 60px;
			font-size: 17px;
		}
	}
</style>
