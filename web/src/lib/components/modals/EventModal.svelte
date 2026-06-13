<!--
  EventModal — announcement / event (이벤트 · 공지).

  Ink-block hero + tag + title + body + optional data strip.
  Footer carries a "don't show for a week" toggle and a close button.
  The toggle state is internal; on close, if it's checked, onHideWeek fires
  so the parent can persist (localStorage / server). Persistence is the
  caller's responsibility — this component stays content-only.

  Usage:
    <EventModal
        tag="Event · 이벤트"
        title={"2026 봄 시즌 오픈\n인증 챌린지"}
        heroGoal="100K / 30 DAYS"
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
        /** Tag colour variant. */
        variant?: 'event' | 'warn' | 'ink';
        meta?: EventMeta[];
        /** Large display text inside the ink-block hero (e.g. "100K / 30 DAYS"). */
        heroGoal?: string;
        /** Sub-caption below the hero goal. */
        heroCaption?: string;
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
        heroGoal,
        heroCaption,
        ctaLabel,
        onCta,
        onClose,
        showHideWeek = true,
        hideWeekLabel = '일주일 동안 보지 않기',
        closeLabel = '챌린지 참여 →',
        onHideWeek,
    }: Props = $props();

    let dontShow = $state(false);
    const titleId = 'event-modal-title';

    function close() {
        if (dontShow) onHideWeek?.();
        onClose();
    }
</script>

<Modal onClose={close} labelledby={titleId}>
    <span class="ev-tag" class:event={variant === 'event'} class:warn={variant === 'warn'}>{tag}</span>
    <h2 class="m-title pre" id={titleId}>{title}</h2>
    <p class="m-sub">{@render description()}</p>

    {#if heroGoal}
        <div class="m-hero">
            <span class="hero-label">GOAL</span>
            <div class="big eh-data">{heroGoal}</div>
            {#if heroCaption}
                <p class="hero-caption">{heroCaption}</p>
            {/if}
        </div>
    {/if}

    {#if meta.length}
        <div class="m-strip">
            {#each meta as m, i (i)}
                <div class="cell">
                    <div class="k">{m.k}</div>
                    <div class="vv">{m.v}</div>
                </div>
            {/each}
        </div>
    {/if}

    {#if ctaLabel}
        <div style="height: 22px"></div>
        <button class="in-cta" onclick={() => onCta?.()}>
            {ctaLabel} →
        </button>
    {/if}

    {#snippet foot()}
        {#if showHideWeek}
            <button
                class="dont {dontShow ? 'on' : ''}"
                onclick={() => (dontShow = !dontShow)}
                aria-pressed={dontShow}
                type="button"
            >
                <span class="box">{#if dontShow}✓{/if}</span>
                {hideWeekLabel}
            </button>
        {:else}
            <span></span>
        {/if}
        <span class="spacer"></span>
        <button class="btn primary" onclick={close}>{closeLabel}</button>
    {/snippet}
</Modal>

<style>
    .pre {
        white-space: pre-line;
    }

    /* tag strip */
    .ev-tag {
        display: inline-flex;
        align-items: center;
        height: 24px;
        padding: 0 9px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 14px;
        background: var(--ink-900);
        color: var(--paper-0);
    }
    .ev-tag.event {
        background: var(--accent);
        color: #fff;
    }
    .ev-tag.warn {
        background: var(--danger);
        color: #fff;
    }

    /* ink-block hero */
    .m-hero {
        margin: 18px -30px 0;
        padding: 26px 24px;
        background: var(--bg-inverse);
        color: var(--paper-0);
    }
    .hero-label {
        font-size: 10px;
        font-weight: 600;
        letter-spacing: var(--track-micro);
        text-transform: uppercase;
        opacity: 0.55;
    }
    .big {
        font-size: 34px;
        font-weight: 900;
        letter-spacing: -0.03em;
        line-height: 1.0;
        margin-top: 4px;
    }
    .hero-caption {
        font-size: 13px;
        opacity: 0.7;
        margin: 10px 0 0;
    }

    /* in-body CTA */
    .in-cta {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 14px 20px;
        background: var(--ink-900);
        color: var(--paper-0);
        border: 0;
        font-family: var(--font-sans);
        font-size: var(--text-body-sm);
        font-weight: var(--w-strong);
        cursor: pointer;
        margin-bottom: 4px;
        width: 100%;
        justify-content: center;
    }
    .in-cta:hover {
        background: var(--ink-700);
    }
</style>
