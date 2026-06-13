<!--
  Modal — reusable Paper Terminal modal shell.

  Owns the scrim, the modal box, the close button, and the shared content
  "vocabulary" (eyebrow / title / sub / checklist / banner / tag / meta /
  buttons / footer bar) that the variant modals render into via snippets.

  Behaviour: Escape + backdrop click close, body scroll-lock while open,
  focus moves to the dialog on open. Honours prefers-reduced-motion.

  Usage:
    <Modal onClose={() => (open = false)}>
      …body markup using the .m-* / .req-* / .btn classes…
      {#snippet foot()} …footer markup… {/snippet}
    </Modal>
-->
<script lang="ts">
    import type { Snippet } from 'svelte';

    interface Props {
        /** Called on Escape, backdrop click, or the × button. */
        onClose: () => void;
        /** Modal body content. */
        children: Snippet;
        /** Optional footer region (buttons, "don't show" bar, etc.). */
        foot?: Snippet;
        /** Override the default 520px max width. */
        maxWidth?: string;
        /** id of the title element, wired to aria-labelledby. */
        labelledby?: string;
        /** Accessible label for the × button. */
        closeLabel?: string;
    }

    let {
        onClose,
        children,
        foot,
        maxWidth = '520px',
        labelledby,
        closeLabel = '닫기',
    }: Props = $props();

    let dialogEl = $state<HTMLDivElement | null>(null);

    function onKeydown(e: KeyboardEvent) {
        if (e.key === 'Escape') {
            e.stopPropagation();
            onClose();
        }
    }

    // Lock background scroll and pull focus into the dialog while open.
    $effect(() => {
        const prevOverflow = document.body.style.overflow;
        document.body.style.overflow = 'hidden';
        dialogEl?.focus();
        return () => {
            document.body.style.overflow = prevOverflow;
        };
    });
</script>

<svelte:window onkeydown={onKeydown} />

<!-- svelte-ignore a11y_no_static_element_interactions -- backdrop is presentational; keyboard close is handled via Escape on window -->
<div
    class="v-scrim"
    role="presentation"
    onmousedown={(e) => {
        if (e.target === e.currentTarget) onClose();
    }}
>
    <div
        class="v-modal"
        style="max-width: {maxWidth}"
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledby}
        tabindex="-1"
        bind:this={dialogEl}
    >
        <button class="m-close" onclick={onClose} aria-label={closeLabel}>×</button>
        <div class="m-body">
            {@render children()}
        </div>
        {#if foot}
            <div class="m-foot">
                {@render foot()}
            </div>
        {/if}
    </div>
</div>

<style>
    /* ── Close button ── */
    .m-close {
        position: absolute;
        top: 12px;
        right: 12px;
        z-index: 2;
        width: 32px;
        height: 32px;
        background: transparent;
        border: 0;
        color: var(--text-faint);
        font-size: 18px;
        display: grid;
        place-items: center;
        cursor: pointer;
    }
    .m-close:hover {
        color: var(--text-strong);
    }

    /* ── Body / foot regions ── */
    .m-body {
        padding: 28px 30px 0;
        overflow-y: auto;
        overscroll-behavior: contain;
        max-height: calc(100vh - 160px);
    }
    .m-foot {
        padding: 22px 30px 26px;
        display: flex;
        gap: 8px;
        align-items: center;
    }

    /* ─────────── Shared content vocabulary ───────────
       Scoped under .v-modal so variant-modal markup
       inherits one source of truth. */

    /* eyebrow */
    :global(.v-modal .m-eyebrow) {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: var(--text-micro);
        font-weight: var(--w-strong);
        letter-spacing: var(--track-micro);
        text-transform: uppercase;
        color: var(--text-accent);
        margin-bottom: 18px;
    }
    :global(.v-modal .m-eyebrow .dot) {
        width: 7px;
        height: 7px;
        background: var(--accent);
        flex: none;
    }
    :global(.v-modal .m-eyebrow.warn) {
        color: var(--danger);
    }
    :global(.v-modal .m-eyebrow.warn .dot) {
        background: var(--danger);
    }

    /* title + sub */
    :global(.v-modal .m-title) {
        font-family: var(--font-sans);
        font-size: 24px;
        font-weight: 800;
        letter-spacing: var(--track-heading);
        line-height: 1.15;
        margin: 0 0 10px;
        color: var(--text-strong);
    }
    :global(.v-modal .m-sub) {
        font-size: var(--text-body-sm);
        line-height: var(--leading-body);
        color: var(--text-muted);
        margin: 0;
    }
    :global(.v-modal .m-sub b) {
        color: var(--text-strong);
        font-weight: var(--w-strong);
    }

    /* checklist of missing info */
    :global(.v-modal .req-list) {
        border: var(--border-hair);
        margin: 22px 0 4px;
    }
    :global(.v-modal .req-row) {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 12px;
        align-items: center;
        padding: 12px 0;
        border-bottom: var(--border-hair);
    }
    :global(.v-modal .req-row:last-child) {
        border-bottom: 0;
    }
    :global(.v-modal .req-row .nm) {
        font-size: var(--text-body-sm);
        font-weight: var(--w-strong);
        color: var(--text-strong);
    }
    :global(.v-modal .req-row .note) {
        display: block;
        font-size: 12px;
        font-weight: 400;
        color: var(--text-faint);
        margin-top: 2px;
    }

    /* event/notice hero strip */
    :global(.v-modal .m-hero) {
        margin: -28px -30px 22px;
        padding: 26px 24px;
        background: var(--bg-inverse);
        color: var(--paper-0);
    }
    :global(.v-modal .m-hero .big) {
        font-size: 34px;
        font-weight: 900;
        letter-spacing: -0.03em;
        line-height: 1.0;
    }
    :global(.v-modal .m-hero .big .acc) {
        color: var(--accent);
    }

    /* urgent strip (2-col data grid) */
    :global(.v-modal .m-strip) {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1px;
        background: var(--line);
        border: var(--border-hair);
        margin-top: 18px;
    }
    :global(.v-modal .m-strip .cell) {
        background: var(--paper-0);
        padding: 12px 14px;
    }
    :global(.v-modal .m-strip .k) {
        font-size: 10px;
        font-weight: var(--w-strong);
        letter-spacing: var(--track-micro);
        text-transform: uppercase;
        color: var(--text-faint);
    }
    :global(.v-modal .m-strip .vv) {
        font-size: 16px;
        font-weight: 700;
        margin-top: 3px;
        font-variant-numeric: tabular-nums;
    }
    :global(.v-modal .m-strip .vv .old) {
        text-decoration: line-through;
        color: var(--text-faint);
        font-weight: 400;
        margin-right: 8px;
    }

    /* "don't show for a week" checkbox */
    :global(.v-modal .dont) {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: none;
        border: 0;
        font-size: 13px;
        color: var(--text-muted);
        padding: 0;
        cursor: pointer;
    }
    :global(.v-modal .dont .box) {
        width: 16px;
        height: 16px;
        border: 1px solid var(--line);
        display: grid;
        place-items: center;
        font-size: 11px;
        color: var(--paper-0);
        background: var(--paper-0);
        flex: none;
    }
    :global(.v-modal .dont.on .box) {
        background: var(--ink-900);
        border-color: var(--ink-900);
    }
    :global(.v-modal .dont:hover) {
        color: var(--text-strong);
    }

    /* buttons */
    :global(.v-modal .m-foot .btn) {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        padding: 15px 22px;
        border: 1px solid var(--line);
        background: transparent;
        font-family: var(--font-sans);
        font-size: var(--text-body-sm);
        font-weight: var(--w-strong);
        color: var(--text-strong);
        cursor: pointer;
        text-decoration: none;
    }
    :global(.v-modal .m-foot .btn.primary) {
        background: var(--ink-900);
        color: var(--paper-0);
        border-color: var(--ink-900);
    }
    :global(.v-modal .m-foot .btn.signal) {
        background: var(--accent);
        color: #fff;
        border-color: var(--accent);
    }
    :global(.v-modal .m-foot .btn.ghost) {
        background: transparent;
        border-color: var(--line);
        color: var(--text-muted);
    }
    :global(.v-modal .m-foot .btn.ghost:hover) {
        color: var(--text-strong);
        border-color: var(--ink-900);
    }
    :global(.v-modal .m-foot .spacer) {
        flex: 1;
    }

    @media (max-width: 480px) {
        :global(.v-scrim) {
            padding: 0;
            place-items: end center;
        }
        :global(.v-modal) {
            max-width: 100% !important;
            max-height: 100vh;
        }
        .m-body {
            max-height: calc(100vh - 140px);
        }
    }
</style>
