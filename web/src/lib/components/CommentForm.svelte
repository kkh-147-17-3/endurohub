<script lang="ts">
    import { invalidateAll } from '$app/navigation';
    import { page } from '$app/stores';
    import { clientApiFetch } from '$lib/api.client';
    import type { CommentCreateResponse } from '$lib/types';

    let {
        postId,
        parentId = null,
        onCancel = null,
        placeholder = '댓글을 입력하세요...'
    }: {
        postId: number;
        parentId?: number | null;
        onCancel?: (() => void) | null;
        placeholder?: string;
    } = $props();

    let isLoggedIn = $derived(!!$page.data.user);

    let nickname = $state('');
    let content = $state('');
    let password = $state('');
    let isSubmitting = $state(false);
    let errors = $state<Record<string, string>>({});

    $effect(() => {
        const savedNickname = localStorage.getItem('nickname');
        const savedPassword = localStorage.getItem('commentPassword');
        if (savedNickname) nickname = savedNickname;
        if (savedPassword) password = savedPassword;
    });

    async function handleSubmit(e: Event) {
        e.preventDefault();
        if (isSubmitting) return;

        isSubmitting = true;
        errors = {};

        if (nickname) localStorage.setItem('nickname', nickname);
        if (password) localStorage.setItem('commentPassword', password);

        try {
            const result = await clientApiFetch<CommentCreateResponse | { errors: Record<string, string[]> }>(
                `/posts/${postId}/comments/`,
                {
                    method: 'POST',
                    body: {
                        parent_id: parentId,
                        nickname: nickname || null,
                        content,
                        password,
                    },
                }
            );

            if ('errors' in result) {
                for (const [key, msgs] of Object.entries(result.errors)) {
                    errors[key] = Array.isArray(msgs) ? msgs[0] : msgs;
                }
            } else {
                content = '';
                if (onCancel) onCancel();
                await invalidateAll();
            }
        } catch {
            errors = { comment: '댓글 등록 중 오류가 발생했습니다.' };
        } finally {
            isSubmitting = false;
        }
    }
</script>

<form onsubmit={handleSubmit} class="comment-form">
    {#if !isLoggedIn}
        <div class="meta-row">
            <input
                type="text"
                class="text-input"
                placeholder="닉네임 (익명)"
                maxlength="50"
                bind:value={nickname}
            />
            <input
                type="password"
                class="text-input"
                class:error={errors.password}
                placeholder="비밀번호 (수정/삭제용)"
                minlength="4"
                maxlength="50"
                required
                bind:value={password}
            />
        </div>
    {/if}

    <textarea
        class="textarea"
        class:error={errors.content}
        {placeholder}
        maxlength="1000"
        required
        bind:value={content}
    ></textarea>

    <div class="action-row">
        <span class="counter">{content.length} / 1000</span>
        <div class="action-buttons">
            {#if onCancel}
                <button type="button" class="btn ghost" onclick={onCancel}>취소</button>
            {/if}
            <button type="submit" class="btn primary" disabled={isSubmitting || !content.trim()}>
                {isSubmitting ? '...' : parentId ? '답글 등록' : '댓글 등록'}
            </button>
        </div>
    </div>

    {#if errors.content || errors.password || errors.comment}
        <div class="error-box">
            {#if errors.content}<p>{errors.content}</p>{/if}
            {#if errors.password}<p>{errors.password}</p>{/if}
            {#if errors.comment}<p>{errors.comment}</p>{/if}
        </div>
    {/if}
</form>

<style>
    .comment-form {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .meta-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }
    .text-input {
        flex: 1;
        min-width: 140px;
        border: 1px solid var(--arena-line);
        border-radius: 0;
        background: var(--arena-paper);
        padding: 8px 12px;
        font-family: var(--arena-f-body);
        font-size: 13px;
        color: var(--arena-ink);
        appearance: none;
        -webkit-appearance: none;
    }
    .text-input:focus {
        outline: none;
        border-color: var(--arena-ink);
    }
    .text-input::placeholder {
        color: var(--arena-ink-mute);
    }
    .text-input.error,
    .textarea.error {
        border-color: var(--arena-urgent);
    }

    .textarea {
        width: 100%;
        min-height: 96px;
        resize: vertical;
        border: 1px solid var(--arena-line);
        border-radius: 0;
        background: var(--arena-paper);
        padding: 10px 12px;
        font-family: var(--arena-f-body);
        font-size: 14px;
        line-height: 1.55;
        color: var(--arena-ink);
        appearance: none;
        -webkit-appearance: none;
    }
    .textarea:focus {
        outline: none;
        border-color: var(--arena-ink);
    }
    .textarea::placeholder {
        color: var(--arena-ink-mute);
    }

    .action-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
    }
    .counter {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        color: var(--arena-ink-mute);
        letter-spacing: 1px;
    }
    .action-buttons {
        display: flex;
        gap: 8px;
    }
    .btn {
        border: 1px solid var(--arena-ink);
        padding: 7px 14px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1px;
        text-transform: uppercase;
        cursor: pointer;
        line-height: 1.4;
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

    .error-box {
        border: 1px solid var(--arena-urgent);
        background: color-mix(in oklch, var(--arena-urgent), transparent 90%);
        padding: 8px 12px;
    }
    .error-box p {
        margin: 0;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-urgent);
    }
</style>
