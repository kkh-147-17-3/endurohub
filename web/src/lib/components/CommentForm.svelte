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
        if (savedNickname) {
            nickname = savedNickname;
        }
        if (savedPassword) {
            password = savedPassword;
        }
    });

    async function handleSubmit(e: Event) {
        e.preventDefault();
        if (isSubmitting) return;

        isSubmitting = true;
        errors = {};

        if (nickname) {
            localStorage.setItem('nickname', nickname);
        }
        if (password) {
            localStorage.setItem('commentPassword', password);
        }

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
                const apiErrors = result.errors;
                for (const [key, msgs] of Object.entries(apiErrors)) {
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

<form onsubmit={handleSubmit} class="space-y-3">
    {#if !isLoggedIn}
        <div class="flex flex-wrap gap-2">
            <div class="flex-1 min-w-[140px]">
                <input
                    type="text"
                    class="input input-bordered input-sm w-full"
                    placeholder="닉네임 (익명)"
                    maxlength="50"
                    bind:value={nickname}
                />
            </div>
            <div class="flex-1 min-w-[140px]">
                <input
                    type="password"
                    class="input input-bordered input-sm w-full"
                    class:input-error={errors.password}
                    placeholder="비밀번호 (수정/삭제용)"
                    minlength="4"
                    maxlength="50"
                    required
                    bind:value={password}
                />
            </div>
        </div>
    {/if}

    <div class="relative">
        <textarea
            class="textarea textarea-bordered w-full h-28 text-sm focus:textarea-primary resize-none p-3"
            class:textarea-error={errors.content}
            {placeholder}
            maxlength="1000"
            required
            bind:value={content}
        ></textarea>
        
        <div class="absolute bottom-3 right-3 flex items-center gap-3">
            <span class="text-[10px] text-base-content/30">{content.length}/1000</span>
            <button type="submit" class="btn btn-primary btn-sm h-8 min-h-[2rem] px-4" disabled={isSubmitting || !content.trim()}>
                {#if isSubmitting}
                    <span class="loading loading-spinner loading-xs"></span>
                {/if}
                {parentId ? '답글 남기기' : '댓글 등록'}
            </button>
        </div>
    </div>

    {#if onCancel}
        <div class="flex justify-start">
            <button type="button" class="btn btn-ghost btn-xs text-base-content/50 hover:text-base-content" onclick={onCancel}>
                작성 취소
            </button>
        </div>
    {/if}

    {#if errors.content || errors.password || errors.comment}
        <div class="mt-2 p-2 bg-error/10 rounded border border-error/20">
            {#if errors.content}<p class="text-[11px] text-error">{errors.content}</p>{/if}
            {#if errors.password}<p class="text-[11px] text-error">{errors.password}</p>{/if}
            {#if errors.comment}<p class="text-[11px] text-error">{errors.comment}</p>{/if}
        </div>
    {/if}
</form>
