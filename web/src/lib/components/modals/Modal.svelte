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
        /** Override the default 460px max width. */
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
        maxWidth = '460px',
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
    class="eh-scrim"
    role="presentation"
    onmousedown={(e) => {
        if (e.target === e.currentTarget) onClose();
    }}
>
    <div
        class="eh-modal"
        style="max-width: {maxWidth}"
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledby}
        tabindex="-1"
        bind:this={dialogEl}
    >
        <button class="eh-modal-close" onclick={onClose} aria-label={closeLabel}>×</button>
        <div class="eh-modal-body">
            {@render children()}
        </div>
        {#if foot}
            <div class="eh-modal-foot">
                {@render foot()}
            </div>
        {/if}
    </div>
</div>

<style>
    /* ───────────── Shell ───────────── */
    .eh-scrim {
        position: fixed;
        inset: 0;
        z-index: 200;
        background: color-mix(in oklch, var(--arena-ink) 55%, transparent);
        backdrop-filter: blur(3px);
        display: grid;
        place-items: center;
        padding: 24px;
        animation: eh-scrim-in 0.22s ease both;
    }
    @keyframes eh-scrim-in {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }

    .eh-modal {
        position: relative;
        width: 100%;
        background: var(--arena-paper);
        border: 1px solid var(--arena-line);
        box-shadow: 0 24px 60px -20px color-mix(in oklch, var(--arena-ink) 50%, transparent);
        animation: eh-modal-in 0.28s cubic-bezier(0.2, 0.8, 0.2, 1) both;
        max-height: calc(100vh - 48px);
        display: flex;
        flex-direction: column;
        outline: none;

        /* warn shades derived from the single arena urgent token */
        --eh-warn: var(--arena-urgent);
        --eh-warn-deep: color-mix(in oklch, var(--arena-urgent) 84%, black);
    }
    @keyframes eh-modal-in {
        from {
            opacity: 0;
            transform: translateY(12px) scale(0.98);
        }
        to {
            opacity: 1;
            transform: none;
        }
    }

    .eh-modal-close {
        position: absolute;
        top: 14px;
        right: 14px;
        z-index: 2;
        width: 30px;
        height: 30px;
        background: transparent;
        border: 1px solid transparent;
        color: var(--arena-ink-mute);
        font-size: 20px;
        line-height: 1;
        display: grid;
        place-items: center;
    }
    .eh-modal-close:hover {
        color: var(--arena-ink);
        border-color: var(--arena-line-soft);
    }

    .eh-modal-body {
        padding: 30px 30px 0;
        overflow-y: auto;
        overscroll-behavior: contain;
    }
    .eh-modal-foot {
        padding: 22px 30px 26px;
    }

    @media (prefers-reduced-motion: reduce) {
        .eh-scrim,
        .eh-modal {
            animation: none;
        }
    }

    @media (max-width: 480px) {
        .eh-scrim {
            padding: 0;
            place-items: end center;
        }
        .eh-modal {
            max-width: 100% !important;
            max-height: 100vh;
        }
    }

    /* ───────────── Shared content vocabulary ─────────────
       Scoped under .eh-modal so the :global content rendered by the
       variant components is styled from one source of truth. */

    /* eyebrow */
    .eh-modal :global(.m-eyebrow) {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--arena-accent-deep);
        margin-bottom: 18px;
    }
    .eh-modal :global(.m-eyebrow .dot) {
        width: 7px;
        height: 7px;
        background: var(--arena-accent);
    }
    .eh-modal :global(.m-eyebrow.warn) {
        color: var(--eh-warn-deep);
    }
    .eh-modal :global(.m-eyebrow.warn .dot) {
        background: var(--eh-warn);
    }

    /* title + sub */
    .eh-modal :global(.m-title) {
        font-family: var(--arena-f-display);
        font-size: 24px;
        font-weight: 700;
        letter-spacing: -0.02em;
        line-height: 1.2;
        margin: 0 0 12px;
        color: var(--arena-ink);
    }
    .eh-modal :global(.m-sub) {
        font-size: 14px;
        line-height: 1.6;
        color: var(--arena-ink-soft);
        margin: 0;
    }
    .eh-modal :global(.m-sub b) {
        color: var(--arena-ink);
        font-weight: 600;
    }

    /* checklist of missing info */
    .eh-modal :global(.req-list) {
        border: 1px solid var(--arena-line-soft);
        margin: 22px 0 4px;
    }
    .eh-modal :global(.req-row) {
        display: grid;
        grid-template-columns: 22px 1fr auto;
        align-items: center;
        gap: 14px;
        padding: 14px 16px;
        border-bottom: 1px solid var(--arena-line-soft);
    }
    .eh-modal :global(.req-row:last-child) {
        border-bottom: 0;
    }
    .eh-modal :global(.req-mark) {
        width: 22px;
        height: 22px;
        display: grid;
        place-items: center;
    }
    .eh-modal :global(.req-mark.ok) {
        background: var(--arena-ink);
    }
    .eh-modal :global(.req-mark.ok::after) {
        content: '';
        width: 7px;
        height: 11px;
        border: solid var(--arena-paper);
        border-width: 0 2px 2px 0;
        transform: rotate(45deg) translate(-1px, -1px);
    }
    .eh-modal :global(.req-mark.todo) {
        border: 1px solid var(--arena-line);
    }
    .eh-modal :global(.req-mark.todo::after) {
        content: '';
        width: 7px;
        height: 7px;
        background: var(--eh-warn);
    }
    .eh-modal :global(.req-name) {
        font-size: 14px;
        font-weight: 600;
        color: var(--arena-ink);
    }
    .eh-modal :global(.req-name .note) {
        display: block;
        font-size: 12px;
        font-weight: 400;
        color: var(--arena-ink-mute);
        margin-top: 2px;
    }
    .eh-modal :global(.req-state) {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 0.1em;
        color: var(--arena-ink-mute);
    }
    .eh-modal :global(.req-state.ok) {
        color: var(--arena-accent-deep);
    }
    .eh-modal :global(.req-state.todo) {
        color: var(--eh-warn-deep);
    }

    /* event banner */
    .eh-modal :global(.m-banner) {
        margin: -30px -30px 22px;
        height: 188px;
        border-bottom: 1px solid var(--arena-line);
        background-color: var(--arena-paper-deep);
        background-size: cover;
        background-position: center;
        display: grid;
        place-items: center;
        position: relative;
        overflow: hidden;
    }
    .eh-modal :global(.m-banner.placeholder) {
        background-image: repeating-linear-gradient(
            135deg,
            transparent 0 14px,
            color-mix(in oklch, var(--arena-ink) 5%, transparent) 14px 28px
        );
    }
    .eh-modal :global(.m-banner .ph) {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.14em;
        color: var(--arena-ink-mute);
        text-transform: uppercase;
    }
    .eh-modal :global(.m-banner .ph::before) {
        content: '[ ';
    }
    .eh-modal :global(.m-banner .ph::after) {
        content: ' ]';
    }

    /* tag */
    .eh-modal :global(.m-tag) {
        display: inline-block;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        padding: 4px 8px;
        margin-bottom: 14px;
        background: var(--arena-ink);
        color: var(--arena-paper);
    }
    .eh-modal :global(.m-tag.event) {
        background: var(--arena-accent-deep);
    }
    .eh-modal :global(.m-tag.warn) {
        background: var(--eh-warn-deep);
    }

    /* meta row */
    .eh-modal :global(.m-meta) {
        display: flex;
        gap: 18px;
        margin: 20px 0 4px;
        flex-wrap: wrap;
    }
    .eh-modal :global(.m-meta .k) {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 0.12em;
        color: var(--arena-ink-soft);
        margin-bottom: 5px;
        text-transform: uppercase;
    }
    .eh-modal :global(.m-meta .v) {
        font-size: 14px;
        font-weight: 600;
        color: var(--arena-ink);
    }

    /* buttons */
    .eh-modal :global(.btn) {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        padding: 15px 22px;
        border: 1px solid var(--arena-line);
        background: transparent;
        font-family: var(--arena-f-body);
        font-size: 14px;
        font-weight: 600;
        color: var(--arena-ink);
        width: 100%;
    }
    .eh-modal :global(.btn.primary) {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border-color: var(--arena-ink);
    }
    .eh-modal :global(.btn.primary .arrow) {
        color: var(--arena-accent);
    }
    .eh-modal :global(.btn.primary.warn) {
        background: var(--eh-warn-deep);
        border-color: var(--eh-warn-deep);
        color: var(--arena-paper);
    }
    .eh-modal :global(.btn.primary.warn .arrow) {
        color: var(--arena-paper);
    }
    .eh-modal :global(.btn.ghost:hover) {
        background: var(--arena-paper-alt);
    }
    .eh-modal :global(.btn-row) {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    /* footer: dont-show + close */
    .eh-modal :global(.foot-bar) {
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-top: 1px solid var(--arena-line-soft);
        margin-top: 4px;
        padding-top: 16px;
    }
    .eh-modal :global(.dont-show) {
        display: inline-flex;
        align-items: center;
        gap: 9px;
        background: transparent;
        border: 0;
        padding: 4px 0;
        font-family: var(--arena-f-body);
        font-size: 13px;
        color: var(--arena-ink-soft);
        font-weight: 500;
        cursor: pointer;
    }
    .eh-modal :global(.dont-show .cb) {
        width: 17px;
        height: 17px;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
        display: grid;
        place-items: center;
        flex-shrink: 0;
    }
    .eh-modal :global(.dont-show.on .cb) {
        background: var(--arena-ink);
        border-color: var(--arena-ink);
    }
    .eh-modal :global(.dont-show.on .cb::after) {
        content: '';
        width: 6px;
        height: 10px;
        border: solid var(--arena-paper);
        border-width: 0 2px 2px 0;
        transform: rotate(45deg) translate(-1px, -1px);
    }
    .eh-modal :global(.dont-show:hover) {
        color: var(--arena-ink);
    }
    .eh-modal :global(.foot-close) {
        background: transparent;
        border: 0;
        padding: 4px 2px;
        font-family: var(--arena-f-body);
        font-size: 13px;
        font-weight: 600;
        color: var(--arena-ink);
        border-bottom: 1px solid var(--arena-line-soft);
        cursor: pointer;
    }
    .eh-modal :global(.foot-close:hover) {
        border-bottom-color: var(--arena-ink);
    }
</style>
