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
        const text = post.content.replace(/\n/g, ' ').trim();
        return text.length > 150 ? text.substring(0, 150) + '...' : text;
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
</script>

<div
    class="bg-base-100 border border-base-300 rounded-lg hover:border-primary/40 hover:shadow-sm transition-all duration-200 cursor-pointer group p-4"
    onclick={handleClick}
    onkeypress={(e) => e.key === 'Enter' && handleClick()}
    role="button"
    tabindex="0"
>
    <div class="flex gap-4">
        <div class="flex-1 min-w-0">
            {#if isHot || isNew}
                <div class="flex items-center gap-1.5 mb-1.5">
                    {#if isHot}
                        <span class="badge badge-error badge-sm font-semibold">인기</span>
                    {/if}
                    {#if isNew}
                        <span class="badge badge-success badge-sm font-semibold">NEW</span>
                    {/if}
                </div>
            {/if}

            <h2 class="font-semibold text-base leading-snug mb-2">
                <span class="group-hover:text-primary transition-colors line-clamp-1">
                    {post.title}
                </span>
            </h2>

            {#if showExcerpt && excerpt()}
                <p class="text-sm text-base-content/70 mb-3 line-clamp-2">
                    {excerpt()}
                </p>
            {/if}

            {#if post.taggedRaces && post.taggedRaces.length > 0}
                <div class="mb-2">
                    <RaceTagBadges races={post.taggedRaces} />
                </div>
            {/if}
        </div>

        {#if thumbnail}
            <div class="shrink-0 w-20 h-20 rounded-lg overflow-hidden border border-base-300">
                <img src={thumbnail} alt={post.title} class="w-full h-full object-cover" loading="lazy" />
            </div>
        {/if}
    </div>

    <div class="flex items-center justify-between text-sm text-base-content/50 pt-2 border-t border-base-200">
        <div class="flex items-center gap-2">
            <span class="font-medium text-base-content/70">{post.nickname}</span>
            <span class="text-base-content/30">|</span>
            <span>{post.createdAtFormatted}</span>
        </div>
        <div class="flex items-center gap-3">
            <div class="flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <span>{post.viewCount}</span>
            </div>
            <div class="flex items-center gap-1 text-error/50">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                </svg>
                <span>{post.likeCount}</span>
            </div>
            <div class="flex items-center gap-1 text-info/50">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <span>{post.commentCount}</span>
            </div>
        </div>
    </div>
</div>

<style>
    .line-clamp-1 {
        display: -webkit-box;
        -webkit-line-clamp: 1;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .line-clamp-2 {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
</style>
