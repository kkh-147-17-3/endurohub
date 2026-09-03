<!--
  EventPopup — 이벤트 배너를 팝업 모달로 띄운다.

  내용은 이미지 한 장이고 django admin 의 "팝업 배너"에서 관리한다. 여기서는
  렌더와 "다시 보지 않기"(localStorage) 만 담당한다. 이미지나 버튼을 누르면
  관리자가 지정한 링크(없으면 연결된 공지 상세)로 간다.
-->
<script lang="ts">
	import Modal from '$lib/components/modals/Modal.svelte';
	import EventBanner from '$lib/components/EventBanner.svelte';
	import { dismissFor, type EventBanner as EventBannerData } from '$lib/popup';

	interface Props {
		banner: EventBannerData;
		onClose: () => void;
	}

	let { banner, onClose }: Props = $props();

	let dontShow = $state(false);
	const hideLabel = $derived(
		banner.dismissDays === 1 ? '오늘 하루 보지 않기' : `${banner.dismissDays}일 동안 보지 않기`
	);
	// 세로형 포스터 + CTA + 하단 제어 영역이 한 화면 안에 들어오도록
	// 이미지 비율로 모달의 최대 폭을 역산한다.
	const imageRatio = $derived(
		banner.imageWidth && banner.imageHeight ? banner.imageWidth / banner.imageHeight : 0.64
	);
	const modalMaxWidth = $derived(
		`min(640px, calc((100dvh - 230px) * ${imageRatio}))`
	);

	function close() {
		if (dontShow) dismissFor(banner, banner.dismissDays);
		onClose();
	}

	// CTA 이동 자체는 숨김 동의가 아니다. 숨김 기한은 사용자가 위 옵션을
	// 직접 선택한 뒤 닫았을 때만 저장한다.
	function onCta() {
		onClose();
	}
</script>

<Modal
	onClose={close}
	maxWidth={modalMaxWidth}
	padded={false}
	closeTone="overlay"
	label={banner.imageAlt || '이벤트 안내'}
>
	<EventBanner {banner} variant="popup" {onCta} />

	{#snippet foot()}
		<button
			class="dont {dontShow ? 'on' : ''}"
			onclick={() => (dontShow = !dontShow)}
			aria-pressed={dontShow}
			type="button"
		>
			<span class="box">{#if dontShow}✓{/if}</span>
			{hideLabel}
		</button>
		<span class="spacer"></span>
		<button class="btn ghost" onclick={close}>닫기</button>
	{/snippet}
</Modal>
