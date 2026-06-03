<!--
  EventModal — announcement / event (이벤트 · 공지).

  Banner image (or striped placeholder) + tag + title + body + meta row +
  in-body CTA. Footer carries a "don't show for a week" toggle and a close
  button. The toggle state is internal; on close, if it's checked, onHideWeek
  fires so the parent can persist (localStorage / server). Persistence is the
  caller's responsibility — this component stays content-only.

  Usage:
    <EventModal
        tag="Event · 이벤트"
        title={"2026 봄 시즌 오픈\n인증 챌린지"}
        meta={[
            { k: 'PERIOD', v: '05.01 — 05.31' },
            { k: 'REWARD', v: '12명 추첨' },
        ]}
        bannerImage="/banners/spring.png"
        ctaLabel="챌린지 참여하기"
        onCta={joinChallenge}
        onClose={() => (open = false)}
        onHideWeek={hideForWeek}
    >
        {#snippet description()} … {/snippet}
    </EventModal>
-->
<script lang="ts">
    import type { Snippet } from 'svelte';
    import Modal from './Modal.svelte';

    export interface EventMeta {
        k: string;
        v: string;
    }

    interface Props {
        /** Title; newlines render as line breaks. */
        title: string;
        description: Snippet;
        tag?: string;
        /** Tag colour. */
        variant?: 'event' | 'warn' | 'ink';
        meta?: EventMeta[];
        /** Banner image URL. Omit for the striped placeholder. */
        bannerImage?: string;
        /** Placeholder caption shown when bannerImage is absent. */
        bannerLabel?: string;
        /** In-body call-to-action; hidden when not provided. */
        ctaLabel?: string;
        onCta?: () => void;
        onClose: () => void;
        /** Show the "don't show for a week" toggle. */
        showHideWeek?: boolean;
        hideWeekLabel?: string;
        closeLabel?: string;
        /** Fired on close when "don't show for a week" is checked. */
        onHideWeek?: () => void;
    }

    let {
        title,
        description,
        tag = 'Event · 이벤트',
        variant = 'event',
        meta = [],
        bannerImage,
        bannerLabel = '이벤트 배너 이미지 · 920×376',
        ctaLabel,
        onCta,
        onClose,
        showHideWeek = true,
        hideWeekLabel = '일주일 동안 보지 않기',
        closeLabel = '닫기',
        onHideWeek,
    }: Props = $props();

    let dontShow = $state(false);
    const tagClass = $derived(variant === 'ink' ? '' : variant);
    const titleId = 'event-modal-title';

    function close() {
        if (dontShow) onHideWeek?.();
        onClose();
    }
</script>

<Modal onClose={close} labelledby={titleId}>
    {#if bannerImage}
        <div class="m-banner" style="background-image: url('{bannerImage}')"></div>
    {:else}
        <div class="m-banner placeholder"><span class="ph">{bannerLabel}</span></div>
    {/if}
    <span class="m-tag {tagClass}">{tag}</span>
    <h2 class="m-title pre" id={titleId}>{title}</h2>
    <p class="m-sub">{@render description()}</p>
    {#if meta.length}
        <div class="m-meta">
            {#each meta as m, i (i)}
                <div class="cell"><div class="k">{m.k}</div><div class="v">{m.v}</div></div>
            {/each}
        </div>
    {/if}
    {#if ctaLabel}
        <div style="height: 22px"></div>
        <button class="btn primary" onclick={() => onCta?.()}>
            {ctaLabel} <span class="arrow">→</span>
        </button>
    {/if}

    {#snippet foot()}
        <div class="foot-bar">
            {#if showHideWeek}
                <button
                    class="dont-show {dontShow ? 'on' : ''}"
                    onclick={() => (dontShow = !dontShow)}
                    aria-pressed={dontShow}
                >
                    <span class="cb"></span>
                    {hideWeekLabel}
                </button>
            {:else}
                <span></span>
            {/if}
            <button class="foot-close" onclick={close}>{closeLabel}</button>
        </div>
    {/snippet}
</Modal>

<style>
    .pre {
        white-space: pre-line;
    }
</style>
