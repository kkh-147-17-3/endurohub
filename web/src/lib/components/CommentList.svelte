<script lang="ts">
    import type { PostComment } from '$lib/types';
    import CommentForm from './CommentForm.svelte';
    import CommentItem from './CommentItem.svelte';

    let { comments, postId, commentCount = 0 }: {
        comments: PostComment[];
        postId: number;
        commentCount?: number;
    } = $props();
</script>

<div class="space-y-6">
    <div class="flex items-center gap-2 mb-6">
        <h3 class="font-black text-xl text-base-content">댓글</h3>
        <span class="badge badge-neutral badge-sm font-bold">{commentCount}</span>
    </div>

    <!-- 댓글 작성 폼 (상단) -->
    <div class="bg-base-200/30 rounded-2xl p-4 sm:p-6 border border-base-300/50 mb-8">
        <CommentForm {postId} placeholder="댓글을 작성하세요" />
    </div>

    <!-- 댓글 목록 -->
    {#if comments && comments.length > 0}
        <div class="flex flex-col">
            {#each comments as comment (comment.id)}
                <CommentItem {comment} {postId} />
            {/each}
        </div>
    {:else}
        <div class="py-8 text-center">
            <p class="text-sm text-base-content/50">아직 댓글이 없습니다</p>
        </div>
    {/if}
</div>
