<!--
  NoticeModal — urgent notice variant (긴급 공지).

  Warn-coloured eyebrow + title + body + meta row + a single warn primary
  button. Use for schedule changes, cancellations, and the like.

  Usage:
    <NoticeModal
        title={"서울국제마라톤\n일정이 변경됐어요"}
        meta={[
            { k: '기존', v: '03.16 (일)', tone: 'mute', strike: true },
            { k: '변경', v: '03.23 (일)', tone: 'warn' },
            { k: '장소', v: '광화문 광장' },
        ]}
        ctaLabel="변경된 일정 확인하기"
        onCta={viewSchedule}
        onClose={() => (open = false)}
    >
        {#snippet description()} … {/snippet}
    </NoticeModal>
-->
<script lang="ts">
    import type { Snippet } from 'svelte';
    import Modal from './Modal.svelte';

    export interface NoticeMeta {
        k: string;
        v: string;
        /** Value colour: default ink, 'mute' (faded), or 'warn'. */
        tone?: 'ink' | 'mute' | 'warn';
        /** Strike through the value (e.g. an old, replaced date). */
        strike?: boolean;
    }

    interface Props {
        /** Title; newlines render as line breaks. */
        title: string;
        description: Snippet;
        eyebrow?: string;
        meta?: NoticeMeta[];
        /** Warn primary button; hidden when not provided. */
        ctaLabel?: string;
        onCta?: () => void;
        onClose: () => void;
    }

    let {
        title,
        description,
        eyebrow = 'Notice · 긴급 공지',
        meta = [],
        ctaLabel = '변경된 일정 확인하기',
        onCta,
        onClose,
    }: Props = $props();

    const titleId = 'notice-modal-title';

    function valueStyle(m: NoticeMeta): string {
        const parts: string[] = [];
        if (m.tone === 'mute') parts.push('color: var(--arena-ink-mute)');
        else if (m.tone === 'warn') parts.push('color: var(--arena-urgent)');
        if (m.strike) parts.push('text-decoration: line-through');
        return parts.join('; ');
    }
</script>

<Modal {onClose} labelledby={titleId}>
    <div class="m-eyebrow warn"><span class="dot"></span>{eyebrow}</div>
    <h2 class="m-title pre" id={titleId}>{title}</h2>
    <p class="m-sub">{@render description()}</p>
    {#if meta.length}
        <div class="m-meta">
            {#each meta as m, i (i)}
                <div class="cell">
                    <div class="k">{m.k}</div>
                    <div class="v" style={valueStyle(m)}>{m.v}</div>
                </div>
            {/each}
        </div>
    {/if}

    {#snippet foot()}
        {#if ctaLabel}
            <div class="btn-row">
                <button class="btn primary warn" onclick={() => onCta?.()}>
                    {ctaLabel} <span class="arrow">→</span>
                </button>
            </div>
        {/if}
    {/snippet}
</Modal>

<style>
    .pre {
        white-space: pre-line;
    }
</style>
