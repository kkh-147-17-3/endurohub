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

<div class="space-y-4">
    <h3 class="font-semibold text-lg">
        댓글 <span class="text-base-content/60 font-normal">{commentCount}개</span>
    </h3>

    <!-- 댓글 목록 -->
    {#if comments && comments.length > 0}
        <div class="divide-y divide-base-200">
            {#each comments as comment (comment.id)}
                <CommentItem {comment} {postId} />
            {/each}
        </div>
    {:else}
        <p class="text-center text-base-content/60 py-8">아직 댓글이 없습니다. 첫 번째 댓글을 작성해보세요!</p>
    {/if}

    <!-- 댓글 작성 폼 -->
    <div class="bg-base-200/50 rounded-lg p-4">
        <CommentForm {postId} />
    </div>
</div>
