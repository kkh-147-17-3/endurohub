<!--
  NoticeModal — urgent notice variant (긴급 공지).

  Warn-coloured eyebrow + title + body + data strip + a single warn primary
  button. Use for schedule changes, cancellations, and the like.

  Usage:
    <NoticeModal
        title={"서울국제마라톤\n일정이 변경됐어요"}
        meta={[
            { k: 'START', v: '07:30', old: '06:30' },
            { k: '수하물 마감', v: '07:00', old: '06:00' },
            { k: '코스', v: '변경 없음' },
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
        /** Previous value shown struck through before the new value. */
        old?: string;
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
</script>

<Modal {onClose} labelledby={titleId}>
    <div class="m-eyebrow warn"><span class="dot"></span>{eyebrow}</div>
    <h2 class="m-title pre" id={titleId}>{title}</h2>
    <p class="m-sub">{@render description()}</p>

    {#if meta.length}
        <div class="m-strip">
            {#each meta as m, i (i)}
                <div class="cell">
                    <div class="k">{m.k}</div>
                    <div class="vv" style={[
                            m.tone === 'warn' ? 'color: var(--danger)' : m.tone === 'mute' ? 'color: var(--text-faint)' : '',
                            m.strike ? 'text-decoration: line-through' : ''
                        ].filter(Boolean).join('; ')}>
                        {#if m.old}<span class="old">{m.old}</span>{/if}{m.v}
                    </div>
                </div>
            {/each}
        </div>
    {/if}

    {#snippet foot()}
        {#if ctaLabel}
            <button class="btn primary warn-btn" onclick={() => onCta?.()}>
                {ctaLabel} <span class="arrow">→</span>
            </button>
        {/if}
        <span class="spacer"></span>
        <button class="btn ghost" onclick={onClose}>닫기</button>
    {/snippet}
</Modal>

<style>
    .pre {
        white-space: pre-line;
    }
    .old {
        text-decoration: line-through;
        color: var(--text-faint);
        font-weight: 400;
        margin-right: 8px;
    }
    /* warn primary inside foot */
    :global(.v-modal .m-foot .btn.warn-btn) {
        background: var(--danger);
        color: #fff;
        border-color: var(--danger);
    }
    :global(.v-modal .m-foot .btn.warn-btn:hover) {
        background: color-mix(in oklch, var(--danger) 85%, black);
        border-color: color-mix(in oklch, var(--danger) 85%, black);
    }
    .arrow {
        font-family: var(--font-sans);
    }
</style>
