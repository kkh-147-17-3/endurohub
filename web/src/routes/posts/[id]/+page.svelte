<script lang="ts" module>
    declare const Kakao: any;
</script>

<script lang="ts">
    import { page } from '$app/stores';
    import { goto } from '$app/navigation';
    import CommentList from '$lib/components/CommentList.svelte';
    import SportTag from '$lib/components/eh/SportTag.svelte';
    import { clientApiFetch, isApiError } from '$lib/api.client';
    import { formatPostContent } from '$lib/utils';
    import { dsSport } from '$lib/components/eh/meta';
    import type { Post, LikeToggleResponse, VerifyPasswordResponse, PostDeleteResponse, ApiErrors } from '$lib/types';

    let { data } = $props();

    let post = $derived(data.post as Post);
    let prevPost = $derived(data.prevPost as { id: number; title: string } | null);
    let nextPost = $derived(data.nextPost as { id: number; title: string } | null);

    let appUrl = $derived(data.appUrl || 'https://www.endurohub.kr');
    const pageUrl = $derived(`${appUrl}${$page.url.pathname}`);
    let isOwner = $derived(!!post.isOwner);

    const categoryLabels: Record<string, string> = {
        race_review: '후기',
        injury:      '부상/재활',
        gear:        '장비',
        training:    '훈련',
        question:    'Q&A',
        free:        '자유',
    };
    const categoryLabel = $derived(post.category ? categoryLabels[post.category] : null);

    // First char of nickname → avatar initial
    const authorInit = $derived((post.nickname?.trim()?.[0]) || '·');
    // sport from first tagged race
    const postSport = $derived(post.taggedRaces?.[0]?.sport ?? null);

    // ── Modal / UI state ────────────────────────────────────────────
    let showDeleteModal = $state(false);
    let showEditModal   = $state(false);
    let showShareModal  = $state(false);
    let showImageModal  = $state(false);
    let currentImageIndex = $state(0);
    let password = $state('');
    let errors = $state<Record<string, string>>({});
    let isSubmitting = $state(false);
    let menuOpen = $state(false);

    // ── Like state ──────────────────────────────────────────────────
    let hasLiked  = $state(false);
    let likeCount = $state(0);
    $effect(() => {
        hasLiked  = data.hasLiked;
        likeCount = data.post.likeCount;
    });
    let isLiking = $state(false);

    const contentText = $derived(post.contentText || '');

    // ── Structured data ─────────────────────────────────────────────
    let articleSchema = $derived({
        '@context': 'https://schema.org',
        '@type': 'Article',
        headline: post.title,
        author: { '@type': 'Person', name: post.nickname },
        datePublished: post.createdAt,
        dateModified: post.updatedAt,
        articleBody: contentText.substring(0, 500),
        image: post.imageSrcs?.[0],
        publisher: { '@type': 'Organization', name: 'endurohub', url: appUrl },
        mainEntityOfPage: pageUrl,
    });

    let breadcrumbSchema = $derived({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        itemListElement: [
            { '@type': 'ListItem', position: 1, name: '홈',       item: appUrl },
            { '@type': 'ListItem', position: 2, name: '커뮤니티', item: `${appUrl}/community` },
            { '@type': 'ListItem', position: 3, name: post.title, item: pageUrl },
        ],
    });

    // ── Image lightbox ───────────────────────────────────────────────
    function openImageModal(index: number) { currentImageIndex = index; showImageModal = true; }
    function closeImageModal() { showImageModal = false; }
    function nextImage() { if (post.imageSrcs && currentImageIndex < post.imageSrcs.length - 1) currentImageIndex++; }
    function prevImage() { if (currentImageIndex > 0) currentImageIndex--; }

    $effect(() => {
        const saved = typeof localStorage !== 'undefined' ? localStorage.getItem('postPassword') : null;
        if (saved) password = saved;
    });

    // ── Edit/delete handlers ─────────────────────────────────────────
    async function handleEdit() {
        if (isSubmitting) return;
        isSubmitting = true; errors = {};
        try {
            const result = await clientApiFetch<VerifyPasswordResponse | ApiErrors>(
                `/posts/${post.id}/verify-password/`,
                { method: 'POST', body: { password } }
            );
            if (isApiError(result)) {
                errors = Object.fromEntries(
                    Object.entries((result as ApiErrors).errors).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v])
                );
            } else {
                goto(`/posts/${post.id}/edit?token=${(result as VerifyPasswordResponse).editToken}`);
            }
        } catch { errors = { password: '오류가 발생했습니다.' }; }
        finally { isSubmitting = false; }
    }

    async function handleDelete() {
        if (isSubmitting) return;
        isSubmitting = true; errors = {};
        try {
            const result = await clientApiFetch<PostDeleteResponse | ApiErrors>(`/posts/${post.id}/`, {
                method: 'DELETE', body: { password },
            });
            if (isApiError(result)) {
                errors = Object.fromEntries(
                    Object.entries((result as ApiErrors).errors).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v])
                );
            } else { goto('/community'); }
        } catch { errors = { password: '오류가 발생했습니다.' }; }
        finally { isSubmitting = false; }
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Escape') {
            showDeleteModal = showEditModal = showShareModal = showImageModal = false;
            menuOpen = false;
        }
        if (showImageModal) {
            if (e.key === 'ArrowRight') nextImage();
            if (e.key === 'ArrowLeft')  prevImage();
        }
    }

    // ── Toast ────────────────────────────────────────────────────────
    function showToast(message: string) {
        const el = document.createElement('div');
        el.style.cssText =
            'position:fixed;top:24px;left:50%;transform:translateX(-50%);' +
            'background:var(--ink-900);color:var(--paper-0);padding:10px 20px;' +
            'font-family:var(--font-sans);font-size:13px;font-weight:600;z-index:300;' +
            'border:1px solid var(--ink-900);border-radius:var(--r-1);';
        el.textContent = message;
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 2500);
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
                    imageUrl: post.imageSrcs?.[0] || '',
                    link: { webUrl: window.location.href, mobileWebUrl: window.location.href },
                },
            });
        } else { showToast('카카오 공유 기능을 사용할 수 없습니다.'); }
    }

    // ── Like ─────────────────────────────────────────────────────────
    async function handleLike() {
        if (isLiking) return;
        isLiking = true;
        try {
            const result = await clientApiFetch<LikeToggleResponse>(`/posts/${post.id}/like/`, { method: 'POST' });
            if (result.success) { hasLiked = result.liked; likeCount = result.likeCount; }
        } catch (err) { console.error('Like error:', err); }
        finally { isLiking = false; }
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
        <meta name="twitter:image" content={post.imageSrcs[0]} />
    {:else}
        <meta property="og:image" content="{appUrl}/images/og-image.png" />
        <meta property="og:image:width" content="1200" />
        <meta property="og:image:height" content="630" />
        <meta name="twitter:image" content="{appUrl}/images/og-image.png" />
    {/if}
    <meta property="article:published_time" content={post.createdAt} />
    <meta property="article:modified_time" content={post.updatedAt} />
    {@html `<script type="application/ld+json">${JSON.stringify(articleSchema)}</script>`}
    {@html `<script type="application/ld+json">${JSON.stringify(breadcrumbSchema)}</script>`}
</svelte:head>

<div class="v-container post-detail">
    <!-- ── Breadcrumb ──────────────────────────────────────── -->
    <nav class="crumb" aria-label="이동 경로">
        <a href="/community">커뮤니티</a>
        <span aria-hidden="true">›</span>
        {#if categoryLabel}
            <a href="/community?category={post.category}">{categoryLabel}</a>
            <span aria-hidden="true">›</span>
        {/if}
        <span class="here">{post.title}</span>
        <a class="crumb-back" href="/community">← 목록</a>
    </nav>

    <div class="layout">
        <article>
            <!-- ── Article header ──────────────────────────── -->
            <header class="post-hd">
                <div class="tags">
                    {#if categoryLabel}<span class="cat">{categoryLabel}</span>{/if}
                    {#if postSport}<SportTag sport={dsSport(postSport)} />{/if}

                    <div class="hd-right">
                        <span class="eh-micro eh-data no">NO. C-{post.id}</span>
                        <div class="menu-wrap">
                            <button
                                type="button"
                                class="menu-trigger eh-iconbtn eh-iconbtn--outline"
                                aria-label="게시글 관리"
                                aria-expanded={menuOpen}
                                onclick={() => (menuOpen = !menuOpen)}
                            >
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></svg>
                            </button>
                            {#if menuOpen}
                                <button class="menu-backdrop" onclick={() => (menuOpen = false)} aria-label="닫기" tabindex="-1"></button>
                                <ul class="menu-list" role="menu">
                                    <li role="none">
                                        <button
                                            type="button"
                                            role="menuitem"
                                            onclick={() => {
                                                menuOpen = false;
                                                if (isOwner) { handleEdit(); } else { showEditModal = true; }
                                            }}
                                        >수정</button>
                                    </li>
                                    <li role="none">
                                        <button
                                            type="button"
                                            role="menuitem"
                                            class="menu-danger"
                                            onclick={() => { menuOpen = false; showDeleteModal = true; }}
                                        >삭제</button>
                                    </li>
                                </ul>
                            {/if}
                        </div>
                    </div>
                </div>

                <h1>{post.title}</h1>

                <div class="byline">
                    <span class="who"><span class="av">{authorInit}</span>{post.nickname}</span>
                    <span class="eh-data">{post.createdAtFormatted}</span>
                    <span class="eh-data">조회 {post.viewCount.toLocaleString()}</span>
                    <span class="eh-data">댓글 {post.commentCount}</span>
                </div>
            </header>

            <!-- ── Race record (tagged races) ──────────────── -->
            {#if post.taggedRaces && post.taggedRaces.length > 0}
                <section class="record" aria-label="태그된 대회">
                    <div class="eh-micro"><span class="acc">RACE RECORD</span> · 태그된 대회</div>
                    {#each post.taggedRaces as race (race.id)}
                        <div class="race-line">
                            <a href="/races/{race.slug}">{race.title} ↗</a>
                            <SportTag sport={dsSport(race.sport)} muted />
                        </div>
                    {/each}
                </section>
            {/if}

            <!-- ── Body ────────────────────────────────────── -->
            <div class="body prose">{@html formatPostContent(post.content)}</div>

            <!-- ── Images ──────────────────────────────────── -->
            {#if post.imageSrcs && post.imageSrcs.length > 0}
                <section class="sec image-section" aria-label="첨부 이미지">
                    <div class="eh-micro sec-label"><span class="acc">IMAGES</span> · <span class="eh-data">{post.imageSrcs.length}</span></div>
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
                </section>
            {/if}

            <!-- ── Actions ─────────────────────────────────── -->
            <div class="act-row">
                <button
                    type="button"
                    class="action-btn"
                    class:action-btn--active={hasLiked}
                    onclick={handleLike}
                    disabled={isLiking}
                    aria-pressed={hasLiked}
                    aria-label="추천 {likeCount}"
                >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill={hasLiked ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="2"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
                    <span>추천</span>
                    <strong class="eh-data">{likeCount}</strong>
                </button>
                <button type="button" class="action-btn" onclick={() => (showShareModal = true)} aria-label="공유하기">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
                    <span>공유</span>
                </button>
            </div>

            <!-- ── Comments ────────────────────────────────── -->
            <section class="comments" aria-label="댓글">
                <CommentList comments={post.comments || []} postId={post.id} commentCount={post.commentCount} />
            </section>

            <!-- ── Prev / Next ─────────────────────────────── -->
            <nav class="pn" aria-label="이전·다음 글">
                {#if prevPost}
                    <a href="/posts/{prevPost.id}">
                        <span class="dir">이전 글</span>
                        <span class="t">{prevPost.title}</span>
                    </a>
                {/if}
                {#if nextPost}
                    <a href="/posts/{nextPost.id}">
                        <span class="dir">다음 글</span>
                        <span class="t">{nextPost.title}</span>
                    </a>
                {/if}
            </nav>
        </article>
    </div>
</div>

<!-- ── Edit password modal ─────────────────────────────── -->
{#if showEditModal}
    <div class="v-scrim" role="dialog" aria-modal="true" aria-label="글 수정 인증">
        <div class="v-modal modal-content">
            <div class="modal-head">
                <span class="eh-micro">EDIT · 비밀번호 확인</span>
                <h2 class="modal-title">글 수정</h2>
            </div>
            <div class="modal-body">
                <input
                    type="password"
                    class="eh-input"
                    class:field-error={errors.password}
                    placeholder="작성 시 입력한 비밀번호"
                    bind:value={password}
                />
                {#if errors.password}<p class="err-msg">{errors.password}</p>{/if}
            </div>
            <div class="modal-foot">
                <button type="button" class="eh-btn eh-btn--sm eh-btn--ghost" onclick={() => { showEditModal = false; errors = {}; }}>취소</button>
                <button type="button" class="eh-btn eh-btn--sm eh-btn--primary" onclick={handleEdit} disabled={isSubmitting}>
                    {isSubmitting ? '...' : '수정'}
                </button>
            </div>
        </div>
        <button class="v-scrim-close" onclick={() => { showEditModal = false; errors = {}; }} aria-label="닫기" tabindex="-1"></button>
    </div>
{/if}

<!-- ── Delete modal ────────────────────────────────────── -->
{#if showDeleteModal}
    <div class="v-scrim" role="dialog" aria-modal="true" aria-label="글 삭제">
        <div class="v-modal modal-content">
            <div class="modal-head">
                <span class="eh-micro">DELETE · 글 삭제</span>
                <h2 class="modal-title">정말 삭제할까요?</h2>
                <p class="modal-desc">삭제된 글은 복구할 수 없습니다.</p>
            </div>
            {#if !isOwner}
                <div class="modal-body">
                    <input
                        type="password"
                        class="eh-input"
                        class:field-error={errors.password}
                        placeholder="작성 시 입력한 비밀번호"
                        bind:value={password}
                    />
                    {#if errors.password}<p class="err-msg">{errors.password}</p>{/if}
                </div>
            {/if}
            <div class="modal-foot">
                <button type="button" class="eh-btn eh-btn--sm eh-btn--ghost" onclick={() => { showDeleteModal = false; errors = {}; }}>취소</button>
                <button type="button" class="eh-btn eh-btn--sm eh-btn--primary danger-btn" onclick={handleDelete} disabled={isSubmitting}>
                    {isSubmitting ? '...' : '삭제'}
                </button>
            </div>
        </div>
        <button class="v-scrim-close" onclick={() => { showDeleteModal = false; errors = {}; }} aria-label="닫기" tabindex="-1"></button>
    </div>
{/if}

<!-- ── Image lightbox ──────────────────────────────────── -->
{#if showImageModal && post.imageSrcs && post.imageSrcs.length > 0}
    <div class="v-scrim image-scrim" role="dialog" aria-modal="true" aria-label="이미지 확대 보기">
        <div class="image-frame">
            <button onclick={closeImageModal} class="img-close" aria-label="닫기">×</button>
            <img src={post.imageSrcs[currentImageIndex]} alt="첨부 이미지 {currentImageIndex + 1}" />
            {#if post.imageSrcs.length > 1}
                <button onclick={prevImage} disabled={currentImageIndex === 0} class="img-nav img-nav--prev" aria-label="이전 이미지">‹</button>
                <button onclick={nextImage} disabled={currentImageIndex === post.imageSrcs.length - 1} class="img-nav img-nav--next" aria-label="다음 이미지">›</button>
                <div class="img-counter eh-data">{currentImageIndex + 1} / {post.imageSrcs.length}</div>
            {/if}
        </div>
        <button class="v-scrim-close" onclick={closeImageModal} aria-label="닫기" tabindex="-1"></button>
    </div>
{/if}

<!-- ── Share modal ─────────────────────────────────────── -->
{#if showShareModal}
    <div class="v-scrim" role="dialog" aria-modal="true" aria-label="공유하기">
        <div class="v-modal modal-content">
            <div class="modal-head">
                <span class="eh-micro">SHARE · 공유</span>
                <h2 class="modal-title">{post.title}</h2>
            </div>
            <div class="modal-body share-list">
                <button type="button" class="eh-btn eh-btn--md eh-btn--ghost eh-btn--full" onclick={() => { shareKakao(); showShareModal = false; }}>카카오톡 공유</button>
                <button type="button" class="eh-btn eh-btn--md eh-btn--ghost eh-btn--full" onclick={() => { copyLink(); showShareModal = false; }}>링크 복사</button>
            </div>
            <div class="modal-foot">
                <button type="button" class="eh-btn eh-btn--sm eh-btn--ghost" onclick={() => (showShareModal = false)}>닫기</button>
            </div>
        </div>
        <button class="v-scrim-close" onclick={() => (showShareModal = false)} aria-label="닫기" tabindex="-1"></button>
    </div>
{/if}

<style>
    /* ── Page layout ───────────────────────────── */
    .post-detail {
        padding-top: 0;
        padding-bottom: var(--sp-20);
    }
    .acc { color: var(--accent-strong); }

    /* Single-column reading layout — rail removed */
    .layout {
        max-width: 720px;
        margin: 0 auto;
    }

    /* ── Breadcrumb ────────────────────────────── */
    .crumb {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 14px 0;
        font-size: 12.5px;
        color: var(--text-faint);
        flex-wrap: wrap;
    }
    .crumb a {
        color: var(--text-muted);
        text-decoration: none;
        transition: color var(--dur-fast) var(--ease-out);
    }
    .crumb a:hover { color: var(--text-strong); text-decoration: underline; text-underline-offset: 3px; }
    .crumb span[aria-hidden] { opacity: 0.5; }
    .crumb .here {
        color: var(--text-strong);
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 420px;
    }
    .crumb-back { margin-left: auto; font-weight: 600; white-space: nowrap; }

    /* ── Article header ────────────────────────── */
    .post-hd {
        padding: 30px 0 24px;
        border-bottom: var(--border-rule);
    }
    .post-hd .tags {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }
    .hd-right {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-left: auto;
    }
    .no { color: var(--text-faint); white-space: nowrap; }
    .post-hd h1 {
        margin: 14px 0 0;
        max-width: 760px;
        font-size: clamp(24px, 3vw, 34px);
        font-weight: var(--w-display);
        letter-spacing: var(--track-display);
        line-height: 1.22;
        color: var(--text-strong);
        text-wrap: pretty;
    }
    .cat {
        font-size: var(--text-micro);
        font-weight: var(--w-strong);
        letter-spacing: var(--track-micro);
        text-transform: uppercase;
        padding: 2px 7px;
        border: 1px solid var(--line);
        border-radius: var(--r-2);
        color: var(--text-muted);
        white-space: nowrap;
    }
    .byline {
        display: flex;
        align-items: center;
        gap: 14px;
        margin-top: 18px;
        font-size: 12.5px;
        color: var(--text-faint);
        flex-wrap: wrap;
    }
    .byline .who {
        display: flex;
        align-items: center;
        gap: 9px;
        color: var(--text-strong);
        font-weight: 600;
    }
    .byline .av {
        width: 26px;
        height: 26px;
        border: 1px solid var(--ink-900);
        border-radius: var(--r-1);
        display: grid;
        place-items: center;
        font-size: 11px;
        font-weight: 800;
        background: var(--paper-0);
    }

    /* Overflow menu */
    .menu-wrap { position: relative; }
    .menu-trigger { font-size: 16px; }
    .menu-backdrop {
        position: fixed; inset: 0; z-index: 19;
        background: transparent; border: none; cursor: default;
    }
    .menu-list {
        position: absolute; top: calc(100% + 6px); right: 0; z-index: 20;
        list-style: none; margin: 0; padding: 4px 0;
        background: var(--paper-0);
        border: 1px solid var(--ink-900);
        box-shadow: 4px 4px 0 var(--paper-100);
        min-width: 120px;
    }
    .menu-list li { padding: 0; }
    .menu-list button {
        display: block; width: 100%; text-align: left;
        background: transparent; border: none; cursor: pointer;
        padding: 9px 16px;
        font-family: var(--font-sans); font-size: 14px;
        color: var(--text-body);
        transition: background var(--dur-fast) var(--ease-out);
    }
    .menu-list button:hover { background: var(--paper-50); color: var(--text-strong); }
    .menu-list button.menu-danger { color: var(--danger); }

    /* ── Race record ───────────────────────────── */
    .record {
        border-top: var(--border-rule);
        margin-top: 28px;
        padding-top: 14px;
    }
    .race-line {
        display: flex;
        align-items: baseline;
        gap: 12px;
        flex-wrap: wrap;
        margin-top: 8px;
    }
    .race-line a {
        font-size: 17px;
        font-weight: 700;
        color: var(--text-strong);
        text-decoration: none;
        letter-spacing: var(--track-heading);
    }
    .race-line a:hover { text-decoration: underline; text-underline-offset: 3px; }

    /* ── Body prose (matches design `.md`) ─────── */
    .body {
        max-width: 720px;
        padding: 30px 0 0;
        font-size: 15.5px;
        line-height: 1.78;
        color: var(--text-strong);
        word-break: break-word;
    }
    .body :global(p)          { margin: 0 0 16px; }
    .body :global(p:last-child){ margin-bottom: 0; }
    .body :global(a) {
        color: var(--text-strong);
        text-decoration: underline;
        text-underline-offset: 3px;
        text-decoration-thickness: 1px;
    }
    .body :global(a:hover)    { color: var(--text-accent); }
    .body :global(b),
    .body :global(strong)     { font-weight: 700; }
    .body :global(img)        { max-width: 100%; height: auto; border: var(--border-hair); }
    .body :global(blockquote) {
        margin: 16px 0;
        border-left: 2px solid var(--ink-900);
        background: var(--paper-50);
        padding: 13px 18px;
        color: var(--text-muted);
        font-size: 0.95em;
    }
    .body :global(ul),
    .body :global(ol)         { padding-left: 22px; margin: 0 0 16px; }
    .body :global(li + li)    { margin-top: 7px; }
    .body :global(li::marker) { color: var(--text-faint); font-weight: 700; }
    .body :global(code)       { font-family: var(--font-mono); font-size: 0.9em; background: var(--paper-100); padding: 1px 4px; border-radius: var(--r-1); }
    .body :global(h2) {
        margin: 40px 0 16px;
        padding-top: 12px;
        border-top: var(--border-rule);
        font-size: 19px;
        font-weight: var(--w-strong);
        letter-spacing: var(--track-heading);
        line-height: 1.3;
        color: var(--text-strong);
    }
    .body :global(h3) {
        margin: 30px 0 16px;
        font-size: 16.5px;
        font-weight: 700;
        letter-spacing: var(--track-heading);
        color: var(--text-strong);
    }
    .body :global(hr) { border: 0; border-top: var(--border-hair); margin: 32px 0 0; }
    .body :global(table) {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.92em;
        margin: 16px 0;
    }
    .body :global(th) {
        border-top: var(--border-rule);
        border-bottom: var(--border-hair);
        text-align: left;
        padding: 9px 10px;
        font-size: var(--text-micro);
        font-weight: var(--w-strong);
        letter-spacing: var(--track-micro);
        text-transform: uppercase;
        color: var(--text-muted);
    }
    .body :global(td) {
        border-bottom: var(--border-hair);
        padding: 9px 10px;
        font-variant-numeric: tabular-nums;
    }

    /* ── Sections ──────────────────────────────── */
    .sec { margin-top: 36px; }
    .sec-label {
        border-top: var(--border-rule);
        padding-top: 10px;
        margin-bottom: 12px;
        display: block;
    }

    /* ── Images ────────────────────────────────── */
    .image-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
    }
    @media (min-width: 600px) {
        .image-grid { grid-template-columns: repeat(3, 1fr); }
    }
    .image-tile {
        aspect-ratio: 1;
        border: var(--border-hair);
        background: var(--paper-50);
        cursor: pointer; padding: 0; overflow: hidden;
        transition: border-color var(--dur-fast) var(--ease-out);
    }
    .image-tile:hover { border-color: var(--ink-900); }
    .image-tile img { width: 100%; height: 100%; object-fit: cover; display: block; }

    /* ── Actions ───────────────────────────────── */
    .act-row {
        display: flex;
        align-items: center;
        gap: 10px;
        justify-content: center;
        margin-top: 44px;
        padding: 24px 0;
        border-top: var(--border-hair);
        border-bottom: var(--border-rule);
    }
    .action-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: var(--paper-0);
        border: 1px solid var(--line);
        color: var(--text-body);
        padding: 0 18px;
        height: 40px;
        font-family: var(--font-sans);
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        border-radius: var(--r-2);
        transition: border-color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
    }
    .action-btn:hover { border-color: var(--ink-900); color: var(--text-strong); }
    .action-btn--active {
        background: var(--ink-900);
        color: var(--paper-0);
        border-color: var(--ink-900);
    }
    .action-btn:disabled { opacity: 0.5; cursor: not-allowed; }

    /* ── Comments ──────────────────────────────── */
    .comments {
        margin-top: 36px;
        padding-top: 12px;
        border-top: var(--border-rule);
    }

    /* ── Prev / Next ───────────────────────────── */
    .pn {
        margin-top: 36px;
        border-top: var(--border-rule);
    }
    .pn a {
        display: grid;
        grid-template-columns: 64px 1fr;
        gap: 14px;
        align-items: baseline;
        padding: 14px 4px;
        border-bottom: var(--border-hair);
        text-decoration: none;
        color: inherit;
        font-size: 14px;
        transition: background var(--dur-fast) var(--ease-out);
    }
    .pn a:hover { background: var(--paper-50); }
    .pn a:hover .t { text-decoration: underline; text-underline-offset: 3px; }
    .pn .dir {
        font-size: var(--text-micro);
        font-weight: var(--w-strong);
        letter-spacing: var(--track-micro);
        text-transform: uppercase;
        color: var(--text-faint);
    }
    .pn .t {
        font-weight: 600;
        color: var(--text-strong);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* ── Modals ────────────────────────────────── */
    .v-scrim {
        position: fixed; inset: 0; z-index: 200;
        background: rgba(16, 19, 18, 0.50);
        display: grid; place-items: center;
        padding: var(--sp-5);
    }
    .v-scrim-close {
        position: absolute; inset: 0;
        background: transparent; border: none; cursor: pointer; z-index: 0;
    }
    .v-modal {
        position: relative; z-index: 1;
        background: var(--paper-0);
        border: 1px solid var(--ink-900);
        box-shadow: var(--shadow-pop);
        width: 100%; max-width: 400px;
    }
    .modal-content { display: flex; flex-direction: column; }
    .modal-head {
        padding: 20px 22px 16px;
        border-bottom: var(--border-hair);
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .modal-title {
        font-size: 18px;
        font-weight: 700;
        color: var(--text-strong);
        margin: 0;
        line-height: 1.3;
    }
    .modal-desc { margin: 0; font-size: 13px; color: var(--text-muted); }
    .modal-body {
        padding: 16px 22px;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .field-error { border-color: var(--danger) !important; }
    .err-msg {
        margin: 0;
        font-size: 12px;
        color: var(--danger);
        font-weight: 600;
    }
    .modal-foot {
        padding: 12px 22px 18px;
        display: flex;
        justify-content: flex-end;
        gap: 8px;
    }
    .danger-btn {
        background: var(--danger) !important;
        border-color: var(--danger) !important;
        color: var(--paper-0) !important;
    }
    .share-list { display: flex; flex-direction: column; gap: 8px; }

    /* ── Image lightbox ─────────────────────────── */
    .image-scrim { background: rgba(16, 19, 18, 0.88); }
    .image-frame {
        position: relative; z-index: 1;
        max-width: 90vw; max-height: 88vh;
        background: var(--paper-0);
        border: var(--border-hair);
        padding: 4px;
    }
    .image-frame img {
        display: block; max-width: 100%; max-height: 80vh; margin: 0 auto;
    }
    .img-close {
        position: absolute; top: 8px; right: 8px;
        background: var(--ink-900); color: var(--paper-0);
        border: none; width: 32px; height: 32px;
        font-size: 18px; cursor: pointer; line-height: 1;
    }
    .img-nav {
        position: absolute; top: 50%; transform: translateY(-50%);
        background: var(--ink-900); color: var(--paper-0);
        border: none; width: 40px; height: 60px;
        font-size: 28px; cursor: pointer; line-height: 1;
    }
    .img-nav--prev { left: 8px; }
    .img-nav--next { right: 8px; }
    .img-nav:disabled { opacity: 0.3; cursor: not-allowed; }
    .img-counter {
        position: absolute; bottom: 8px; left: 50%; transform: translateX(-50%);
        background: var(--ink-900); color: var(--paper-0);
        padding: 4px 10px; font-size: 11px; font-weight: 600; letter-spacing: 0.04em;
    }

    @media (max-width: 768px) {
        .post-hd h1 { font-size: clamp(22px, 6vw, 28px); }
    }
</style>
