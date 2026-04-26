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
    import { formatDistanceToNow } from '$lib/date';
    import type { Post, LikeToggleResponse, VerifyPasswordResponse, PostDeleteResponse, ApiErrors } from '$lib/types';

    let { data } = $props();

    let post = $derived(data.post as Post);
    let prevPost = $derived(data.prevPost as { id: number; title: string } | null);
    let nextPost = $derived(data.nextPost as { id: number; title: string } | null);

    let appUrl = $derived(data.appUrl || 'https://www.endurohub.kr');
    const pageUrl = $derived(`${appUrl}${$page.url.pathname}`);
    let isOwner = $derived(!!post.isOwner);

    const categoryLabels: Record<string, string> = {
        race_review: '대회 후기',
        injury: '부상/재활',
        gear: '장비',
        training: '훈련',
        question: '질문',
        free: '자유',
    };
    const categoryLabel = $derived(post.category ? categoryLabels[post.category] : null);

    let showDeleteModal = $state(false);
    let showEditModal = $state(false);
    let showShareModal = $state(false);
    let showImageModal = $state(false);
    let currentImageIndex = $state(0);
    let password = $state('');
    let errors = $state<Record<string, string>>({});
    let isSubmitting = $state(false);

    let menuOpen = $state(false);

    let hasLiked = $state(false);
    let likeCount = $state(0);
    $effect(() => {
        hasLiked = data.hasLiked;
        likeCount = data.post.likeCount;
    });
    let isLiking = $state(false);

    const contentText = $derived(post.contentText || '');

    let articleSchema = $derived({
        '@context': 'https://schema.org',
        '@type': 'Article',
        headline: post.title,
        author: { '@type': 'Person', name: post.nickname },
        datePublished: post.createdAt,
        dateModified: post.updatedAt,
        articleBody: contentText.substring(0, 500),
        image: post.imageSrcs && post.imageSrcs.length > 0 ? post.imageSrcs[0] : undefined,
        publisher: { '@type': 'Organization', name: 'EnduroHub', url: appUrl },
        mainEntityOfPage: pageUrl,
    });

    let breadcrumbSchema = $derived({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        itemListElement: [
            { '@type': 'ListItem', position: 1, name: '홈', item: appUrl },
            { '@type': 'ListItem', position: 2, name: '커뮤니티', item: `${appUrl}/posts` },
            { '@type': 'ListItem', position: 3, name: post.title, item: pageUrl },
        ],
    });

    function openImageModal(index: number) {
        currentImageIndex = index;
        showImageModal = true;
    }
    function closeImageModal() {
        showImageModal = false;
    }
    function nextImage() {
        if (post.imageSrcs && currentImageIndex < post.imageSrcs.length - 1) currentImageIndex++;
    }
    function prevImage() {
        if (currentImageIndex > 0) currentImageIndex--;
    }

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
            const result = await clientApiFetch<PostDeleteResponse | ApiErrors>(`/posts/${post.id}/`, {
                method: 'DELETE',
                body: { password: password },
            });

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
            menuOpen = false;
        }
        if (showImageModal) {
            if (e.key === 'ArrowRight') nextImage();
            if (e.key === 'ArrowLeft') prevImage();
        }
    }

    function showToast(message: string) {
        const toast = document.createElement('div');
        toast.style.cssText =
            'position:fixed;top:24px;left:50%;transform:translateX(-50%);background:var(--arena-ink);color:var(--arena-paper);padding:10px 18px;font-family:var(--arena-f-mono);font-size:12px;letter-spacing:1px;z-index:200;border:1px solid var(--arena-ink);box-shadow:4px 4px 0 var(--arena-ink-soft);';
        toast.textContent = message;
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
            const result = await clientApiFetch<LikeToggleResponse>(`/posts/${post.id}/like/`, {
                method: 'POST',
            });
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

<div class="post-wrap">
    <nav class="crumbs">
        <a href="/">홈</a>
        <span class="sep">/</span>
        <a href="/posts">커뮤니티</a>
        <span class="sep">/</span>
        <span class="cur">{post.title}</span>
    </nav>

    <article class="article">
        <header class="article-head">
            <div class="kicker-row">
                <span class="kicker">POST · {categoryLabel ?? '자유'}</span>
                <div class="menu-wrap">
                    <button
                        type="button"
                        class="menu-btn"
                        aria-label="게시글 관리"
                        onclick={() => (menuOpen = !menuOpen)}
                    >
                        ⋯
                    </button>
                    {#if menuOpen}
                        <button class="menu-backdrop" onclick={() => (menuOpen = false)} aria-label="닫기"></button>
                        <ul class="menu" role="menu">
                            <li>
                                <button
                                    type="button"
                                    onclick={() => {
                                        menuOpen = false;
                                        if (isOwner) {
                                            handleEdit();
                                        } else {
                                            showEditModal = true;
                                        }
                                    }}
                                >
                                    수정
                                </button>
                            </li>
                            <li>
                                <button
                                    type="button"
                                    class="danger"
                                    onclick={() => {
                                        menuOpen = false;
                                        showDeleteModal = true;
                                    }}
                                >
                                    삭제
                                </button>
                            </li>
                        </ul>
                    {/if}
                </div>
            </div>

            <h1 class="title">{post.title}</h1>

            <div class="meta">
                <span class="author">{post.nickname}</span>
                <span class="dot">·</span>
                <time datetime={post.createdAt}>{formatDistanceToNow(post.createdAt)}</time>
                <span class="dot">·</span>
                <span>조회 {post.viewCount}</span>
            </div>

            {#if post.taggedRaces && post.taggedRaces.length > 0}
                <div class="tags">
                    <RaceTagBadges races={post.taggedRaces} />
                </div>
            {/if}
        </header>

        <div class="content prose">{@html formatPostContent(post.content)}</div>

        {#if post.imageSrcs && post.imageSrcs.length > 0}
            <div class="images">
                <div class="kicker">IMAGES · {post.imageSrcs.length}</div>
                <div class="image-grid">
                    {#each post.imageSrcs as src, index}
                        <button
                            type="button"
                            class="image-tile"
                            onclick={() => openImageModal(index)}
                            aria-label="이미지 {index + 1} 확대 보기"
                        >
                            <img {src} alt="첨부 이미지 {index + 1}" loading="lazy" />
                        </button>
                    {/each}
                </div>
            </div>
        {/if}

        <div class="actions">
            <button
                type="button"
                class="action-btn like"
                class:active={hasLiked}
                onclick={handleLike}
                disabled={isLiking}
            >
                <span class="symbol">▲</span>
                <span class="label">추천</span>
                <span class="count">{likeCount}</span>
            </button>
            <button type="button" class="action-btn" onclick={() => (showShareModal = true)}>
                <span class="symbol">↗</span>
                <span class="label">공유</span>
            </button>
        </div>
    </article>

    <nav class="adjacent">
        {#if prevPost}
            <a href="/posts/{prevPost.id}" class="adj-link prev">
                <span class="adj-kicker">← 이전 글</span>
                <span class="adj-title">{prevPost.title}</span>
            </a>
        {:else}
            <div class="adj-link disabled prev">
                <span class="adj-kicker">← 이전 글 없음</span>
            </div>
        {/if}

        {#if nextPost}
            <a href="/posts/{nextPost.id}" class="adj-link next">
                <span class="adj-kicker">다음 글 →</span>
                <span class="adj-title">{nextPost.title}</span>
            </a>
        {:else}
            <div class="adj-link disabled next">
                <span class="adj-kicker">다음 글 없음 →</span>
            </div>
        {/if}
    </nav>

    <section class="comments">
        <CommentList comments={post.comments || []} postId={post.id} commentCount={post.commentCount} />
    </section>
</div>

{#if showEditModal}
    <div class="modal-overlay" role="dialog" aria-modal="true" aria-label="글 수정 인증">
        <div class="modal-card">
            <div class="kicker">EDIT · 비밀번호 확인</div>
            <h3 class="modal-title">글 수정</h3>
            <input
                type="password"
                class="modal-input"
                class:error={errors.password}
                placeholder="작성 시 입력한 비밀번호"
                bind:value={password}
            />
            {#if errors.password}<p class="err-msg">{errors.password}</p>{/if}
            <div class="modal-actions">
                <button type="button" class="btn ghost" onclick={() => { showEditModal = false; errors = {}; }}>취소</button>
                <button type="button" class="btn primary" onclick={handleEdit} disabled={isSubmitting}>
                    {isSubmitting ? '...' : '수정'}
                </button>
            </div>
        </div>
        <button class="modal-backdrop" onclick={() => { showEditModal = false; errors = {}; }} aria-label="닫기"></button>
    </div>
{/if}

{#if showDeleteModal}
    <div class="modal-overlay" role="dialog" aria-modal="true" aria-label="글 삭제">
        <div class="modal-card">
            <div class="kicker">DELETE · 글 삭제</div>
            <h3 class="modal-title">정말 삭제할까요?</h3>
            <p class="modal-desc">삭제된 글은 복구할 수 없습니다.</p>
            {#if !isOwner}
                <input
                    type="password"
                    class="modal-input"
                    class:error={errors.password}
                    placeholder="작성 시 입력한 비밀번호"
                    bind:value={password}
                />
                {#if errors.password}<p class="err-msg">{errors.password}</p>{/if}
            {/if}
            <div class="modal-actions">
                <button type="button" class="btn ghost" onclick={() => { showDeleteModal = false; errors = {}; }}>취소</button>
                <button type="button" class="btn danger" onclick={handleDelete} disabled={isSubmitting}>
                    {isSubmitting ? '...' : '삭제'}
                </button>
            </div>
        </div>
        <button class="modal-backdrop" onclick={() => { showDeleteModal = false; errors = {}; }} aria-label="닫기"></button>
    </div>
{/if}

{#if showImageModal && post.imageSrcs && post.imageSrcs.length > 0}
    <div class="modal-overlay image-overlay" role="dialog" aria-modal="true" aria-label="이미지 확대 보기">
        <div class="image-frame">
            <button onclick={closeImageModal} class="img-close" aria-label="닫기">×</button>
            <img src={post.imageSrcs[currentImageIndex]} alt="첨부 이미지 {currentImageIndex + 1}" />
            {#if post.imageSrcs.length > 1}
                <button
                    onclick={prevImage}
                    disabled={currentImageIndex === 0}
                    class="img-nav prev"
                    aria-label="이전 이미지">‹</button>
                <button
                    onclick={nextImage}
                    disabled={currentImageIndex === post.imageSrcs.length - 1}
                    class="img-nav next"
                    aria-label="다음 이미지">›</button>
                <div class="img-counter">
                    {currentImageIndex + 1} / {post.imageSrcs.length}
                </div>
            {/if}
        </div>
        <button class="modal-backdrop" onclick={closeImageModal} aria-label="닫기"></button>
    </div>
{/if}

{#if showShareModal}
    <div class="modal-overlay" role="dialog" aria-modal="true" aria-label="공유하기">
        <div class="modal-card">
            <div class="kicker">SHARE · 공유</div>
            <h3 class="modal-title">{post.title}</h3>
            <div class="share-list">
                <button type="button" class="btn ghost share-btn" onclick={() => { shareKakao(); showShareModal = false; }}>
                    카카오톡 공유
                </button>
                <button type="button" class="btn ghost share-btn" onclick={() => { copyLink(); showShareModal = false; }}>
                    링크 복사
                </button>
            </div>
            <div class="modal-actions">
                <button type="button" class="btn ghost" onclick={() => (showShareModal = false)}>닫기</button>
            </div>
        </div>
        <button class="modal-backdrop" onclick={() => (showShareModal = false)} aria-label="닫기"></button>
    </div>
{/if}

<style>
    .post-wrap {
        max-width: 760px;
        margin: 0 auto;
        padding: 32px 24px 60px;
        font-family: var(--arena-f-body);
        color: var(--arena-ink);
    }
    @media (min-width: 1024px) {
        .post-wrap {
            padding: 40px 32px 80px;
        }
    }

    .crumbs {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.5px;
        color: var(--arena-ink-soft);
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }
    .crumbs a {
        color: var(--arena-ink-soft);
        text-decoration: none;
    }
    .crumbs a:hover {
        color: var(--arena-ink);
    }
    .crumbs .sep {
        opacity: 0.4;
    }
    .crumbs .cur {
        color: var(--arena-ink);
        font-weight: 600;
        max-width: 320px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .article {
        background: var(--arena-paper);
        border: 1px solid var(--arena-line);
        padding: 28px 28px 32px;
    }
    @media (max-width: 640px) {
        .article {
            padding: 22px 18px 26px;
        }
    }
    .article-head {
        padding-bottom: 22px;
        border-bottom: 1px solid var(--arena-line-soft);
        margin-bottom: 24px;
    }
    .kicker-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: var(--arena-ink-soft);
    }

    .menu-wrap {
        position: relative;
    }
    .menu-btn {
        background: transparent;
        border: 1px solid var(--arena-line);
        color: var(--arena-ink-soft);
        padding: 2px 10px;
        font-family: var(--arena-f-mono);
        font-size: 14px;
        line-height: 1;
        cursor: pointer;
    }
    .menu-btn:hover {
        border-color: var(--arena-ink);
        color: var(--arena-ink);
    }
    .menu {
        position: absolute;
        top: calc(100% + 4px);
        right: 0;
        z-index: 30;
        margin: 0;
        padding: 4px 0;
        list-style: none;
        background: var(--arena-paper);
        border: 1px solid var(--arena-ink);
        box-shadow: 4px 4px 0 var(--arena-ink);
        min-width: 120px;
    }
    .menu li {
        padding: 0;
    }
    .menu button {
        display: block;
        width: 100%;
        text-align: left;
        background: transparent;
        border: none;
        cursor: pointer;
        padding: 8px 14px;
        font-family: var(--arena-f-body);
        font-size: 13px;
        color: var(--arena-ink);
    }
    .menu button:hover {
        background: var(--arena-paper-alt);
    }
    .menu button.danger {
        color: var(--arena-urgent);
    }
    .menu-backdrop {
        position: fixed;
        inset: 0;
        z-index: 20;
        background: transparent;
        border: none;
        cursor: default;
    }

    .title {
        font-family: var(--arena-f-display);
        font-size: clamp(24px, 4vw, 34px);
        font-weight: 700;
        letter-spacing: -0.6px;
        line-height: 1.25;
        margin: 0 0 14px;
        color: var(--arena-ink);
        text-wrap: balance;
    }

    .meta {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
        letter-spacing: 0.5px;
    }
    .author {
        color: var(--arena-ink);
        font-family: var(--arena-f-body);
        font-weight: 700;
        font-size: 13px;
    }
    .dot {
        opacity: 0.4;
    }

    .tags {
        margin-top: 14px;
    }

    .content {
        font-size: 15px;
        line-height: 1.75;
        color: var(--arena-ink);
        word-break: break-word;
    }
    .content :global(p) {
        margin: 0 0 14px;
    }
    .content :global(a) {
        color: var(--arena-accent-deep);
        text-decoration: underline;
        text-underline-offset: 2px;
    }
    .content :global(img) {
        max-width: 100%;
        height: auto;
        border: 1px solid var(--arena-line-soft);
    }
    .content :global(blockquote) {
        margin: 16px 0;
        padding: 4px 14px;
        border-left: 3px solid var(--arena-ink);
        color: var(--arena-ink-soft);
    }
    .content :global(ul),
    .content :global(ol) {
        padding-left: 22px;
        margin: 0 0 14px;
    }
    .content :global(code) {
        font-family: var(--arena-f-mono);
        font-size: 0.9em;
        background: var(--arena-paper-alt);
        padding: 1px 4px;
    }

    .images {
        margin-top: 24px;
        padding-top: 20px;
        border-top: 1px solid var(--arena-line-soft);
    }
    .images .kicker {
        margin-bottom: 12px;
        display: block;
    }
    .image-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
    }
    @media (min-width: 768px) {
        .image-grid {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    .image-tile {
        aspect-ratio: 1;
        border: 1px solid var(--arena-line-soft);
        background: var(--arena-paper-alt);
        cursor: pointer;
        padding: 0;
        overflow: hidden;
        transition: border-color 0.1s;
    }
    .image-tile:hover {
        border-color: var(--arena-ink);
    }
    .image-tile img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }

    .actions {
        margin-top: 28px;
        padding-top: 20px;
        border-top: 1px solid var(--arena-line-soft);
        display: flex;
        gap: 8px;
        justify-content: center;
    }
    .action-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: var(--arena-paper);
        border: 1px solid var(--arena-line);
        color: var(--arena-ink);
        padding: 9px 18px;
        font-family: var(--arena-f-mono);
        font-size: 12px;
        letter-spacing: 0.8px;
        cursor: pointer;
        text-transform: uppercase;
        line-height: 1.4;
    }
    .action-btn:hover {
        border-color: var(--arena-ink);
    }
    .action-btn .symbol {
        font-size: 14px;
        line-height: 1;
    }
    .action-btn .count {
        font-weight: 700;
        font-family: var(--arena-f-mono);
    }
    .action-btn.like.active {
        background: var(--arena-ink);
        color: var(--arena-paper);
        border-color: var(--arena-ink);
    }
    .action-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .adjacent {
        display: grid;
        grid-template-columns: 1fr 1fr;
        margin-top: 24px;
        border: 1px solid var(--arena-line);
    }
    .adj-link {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 14px 18px;
        background: var(--arena-paper);
        text-decoration: none;
        color: var(--arena-ink);
        border-right: 1px solid var(--arena-line-soft);
    }
    .adj-link.next {
        text-align: right;
        border-right: none;
    }
    .adj-link:hover {
        background: var(--arena-paper-alt);
    }
    .adj-link.disabled {
        opacity: 0.4;
        cursor: default;
    }
    .adj-kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: var(--arena-ink-soft);
    }
    .adj-title {
        font-family: var(--arena-f-body);
        font-size: 13px;
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .comments {
        margin-top: 40px;
    }

    /* ── Modals ─────────────────────────── */
    .modal-overlay {
        position: fixed;
        inset: 0;
        z-index: 100;
        display: grid;
        place-items: center;
        background: color-mix(in oklch, var(--arena-ink), transparent 50%);
        padding: 16px;
    }
    .modal-card {
        position: relative;
        z-index: 1;
        background: var(--arena-paper);
        border: 1px solid var(--arena-ink);
        box-shadow: 6px 6px 0 var(--arena-ink);
        padding: 22px;
        width: 100%;
        max-width: 380px;
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    .modal-card .kicker {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 2px;
        color: var(--arena-ink-soft);
        text-transform: uppercase;
    }
    .modal-title {
        font-family: var(--arena-f-display);
        font-size: 18px;
        font-weight: 700;
        margin: 0;
        color: var(--arena-ink);
        line-height: 1.3;
        text-wrap: balance;
    }
    .modal-desc {
        margin: 0;
        font-size: 13px;
        color: var(--arena-ink-soft);
    }
    .modal-input {
        width: 100%;
        border: 1px solid var(--arena-line);
        border-radius: 0;
        background: var(--arena-paper);
        padding: 9px 12px;
        font-family: var(--arena-f-body);
        font-size: 14px;
        color: var(--arena-ink);
        appearance: none;
        -webkit-appearance: none;
    }
    .modal-input:focus {
        outline: none;
        border-color: var(--arena-ink);
    }
    .modal-input.error {
        border-color: var(--arena-urgent);
    }
    .modal-actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        margin-top: 4px;
    }
    .modal-backdrop {
        position: absolute;
        inset: 0;
        background: transparent;
        border: none;
        cursor: pointer;
    }

    .err-msg {
        margin: 0;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-urgent);
    }

    .btn {
        border: 1px solid var(--arena-ink);
        padding: 8px 14px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1px;
        text-transform: uppercase;
        cursor: pointer;
        line-height: 1.4;
    }
    .btn.primary {
        background: var(--arena-ink);
        color: var(--arena-paper);
    }
    .btn.primary:hover:not(:disabled) {
        background: var(--arena-ink-soft);
    }
    .btn.primary:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }
    .btn.ghost {
        background: var(--arena-paper);
        color: var(--arena-ink);
        border-color: var(--arena-line);
    }
    .btn.ghost:hover {
        border-color: var(--arena-ink);
    }
    .btn.danger {
        background: var(--arena-urgent);
        color: var(--arena-paper);
        border-color: var(--arena-urgent);
    }
    .btn.danger:hover:not(:disabled) {
        opacity: 0.9;
    }

    .share-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .share-btn {
        width: 100%;
        text-align: center;
        padding: 12px 16px;
        font-size: 12px;
    }

    /* ── Image modal ─────────────────────────── */
    .image-overlay {
        background: color-mix(in oklch, var(--arena-ink), transparent 15%);
    }
    .image-frame {
        position: relative;
        z-index: 1;
        max-width: 90vw;
        max-height: 88vh;
        background: var(--arena-paper);
        border: 1px solid var(--arena-paper);
        padding: 4px;
    }
    .image-frame img {
        display: block;
        max-width: 100%;
        max-height: 80vh;
        margin: 0 auto;
    }
    .img-close {
        position: absolute;
        top: 8px;
        right: 8px;
        background: var(--arena-ink);
        color: var(--arena-paper);
        border: none;
        width: 32px;
        height: 32px;
        font-size: 18px;
        cursor: pointer;
        line-height: 1;
    }
    .img-nav {
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        background: var(--arena-ink);
        color: var(--arena-paper);
        border: none;
        width: 40px;
        height: 60px;
        font-size: 28px;
        cursor: pointer;
        line-height: 1;
    }
    .img-nav.prev {
        left: 8px;
    }
    .img-nav.next {
        right: 8px;
    }
    .img-nav:disabled {
        opacity: 0.3;
        cursor: not-allowed;
    }
    .img-counter {
        position: absolute;
        bottom: 8px;
        left: 50%;
        transform: translateX(-50%);
        background: var(--arena-ink);
        color: var(--arena-paper);
        padding: 4px 10px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1px;
    }
</style>
