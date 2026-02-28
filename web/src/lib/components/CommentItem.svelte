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

<div class="group/comment py-4 px-2 rounded-lg transition-colors {isReply ? 'ml-6 sm:ml-10 border-l-2 border-base-200 pl-4 bg-base-200/20 mt-2' : 'border-b border-base-200 last:border-0'}">
    <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
            <span class="text-sm font-semibold">{comment.nickname}</span>
            <span class="text-[10px] sm:text-xs text-base-content/40">{comment.createdAtFormatted}</span>
        </div>
        <div class="flex items-center gap-1 opacity-60 sm:opacity-0 group-hover/comment:opacity-100 transition-opacity">
            <button
                class="btn btn-ghost btn-xs h-7 min-h-[1.75rem] px-2 text-base-content/60 hover:text-primary"
                onclick={() => { showEditForm = true; }}
            >
                수정
            </button>
            <button
                class="btn btn-ghost btn-xs h-7 min-h-[1.75rem] px-2 text-base-content/60 hover:text-error"
                onclick={() => { showDeleteModal = true; }}
            >
                삭제
            </button>
        </div>
    </div>

    {#if showEditForm}
        <div class="space-y-3 bg-base-100 p-3 rounded-lg border border-base-300 shadow-sm mb-3">
            <textarea
                class="textarea textarea-bordered w-full h-24 text-sm resize-none focus:textarea-primary"
                class:textarea-error={errors.content}
                bind:value={editContent}
                maxlength="1000"
                placeholder="수정할 내용을 입력하세요..."
            ></textarea>
            <div class="flex items-center gap-2">
                {#if !isOwner}
                    <input
                        type="password"
                        class="input input-bordered input-sm w-36"
                        class:input-error={errors.password}
                        placeholder="비밀번호"
                        bind:value={password}
                    />
                {/if}
                <div class="flex-1"></div>
                <button class="btn btn-ghost btn-sm" onclick={cancelEdit}>취소</button>
                <button class="btn btn-primary btn-sm" onclick={handleEdit} disabled={isSubmitting}>
                    {#if isSubmitting}
                        <span class="loading loading-spinner loading-xs"></span>
                    {/if}
                    수정 완료
                </button>
            </div>
            {#if errors.content}
                <p class="text-xs text-error mt-1">{errors.content}</p>
            {/if}
            {#if errors.password}
                <p class="text-xs text-error mt-1">{errors.password}</p>
            {/if}
        </div>
    {:else}
        <div class="pr-2">
            <p class="text-sm text-base-content/80 leading-relaxed whitespace-pre-wrap">{comment.content}</p>
            
            <div class="mt-3 flex items-center gap-4">
                {#if !isReply}
                    <button
                        class="text-[11px] font-medium text-base-content/50 hover:text-primary flex items-center gap-1 transition-colors"
                        onclick={() => { showReplyForm = !showReplyForm; }}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" /></svg>
                        답글 달기
                    </button>
                {/if}
            </div>
        </div>
    {/if}

    {#if showReplyForm}
        <div class="mt-4 ml-10 p-4 bg-base-200/30 rounded-xl border border-base-300/50">
            <div class="flex items-center gap-2 mb-3">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-base-content/40" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" /></svg>
                <span class="text-xs font-medium text-base-content/60">답글 작성</span>
            </div>
            <CommentForm
                {postId}
                parentId={comment.id}
                onCancel={cancelReply}
                placeholder="{comment.nickname}님에게 답글 남기기..."
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
            {#if !isOwner}
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
            {/if}
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
