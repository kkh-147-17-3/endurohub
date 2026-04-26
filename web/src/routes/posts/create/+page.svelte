<script lang="ts">
    import { browser } from '$app/environment';
    import { enhance } from '$app/forms';
    import { page } from '$app/stores';
    import RaceTagSelector from '$lib/components/RaceTagSelector.svelte';
    import RichEditor from '$lib/components/RichEditor.svelte';

    let { data, form } = $props();

    let isLoggedIn = $derived(!!$page.data.user);

    let nickname = $state('');
    let title = $state('');
    let content = $state('');
    let textLength = $state(0);
    let password = $state('');
    let category = $state('');
    let selectedRaceIds = $state<number[]>([]);

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

    $effect(() => {
        const savedNickname = localStorage.getItem('nickname');
        const savedPassword = localStorage.getItem('postPassword');
        if (savedNickname) nickname = savedNickname;
        if (savedPassword) password = savedPassword;
    });

    function handleEnhance() {
        isSubmitting = true;
        if (nickname) localStorage.setItem('nickname', nickname);
        if (password) localStorage.setItem('postPassword', password);

        return async ({ update }: { update: () => Promise<void> }) => {
            isSubmitting = false;
            await update();
        };
    }
</script>

<svelte:head>
    <title>글쓰기 - 엔듀로허브</title>
    <meta name="description" content="자유게시판에 글을 작성합니다." />
    <meta name="robots" content="noindex" />
</svelte:head>

<div class="form-wrap">
    <header class="page-head">
        <a href="/posts" class="back-link">← 커뮤니티</a>
        <div class="kicker">NEW POST · 글쓰기</div>
        <h1 class="page-title">새 글 작성</h1>
    </header>

    <form
        id="post-form"
        method="POST"
        enctype="multipart/form-data"
        use:enhance={handleEnhance}
        class="form-grid"
    >
        {#if !isLoggedIn}
            <div class="row two">
                <div class="field">
                    <label class="label" for="nickname">
                        <span>닉네임</span>
                        <span class="hint">선택</span>
                    </label>
                    <input
                        type="text"
                        id="nickname"
                        name="nickname"
                        class="text-input"
                        placeholder="익명"
                        maxlength="50"
                        bind:value={nickname}
                    />
                </div>

                <div class="field">
                    <label class="label" for="password">
                        <span>비밀번호 <em>*</em></span>
                        <span class="hint">수정/삭제 시 필요</span>
                    </label>
                    <input
                        type="password"
                        id="password"
                        name="password"
                        class="text-input"
                        class:error={errors.password}
                        placeholder="4자 이상"
                        minlength="4"
                        maxlength="50"
                        required
                        bind:value={password}
                    />
                    {#if errors.password}<p class="err-msg" role="alert">{errors.password}</p>{/if}
                </div>
            </div>
        {/if}

        <div class="row two">
            <div class="field">
                <label class="label" for="category">
                    <span>카테고리</span>
                    <span class="hint">선택</span>
                </label>
                <select id="category" name="category" class="select" bind:value={category}>
                    <option value="">— 미선택 —</option>
                    <option value="free">자유</option>
                    <option value="race_review">대회 후기</option>
                    <option value="injury">부상/재활</option>
                    <option value="gear">장비</option>
                    <option value="training">훈련</option>
                    <option value="question">질문</option>
                </select>
            </div>

            <div class="field">
                <label class="label" for="title">
                    <span>제목 <em>*</em></span>
                    <span class="hint">{title.length} / 100</span>
                </label>
                <input
                    type="text"
                    id="title"
                    name="title"
                    class="text-input"
                    class:error={errors.title}
                    placeholder="제목을 입력하세요"
                    maxlength="100"
                    required
                    bind:value={title}
                />
                {#if errors.title}<p class="err-msg" role="alert">{errors.title}</p>{/if}
            </div>
        </div>

        <div class="field">
            <div class="label">
                <span>내용 <em>*</em></span>
                <span class="hint">최대 10,000자</span>
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
            {#if errors.content}<p class="err-msg" role="alert">{errors.content}</p>{/if}
        </div>

        <div class="field">
            <RaceTagSelector races={data.races} bind:selectedIds={selectedRaceIds} />
            {#if errors.race_ids}<p class="err-msg" role="alert">{errors.race_ids}</p>{/if}
        </div>

        {#each selectedRaceIds as raceId}
            <input type="hidden" name="race_ids" value={raceId} />
        {/each}

        {#if errors.post}
            <div class="error-box" role="alert">{errors.post}</div>
        {/if}

        <div class="submit-row">
            <a href="/posts" class="btn ghost">취소</a>
            <button type="submit" class="btn primary" disabled={isSubmitting}>
                {isSubmitting ? '등록 중...' : '등록하기 →'}
            </button>
        </div>
    </form>
</div>

<style>
    .form-wrap {
        max-width: 760px;
        margin: 0 auto;
        padding: 32px 24px 60px;
    }
    @media (min-width: 1024px) {
        .form-wrap {
            padding: 40px 32px 80px;
        }
    }

    .page-head {
        margin-bottom: 28px;
        padding-bottom: 18px;
        border-bottom: 1px solid var(--arena-line);
    }
    .back-link {
        display: inline-block;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        text-decoration: none;
        margin-bottom: 14px;
    }
    .back-link:hover {
        color: var(--arena-ink);
    }
    .kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .page-title {
        font-family: var(--arena-f-display);
        font-size: clamp(24px, 3.5vw, 32px);
        font-weight: 700;
        letter-spacing: -0.5px;
        margin: 0;
        color: var(--arena-ink);
    }

    .form-grid {
        display: flex;
        flex-direction: column;
        gap: 24px;
    }
    .row.two {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
    }
    @media (max-width: 640px) {
        .row.two {
            grid-template-columns: 1fr;
        }
    }
    .field {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .label {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
    }
    .label em {
        font-style: normal;
        color: var(--arena-urgent);
        margin-left: 2px;
    }
    .hint {
        color: var(--arena-ink-mute);
        font-size: 10px;
        letter-spacing: 1px;
    }

    .text-input,
    .select {
        width: 100%;
        border: 1px solid var(--arena-line);
        border-radius: 0;
        background: var(--arena-paper);
        padding: 10px 12px;
        font-family: var(--arena-f-body);
        font-size: 14px;
        color: var(--arena-ink);
        line-height: 1.4;
        appearance: none;
        -webkit-appearance: none;
        -moz-appearance: none;
    }
    .select {
        background-image: linear-gradient(45deg, transparent 50%, var(--arena-ink) 50%),
            linear-gradient(135deg, var(--arena-ink) 50%, transparent 50%);
        background-position: calc(100% - 16px) 50%, calc(100% - 11px) 50%;
        background-size: 5px 5px, 5px 5px;
        background-repeat: no-repeat;
        padding-right: 32px;
    }
    .text-input:focus,
    .select:focus {
        outline: none;
        border-color: var(--arena-ink);
        background-color: var(--arena-paper-alt);
    }
    .text-input::placeholder {
        color: var(--arena-ink-mute);
    }
    .text-input.error {
        border-color: var(--arena-urgent);
    }

    .editor-wrap {
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
    }
    .editor-skeleton {
        min-height: 240px;
        background: var(--arena-paper-alt);
        border: 1px solid var(--arena-line);
    }

    .err-msg {
        margin: 0;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-urgent);
        letter-spacing: 0.5px;
    }
    .error-box {
        border: 1px solid var(--arena-urgent);
        background: color-mix(in oklch, var(--arena-urgent), transparent 92%);
        color: var(--arena-urgent);
        padding: 10px 14px;
        font-family: var(--arena-f-mono);
        font-size: 12px;
    }

    .submit-row {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        margin-top: 8px;
        padding-top: 20px;
        border-top: 1px solid var(--arena-line-soft);
    }
    .btn {
        border: 1px solid var(--arena-ink);
        padding: 10px 18px;
        font-family: var(--arena-f-mono);
        font-size: 12px;
        letter-spacing: 1px;
        text-transform: uppercase;
        cursor: pointer;
        text-decoration: none;
        line-height: 1.4;
        display: inline-flex;
        align-items: center;
    }
    .btn.primary {
        background: var(--arena-ink);
        color: var(--arena-paper);
    }
    .btn.primary:hover:not(:disabled) {
        background: var(--arena-ink-soft);
    }
    .btn.primary:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }
    .btn.ghost {
        background: var(--arena-paper);
        color: var(--arena-ink);
        border-color: var(--arena-line);
    }
    .btn.ghost:hover {
        border-color: var(--arena-ink);
    }
</style>
