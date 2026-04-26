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

<section class="comment-section">
    <header class="comment-head">
        <span class="kicker">COMMENTS · {commentCount}</span>
        <h3 class="title">댓글</h3>
    </header>

    <div class="form-wrap">
        <CommentForm {postId} placeholder="댓글을 작성하세요" />
    </div>

    {#if comments && comments.length > 0}
        <div class="comment-list">
            {#each comments as comment (comment.id)}
                <CommentItem {comment} {postId} />
            {/each}
        </div>
    {:else}
        <div class="empty">
            <span class="kicker-muted">NO COMMENTS</span>
            <p>아직 댓글이 없습니다.</p>
        </div>
    {/if}
</section>

<style>
    .comment-section {
        display: flex;
        flex-direction: column;
        gap: 0;
    }
    .comment-head {
        padding-bottom: 12px;
        border-bottom: 1px solid var(--arena-line);
        margin-bottom: 16px;
    }
    .kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: var(--arena-ink-soft);
        display: block;
        margin-bottom: 4px;
    }
    .title {
        font-family: var(--arena-f-display);
        font-size: 22px;
        font-weight: 700;
        letter-spacing: -0.4px;
        color: var(--arena-ink);
        margin: 0;
    }
    .form-wrap {
        border: 1px solid var(--arena-line-soft);
        background: var(--arena-paper-alt);
        padding: 14px;
        margin-bottom: 24px;
    }
    .comment-list {
        display: flex;
        flex-direction: column;
        border-top: 1px solid var(--arena-line-soft);
    }
    .empty {
        padding: 32px 16px;
        text-align: center;
        font-family: var(--arena-f-body);
        color: var(--arena-ink-soft);
        border: 1px solid var(--arena-line-soft);
        display: flex;
        flex-direction: column;
        gap: 6px;
        align-items: center;
    }
    .kicker-muted {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        color: var(--arena-ink-mute);
    }
    .empty p {
        margin: 0;
        font-size: 13px;
    }
</style>
