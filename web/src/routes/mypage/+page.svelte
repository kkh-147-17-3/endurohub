<script lang="ts">
    import { enhance } from '$app/forms';

    let { data, form } = $props();

    let user = $derived(form?.user || data.user);
    let emailUpdatesOptIn = $state(false);
    let isSubmitting = $state(false);
    let errors = $derived(flattenErrors(form?.errors));
    let successMessage = $derived(form?.successMessage || '');

    let initials = $derived(
        (user.nickname || user.email || '?').slice(0, 1).toUpperCase()
    );

    function flattenErrors(errs: Record<string, string[]> | undefined): Record<string, string> {
        if (!errs) return {};
        const flat: Record<string, string> = {};
        for (const [key, msgs] of Object.entries(errs)) {
            flat[key] = Array.isArray(msgs) ? msgs[0] : msgs;
        }
        return flat;
    }

    $effect(() => {
        if (form?.emailUpdatesOptIn !== undefined) {
            emailUpdatesOptIn = !!form.emailUpdatesOptIn;
        } else if (user?.emailUpdatesOptIn !== undefined) {
            emailUpdatesOptIn = !!user.emailUpdatesOptIn;
        }
    });
</script>

<svelte:head>
    <title>마이페이지 - 엔듀로허브</title>
    <meta name="robots" content="noindex" />
</svelte:head>

<div class="page-wrap">
    <article class="page-shell">

        <header class="page-head">
            <div class="arena-kicker">계정</div>
            <h1 class="page-title">마이페이지</h1>
            <p class="page-lead">계정 정보와 알림 설정을 한곳에서 관리합니다.</p>
        </header>

        <!-- Profile -->
        <section class="profile-row">
            {#if user.profileImage}
                <img src={user.profileImage} alt={user.nickname || '프로필'} class="avatar-img" />
            {:else}
                <div class="avatar-fallback">{initials}</div>
            {/if}
            <div class="profile-meta">
                <div class="profile-name">{user.nickname || '닉네임 미설정'}</div>
                <div class="profile-email">{user.email || '이메일 미등록'}</div>
            </div>
            {#if user.emailVerified}
                <span class="arena-chip arena-chip-accent">인증됨</span>
            {:else if user.email}
                <span class="arena-chip arena-chip-urgent">미인증</span>
            {/if}
        </section>

        <!-- Email Verification CTA -->
        {#if !user.emailVerified}
            <section class="alert">
                <div class="alert-body">
                    <div class="arena-kicker alert-kicker">필수 안내</div>
                    <div class="alert-title">이메일 인증이 필요합니다</div>
                    <p class="alert-desc">
                        인증을 완료하면 계정 관련 안내와 알림을 받을 수 있습니다.
                    </p>
                </div>
                <a href="/auth/verify-email" class="alert-btn">
                    인증하기 <span class="arrow">→</span>
                </a>
            </section>
        {/if}

        <!-- Account Info -->
        <section class="page-section">
            <div class="arena-kicker">계정 정보</div>
            <div class="info-grid">
                <div class="info-row">
                    <span class="info-label">닉네임</span>
                    <span class="info-value">{user.nickname || '미설정'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">이메일</span>
                    <span class="info-value email-value">{user.email || '미등록'}</span>
                </div>
            </div>
        </section>

        <!-- Quick Links -->
        <section class="page-section">
            <div class="arena-kicker">바로가기</div>
            <a href="/mypage/favorites" class="quick-link">
                <span class="quick-label">관심 대회</span>
                <span class="quick-desc">저장한 대회 보기</span>
                <span class="quick-arrow">→</span>
            </a>
        </section>

        <!-- Notifications -->
        <section class="page-section">
            <div class="arena-kicker">알림 설정</div>
            <form
                method="POST"
                class="notif-form"
                use:enhance={() => {
                    isSubmitting = true;
                    return async ({ update }) => {
                        isSubmitting = false;
                        await update();
                    };
                }}
            >
                <label class="notif-row">
                    <div class="notif-text">
                        <div class="notif-title">이메일 알림 수신</div>
                        <div class="notif-desc">대회 소식 · 일정 업데이트 · 이벤트 안내</div>
                    </div>
                    <span class="arena-toggle">
                        <input
                            type="checkbox"
                            name="email_updates_opt_in"
                            bind:checked={emailUpdatesOptIn}
                        />
                        <span class="arena-toggle-track">
                            <span class="arena-toggle-thumb"></span>
                        </span>
                    </span>
                </label>

                <p class="notif-fineprint">
                    계정 보안 · 인증 등 필수 안내는 동의 여부와 관계없이 발송됩니다.
                </p>

                {#if successMessage}
                    <div class="status status-ok">{successMessage}</div>
                {/if}

                {#if errors.profile || errors.email_updates_opt_in}
                    <div class="status status-err">
                        {errors.profile || errors.email_updates_opt_in}
                    </div>
                {/if}

                <button type="submit" class="arena-btn arena-btn-primary save-btn" disabled={isSubmitting}>
                    {#if isSubmitting}저장 중…{:else}저장{/if}
                </button>
            </form>
        </section>

        <!-- Logout -->
        <form method="POST" action="/auth/logout" class="logout-form">
            <button type="submit" class="logout-btn">로그아웃 →</button>
        </form>

    </article>
</div>

<style>
    .page-wrap {
        background: var(--arena-paper);
        padding: 56px 24px 80px;
    }
    .page-shell {
        max-width: 720px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        gap: 40px;
    }

    .page-head {
        display: flex;
        flex-direction: column;
        gap: 14px;
        padding-bottom: 24px;
        border-bottom: 1px solid var(--arena-line);
    }
    .page-title {
        font-family: var(--arena-f-display);
        font-size: 56px;
        font-weight: 700;
        letter-spacing: -2px;
        line-height: 1;
        margin: 0;
        color: var(--arena-ink);
    }
    .page-lead {
        font-family: var(--arena-f-body);
        font-size: 15px;
        line-height: 1.6;
        color: var(--arena-ink-soft);
        margin: 0;
        word-break: keep-all;
    }

    /* Profile row */
    .profile-row {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 18px 18px;
        background: var(--arena-paper-alt);
        border: 1px solid var(--arena-line);
    }
    .avatar-img,
    .avatar-fallback {
        width: 56px;
        height: 56px;
        flex-shrink: 0;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
        display: grid;
        place-items: center;
        overflow: hidden;
    }
    .avatar-img {
        object-fit: cover;
    }
    .avatar-fallback {
        font-family: var(--arena-f-display);
        font-weight: 700;
        font-size: 22px;
        color: var(--arena-ink);
    }
    .profile-meta {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .profile-name {
        font-family: var(--arena-f-display);
        font-size: 18px;
        font-weight: 600;
        letter-spacing: -0.4px;
        color: var(--arena-ink);
        word-break: keep-all;
    }
    .profile-email {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* Alert */
    .alert {
        display: flex;
        flex-direction: column;
        gap: 16px;
        padding: 18px 18px 20px;
        background: var(--arena-paper);
        border: 1px solid var(--arena-urgent);
        border-left-width: 4px;
    }
    @media (min-width: 600px) {
        .alert {
            flex-direction: row;
            align-items: center;
        }
    }
    .alert-body {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .alert-kicker {
        color: var(--arena-urgent);
        letter-spacing: 1.5px;
    }
    .alert-title {
        font-family: var(--arena-f-display);
        font-size: 16px;
        font-weight: 600;
        color: var(--arena-ink);
    }
    .alert-desc {
        font-family: var(--arena-f-body);
        font-size: 13px;
        color: var(--arena-ink-soft);
        line-height: 1.6;
        margin: 0;
        word-break: keep-all;
    }
    .alert-btn {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
        background: var(--arena-urgent);
        color: var(--arena-paper);
        font-family: var(--arena-f-display);
        font-weight: 600;
        font-size: 13px;
        letter-spacing: -0.2px;
        text-decoration: none;
        flex-shrink: 0;
        align-self: flex-start;
    }
    @media (min-width: 600px) {
        .alert-btn {
            align-self: center;
        }
    }
    .alert-btn .arrow {
        font-family: var(--arena-f-mono);
    }

    /* Sections */
    .page-section {
        display: flex;
        flex-direction: column;
        gap: 14px;
    }

    /* Account info grid */
    .info-grid {
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
    }
    .info-row {
        display: grid;
        grid-template-columns: 100px 1fr;
        gap: 16px;
        align-items: center;
        padding: 14px 16px;
        border-bottom: 1px solid var(--arena-line-soft);
    }
    .info-row:last-child {
        border-bottom: none;
    }
    .info-label {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: var(--arena-ink-soft);
    }
    .info-value {
        font-family: var(--arena-f-body);
        font-size: 14px;
        font-weight: 500;
        color: var(--arena-ink);
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .email-value {
        font-family: var(--arena-f-mono);
        font-size: 12px;
    }

    /* Quick link */
    .quick-link {
        display: grid;
        grid-template-columns: 1fr auto;
        grid-template-rows: auto auto;
        align-items: center;
        gap: 4px 14px;
        padding: 16px 18px;
        background: var(--arena-paper);
        border: 1px solid var(--arena-line);
        text-decoration: none;
        color: var(--arena-ink);
        transition: transform 0.15s, box-shadow 0.15s;
    }
    .quick-link:hover {
        transform: translate(-2px, -2px);
        box-shadow: 4px 4px 0 var(--arena-ink);
    }
    .quick-label {
        grid-column: 1;
        grid-row: 1;
        font-family: var(--arena-f-display);
        font-size: 16px;
        font-weight: 600;
        letter-spacing: -0.3px;
    }
    .quick-desc {
        grid-column: 1;
        grid-row: 2;
        font-family: var(--arena-f-body);
        font-size: 12px;
        color: var(--arena-ink-soft);
    }
    .quick-arrow {
        grid-column: 2;
        grid-row: 1 / span 2;
        font-family: var(--arena-f-mono);
        font-size: 16px;
        color: var(--arena-ink-soft);
    }

    /* Notification form */
    .notif-form {
        display: flex;
        flex-direction: column;
        gap: 14px;
    }
    .notif-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        padding: 16px 18px;
        background: var(--arena-paper);
        border: 1px solid var(--arena-line);
        cursor: pointer;
    }
    .notif-row:hover {
        background: var(--arena-paper-alt);
    }
    .notif-text {
        display: flex;
        flex-direction: column;
        gap: 4px;
        min-width: 0;
    }
    .notif-title {
        font-family: var(--arena-f-display);
        font-size: 14px;
        font-weight: 600;
        color: var(--arena-ink);
    }
    .notif-desc {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        color: var(--arena-ink-soft);
        letter-spacing: 0.3px;
    }
    .notif-fineprint {
        margin: 0;
        padding: 0 4px;
        font-family: var(--arena-f-body);
        font-size: 12px;
        color: var(--arena-ink-mute);
        line-height: 1.6;
        word-break: keep-all;
    }

    /* Arena toggle */
    .arena-toggle {
        position: relative;
        flex-shrink: 0;
        display: inline-flex;
    }
    .arena-toggle input {
        position: absolute;
        inset: 0;
        opacity: 0;
        cursor: pointer;
    }
    .arena-toggle-track {
        width: 44px;
        height: 22px;
        background: var(--arena-paper-alt);
        border: 1px solid var(--arena-line);
        position: relative;
        transition: background 0.15s;
    }
    .arena-toggle-thumb {
        position: absolute;
        top: 1px;
        left: 1px;
        width: 18px;
        height: 18px;
        background: var(--arena-ink);
        transition: transform 0.15s;
    }
    .arena-toggle input:checked ~ .arena-toggle-track {
        background: var(--arena-accent);
        border-color: var(--arena-accent-deep);
    }
    .arena-toggle input:checked ~ .arena-toggle-track .arena-toggle-thumb {
        transform: translateX(22px);
        background: var(--arena-ink);
    }

    /* Status */
    .status {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.5px;
        padding: 8px 12px;
        border: 1px solid;
    }
    .status-ok {
        color: var(--arena-accent-deep);
        border-color: var(--arena-accent);
        background: color-mix(in oklch, var(--arena-accent), transparent 88%);
    }
    .status-err {
        color: var(--arena-urgent);
        border-color: var(--arena-urgent);
        background: color-mix(in oklch, var(--arena-urgent), transparent 90%);
    }

    .save-btn {
        width: 100%;
        justify-content: center;
        padding: 12px 16px;
    }

    /* Logout */
    .logout-form {
        margin: 0;
        padding-top: 16px;
        border-top: 1px solid var(--arena-line-soft);
    }
    .logout-btn {
        width: 100%;
        background: transparent;
        border: 1px solid var(--arena-line-soft);
        padding: 12px 16px;
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: var(--arena-ink-soft);
        cursor: pointer;
        transition: color 0.15s, border-color 0.15s, background 0.15s;
    }
    .logout-btn:hover {
        color: var(--arena-urgent);
        border-color: var(--arena-urgent);
        background: var(--arena-paper);
    }

    @media (max-width: 640px) {
        .page-title {
            font-size: 40px;
            letter-spacing: -1.5px;
        }
        .info-row {
            grid-template-columns: 80px 1fr;
            gap: 12px;
            padding: 12px 14px;
        }
    }
</style>
