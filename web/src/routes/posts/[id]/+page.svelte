<script lang="ts" module>
    declare const Kakao: any;
</script>

<script lang="ts">
    import { page } from '$app/stores';
    import { goto } from '$app/navigation';
    import RaceTagBadges from '$lib/components/RaceTagBadges.svelte';
    import CommentList from '$lib/components/CommentList.svelte';
    import { clientApiFetch, isApiError } from '$lib/api.client';
    import { formatPostContent } from '$lib/utils';
    import RaceCard from '$lib/components/RaceCard.svelte';
    import { formatDistanceToNow } from '$lib/date';
    import type { Post, LikeToggleResponse, PostList, VerifyPasswordResponse, PostDeleteResponse, ApiErrors } from '$lib/types';

    let { data } = $props();

    let post = $derived(data.post as Post);
    let prevPost = $derived(data.prevPost as { id: number; title: string } | null);
    let nextPost = $derived(data.nextPost as { id: number; title: string } | null);
    let sidebar = $derived(data.sidebar as { popularPosts: PostList[]; upcomingRaces: any[] });

    let appUrl = $derived(data.appUrl || 'https://www.endurohub.kr');
    const pageUrl = $derived(`${appUrl}${$page.url.pathname}`);
    let isOwner = $derived(!!post.isOwner);

    const categoryLabels: Record<string, { label: string; badge: string }> = {
        race_review: { label: '대회 후기', badge: 'badge-primary' },
        injury: { label: '부상/재활', badge: 'badge-error' },
        gear: { label: '장비 추천', badge: 'badge-warning' },
        training: { label: '훈련 팁', badge: 'badge-success' },
        question: { label: '질문', badge: 'badge-info' },
        free: { label: '자유', badge: 'badge-ghost' },
    };
    const categoryInfo = $derived(post.category ? categoryLabels[post.category] : null);

    let showDeleteModal = $state(false);
    let showEditModal = $state(false);
    let showShareModal = $state(false);
    let password = $state('');
    let errors = $state<Record<string, string>>({});
    let isSubmitting = $state(false);

    let hasLiked = $state(false);
    let likeCount = $state(0);
    $effect(() => { hasLiked = data.hasLiked; likeCount = data.post.likeCount; });
    let isLiking = $state(false);

    let showImageModal = $state(false);
    let currentImageIndex = $state(0);

    const contentText = $derived(post.contentText || '');

    let articleSchema = $derived({
        '@context': 'https://schema.org',
        '@type': 'Article',
        'headline': post.title,
        'author': { '@type': 'Person', 'name': post.nickname },
        'datePublished': post.createdAt,
        'dateModified': post.updatedAt,
        'articleBody': contentText.substring(0, 500),
        'image': post.imageSrcs && post.imageSrcs.length > 0 ? post.imageSrcs[0] : undefined,
        'publisher': { '@type': 'Organization', 'name': 'EnduroHub', 'url': appUrl },
        'mainEntityOfPage': pageUrl,
    });

    let breadcrumbSchema = $derived({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            { '@type': 'ListItem', 'position': 1, 'name': '홈', 'item': appUrl },
            { '@type': 'ListItem', 'position': 2, 'name': '자유게시판', 'item': `${appUrl}/posts` },
            { '@type': 'ListItem', 'position': 3, 'name': post.title, 'item': pageUrl },
        ],
    });

    function openImageModal(index: number) { currentImageIndex = index; showImageModal = true; }
    function closeImageModal() { showImageModal = false; }
    function nextImage() { if (post.imageSrcs && currentImageIndex < post.imageSrcs.length - 1) currentImageIndex++; }
    function prevImage() { if (currentImageIndex > 0) currentImageIndex--; }

    $effect(() => {
        const savedPassword = localStorage.getItem('postPassword');
        if (savedPassword) password = savedPassword;
    });

    async function handleEdit() {
        if (isSubmitting) return;
        isSubmitting = true;
        errors = {};

        try {
            const result = await clientApiFetch<VerifyPasswordResponse | ApiErrors>(
                `/posts/${post.id}/verify-password/`,
                { method: 'POST', body: { password: password } }
            );

            if (isApiError(result)) {
                errors = Object.fromEntries(
                    Object.entries(result.errors).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v])
                );
            } else {
                const verified = result as VerifyPasswordResponse;
                goto(`/posts/${post.id}/edit?token=${verified.editToken}`);
            }
        } catch {
            errors = { password: '오류가 발생했습니다.' };
        } finally {
            isSubmitting = false;
        }
    }

    async function handleDelete() {
        if (isSubmitting) return;
        isSubmitting = true;
        errors = {};

        try {
            const result = await clientApiFetch<PostDeleteResponse | ApiErrors>(
                `/posts/${post.id}/`,
                { method: 'DELETE', body: { password: password } }
            );

            if (isApiError(result)) {
                errors = Object.fromEntries(
                    Object.entries(result.errors).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v])
                );
            } else {
                goto('/posts');
            }
        } catch {
            errors = { password: '오류가 발생했습니다.' };
        } finally {
            isSubmitting = false;
        }
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Escape') {
            showDeleteModal = false;
            showEditModal = false;
            showShareModal = false;
            showImageModal = false;
        }
        if (showImageModal) {
            if (e.key === 'ArrowRight') nextImage();
            if (e.key === 'ArrowLeft') prevImage();
        }
    }

    function showToast(message: string) {
        const toast = document.createElement('div');
        toast.className = 'toast toast-top toast-center z-50';
        toast.innerHTML = `<div class="alert" style="background:#1e293b;color:#fff;border:none;">${message}</div>`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2500);
    }

    function copyLink() {
        navigator.clipboard.writeText(window.location.href).then(() => showToast('링크가 복사되었습니다.'));
    }

    function shareKakao() {
        if (typeof Kakao !== 'undefined' && Kakao.isInitialized()) {
            Kakao.Share.sendDefault({
                objectType: 'feed',
                content: {
                    title: post.title,
                    description: contentText.substring(0, 100),
                    imageUrl: post.imageSrcs && post.imageSrcs.length > 0 ? post.imageSrcs[0] : '',
                    link: { webUrl: window.location.href, mobileWebUrl: window.location.href },
                },
            });
        } else {
            showToast('카카오 공유 기능을 사용할 수 없습니다.');
        }
    }

    async function handleLike() {
        if (isLiking) return;
        isLiking = true;
        try {
            const result = await clientApiFetch<LikeToggleResponse>(`/posts/${post.id}/like/`, { method: 'POST' });
            if (result.success) {
                hasLiked = result.liked;
                likeCount = result.likeCount;
            }
        } catch (error) {
            console.error('Like error:', error);
        } finally {
            isLiking = false;
        }
    }
</script>

<svelte:window onkeydown={handleKeydown} />

<svelte:head>
    <title>{post.title} - 엔듀로허브</title>
    <meta name="description" content={contentText.substring(0, 160)} />
    <meta property="og:type" content="article" />
    <meta property="og:title" content={post.title} />
    <meta property="og:description" content={contentText.substring(0, 160)} />
    {#if post.imageSrcs && post.imageSrcs.length > 0}
        <meta property="og:image" content={post.imageSrcs[0]} />
    {/if}
    <meta property="article:published_time" content={post.createdAt} />
    <meta property="article:modified_time" content={post.updatedAt} />
    {@html `<script type="application/ld+json">${JSON.stringify(articleSchema)}</script>`}
    {@html `<script type="application/ld+json">${JSON.stringify(breadcrumbSchema)}</script>`}
</svelte:head>

<div class="container mx-auto px-4 py-8 max-w-7xl">
    <div class="breadcrumbs text-sm mb-6 opacity-60">
        <ul>
            <li><a href="/" class="hover:text-primary transition-colors">홈</a></li>
            <li><a href="/posts" class="hover:text-primary transition-colors">자유게시판</a></li>
            <li class="font-medium text-base-content">{post.title}</li>
        </ul>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <!-- Sticky Like Sidebar (Lg+) -->
        <aside class="hidden lg:block lg:col-span-1 sticky top-24 pt-4">
            <div class="flex flex-col items-center gap-6">
                <button 
                    class="group flex flex-col items-center gap-2" 
                    onclick={handleLike} 
                    disabled={isLiking}
                    aria-label="추천하기"
                >
                    <div class="w-12 h-12 rounded-full border-2 flex items-center justify-center transition-all duration-300 {hasLiked ? 'bg-primary border-primary text-primary-content shadow-lg shadow-primary/20 scale-110' : 'bg-base-100 border-base-200 text-base-content/40 hover:border-primary hover:text-primary hover:scale-105'}">
                        {#if isLiking}
                            <span class="loading loading-spinner loading-xs"></span>
                        {:else}
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill={hasLiked ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" /></svg>
                        {/if}
                    </div>
                    <span class="text-sm font-bold {hasLiked ? 'text-primary' : 'text-base-content/40 group-hover:text-primary'}">{likeCount}</span>
                </button>
                
                <button 
                    class="w-12 h-12 rounded-full border-2 bg-base-100 border-base-200 text-base-content/40 flex items-center justify-center hover:border-primary hover:text-primary transition-all hover:scale-105" 
                    onclick={() => { showShareModal = true; }}
                    aria-label="공유하기"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" /></svg>
                </button>
            </div>
        </aside>

        <!-- Main Content -->
        <main class="lg:col-span-8 flex flex-col gap-8">
            <article class="card bg-base-100 shadow-xl border border-base-200 overflow-hidden">
                <div class="card-body p-6 sm:p-10">
                    <!-- Category & Tags -->
                    <div class="flex items-center gap-2 mb-4">
                        {#if categoryInfo}
                            <span class="badge {categoryInfo.badge} badge-sm">{categoryInfo.label}</span>
                        {/if}
                        {#if post.taggedRaces && post.taggedRaces.length > 0}
                            <RaceTagBadges races={post.taggedRaces} />
                        {/if}
                    </div>

                    <h1 class="card-title text-2xl sm:text-3xl font-black mb-6 leading-tight text-base-content">{post.title}</h1>

                    <!-- Author Block -->
                    <div class="flex items-center justify-between mb-8 pb-6 border-b border-base-200">
                        <div class="flex items-center gap-3">
                            <div class="flex flex-col">
                                <span class="font-bold text-sm lg:text-base text-base-content">{post.nickname}</span>
                                <div class="flex items-center gap-2 text-xs lg:text-sm text-base-content/40">
                                    <time datetime={post.createdAt}>{formatDistanceToNow(post.createdAt)}</time>
                                    <span class="w-1 h-1 rounded-full bg-base-content/20"></span>
                                    <div class="flex items-center gap-1">
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                                        <span>{post.viewCount}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="dropdown dropdown-end">
                            <button tabindex="0" class="btn btn-ghost btn-sm btn-circle" aria-label="게시글 관리">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" /></svg>
                            </button>
                            <ul tabindex="0" role="menu" class="dropdown-content menu bg-base-100 rounded-box z-10 w-40 p-2 shadow-xl border border-base-200">
                                <li><button onclick={() => { if (isOwner) { handleEdit(); } else { showEditModal = true; } }} class="gap-2 text-sm">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                                    수정
                                </button></li>
                                <li><button onclick={() => { showDeleteModal = true; }} class="gap-2 text-sm text-error">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                    삭제
                                </button></li>
                            </ul>
                        </div>
                    </div>

                    <!-- Content -->
                    <div class="prose max-w-none text-base sm:text-lg leading-relaxed text-base-content/90 mb-10 min-h-32">{@html formatPostContent(post.content)}</div>

                    {#if post.imageSrcs && post.imageSrcs.length > 0}
                        <div class="mt-8 pt-8 border-t border-base-200">
                            <h3 class="text-sm lg:text-base font-bold text-base-content/50 mb-4 flex items-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 lg:h-5 lg:w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                첨부 이미지 ({post.imageSrcs.length})
                            </h3>
                            <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                                {#each post.imageSrcs as src, index}
                                    <button 
                                        onclick={() => openImageModal(index)} 
                                        class="aspect-square relative group overflow-hidden rounded-xl border border-base-200 transition-all hover:border-primary"
                                        aria-label="이미지 {index + 1} 확대 보기"
                                    >
                                        <img {src} alt="게시글 이미지 {index + 1}" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" loading="lazy" />
                                        <div class="absolute inset-0 bg-primary/0 group-hover:bg-primary/5 transition-colors"></div>
                                    </button>
                                {/each}
                            </div>
                        </div>
                    {/if}

                    <!-- Mobile Like/Share Buttons -->
                    <div class="flex lg:hidden justify-center gap-4 mt-10 pt-10 border-t border-base-200">
                        <button class="btn {hasLiked ? 'btn-primary' : 'btn-outline'} btn-lg flex-1 gap-2" onclick={handleLike} disabled={isLiking}>
                            {#if isLiking}
                                <span class="loading loading-spinner loading-sm"></span>
                            {:else}
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill={hasLiked ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" /></svg>
                            {/if}
                            {likeCount}
                        </button>
                        <button class="btn btn-outline btn-lg gap-2" onclick={() => { showShareModal = true; }} aria-label="게시글 공유">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" /></svg>
                            공유
                        </button>
                    </div>
                </div>

                <!-- Post Navigation -->
                <div class="bg-base-200/50 border-t border-base-200">
                    <div class="grid grid-cols-2 divide-x divide-base-200">
                        {#if prevPost}
                            <a href="/posts/{prevPost.id}" class="flex flex-col gap-1 p-4 sm:p-6 hover:bg-base-200 transition-colors">
                                <span class="text-[10px] lg:text-xs font-bold text-primary flex items-center gap-1 uppercase tracking-wider">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M15 19l-7-7 7-7" /></svg>
                                    이전 글
                                </span>
                                <span class="text-sm lg:text-base font-medium text-base-content line-clamp-1">{prevPost.title}</span>
                            </a>
                        {:else}
                            <div class="p-4 sm:p-6 opacity-30 cursor-not-allowed">
                                <span class="text-[10px] lg:text-xs font-bold text-base-content/50 uppercase tracking-wider flex items-center gap-1">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M15 19l-7-7 7-7" /></svg>
                                    이전 글 없음
                                </span>
                            </div>
                        {/if}

                        {#if nextPost}
                            <a href="/posts/{nextPost.id}" class="flex flex-col gap-1 p-4 sm:p-6 text-right hover:bg-base-200 transition-colors">
                                <span class="text-[10px] lg:text-xs font-bold text-primary flex items-center justify-end gap-1 uppercase tracking-wider">
                                    다음 글
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M9 5l7 7-7 7" /></svg>
                                </span>
                                <span class="text-sm lg:text-base font-medium text-base-content line-clamp-1">{nextPost.title}</span>
                            </a>
                        {:else}
                            <div class="p-4 sm:p-6 text-right opacity-30 cursor-not-allowed">
                                <span class="text-[10px] lg:text-xs font-bold text-base-content/50 uppercase tracking-wider flex items-center justify-end gap-1">
                                    다음 글 없음
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M9 5l7 7-7 7" /></svg>
                                </span>
                            </div>
                        {/if}
                    </div>
                </div>
            </article>

            <!-- Back to List -->
            <div class="flex justify-center">
                <a href="/posts" class="btn btn-ghost gap-2 text-base-content/50 hover:text-primary transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" /></svg>
                    전체 목록으로 돌아가기
                </a>
            </div>

            <!-- Comment Area -->
            <div id="comments" class="bg-base-100 rounded-2xl shadow-lg border border-base-200 p-6 sm:p-10">
                <CommentList comments={post.comments || []} postId={post.id} commentCount={post.commentCount} />
            </div>
        </main>

        <!-- Sidebar -->
        <aside class="lg:col-span-3 flex flex-col gap-8">
            <!-- Popular Posts -->
            {#if sidebar.popularPosts && sidebar.popularPosts.length > 0}
                <section class="card bg-base-100 border border-base-200 shadow-sm overflow-hidden">
                    <div class="card-body p-5">
                        <h3 class="font-black text-sm lg:text-base uppercase tracking-tight mb-4 flex items-center gap-2">
                            <span class="w-1.5 h-1.5 rounded-full bg-error animate-pulse"></span>
                            실시간 인기 게시글
                        </h3>
                        <div class="flex flex-col gap-1">
                            {#each sidebar.popularPosts as p, i}
                                <a href="/posts/{p.id}" class="group flex items-start gap-3 p-2 rounded-lg hover:bg-base-200 transition-all">
                                    <span class="font-black text-primary/30 text-lg italic">{i + 1}</span>
                                    <div class="flex flex-col">
                                        <span class="text-[13px] lg:text-sm font-semibold text-base-content group-hover:text-primary transition-colors line-clamp-2 leading-snug">{p.title}</span>
                                        <div class="flex items-center gap-2 mt-1 opacity-40 text-[10px] lg:text-xs">
                                            <span>{p.nickname}</span>
                                            <span>·</span>
                                            <div class="flex items-center gap-0.5">
                                                <svg xmlns="http://www.w3.org/2000/svg" class="h-2.5 w-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" /></svg>
                                                <span>{p.likeCount}</span>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            {/each}
                        </div>
                    </div>
                </section>
            {/if}

            <!-- Upcoming Races -->
            {#if sidebar.upcomingRaces && sidebar.upcomingRaces.length > 0}
                <div class="flex flex-col gap-4">
                    <h3 class="font-black text-sm lg:text-base uppercase tracking-tight flex items-center gap-2 px-1">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 lg:h-5 lg:w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                        추천 대회 일정
                    </h3>
                    <div class="flex flex-col gap-3">
                        {#each sidebar.upcomingRaces as race}
                            <RaceCard {race} variant="minimal" />
                        {/each}
                    </div>
                    <a href="/calendar" class="btn btn-outline btn-sm btn-block border-base-300 font-bold">전체 일정 보기</a>
                </div>
            {/if}
        </aside>
    </div>
</div>

{#if showEditModal}
    <div class="modal modal-open">
        <div class="modal-box max-w-sm">
            <h3 class="font-bold text-lg mb-4">글 수정</h3>
            <div class="form-control">
                <label class="label" for="edit-password"><span class="label-text">비밀번호</span></label>
                <input type="password" id="edit-password" class="input input-bordered" class:input-error={errors.password} placeholder="글 작성 시 입력한 비밀번호" bind:value={password} />
                {#if errors.password}<div class="label"><span class="label-text-alt text-error">{errors.password}</span></div>{/if}
            </div>
            <div class="modal-action">
                <button class="btn btn-ghost" onclick={() => { showEditModal = false; errors = {}; }}>취소</button>
                <button class="btn btn-primary" onclick={handleEdit} disabled={isSubmitting}>
                    {#if isSubmitting}<span class="loading loading-spinner loading-sm"></span>{/if}
                    수정하기
                </button>
            </div>
        </div>
        <button class="modal-backdrop" onclick={() => { showEditModal = false; errors = {}; }} aria-label="닫기"></button>
    </div>
{/if}

{#if showDeleteModal}
    <div class="modal modal-open">
        <div class="modal-box max-w-sm">
            <h3 class="font-bold text-lg mb-4">글 삭제</h3>
            <p class="text-base-content/70 mb-4">정말 이 글을 삭제하시겠습니까? 삭제된 글은 복구할 수 없습니다.</p>
            {#if !isOwner}
                <div class="form-control">
                    <label class="label" for="delete-password"><span class="label-text">비밀번호</span></label>
                    <input type="password" id="delete-password" class="input input-bordered" class:input-error={errors.password} placeholder="글 작성 시 입력한 비밀번호" bind:value={password} />
                    {#if errors.password}<div class="label"><span class="label-text-alt text-error">{errors.password}</span></div>{/if}
                </div>
            {/if}
            <div class="modal-action">
                <button class="btn btn-ghost" onclick={() => { showDeleteModal = false; errors = {}; }}>취소</button>
                <button class="btn btn-error" onclick={handleDelete} disabled={isSubmitting}>
                    {#if isSubmitting}<span class="loading loading-spinner loading-sm"></span>{/if}
                    삭제하기
                </button>
            </div>
        </div>
        <button class="modal-backdrop" onclick={() => { showDeleteModal = false; errors = {}; }} aria-label="닫기"></button>
    </div>
{/if}

{#if showImageModal && post.imageSrcs && post.imageSrcs.length > 0}
    <div class="modal modal-open" role="dialog" aria-modal="true" aria-label="이미지 확대 보기">
        <div class="modal-box max-w-4xl p-2 relative">
            <button onclick={closeImageModal} class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2 z-10" aria-label="닫기">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
            <img src={post.imageSrcs[currentImageIndex]} alt="첨부 이미지 {currentImageIndex + 1}" class="w-full rounded-lg" />
            {#if post.imageSrcs.length > 1}
                <div class="absolute inset-y-0 left-0 flex items-center">
                    <button onclick={prevImage} disabled={currentImageIndex === 0} class="btn btn-circle btn-sm ml-2 {currentImageIndex === 0 ? 'btn-disabled' : ''}" aria-label="이전 이미지">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
                    </button>
                </div>
                <div class="absolute inset-y-0 right-0 flex items-center">
                    <button onclick={nextImage} disabled={currentImageIndex === post.imageSrcs.length - 1} class="btn btn-circle btn-sm mr-2 {currentImageIndex === post.imageSrcs.length - 1 ? 'btn-disabled' : ''}" aria-label="다음 이미지">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
                    </button>
                </div>
                <div class="text-center mt-2 text-sm text-base-content/60">{currentImageIndex + 1} / {post.imageSrcs.length}</div>
            {/if}
        </div>
        <button class="modal-backdrop" onclick={closeImageModal} aria-label="닫기"></button>
    </div>
{/if}

{#if showShareModal}
    <div class="modal modal-open" role="dialog" aria-modal="true" aria-label="공유하기">
        <div class="modal-box max-w-sm relative">
            <button onclick={() => { showShareModal = false; }} class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2" aria-label="닫기">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
            <h3 class="font-bold text-lg mb-4">공유하기</h3>
            <div class="flex flex-col gap-3">
                <button onclick={() => { shareKakao(); showShareModal = false; }} class="btn btn-block justify-start gap-3 bg-[#FEE500] hover:bg-[#FDD835] text-[#191919] border-none">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" viewBox="0 0 24 24" fill="#191919"><path d="M12 3C6.48 3 2 6.48 2 10.5c0 2.55 1.7 4.8 4.25 6.08-.13.47-.85 3.02-.88 3.24 0 0-.02.17.08.24.1.07.22.03.22.03.3-.04 3.44-2.27 3.98-2.66.77.1 1.56.17 2.35.17 5.52 0 10-3.48 10-7.78C22 6.48 17.52 3 12 3z"/></svg>
                    카카오톡으로 공유
                </button>
                <button onclick={() => { copyLink(); showShareModal = false; }} class="btn btn-block justify-start gap-3">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                    링크 복사
                </button>
            </div>
        </div>
        <button class="modal-backdrop" onclick={() => { showShareModal = false; }} aria-label="닫기"></button>
    </div>
{/if}
