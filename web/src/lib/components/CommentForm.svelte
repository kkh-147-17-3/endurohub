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
        <div class="flex gap-3">
            <input
                type="text"
                class="input input-bordered input-sm w-32"
                placeholder="닉네임"
                maxlength="50"
                bind:value={nickname}
            />
            <input
                type="password"
                class="input input-bordered input-sm w-32"
                class:input-error={errors.password}
                placeholder="비밀번호"
                minlength="4"
                maxlength="50"
                required
                bind:value={password}
            />
        </div>
    {/if}

    <textarea
        class="textarea textarea-bordered w-full h-24"
        class:textarea-error={errors.content}
        {placeholder}
        maxlength="1000"
        required
        bind:value={content}
    ></textarea>

    {#if errors.content}
        <p class="text-sm text-error">{errors.content}</p>
    {/if}
    {#if errors.password}
        <p class="text-sm text-error">{errors.password}</p>
    {/if}
    {#if errors.comment}
        <p class="text-sm text-error">{errors.comment}</p>
    {/if}

    <div class="flex justify-end gap-2">
        {#if onCancel}
            <button type="button" class="btn btn-ghost btn-sm" onclick={onCancel}>
                취소
            </button>
        {/if}
        <button type="submit" class="btn btn-primary btn-sm" disabled={isSubmitting}>
            {#if isSubmitting}
                <span class="loading loading-spinner loading-xs"></span>
            {/if}
            {parentId ? '답글 등록' : '댓글 등록'}
        </button>
    </div>
</form>
