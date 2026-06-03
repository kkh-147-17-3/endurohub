<!--
  ActionModal — action-driving nudge (정보 등록 유도).

  Announces a new feature and shows a checklist of info the user still needs
  to register before they can use it. Primary + secondary stacked buttons.

  Usage:
    <ActionModal
        title={"시즌 플래너가\n새로 추가됐어요"}
        reqs={[
            { name: '관심 종목', note: '러닝 · 트레일', state: '등록됨', ok: true },
            { name: '활동 지역', note: '지역별 대회 추천에 사용', state: '필요', ok: false },
        ]}
        primaryLabel="정보 등록하고 시작하기"
        onPrimary={goToOnboarding}
        onClose={() => (open = false)}
    >
        {#snippet description()}
            … rich text with <b>…</b> …
        {/snippet}
    </ActionModal>
-->
<script lang="ts">
    import type { Snippet } from 'svelte';
    import Modal from './Modal.svelte';

    export interface ActionReq {
        name: string;
        note?: string;
        /** Short state label, e.g. "등록됨" / "필요". */
        state: string;
        /** true → done (checked), false → todo (dot). */
        ok: boolean;
    }

    interface Props {
        /** Title; newlines render as line breaks. */
        title: string;
        /** Rich body copy. */
        description: Snippet;
        reqs: ActionReq[];
        eyebrow?: string;
        primaryLabel?: string;
        /** Secondary text button; hidden when not provided. */
        secondaryLabel?: string;
        onPrimary?: () => void;
        onClose: () => void;
    }

    let {
        title,
        description,
        reqs,
        eyebrow = 'New Feature · 기능 추가',
        primaryLabel = '정보 등록하고 시작하기',
        secondaryLabel = '나중에 할게요',
        onPrimary,
        onClose,
    }: Props = $props();

    const titleId = 'action-modal-title';
</script>

<Modal {onClose} labelledby={titleId}>
    <div class="m-eyebrow"><span class="dot"></span>{eyebrow}</div>
    <h2 class="m-title pre" id={titleId}>{title}</h2>
    <p class="m-sub">{@render description()}</p>
    <div class="req-list">
        {#each reqs as r, i (i)}
            <div class="req-row">
                <span class="req-mark {r.ok ? 'ok' : 'todo'}"></span>
                <span class="req-name"
                    >{r.name}{#if r.note}<span class="note">{r.note}</span>{/if}</span
                >
                <span class="req-state {r.ok ? 'ok' : 'todo'}">{r.state}</span>
            </div>
        {/each}
    </div>

    {#snippet foot()}
        <div class="btn-row">
            <button class="btn primary" onclick={() => onPrimary?.()}>
                {primaryLabel} <span class="arrow">→</span>
            </button>
            {#if secondaryLabel}
                <button class="btn ghost" onclick={onClose}>{secondaryLabel}</button>
            {/if}
        </div>
    {/snippet}
</Modal>

<style>
    /* newlines in the title prop become visible line breaks */
    .pre {
        white-space: pre-line;
    }
</style>
