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

<div class="mp-wrap v-container">
    <div class="mp-page">

        <!-- Page header -->
        <header class="mp-hd">
            <div class="eh-micro"><span class="acc">ACCOUNT</span> · 계정 / 설정</div>
            <h1 class="eh-h1">마이페이지</h1>
            <p class="eh-body mp-lead">계정 정보와 알림 설정을 한곳에서 관리합니다.</p>
        </header>

        <!-- ── 01 · Identity strip ── -->
        <div class="identity">
            <!-- Avatar + name -->
            <div class="id-main">
                <div class="id-row">
                    {#if user.profileImage}
                        <img src={user.profileImage} alt={user.nickname || '프로필'} class="id-avatar id-avatar--img" />
                    {:else}
                        <span class="id-avatar">{initials}</span>
                    {/if}
                    <span>
                        <span class="id-name">{user.nickname || '닉네임 미설정'}</span>
                        <span class="id-email">{user.email || '이메일 미등록'}</span>
                    </span>
                </div>
                <div class="id-badges">
                    {#if user.emailVerified}
                        <span class="badge ok">VERIFIED</span>
                    {:else if user.email}
                        <span class="badge warn">미인증</span>
                    {/if}
                    <span class="eh-micro" style="color: var(--text-faint)">GOOGLE OAUTH</span>
                </div>
            </div>
            <!-- Stat cells -->
            <div class="id-stat">
                <span class="stat-label">Saved races</span>
                <span class="stat-val eh-data">—</span>
                <span class="stat-note">저장한 대회</span>
            </div>
            <div class="id-stat">
                <span class="stat-label">PB records</span>
                <span class="stat-val eh-data accent">—</span>
                <span class="stat-note">개인 최고 기록</span>
            </div>
        </div>

        <!-- ── 이메일 미인증 안내 ── -->
        {#if !user.emailVerified}
            <div class="alert-bar">
                <div class="alert-body">
                    <span class="eh-micro" style="color: var(--danger)">필수 안내</span>
                    <div class="alert-title">이메일 인증이 필요합니다</div>
                    <p class="alert-desc">인증을 완료하면 계정 관련 안내와 알림을 받을 수 있습니다.</p>
                </div>
                <a href="/auth/onboarding" class="alert-cta">인증하기 →</a>
            </div>
        {/if}

        <!-- ── 01 · 계정 정보 ── -->
        <section class="mp-section">
            <div class="v-sechead">
                <span>
                    <span class="eh-micro" style="color: var(--text-faint)">01</span>
                    <span class="eh-h3" style="margin-left: var(--sp-2)">계정 정보</span>
                </span>
                <span class="eh-micro" style="color: var(--text-faint)">ACCOUNT</span>
            </div>

            <div class="v-table" style="margin-top: var(--sp-4)">
                <div class="info-row">
                    <span class="eh-micro info-key">EMAIL</span>
                    <span class="info-val">
                        {user.email || '미등록'}
                        {#if user.emailVerified}
                            <span class="badge ok" style="margin-left: var(--sp-2)">인증됨</span>
                        {/if}
                    </span>
                    <a href="/auth/onboarding" class="info-action">변경</a>
                </div>
                <div class="info-row">
                    <span class="eh-micro info-key">NICKNAME</span>
                    <span class="info-val">
                        {user.nickname || '미설정'}
                        <span class="info-note">커뮤니티 표시 이름</span>
                    </span>
                    <a href="/auth/onboarding" class="info-action">변경</a>
                </div>
                <div class="info-row info-row--last">
                    <span class="eh-micro info-key">PASSWORD</span>
                    <span class="info-val">
                        <span class="info-note">소셜 로그인 계정 — 비밀번호 없음</span>
                    </span>
                    <span class="info-action faint">설정</span>
                </div>
            </div>
        </section>

        <!-- ── 02 · 바로가기 ── -->
        <section class="mp-section">
            <div class="v-sechead">
                <span>
                    <span class="eh-micro" style="color: var(--text-faint)">02</span>
                    <span class="eh-h3" style="margin-left: var(--sp-2)">바로가기</span>
                </span>
                <span class="eh-micro" style="color: var(--text-faint)">QUICK ACCESS</span>
            </div>

            <div class="shortcuts">
                <a href="/mypage/favorites" class="v-card shortcut">
                    <span class="sh-num eh-data">01</span>
                    <span class="sh-arrow">↗</span>
                    <span class="sh-label">관심 대회</span>
                    <span class="sh-meta">저장한 대회 보기</span>
                </a>
                <a href="/calendar" class="v-card shortcut">
                    <span class="sh-num eh-data">02</span>
                    <span class="sh-arrow">↗</span>
                    <span class="sh-label">캘린더</span>
                    <span class="sh-meta">내 종목 일정 보기</span>
                </a>
                <a href="/tools/pace-calculator" class="v-card shortcut">
                    <span class="sh-num eh-data">03</span>
                    <span class="sh-arrow">↗</span>
                    <span class="sh-label">페이스 도구</span>
                    <span class="sh-meta">목표 페이스 계산</span>
                </a>
                <a href="/posts" class="v-card shortcut">
                    <span class="sh-num eh-data">04</span>
                    <span class="sh-arrow">↗</span>
                    <span class="sh-label">커뮤니티</span>
                    <span class="sh-meta">훈련 일지 · 자유 게시판</span>
                </a>
            </div>
        </section>

        <!-- ── 03 · 알림 설정 ── -->
        <section class="mp-section">
            <div class="v-sechead">
                <span>
                    <span class="eh-micro" style="color: var(--text-faint)">03</span>
                    <span class="eh-h3" style="margin-left: var(--sp-2)">알림 설정</span>
                </span>
                <span class="eh-micro" style="color: var(--text-faint)">EMAIL / PUSH</span>
            </div>

            <form
                method="POST"
                class="notif-form"
                style="margin-top: var(--sp-4)"
                use:enhance={() => {
                    isSubmitting = true;
                    return async ({ update }) => {
                        isSubmitting = false;
                        await update();
                    };
                }}
            >
                <div class="v-table">
                    <!-- Table head -->
                    <div class="v-thead notif-head">
                        <span>유형</span>
                        <span style="display:none"></span>
                        <span style="text-align:center">EMAIL</span>
                    </div>
                    <!-- Single row (existing backend field) -->
                    <label class="v-trow notif-row">
                        <span>
                            <span class="notif-name">이메일 알림 수신</span>
                        </span>
                        <span class="notif-desc">대회 소식 · 일정 업데이트 · 이벤트 안내</span>
                        <span class="notif-toggle-wrap">
                            <span class="v-sw" class:on={emailUpdatesOptIn}>
                                <span class="knob"></span>
                            </span>
                            <input
                                type="checkbox"
                                name="email_updates_opt_in"
                                bind:checked={emailUpdatesOptIn}
                                class="sw-hidden"
                            />
                        </span>
                    </label>
                </div>

                <p class="notif-fine">
                    계정 보안 · 인증 등 필수 안내는 동의 여부와 관계없이 발송됩니다.
                </p>

                {#if successMessage}
                    <div class="status-bar ok">{successMessage}</div>
                {/if}
                {#if errors.profile || errors.email_updates_opt_in}
                    <div class="status-bar err">{errors.profile || errors.email_updates_opt_in}</div>
                {/if}

                <div style="margin-top: var(--sp-4); display: flex; justify-content: flex-end">
                    <button type="submit" class="save-btn" disabled={isSubmitting}>
                        {isSubmitting ? '저장 중…' : '저장'}
                    </button>
                </div>
            </form>
        </section>

        <!-- ── 04 · 계정 관리 ── -->
        <section class="mp-section">
            <div class="v-sechead">
                <span>
                    <span class="eh-micro" style="color: var(--text-faint)">04</span>
                    <span class="eh-h3" style="margin-left: var(--sp-2)">계정 관리</span>
                </span>
                <span class="eh-micro" style="color: var(--text-faint)">SIGN OUT / DELETE</span>
            </div>

            <div class="danger-box" style="margin-top: var(--sp-4)">
                <!-- Logout -->
                <div class="danger-row">
                    <div>
                        <div class="danger-name">로그아웃</div>
                        <p class="danger-desc">이 기기에서 로그아웃합니다. 저장한 대회와 설정은 유지됩니다.</p>
                    </div>
                    <form method="POST" action="/auth/logout">
                        <button type="submit" class="ghost-btn">로그아웃</button>
                    </form>
                </div>
                <!-- Delete account -->
                <div class="danger-row danger-row--last">
                    <div>
                        <div class="danger-name">계정 삭제</div>
                        <p class="danger-desc">모든 기록·관심 대회·커뮤니티 활동이 영구 삭제됩니다. 30일 이내 복구할 수 없습니다.</p>
                    </div>
                    <button type="button" class="danger-btn">계정 삭제</button>
                </div>
            </div>
        </section>

    </div>
</div>

<style>
    .mp-wrap {
        padding-top: var(--sp-10);
        padding-bottom: var(--sp-20);
    }
    .mp-page {
        max-width: 980px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        gap: var(--sp-12);
    }

    /* ── Header ── */
    .mp-hd {
        display: flex;
        flex-direction: column;
        gap: var(--sp-3);
        padding-bottom: var(--sp-6);
        border-bottom: var(--border-rule);
    }
    .mp-lead {
        color: var(--text-muted);
        max-width: 540px;
        margin: 0;
    }

    /* ── Identity strip ── */
    .identity {
        display: grid;
        grid-template-columns: 1.4fr 1fr 1fr;
        border: 1px solid var(--ink-900);
        background: var(--paper-0);
    }
    .identity > div {
        padding: 22px 24px;
        border-right: var(--border-hair);
        min-height: 116px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        gap: var(--sp-2);
    }
    .identity > div:last-child { border-right: 0; }

    .id-main { /* first cell: wider */ }
    .id-row {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .id-avatar {
        width: 52px;
        height: 52px;
        flex: none;
        border: 1.5px solid var(--ink-900);
        border-radius: var(--r-1);
        display: grid;
        place-items: center;
        font-size: 22px;
        font-weight: 800;
        background: var(--paper-50);
        color: var(--text-strong);
    }
    .id-avatar--img {
        object-fit: cover;
        font-size: 0;
    }
    .id-name {
        display: block;
        font-size: 20px;
        font-weight: 700;
        letter-spacing: var(--track-heading);
        line-height: 1.1;
        color: var(--text-strong);
    }
    .id-email {
        display: block;
        font-size: 12px;
        color: var(--text-muted);
        margin-top: 4px;
    }
    .id-badges {
        display: flex;
        align-items: center;
        gap: var(--sp-2);
        flex-wrap: wrap;
    }

    /* Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        height: 22px;
        padding: 0 8px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        border-radius: var(--r-2);
    }
    .badge.ok { color: var(--positive); background: var(--positive-bg); }
    .badge.warn { color: var(--danger); background: var(--danger-bg); }

    /* Stat cells */
    .id-stat { }
    .stat-label {
        font-size: var(--text-micro);
        font-weight: var(--w-strong);
        letter-spacing: var(--track-micro);
        text-transform: uppercase;
        color: var(--text-muted);
    }
    .stat-val {
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1;
        color: var(--text-strong);
        font-variant-numeric: tabular-nums;
    }
    .stat-val.accent { color: var(--accent-strong); }
    .stat-note {
        font-size: 12px;
        color: var(--text-muted);
    }

    /* ── Alert bar ── */
    .alert-bar {
        display: flex;
        align-items: center;
        gap: var(--sp-5);
        padding: 18px 22px;
        border: 1px solid var(--danger);
        border-left-width: 3px;
        background: var(--danger-bg);
        flex-wrap: wrap;
    }
    .alert-body { flex: 1; display: flex; flex-direction: column; gap: var(--sp-1); min-width: 0; }
    .alert-title {
        font-size: 15px;
        font-weight: 700;
        color: var(--text-strong);
    }
    .alert-desc {
        font-size: 13px;
        color: var(--text-muted);
        line-height: 1.5;
        margin: 0;
        word-break: keep-all;
    }
    .alert-cta {
        display: inline-flex;
        align-items: center;
        gap: var(--sp-2);
        padding: 10px 16px;
        background: var(--danger);
        color: #fff;
        font-size: 13px;
        font-weight: 700;
        text-decoration: none;
        flex-shrink: 0;
        border-radius: var(--r-1);
    }
    .alert-cta:hover { background: color-mix(in oklch, var(--danger) 85%, black); }

    /* ── Section wrapper ── */
    .mp-section { display: flex; flex-direction: column; }

    /* ── Account info table ── */
    .info-row {
        display: grid;
        grid-template-columns: 110px 1fr auto;
        align-items: center;
        gap: var(--sp-5);
        padding: 16px 22px;
        border-bottom: var(--border-hair);
    }
    .info-row--last { border-bottom: 0; }
    .info-key { color: var(--text-faint); }
    .info-val {
        font-size: var(--text-body-sm);
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: var(--sp-2);
        flex-wrap: wrap;
        min-width: 0;
        color: var(--text-strong);
    }
    .info-note {
        font-size: 12px;
        color: var(--text-faint);
    }
    .info-action {
        font-size: 12px;
        font-weight: var(--w-strong);
        color: var(--text-muted);
        text-decoration: none;
        border-bottom: 1px solid var(--line);
        white-space: nowrap;
        cursor: pointer;
        background: transparent;
        border-top: 0;
        border-left: 0;
        border-right: 0;
        padding: 0;
        font-family: var(--font-sans);
    }
    .info-action:hover { color: var(--text-strong); border-bottom-color: var(--ink-900); }
    .info-action.faint { color: var(--text-faint); cursor: default; }

    /* ── Shortcuts grid ── */
    .shortcuts {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: var(--sp-3);
        margin-top: var(--sp-4);
    }
    .shortcut {
        padding: 18px 20px;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        position: relative;
        text-decoration: none;
        color: var(--text-strong);
    }
    .shortcut:hover { border-color: var(--ink-900); transform: translateY(-2px); box-shadow: var(--shadow-card-hover); }
    .sh-num {
        font-size: var(--text-micro);
        font-weight: var(--w-strong);
        letter-spacing: var(--track-micro);
        color: var(--text-faint);
    }
    .sh-arrow {
        position: absolute;
        top: 14px;
        right: 18px;
        color: var(--text-faint);
        font-size: 15px;
    }
    .shortcut:hover .sh-arrow { color: var(--text-strong); }
    .sh-label {
        font-size: 16px;
        font-weight: 700;
        letter-spacing: var(--track-heading);
        margin-top: auto;
        color: var(--text-strong);
    }
    .sh-meta {
        font-size: 12px;
        color: var(--text-muted);
        margin-top: var(--sp-1);
        line-height: 1.45;
    }

    /* ── Notifications ── */
    .notif-head {
        grid-template-columns: 1.4fr 1fr 80px;
    }
    .notif-row {
        grid-template-columns: 1.4fr 1fr 80px;
        cursor: pointer;
    }
    .notif-name {
        font-size: var(--text-body-sm);
        font-weight: var(--w-strong);
        color: var(--text-strong);
    }
    .notif-desc {
        font-size: 12px;
        color: var(--text-muted);
        line-height: 1.5;
    }
    .notif-toggle-wrap {
        display: flex;
        justify-content: center;
        align-items: center;
        position: relative;
    }
    /* DS switch */
    .v-sw {
        width: 38px;
        height: 22px;
        border: 1px solid var(--line);
        background: var(--paper-50);
        position: relative;
        border-radius: var(--r-1);
        transition: background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
        flex-shrink: 0;
    }
    .v-sw .knob {
        position: absolute;
        top: 2px;
        left: 2px;
        width: 16px;
        height: 16px;
        background: var(--ink-300);
        border-radius: var(--r-1);
        transition: left var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out);
    }
    .v-sw.on { background: var(--accent); border-color: var(--accent-strong); }
    .v-sw.on .knob { left: 18px; background: #fff; }
    .sw-hidden {
        position: absolute;
        inset: 0;
        opacity: 0;
        cursor: pointer;
        width: 100%;
        height: 100%;
        margin: 0;
    }

    .notif-fine {
        margin: var(--sp-3) 0 0;
        font-size: 12px;
        color: var(--text-faint);
        line-height: 1.6;
        word-break: keep-all;
    }
    .status-bar {
        margin-top: var(--sp-3);
        padding: 10px 14px;
        font-size: 13px;
        border: 1px solid;
        line-height: 1.5;
        word-break: keep-all;
        border-radius: var(--r-1);
    }
    .status-bar.ok {
        color: var(--positive);
        border-color: var(--positive);
        background: var(--positive-bg);
    }
    .status-bar.err {
        color: var(--danger);
        border-color: var(--danger);
        background: var(--danger-bg);
    }
    .save-btn {
        height: 34px;
        padding: 0 16px;
        background: var(--ink-900);
        color: var(--paper-0);
        border: 1px solid var(--ink-900);
        font-size: 13px;
        font-weight: var(--w-strong);
        cursor: pointer;
        font-family: var(--font-sans);
        border-radius: var(--r-1);
    }
    .save-btn:hover:not(:disabled) { background: var(--ink-700); border-color: var(--ink-700); }
    .save-btn:disabled { cursor: not-allowed; opacity: 0.5; }

    /* ── Danger zone ── */
    .danger-box {
        border: var(--border-hair);
        background: var(--paper-50);
    }
    .danger-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--sp-5);
        padding: 16px 22px;
        border-bottom: var(--border-hair);
        flex-wrap: wrap;
    }
    .danger-row--last { border-bottom: 0; }
    .danger-name {
        font-size: var(--text-body-sm);
        font-weight: var(--w-strong);
        color: var(--text-strong);
    }
    .danger-desc {
        font-size: 12px;
        color: var(--text-muted);
        margin: var(--sp-1) 0 0;
        line-height: 1.5;
        max-width: 520px;
        word-break: keep-all;
    }
    .ghost-btn {
        height: 34px;
        padding: 0 14px;
        font-size: 13px;
        font-weight: var(--w-strong);
        background: transparent;
        border: 1px solid var(--line);
        color: var(--text-muted);
        cursor: pointer;
        font-family: var(--font-sans);
        border-radius: var(--r-1);
        transition: border-color var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
    }
    .ghost-btn:hover { border-color: var(--ink-900); color: var(--text-strong); }
    .danger-btn {
        height: 34px;
        padding: 0 14px;
        font-size: 13px;
        font-weight: var(--w-strong);
        background: transparent;
        border: 1px solid var(--danger);
        color: var(--danger);
        cursor: pointer;
        font-family: var(--font-sans);
        border-radius: var(--r-1);
    }
    .danger-btn:hover { background: var(--danger-bg); }

    /* ── Responsive ── */
    @media (max-width: 900px) {
        .identity { grid-template-columns: 1fr 1fr; }
        .identity > .id-main { grid-column: 1 / -1; border-bottom: var(--border-hair); }
        .identity > .id-stat:first-of-type { border-right: var(--border-hair); }
        .shortcuts { grid-template-columns: 1fr 1fr; }
    }
    @media (max-width: 768px) {
        .mp-wrap { padding-top: var(--sp-6); }
        .info-row { grid-template-columns: 1fr auto; }
        .info-key { display: none; }
        .notif-row, .notif-head { grid-template-columns: 1fr 80px; }
        .notif-desc { display: none; }
    }
    @media (max-width: 540px) {
        .shortcuts { grid-template-columns: 1fr 1fr; }
    }
</style>
