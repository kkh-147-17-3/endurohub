<script lang="ts">
    import { browser } from '$app/environment';
    import { enhance } from '$app/forms';
    import RaceTagSelector from '$lib/components/RaceTagSelector.svelte';
    import RichEditor from '$lib/components/RichEditor.svelte';

    let { data, form } = $props();

    let nickname    = $state('');
    let title       = $state('');
    let content     = $state('');
    let textLength  = $state(0);
    let category    = $state('');
    let selectedRaceIds = $state<number[]>([]);

    $effect(() => {
        nickname        = data.post.nickname === '익명' ? '' : data.post.nickname;
        title           = data.post.title;
        content         = data.post.content;
        category        = data.post.category || '';
        selectedRaceIds = data.post.taggedRaces?.map((r: { id: number }) => r.id) || [];
    });

    let isSubmitting = $state(false);

    let errors = $derived(flattenErrors(form?.errors));

    function flattenErrors(errs: Record<string, string[]> | undefined): Record<string, string> {
        if (!errs) return {};
        const flat: Record<string, string> = {};
        for (const [key, msgs] of Object.entries(errs)) {
            flat[key] = Array.isArray(msgs) ? msgs[0] : msgs;
        }
        return flat;
    }

    function handleEnhance() {
        isSubmitting = true;
        if (nickname) localStorage.setItem('nickname', nickname);

        return async ({ update }: { update: () => Promise<void> }) => {
            isSubmitting = false;
            await update();
        };
    }
</script>

<svelte:head>
    <title>글 수정 - 엔듀로허브</title>
    <meta name="description" content="커뮤니티 글을 수정합니다." />
    <meta name="robots" content="noindex" />
</svelte:head>

<div class="v-container form-page">
    <header class="page-head">
        <a href="/posts/{data.post.id}" class="back-link eh-micro">← 글로 돌아가기</a>
        <div class="eh-micro page-kicker">EDIT POST · 글 수정</div>
        <h1 class="eh-h2 page-title">글 수정</h1>
    </header>

    <form
        id="edit-form"
        method="POST"
        enctype="multipart/form-data"
        use:enhance={handleEnhance}
        class="form-grid"
    >
        <input type="hidden" name="edit_token" value={data.editToken} />

        <!-- Nickname + Category -->
        <div class="row row--two">
            <div class="eh-field">
                <label class="eh-field__label" for="nickname">
                    닉네임 <span class="label-hint">선택</span>
                </label>
                <input
                    type="text"
                    id="nickname"
                    name="nickname"
                    class="eh-input"
                    placeholder="익명"
                    maxlength="50"
                    bind:value={nickname}
                />
            </div>

            <div class="eh-field">
                <label class="eh-field__label" for="category">
                    카테고리 <span class="label-hint">선택</span>
                </label>
                <div class="select-wrap">
                    <select id="category" name="category" class="eh-select" bind:value={category}>
                        <option value="">— 미선택 —</option>
                        <option value="race_review">후기</option>
                        <option value="question">Q&A</option>
                        <option value="free">자유</option>
                        <option value="injury">부상/재활</option>
                        <option value="gear">장비</option>
                        <option value="training">훈련</option>
                    </select>
                    <svg class="select-chev" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
                </div>
            </div>
        </div>

        <!-- Title -->
        <div class="eh-field" class:eh-field--error={!!errors.title}>
            <label class="eh-field__label" for="title">
                제목 <em class="required">*</em>
                <span class="label-hint">{title.length} / 100</span>
            </label>
            <input
                type="text"
                id="title"
                name="title"
                class="eh-input"
                placeholder="제목을 입력하세요"
                maxlength="100"
                required
                bind:value={title}
            />
            {#if errors.title}<p class="eh-field__hint">{errors.title}</p>{/if}
        </div>

        <!-- Content -->
        <div class="eh-field" class:eh-field--error={!!errors.content}>
            <div class="eh-field__label">
                내용 <em class="required">*</em>
                <span class="label-hint">최대 10,000자</span>
            </div>
            {#if browser}
                <div class="editor-wrap">
                    <RichEditor
                        bind:content
                        bind:textLength
                        maxLength={10000}
                        placeholder="내용을 입력하세요"
                        error={!!errors.content}
                    />
                </div>
            {:else}
                <div class="editor-skeleton"></div>
            {/if}
            <input type="hidden" name="content" value={content} />
            {#if errors.content}<p class="eh-field__hint">{errors.content}</p>{/if}
        </div>

        <!-- Race tags -->
        <div class="eh-field">
            <RaceTagSelector races={data.races} bind:selectedIds={selectedRaceIds} />
            {#if errors.race_ids}<p class="eh-field__hint">{errors.race_ids}</p>{/if}
        </div>

        {#each selectedRaceIds as raceId}
            <input type="hidden" name="race_ids" value={raceId} />
        {/each}

        {#if errors.password}
            <div class="error-box" role="alert">{errors.password}</div>
        {/if}

        <div class="submit-row">
            <a href="/posts/{data.post.id}" class="eh-btn eh-btn--md eh-btn--ghost">취소</a>
            <button type="submit" class="eh-btn eh-btn--md eh-btn--primary" disabled={isSubmitting}>
                {isSubmitting ? '저장 중...' : '수정 저장'}
            </button>
        </div>
    </form>
</div>

<style>
    .form-page {
        max-width: 760px;
        padding-top: 0;
        padding-bottom: var(--sp-20);
    }

    .page-head {
        padding: var(--sp-8) 0 var(--sp-6);
        border-bottom: var(--border-rule);
        margin-bottom: var(--sp-8);
        display: flex;
        flex-direction: column;
        gap: var(--sp-2);
    }
    .back-link {
        color: var(--text-muted);
        text-decoration: none;
        transition: color var(--dur-fast) var(--ease-out);
    }
    .back-link:hover { color: var(--text-strong); }
    .page-kicker { color: var(--text-muted); }
    .page-title { margin: 0; }

    .form-grid {
        display: flex;
        flex-direction: column;
        gap: var(--sp-6);
    }

    .row { display: flex; flex-direction: column; gap: var(--sp-4); }
    .row--two {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: var(--sp-4);
    }
    @media (max-width: 600px) {
        .row--two { grid-template-columns: 1fr; }
    }

    .label-hint {
        font-weight: 400;
        color: var(--text-faint);
        margin-left: 6px;
        text-transform: none;
        letter-spacing: 0;
    }
    .required {
        font-style: normal;
        color: var(--danger);
        margin-left: 2px;
    }

    .select-wrap { position: relative; }
    .eh-select {
        appearance: none;
        height: 44px;
        padding: 0 36px 0 14px;
        font-family: var(--font-sans);
        font-size: 15px;
        color: var(--text-strong);
        background: var(--paper-0);
        border: 1px solid var(--line);
        border-radius: var(--r-1);
        cursor: pointer;
        width: 100%;
        transition: border-color var(--dur-fast) var(--ease-out);
    }
    .eh-select:hover { border-color: var(--ink-300); }
    .eh-select:focus { outline: none; border-color: var(--ink-900); }
    .select-chev {
        position: absolute;
        right: 12px;
        bottom: 50%;
        transform: translateY(50%);
        pointer-events: none;
        color: var(--text-muted);
    }

    .editor-wrap {
        border: 1px solid var(--line);
        border-radius: var(--r-1);
        background: var(--paper-0);
        overflow: hidden;
        transition: border-color var(--dur-fast) var(--ease-out);
    }
    .editor-wrap:focus-within { border-color: var(--ink-900); }
    .editor-skeleton {
        min-height: 240px;
        background: var(--paper-50);
        border: 1px solid var(--line);
        border-radius: var(--r-1);
    }

    .error-box {
        border: 1px solid var(--danger);
        background: var(--danger-bg);
        color: var(--danger);
        padding: 10px 14px;
        font-size: 13px;
        font-weight: 600;
        border-radius: var(--r-1);
    }

    .submit-row {
        display: flex;
        justify-content: flex-end;
        gap: var(--sp-2);
        margin-top: var(--sp-2);
        padding-top: var(--sp-5);
        border-top: var(--border-hair);
    }
</style>
