<script lang="ts" module>
    declare const Kakao: any;
</script>

<script lang="ts">
    import { page } from '$app/stores';
    import RaceTagBadges from '$lib/components/RaceTagBadges.svelte';
    import CommentList from '$lib/components/CommentList.svelte';
    import { clientApiFetch } from '$lib/api.client';
    import type { Post, LikeToggleResponse } from '$lib/types';

    let { data } = $props();

    let post = $derived(data.post as Post);
    let appUrl = $derived(data.appUrl || 'https://www.endurohub.kr');
    const pageUrl = $derived(`${appUrl}${$page.url.pathname}`);

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

    let articleSchema = $derived({
        '@context': 'https://schema.org',
        '@type': 'Article',
        'headline': post.title,
        'author': { '@type': 'Person', 'name': post.nickname },
        'datePublished': post.createdAt,
        'dateModified': post.updatedAt,
        'articleBody': post.content.substring(0, 500),
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

        const formData = new FormData();
        formData.set('password', password);

        const response = await fetch(`?/verifyEdit`, { method: 'POST', body: formData });
        const result = await response.json();

        if (result.type === 'failure') {
            errors = Object.fromEntries(Object.entries(result.data?.errors || {}).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v]));
            isSubmitting = false;
        }
        // If redirect, the browser will follow it automatically
        isSubmitting = false;
    }

    async function handleDelete() {
        if (isSubmitting) return;
        isSubmitting = true;
        errors = {};

        const formData = new FormData();
        formData.set('password', password);

        const response = await fetch(`?/delete`, { method: 'POST', body: formData });
        const result = await response.json();

        if (result.type === 'failure') {
            errors = Object.fromEntries(Object.entries(result.data?.errors || {}).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v]));
        }
        isSubmitting = false;
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
                    description: post.content.substring(0, 100),
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
    <meta name="description" content={post.content.substring(0, 160)} />
    <meta property="og:type" content="article" />
    <meta property="og:title" content={post.title} />
    <meta property="og:description" content={post.content.substring(0, 160)} />
    {#if post.imageSrcs && post.imageSrcs.length > 0}
        <meta property="og:image" content={post.imageSrcs[0]} />
    {/if}
    <meta property="article:published_time" content={post.createdAt} />
    <meta property="article:modified_time" content={post.updatedAt} />
    {@html `<script type="application/ld+json">${JSON.stringify(articleSchema)}</script>`}
    {@html `<script type="application/ld+json">${JSON.stringify(breadcrumbSchema)}</script>`}
</svelte:head>

<div class="container mx-auto px-4 py-8">
    <div class="breadcrumbs text-sm mb-6">
        <ul>
            <li><a href="/">홈</a></li>
            <li><a href="/posts">자유게시판</a></li>
            <li>{post.title}</li>
        </ul>
    </div>

    <div class="max-w-3xl mx-auto">
        <article class="card bg-base-100 shadow-xl">
            <div class="card-body">
                <h1 class="card-title text-2xl mb-2">{post.title}</h1>

                {#if post.taggedRaces && post.taggedRaces.length > 0}
                    <div class="mb-4"><RaceTagBadges races={post.taggedRaces} /></div>
                {/if}

                <div class="flex items-center justify-between text-sm text-base-content/60 mb-6 pb-4 border-b border-base-200">
                    <div class="flex items-center gap-4">
                        <span>{post.nickname}</span>
                        <span>{post.createdAtFormatted}</span>
                        <div class="flex items-center gap-1">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                            <span>{post.viewCount}</span>
                        </div>
                    </div>
                    <div class="dropdown dropdown-end">
                        <button tabindex="0" class="btn btn-ghost btn-sm btn-circle" aria-label="더보기">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" /></svg>
                        </button>
                        <ul tabindex="0" role="menu" class="dropdown-content menu bg-base-100 rounded-box z-10 w-40 p-2 shadow-lg border border-base-300">
                            <li><button onclick={() => { showEditModal = true; }} class="gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                                수정
                            </button></li>
                            <li><button onclick={() => { showDeleteModal = true; }} class="gap-2 text-error">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                삭제
                            </button></li>
                        </ul>
                    </div>
                </div>

                <div class="prose max-w-none min-h-32">{@html post.content.replace(/\n/g, '<br>')}</div>

                {#if post.imageSrcs && post.imageSrcs.length > 0}
                    <div class="mt-6 pt-6 border-t border-base-200">
                        <h3 class="text-sm font-medium text-base-content/70 mb-3">첨부 이미지</h3>
                        <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
                            {#each post.imageSrcs as src, index}
                                <button onclick={() => openImageModal(index)} class="cursor-pointer group">
                                    <img {src} alt="첨부 이미지 {index + 1}" class="w-full h-32 object-cover rounded-lg border border-base-300 group-hover:opacity-90 group-hover:border-primary transition-all" loading="lazy" />
                                </button>
                            {/each}
                        </div>
                    </div>
                {/if}

                <div class="flex justify-center gap-3 mt-8 pt-4 border-t border-base-200">
                    <button class="btn {hasLiked ? 'btn-primary' : 'btn-outline'} gap-2" onclick={handleLike} disabled={isLiking}>
                        {#if isLiking}
                            <span class="loading loading-spinner loading-sm"></span>
                        {:else}
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill={hasLiked ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" /></svg>
                        {/if}
                        추천 {likeCount}
                    </button>
                    <button class="btn btn-outline gap-2" onclick={() => { showShareModal = true; }}>
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" /></svg>
                        공유
                    </button>
                </div>

                <div class="card-actions justify-start mt-4 pt-4 border-t border-base-200">
                    <a href="/posts" class="btn btn-ghost btn-sm">← 목록으로</a>
                </div>
            </div>
        </article>

        <div class="mt-8">
            <CommentList comments={post.comments || []} postId={post.id} commentCount={post.commentCount} />
        </div>
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
            <div class="form-control">
                <label class="label" for="delete-password"><span class="label-text">비밀번호</span></label>
                <input type="password" id="delete-password" class="input input-bordered" class:input-error={errors.password} placeholder="글 작성 시 입력한 비밀번호" bind:value={password} />
                {#if errors.password}<div class="label"><span class="label-text-alt text-error">{errors.password}</span></div>{/if}
            </div>
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
