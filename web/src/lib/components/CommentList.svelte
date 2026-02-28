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
        <CommentForm {postId} placeholder="따뜻한 댓글은 작성자에게 큰 힘이 됩니다." />
    </div>

    <!-- 댓글 목록 -->
    {#if comments && comments.length > 0}
        <div class="flex flex-col">
            {#each comments as comment (comment.id)}
                <CommentItem {comment} {postId} />
            {/each}
        </div>
    {:else}
        <div class="flex flex-col items-center justify-center py-16 px-4 bg-base-200/10 rounded-2xl border border-dashed border-base-300">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-base-content/20 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
            <p class="text-sm text-base-content/40">아직 댓글이 없습니다. 첫 번째 댓글을 작성해보세요!</p>
        </div>
    {/if}
</div>
