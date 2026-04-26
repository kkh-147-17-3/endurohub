<script lang="ts">
    import { goto } from '$app/navigation';
    import type { Post } from '$lib/types';
    import RaceTagBadges from './RaceTagBadges.svelte';

    let { post, showExcerpt = false }: { post: Post; showExcerpt?: boolean } = $props();

    function handleClick() {
        goto(`/posts/${post.id}`);
    }

    const excerpt = $derived(() => {
        if (!post.content) return '';
        const text = post.content.replace(/<[^>]*>/g, '').replace(/\n/g, ' ').trim();
        return text.length > 140 ? text.substring(0, 140) + '…' : text;
    });

    const isNew = $derived.by(() => {
        if (!post.createdAt) return false;
        const created = new Date(post.createdAt);
        const now = new Date();
        const daysDiff = (now.getTime() - created.getTime()) / (1000 * 60 * 60 * 24);
        return daysDiff <= 3;
    });

    const isHot = $derived(post.likeCount >= 5 || post.commentCount >= 5);
    const thumbnail = $derived(post.imageSrcs?.[0] || null);

    const categoryLabels: Record<string, string> = {
        race_review: '대회 후기',
        injury: '부상 / 재활',
        gear: '장비',
        training: '훈련',
        question: '질문',
        free: '자유',
    };
    const categoryLabel = $derived(post.category ? categoryLabels[post.category] : null);
</script>

<div
    class="arena-post-card"
    onclick={handleClick}
    onkeypress={(e) => e.key === 'Enter' && handleClick()}
    role="button"
    tabindex="0"
>
    <div class="head">
        <div class="head-left">
            {#if categoryLabel}
                <span class="kicker">{categoryLabel}</span>
            {/if}
            {#if isHot}
                <span class="kicker urgent">HOT</span>
            {/if}
            {#if isNew}
                <span class="kicker accent">NEW</span>
            {/if}
        </div>
        <span class="kicker date">{post.createdAtFormatted}</span>
    </div>

    <div class="body">
        <div class="text-col">
            <h2 class="title">{post.title}</h2>
            {#if showExcerpt}
                <p class="excerpt">{excerpt() || ' '}</p>
            {/if}
            {#if post.taggedRaces && post.taggedRaces.length > 0}
                <RaceTagBadges races={post.taggedRaces} />
            {/if}
        </div>
        {#if thumbnail}
            <div class="thumb">
                <img src={thumbnail} alt={post.title} loading="lazy" />
            </div>
        {/if}
    </div>

    <div class="foot">
        <span class="author">{post.nickname}</span>
        <span class="dot">·</span>
        <span class="meta">조회 {post.viewCount}</span>
        <span class="dot">·</span>
        <span class="meta">추천 {post.likeCount}</span>
        <span class="dot">·</span>
        <span class="meta">댓글 {post.commentCount}</span>
    </div>
</div>

<style>
    .arena-post-card {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 16px 20px;
        background: var(--arena-paper);
        border: 1px solid var(--arena-line);
        cursor: pointer;
        transition: transform 0.15s, box-shadow 0.15s;
    }
    .arena-post-card:hover {
        transform: translate(-2px, -2px);
        box-shadow: 4px 4px 0 var(--arena-ink);
    }
    .arena-post-card:focus-visible {
        outline: 2px solid var(--arena-accent);
        outline-offset: 2px;
    }

    .head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
    }
    .head-left {
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;
    }
    .kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: var(--arena-ink-soft);
        padding: 2px 6px;
        border: 1px solid var(--arena-line-soft);
        line-height: 1.4;
    }
    .kicker.urgent {
        color: var(--arena-paper);
        background: var(--arena-urgent);
        border-color: var(--arena-urgent);
    }
    .kicker.accent {
        color: var(--arena-ink);
        background: var(--arena-accent);
        border-color: var(--arena-accent);
    }
    .kicker.date {
        border: none;
        padding: 0;
        letter-spacing: 1px;
    }

    .body {
        display: flex;
        gap: 16px;
        align-items: flex-start;
    }
    .text-col {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .title {
        font-family: var(--arena-f-body);
        font-weight: 700;
        font-size: 17px;
        letter-spacing: -0.3px;
        line-height: 1.35;
        color: var(--arena-ink);
        margin: 0;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .excerpt {
        font-size: 13px;
        line-height: 1.55;
        color: var(--arena-ink-soft);
        margin: 0;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        min-height: 2.4em;
    }
    .thumb {
        flex-shrink: 0;
        width: 84px;
        height: 84px;
        border: 1px solid var(--arena-line-soft);
        overflow: hidden;
    }
    .thumb img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .foot {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
        padding-top: 10px;
        border-top: 1px solid var(--arena-line-soft);
        letter-spacing: 0.3px;
    }
    .author {
        color: var(--arena-ink);
        font-weight: 600;
    }
    .dot {
        opacity: 0.4;
    }

    @media (max-width: 640px) {
        .arena-post-card {
            padding: 14px 16px;
        }
        .thumb {
            width: 72px;
            height: 72px;
        }
        .title {
            font-size: 15px;
        }
    }
</style>
