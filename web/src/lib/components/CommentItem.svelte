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

    let showReplyForm = $state(false);
    let showEditForm = $state(false);
    let showDeleteModal = $state(false);
    let editContent = $state('');
    $effect(() => { editContent = comment.content; });
    let password = $state('');
    let isSubmitting = $state(false);
    let errors = $state<Record<string, string>>({});

    $effect(() => {
        const savedPassword = localStorage.getItem('commentPassword');
        if (savedPassword) {
            password = savedPassword;
        }
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
                    body: { content: editContent, password },
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
                    body: { password },
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

<div class="py-3 {isReply ? 'ml-8 border-l-2 border-base-200 pl-4' : ''}">
    <div class="flex items-center justify-between mb-2">
        <div class="flex items-center gap-2 text-sm">
            <span class="font-medium">{comment.nickname}</span>
            <span class="text-base-content/50">{comment.createdAtFormatted}</span>
        </div>
        <div class="flex items-center gap-1">
            {#if !isReply}
                <button
                    class="btn btn-ghost btn-xs"
                    onclick={() => { showReplyForm = !showReplyForm; }}
                >
                    답글
                </button>
            {/if}
            <button
                class="btn btn-ghost btn-xs"
                onclick={() => { showEditForm = true; }}
            >
                수정
            </button>
            <button
                class="btn btn-ghost btn-xs text-error"
                onclick={() => { showDeleteModal = true; }}
            >
                삭제
            </button>
        </div>
    </div>

    {#if showEditForm}
        <div class="space-y-2">
            <textarea
                class="textarea textarea-bordered w-full h-20"
                class:textarea-error={errors.content}
                bind:value={editContent}
                maxlength="1000"
            ></textarea>
            <div class="flex items-center gap-2">
                <input
                    type="password"
                    class="input input-bordered input-sm w-32"
                    class:input-error={errors.password}
                    placeholder="비밀번호"
                    bind:value={password}
                />
                <div class="flex-1"></div>
                <button class="btn btn-ghost btn-sm" onclick={cancelEdit}>취소</button>
                <button class="btn btn-primary btn-sm" onclick={handleEdit} disabled={isSubmitting}>
                    {#if isSubmitting}
                        <span class="loading loading-spinner loading-xs"></span>
                    {/if}
                    수정
                </button>
            </div>
            {#if errors.content}
                <p class="text-sm text-error">{errors.content}</p>
            {/if}
            {#if errors.password}
                <p class="text-sm text-error">{errors.password}</p>
            {/if}
        </div>
    {:else}
        <p class="text-sm whitespace-pre-wrap">{comment.content}</p>
    {/if}

    {#if showReplyForm}
        <div class="mt-3">
            <CommentForm
                {postId}
                parentId={comment.id}
                onCancel={cancelReply}
                placeholder="답글을 입력하세요..."
            />
        </div>
    {/if}

    {#if comment.replies && comment.replies.length > 0}
        <div class="mt-2">
            {#each comment.replies as reply (reply.id)}
                <CommentItem comment={reply} {postId} isReply={true} />
            {/each}
        </div>
    {/if}
</div>

{#if showDeleteModal}
    <div class="modal modal-open">
        <div class="modal-box max-w-sm">
            <h3 class="font-bold text-lg mb-4">댓글 삭제</h3>
            <p class="text-base-content/70 mb-4">정말 이 댓글을 삭제하시겠습니까?</p>
            <div class="form-control">
                <input
                    type="password"
                    class="input input-bordered"
                    class:input-error={errors.password}
                    placeholder="비밀번호"
                    bind:value={password}
                />
                {#if errors.password}
                    <div class="label">
                        <span class="label-text-alt text-error">{errors.password}</span>
                    </div>
                {/if}
            </div>
            <div class="modal-action">
                <button class="btn btn-ghost" onclick={() => { showDeleteModal = false; errors = {}; }}>취소</button>
                <button class="btn btn-error" onclick={handleDelete} disabled={isSubmitting}>
                    {#if isSubmitting}
                        <span class="loading loading-spinner loading-sm"></span>
                    {/if}
                    삭제
                </button>
            </div>
        </div>
        <button class="modal-backdrop" onclick={() => { showDeleteModal = false; errors = {}; }} aria-label="닫기"></button>
    </div>
{/if}
