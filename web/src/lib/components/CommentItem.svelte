<script lang="ts">
    import { invalidateAll } from '$app/navigation';
    import { clientApiFetch } from '$lib/api.client';
    import type { PostComment } from '$lib/types';
    import CommentForm from './CommentForm.svelte';
    import CommentItem from './CommentItem.svelte';

    let { comment, postId, isReply = false }: {
        comment: PostComment;
        postId: number;
        isReply?: boolean;
    } = $props();

    let isOwner = $derived(!!comment.isOwner);

    let showReplyForm = $state(false);
    let showEditForm = $state(false);
    let showDeleteModal = $state(false);
    let editContent = $state('');
    $effect(() => {
        editContent = comment.content;
    });
    let password = $state('');
    let isSubmitting = $state(false);
    let errors = $state<Record<string, string>>({});

    $effect(() => {
        const savedPassword = localStorage.getItem('commentPassword');
        if (savedPassword) password = savedPassword;
    });

    async function handleEdit() {
        if (isSubmitting) return;
        isSubmitting = true;
        errors = {};

        try {
            const result = await clientApiFetch<{ success: boolean } | { errors: Record<string, string[]> }>(
                `/posts/${postId}/comments/${comment.id}/`,
                {
                    method: 'PUT',
                    body: { content: editContent, password: isOwner ? '' : password },
                }
            );

            if ('errors' in result) {
                for (const [key, msgs] of Object.entries(result.errors)) {
                    errors[key] = Array.isArray(msgs) ? msgs[0] : msgs;
                }
            } else {
                showEditForm = false;
                await invalidateAll();
            }
        } catch {
            errors = { content: '수정 중 오류가 발생했습니다.' };
        } finally {
            isSubmitting = false;
        }
    }

    async function handleDelete() {
        if (isSubmitting) return;
        isSubmitting = true;
        errors = {};

        try {
            const result = await clientApiFetch<{ success: boolean } | { errors: Record<string, string[]> }>(
                `/posts/${postId}/comments/${comment.id}/`,
                {
                    method: 'DELETE',
                    body: { password: isOwner ? '' : password },
                }
            );

            if ('errors' in result) {
                for (const [key, msgs] of Object.entries(result.errors)) {
                    errors[key] = Array.isArray(msgs) ? msgs[0] : msgs;
                }
            } else {
                showDeleteModal = false;
                await invalidateAll();
            }
        } catch {
            errors = { password: '삭제 중 오류가 발생했습니다.' };
        } finally {
            isSubmitting = false;
        }
    }

    function cancelReply() {
        showReplyForm = false;
    }

    function cancelEdit() {
        showEditForm = false;
        editContent = comment.content;
        errors = {};
    }
</script>

<article class="comment" class:reply={isReply}>
    <header class="head">
        <div class="ident">
            <span class="nickname">{comment.nickname}</span>
            <span class="dot">·</span>
            <span class="date">{comment.createdAtFormatted}</span>
        </div>
        <div class="actions">
            <button type="button" class="action-btn" onclick={() => { showEditForm = true; }}>수정</button>
            <button type="button" class="action-btn danger" onclick={() => { showDeleteModal = true; }}>삭제</button>
        </div>
    </header>

    {#if showEditForm}
        <div class="edit-wrap">
            <textarea
                class="edit-textarea"
                class:error={errors.content}
                bind:value={editContent}
                maxlength="1000"
                placeholder="수정할 내용을 입력하세요"
            ></textarea>
            <div class="edit-actions">
                {#if !isOwner}
                    <input
                        type="password"
                        class="pw-input"
                        class:error={errors.password}
                        placeholder="비밀번호"
                        bind:value={password}
                    />
                {/if}
                <div class="spacer"></div>
                <button type="button" class="btn ghost" onclick={cancelEdit}>취소</button>
                <button type="button" class="btn primary" onclick={handleEdit} disabled={isSubmitting}>
                    {isSubmitting ? '...' : '수정 완료'}
                </button>
            </div>
            {#if errors.content}<p class="err-msg">{errors.content}</p>{/if}
            {#if errors.password}<p class="err-msg">{errors.password}</p>{/if}
        </div>
    {:else}
        <p class="content">{comment.content}</p>

        {#if !isReply}
            <div class="footer">
                <button type="button" class="reply-btn" onclick={() => { showReplyForm = !showReplyForm; }}>
                    답글 달기
                </button>
            </div>
        {/if}
    {/if}

    {#if showReplyForm}
        <div class="reply-wrap">
            <CommentForm
                {postId}
                parentId={comment.id}
                onCancel={cancelReply}
                placeholder="{comment.nickname}님에게 답글 남기기..."
            />
        </div>
    {/if}

    {#if comment.replies && comment.replies.length > 0}
        <div class="replies">
            {#each comment.replies as reply (reply.id)}
                <CommentItem comment={reply} {postId} isReply={true} />
            {/each}
        </div>
    {/if}
</article>

{#if showDeleteModal}
    <div class="modal-overlay" role="dialog" aria-modal="true" aria-label="댓글 삭제">
        <div class="modal-card">
            <header class="modal-head">
                <span class="kicker">DELETE · 댓글 삭제</span>
                <h3 class="modal-title">정말 삭제할까요?</h3>
            </header>
            <p class="modal-desc">삭제된 댓글은 복구할 수 없습니다.</p>
            {#if !isOwner}
                <input
                    type="password"
                    class="pw-input"
                    class:error={errors.password}
                    placeholder="비밀번호"
                    bind:value={password}
                />
                {#if errors.password}<p class="err-msg">{errors.password}</p>{/if}
            {/if}
            <div class="modal-actions">
                <button type="button" class="btn ghost" onclick={() => { showDeleteModal = false; errors = {}; }}>취소</button>
                <button type="button" class="btn danger" onclick={handleDelete} disabled={isSubmitting}>
                    {isSubmitting ? '...' : '삭제'}
                </button>
            </div>
        </div>
        <button class="modal-backdrop" onclick={() => { showDeleteModal = false; errors = {}; }} aria-label="닫기"></button>
    </div>
{/if}

<style>
    .comment {
        padding: 14px 4px;
        border-bottom: 1px solid var(--arena-line-soft);
        font-family: var(--arena-f-body);
    }
    .comment:last-child {
        border-bottom: none;
    }
    .comment.reply {
        margin-top: 4px;
        padding-left: 16px;
        border-left: 2px solid var(--arena-line-soft);
        background: var(--arena-paper-alt);
    }

    .head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        margin-bottom: 6px;
    }
    .ident {
        display: flex;
        align-items: center;
        gap: 8px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
    }
    .nickname {
        color: var(--arena-ink);
        font-weight: 700;
        font-family: var(--arena-f-body);
        font-size: 13px;
    }
    .dot {
        opacity: 0.4;
    }
    .date {
        letter-spacing: 0.5px;
    }
    .actions {
        display: flex;
        gap: 4px;
    }
    .action-btn {
        background: transparent;
        border: none;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1px;
        color: var(--arena-ink-mute);
        cursor: pointer;
        text-transform: uppercase;
        padding: 2px 6px;
    }
    .action-btn:hover {
        color: var(--arena-ink);
    }
    .action-btn.danger:hover {
        color: var(--arena-urgent);
    }

    .content {
        font-size: 14px;
        line-height: 1.6;
        color: var(--arena-ink);
        margin: 0;
        white-space: pre-wrap;
    }

    .footer {
        margin-top: 8px;
    }
    .reply-btn {
        background: transparent;
        border: none;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: var(--arena-ink-mute);
        cursor: pointer;
        padding: 0;
    }
    .reply-btn:hover {
        color: var(--arena-ink);
    }

    .reply-wrap {
        margin-top: 12px;
        margin-left: 16px;
        padding: 12px;
        border: 1px solid var(--arena-line-soft);
        background: var(--arena-paper);
    }
    .replies {
        margin-top: 8px;
    }

    .edit-wrap {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-top: 4px;
    }
    .edit-textarea {
        width: 100%;
        min-height: 80px;
        resize: vertical;
        border: 1px solid var(--arena-line);
        border-radius: 0;
        background: var(--arena-paper);
        padding: 8px 10px;
        font-family: var(--arena-f-body);
        font-size: 13px;
        line-height: 1.55;
        color: var(--arena-ink);
        appearance: none;
        -webkit-appearance: none;
    }
    .edit-textarea:focus {
        outline: none;
        border-color: var(--arena-ink);
    }
    .edit-textarea.error,
    .pw-input.error {
        border-color: var(--arena-urgent);
    }
    .edit-actions {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .spacer {
        flex: 1;
    }
    .pw-input {
        width: 140px;
        border: 1px solid var(--arena-line);
        border-radius: 0;
        background: var(--arena-paper);
        padding: 7px 10px;
        font-family: var(--arena-f-body);
        font-size: 13px;
        appearance: none;
        -webkit-appearance: none;
    }
    .pw-input:focus {
        outline: none;
        border-color: var(--arena-ink);
    }

    .btn {
        border: 1px solid var(--arena-ink);
        padding: 6px 12px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1px;
        text-transform: uppercase;
        cursor: pointer;
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
    .btn.danger {
        background: var(--arena-urgent);
        color: var(--arena-paper);
        border-color: var(--arena-urgent);
    }
    .btn.danger:hover:not(:disabled) {
        opacity: 0.9;
    }

    .err-msg {
        margin: 0;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-urgent);
    }

    /* Modal */
    .modal-overlay {
        position: fixed;
        inset: 0;
        z-index: 100;
        display: grid;
        place-items: center;
        background: color-mix(in oklch, var(--arena-ink), transparent 50%);
    }
    .modal-card {
        position: relative;
        z-index: 1;
        background: var(--arena-paper);
        border: 1px solid var(--arena-ink);
        box-shadow: 6px 6px 0 var(--arena-ink);
        padding: 22px;
        max-width: 360px;
        width: calc(100% - 32px);
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    .modal-head .kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
        display: block;
        margin-bottom: 4px;
    }
    .modal-title {
        font-family: var(--arena-f-display);
        font-size: 18px;
        font-weight: 700;
        margin: 0;
        color: var(--arena-ink);
    }
    .modal-desc {
        margin: 0;
        font-size: 13px;
        color: var(--arena-ink-soft);
    }
    .modal-actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        margin-top: 4px;
    }
    .modal-backdrop {
        position: absolute;
        inset: 0;
        background: transparent;
        border: none;
        cursor: pointer;
    }
</style>
