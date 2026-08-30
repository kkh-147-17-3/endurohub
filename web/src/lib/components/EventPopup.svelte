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

	function close() {
		if (dontShow) dismissFor(banner, banner.dismissDays);
		onClose();
	}

	// 이미지·버튼으로 나가는 경우엔 다시 뜨지 않도록 항상 기간만큼 숨긴다 —
	// 상세를 이미 본 사람에게 같은 팝업을 다시 띄울 이유가 없다.
	function onCta() {
		dismissFor(banner, banner.dismissDays);
		onClose();
	}
</script>

<Modal
	onClose={close}
	maxWidth="640px"
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
