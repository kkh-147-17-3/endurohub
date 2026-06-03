<script lang="ts">
    import { enhance, applyAction } from '$app/forms';
    import ProgressBar from '$lib/components/ProgressBar.svelte';
    import type { AuthUser } from '$lib/types';

    let { data, form } = $props();

    /* ─────────── Static data ─────────── */
    type SportMeta = { value: string; code: string; ko: string; tag: string };
    const SPORTS: SportMeta[] = [
        { value: 'running', code: 'RUN', ko: '러닝', tag: 'run' },
        { value: 'trail_running', code: 'TRL', ko: '트레일', tag: 'trl' },
        { value: 'cycling', code: 'CYCLE', ko: '자전거', tag: 'cycle' },
        { value: 'swimming', code: 'SWIM', ko: '수영', tag: 'swim' },
        { value: 'triathlon', code: 'TRI', ko: '철인3종', tag: 'tri' },
    ];
    const SPORT_BY_VALUE = Object.fromEntries(SPORTS.map((s) => [s.value, s]));

    const DISTANCES: Record<string, string[]> = {
        running: ['5K', '10K', '하프', '풀코스', '울트라'],
        trail_running: ['10K↓', '10–30K', '30–50K', '50–100K', '100K↑'],
        cycling: ['그란폰도', '100K', '200K', 'MTB XC', 'MTB DH'],
        swimming: ['오픈워터 1.5K', '오픈워터 3K', '오픈워터 5K', '수영장 단축', '수영장 장축'],
        triathlon: ['스프린트', '올림픽', '하프(70.3)', '풀(140.6)'],
    };

    const REGIONS = [
        '서울', '경기', '인천', '부산', '대구', '광주', '대전', '울산', '세종',
        '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주',
    ];

    const STEP_LABELS = ['EMAIL', 'NICKNAME', 'SPORT', 'REGION', 'RECORDS'];

    /* ─────────── Flow state ─────────── */
    let user = $state<AuthUser | null>(data.user);
    // 0 EMAIL · 1 NICKNAME · 2 SPORT · 3 REGION · 4 RECORDS · 5 DONE
    let step = $state<number>(data.startStep ?? 0);

    // Email step
    let email = $state(data.user?.email ?? '');
    let code = $state('');
    let emailUpdatesOptIn = $state(!!data.user?.emailUpdatesOptIn);
    let resendIn = $state(0);
    let isSending = $state(false);
    let isVerifying = $state(false);
    let otpInput = $state<HTMLInputElement | null>(null);

    // Nickname step
    let nickname = $state(data.user?.nickname ?? '');
    let isSavingNick = $state(false);

    // Sport / region steps
    let sports = $state<string[]>([...(data.user?.preferredSports ?? [])]);
    let regions = $state<string[]>([...(data.user?.preferredRegions ?? [])]);

    // Records step
    type DraftRecord = { id: number; sport: string; distance: string; name: string; date: string; time: string };
    let records = $state<DraftRecord[]>([]);
    let adding = $state(true);
    let draft = $state({ sport: data.user?.preferredSports?.[0] ?? 'running', distance: '', name: '', date: '', h: '', m: '', s: '' });
    let isSubmitting = $state(false);
    let recordSeq = 0;

    /* ─────────── Derived ─────────── */
    const emailValid = $derived(/.+@.+\..+/.test(email));
    const codeFilled = $derived(code.length === 6);
    const nickOk = $derived(nickname.trim().length >= 2 && nickname.trim().length <= 50);
    const draftDistances = $derived(DISTANCES[draft.sport] || []);
    const isCustomDistance = $derived(
        draft.distance === '__custom__' || (!!draft.distance && !draftDistances.includes(draft.distance))
    );
    const canSaveRecord = $derived(
        !!draft.distance && draft.distance !== '__custom__' && (!!draft.h || !!draft.m || !!draft.s)
    );

    const sendErrors = $derived(flatten(form?.action === 'sendEmail' ? form?.sendErrors : undefined));
    const sendMessage = $derived(form?.action === 'sendEmail' ? (form?.sendMessage ?? '') : '');
    const verifyErrors = $derived(flatten(form?.action === 'verifyEmail' ? form?.verifyErrors : undefined));
    const nicknameErrors = $derived(flatten(form?.action === 'setNickname' ? form?.nicknameErrors : undefined));
    const completeErrors = $derived(flatten(form?.action === 'complete' ? form?.errors : undefined));

    function flatten(errs: Record<string, string[]> | undefined): Record<string, string> {
        if (!errs) return {};
        const flat: Record<string, string> = {};
        for (const [key, msgs] of Object.entries(errs)) flat[key] = Array.isArray(msgs) ? msgs[0] : (msgs as string);
        return flat;
    }

    /* ─────────── Navigation ─────────── */
    function goTo(n: number) {
        step = Math.max(0, Math.min(4, n));
    }
    function advanceFromEmail() {
        if (!user?.nickname) step = 1;
        else if (!user?.onboardingCompleted) step = 2;
        else step = 5;
    }
    function advanceFromNickname() {
        step = user?.onboardingCompleted ? 5 : 2;
    }

    /* ─────────── Email ─────────── */
    function normalizeOtp(raw: string): string {
        const ascii = raw.replace(/[０-９]/g, (c) => String.fromCharCode(c.charCodeAt(0) - 0xff10 + 0x30));
        return ascii.replace(/\D/g, '').slice(0, 6);
    }
    let resendTimer: ReturnType<typeof setInterval> | null = null;
    function startResendCountdown() {
        resendIn = 120;
        if (resendTimer) clearInterval(resendTimer);
        resendTimer = setInterval(() => {
            resendIn -= 1;
            if (resendIn <= 0 && resendTimer) {
                clearInterval(resendTimer);
                resendTimer = null;
            }
        }, 1000);
    }
    const resendLabel = $derived(
        `${Math.floor(resendIn / 60)}:${String(resendIn % 60).padStart(2, '0')}`
    );

    /* ─────────── Sport / region ─────────── */
    function toggleSport(value: string) {
        sports = sports.includes(value) ? sports.filter((s) => s !== value) : [...sports, value];
    }
    function toggleRegion(r: string) {
        regions = regions.includes(r) ? regions.filter((x) => x !== r) : [...regions, r];
    }

    /* ─────────── Records ─────────── */
    function setDraftSport(value: string) {
        draft = { ...draft, sport: value, distance: '' };
    }
    function pickDistance(d: string) {
        draft = { ...draft, distance: d };
    }
    function toggleCustomDistance() {
        draft = { ...draft, distance: isCustomDistance ? '' : '__custom__' };
    }
    function resetDraft() {
        draft = { sport: sports[0] ?? 'running', distance: '', name: '', date: '', h: '', m: '', s: '' };
    }
    function saveRecord() {
        if (!canSaveRecord) return;
        const time = `${(draft.h || '0').padStart(2, '0')}:${(draft.m || '00').padStart(2, '0')}:${(draft.s || '00').padStart(2, '0')}`;
        records = [
            ...records,
            {
                id: ++recordSeq,
                sport: draft.sport,
                distance: draft.distance,
                name: draft.name.trim() || '—',
                date: draft.date.trim() || '—',
                time,
            },
        ];
        resetDraft();
        adding = false;
    }
    function removeRecord(id: number) {
        records = records.filter((r) => r.id !== id);
    }

    // Serialised payload for the `complete` action — backend shape.
    const recordsPayload = $derived(
        JSON.stringify(
            records.map((r) => {
                const [h, m, s] = r.time.split(':').map((n) => parseInt(n, 10) || 0);
                return {
                    sport: r.sport,
                    distance: r.distance,
                    name: r.name === '—' ? '' : r.name,
                    record_date: r.date === '—' ? '' : r.date,
                    hours: h,
                    minutes: m,
                    seconds: s,
                };
            })
        )
    );

    function sportMeta(value: string): SportMeta {
        return SPORT_BY_VALUE[value] ?? { value, code: value.toUpperCase(), ko: value, tag: 'run' };
    }
</script>

<svelte:head>
    <title>endurohub · 온보딩</title>
    <meta name="robots" content="noindex" />
</svelte:head>

<ProgressBar active={isSending || isVerifying || isSavingNick || isSubmitting} />

<div class="ob-page">
    {#if step <= 4}
        <div class="step-tabs">
            {#each STEP_LABELS as label, i}
                <button
                    type="button"
                    class="tab"
                    class:on={i === step}
                    class:done={i < step}
                    onclick={() => goTo(i)}
                >
                    {String(i + 1).padStart(2, '0')} · {label}
                </button>
            {/each}
        </div>
    {/if}

    {#if step >= 2 && step <= 4}
        <div class="progress-row">
            <div class="progress-track">
                <div class="progress-fill" style="width: {((step - 1) / 3) * 100}%"></div>
            </div>
            <div class="progress-label"><b>{step - 1}</b> / 3</div>
        </div>
    {/if}

    <!-- ─────────── STEP 01 · EMAIL ─────────── -->
    {#if step === 0}
        <div class="eyebrow">STEP 01 · EMAIL</div>
        <h1 class="title">이메일 인증</h1>
        <p class="subtitle">
            {#if data.hasPendingSocialLogin}
                소셜 로그인 가입을 완료하려면 이메일 인증이 필요합니다.
            {:else}
                인증 코드를 받을 이메일을 확인하고 인증을 완료해주세요.
            {/if}
        </p>

        <div class="card">
            <div class="step-row"><div class="step-num">1</div><h3>이메일 입력</h3></div>
            <div class="field-label">이메일</div>
            <form
                method="POST"
                action="?/sendEmail"
                use:enhance={() => {
                    isSending = true;
                    return async ({ result }) => {
                        isSending = false;
                        await applyAction(result);
                        if (result.type === 'success' && (result.data as { sendMessage?: string })?.sendMessage) {
                            startResendCountdown();
                        }
                    };
                }}
            >
                <input
                    class="input"
                    name="email"
                    placeholder="you@example.com"
                    autocomplete="email"
                    bind:value={email}
                />
                {#if sendErrors.email}
                    <div class="field-help err">{sendErrors.email}</div>
                {:else}
                    <div class="field-help">인증 코드는 이 주소로 발송됩니다.</div>
                {/if}

                <label class="consent">
                    <input type="checkbox" name="email_updates_opt_in" bind:checked={emailUpdatesOptIn} />
                    <span class="cb"></span>
                    <span class="consent-body">
                        <span class="tag">선택</span>
                        대회 소식, 업데이트, 이벤트 등 이메일 알림 수신에 동의합니다.
                        <span class="sub">계정 관련 중요 안내는 동의 여부와 관계없이 발송됩니다.</span>
                    </span>
                </label>

                <div style="height: 14px"></div>
                <button
                    class="btn {emailValid && resendIn === 0 ? 'primary' : 'muted'}"
                    disabled={!emailValid || isSending || resendIn > 0}
                >
                    {resendIn > 0 ? `발송 완료 · ${resendLabel} 후 재전송` : '인증 코드 발송'}
                    <span class="arrow">→</span>
                </button>
                {#if sendMessage}
                    <div class="send-ok"><span class="send-ok-dot"></span>{sendMessage}</div>
                {/if}
            </form>

            <div class="divider"></div>

            <div class="step-row"><div class="step-num">2</div><h3>인증 코드 입력</h3></div>
            <div class="field-label">인증 코드 <span class="hint">6자리 숫자</span></div>
            <form
                method="POST"
                action="?/verifyEmail"
                use:enhance={() => {
                    isVerifying = true;
                    return async ({ result }) => {
                        isVerifying = false;
                        await applyAction(result);
                        if (result.type === 'success') {
                            const u = (result.data as { user?: AuthUser })?.user;
                            if (u) {
                                user = u;
                                advanceFromEmail();
                            }
                        }
                    };
                }}
            >
                <input type="hidden" name="code" value={code} />
                <input type="hidden" name="email_updates_opt_in" value={emailUpdatesOptIn ? 'true' : 'false'} />

                <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
                <div class="otp" onclick={() => otpInput?.focus()}>
                    {#each Array.from({ length: 6 }) as _, i}
                        <div class="cell" class:filled={!!code[i]}>{code[i] || '0'}</div>
                    {/each}
                    <input
                        bind:this={otpInput}
                        class="otp-hidden"
                        value={code}
                        inputmode="numeric"
                        autocomplete="one-time-code"
                        oninput={(e) => (code = normalizeOtp(e.currentTarget.value))}
                    />
                </div>
                {#if verifyErrors.code}
                    <div class="field-help err">{verifyErrors.code}</div>
                {/if}

                <div style="height: 18px"></div>
                <button class="btn {codeFilled ? 'primary' : 'muted'}" disabled={!codeFilled || isVerifying}>
                    인증 확인 <span class="arrow">→</span>
                </button>
            </form>
        </div>

        <div class="footer-link">
            <a href="/auth/login" class="text-link">← 로그인 다시 하기</a>
        </div>
    {/if}

    <!-- ─────────── STEP 02 · NICKNAME ─────────── -->
    {#if step === 1}
        <div class="eyebrow">STEP 02 · NICKNAME</div>
        <h1 class="title">닉네임 설정</h1>
        <p class="subtitle">커뮤니티에서 사용할 닉네임을 정해주세요.</p>

        <div class="card">
            <form
                method="POST"
                action="?/setNickname"
                use:enhance={() => {
                    isSavingNick = true;
                    return async ({ result }) => {
                        isSavingNick = false;
                        await applyAction(result);
                        if (result.type === 'success') {
                            const u = (result.data as { user?: AuthUser })?.user;
                            if (u) {
                                user = u;
                                advanceFromNickname();
                            }
                        }
                    };
                }}
            >
                <div class="field-label mono-label">NICKNAME *</div>
                <input
                    class="input"
                    name="nickname"
                    placeholder="2~50자, 한글/영문/숫자"
                    minlength="2"
                    maxlength="50"
                    bind:value={nickname}
                />
                {#if nicknameErrors.nickname}
                    <div class="field-help err">{nicknameErrors.nickname}</div>
                {:else}
                    <div class="field-help">한글, 영문, 숫자, 밑줄(_), 하이픈(-) 사용 가능</div>
                {/if}
                <div style="height: 18px"></div>
                <button class="btn {nickOk ? 'primary' : 'muted'}" disabled={!nickOk || isSavingNick}>
                    설정 완료 <span class="arrow">→</span>
                </button>
            </form>
        </div>
    {/if}

    <!-- ─────────── STEP 03 · SPORT ─────────── -->
    {#if step === 2}
        <div class="eyebrow">STEP 03 · SPORT</div>
        <h1 class="title">어떤 종목에<br />관심 있으세요?</h1>
        <p class="subtitle">관심 종목을 선택하면 맞춤 대회 정보를 받을 수 있어요</p>

        <div class="sport-list">
            {#each SPORTS as s}
                <button type="button" class="sport-row" class:on={sports.includes(s.value)} onclick={() => toggleSport(s.value)}>
                    <div class="code">{s.code}</div>
                    <div class="name">{s.ko}</div>
                    <div class="cb"></div>
                </button>
            {/each}
        </div>

        <button class="btn {sports.length ? 'primary' : 'muted'}" onclick={() => (step = 3)}>
            {sports.length ? '다음' : '건너뛰기'} <span class="arrow">→</span>
        </button>
        <div class="footer-link">
            <button type="button" class="text-link" onclick={() => (step = 3)}>나중에 설정할게요</button>
        </div>
    {/if}

    <!-- ─────────── STEP 04 · REGION ─────────── -->
    {#if step === 3}
        <div class="eyebrow">STEP 04 · REGION</div>
        <h1 class="title">주로 어디서<br />활동하세요?</h1>
        <p class="subtitle">관심 지역의 대회를 우선 추천해드릴게요</p>

        <div class="region-grid">
            {#each REGIONS as r}
                <button type="button" class="chip" class:on={regions.includes(r)} onclick={() => toggleRegion(r)}>{r}</button>
            {/each}
        </div>

        <div class="selected-bar">
            <span class="key">SELECTED</span>
            <span class="vals">{regions.length ? regions.join('  ·  ') : '(없음)'}</span>
        </div>

        <div class="button-row">
            <button type="button" class="btn back" onclick={() => (step = 2)}>← 이전</button>
            <button type="button" class="btn primary" onclick={() => (step = 4)}>다음 <span class="arrow">→</span></button>
        </div>
        <div class="footer-link">
            <button type="button" class="text-link" onclick={() => (step = 4)}>나중에 설정할게요</button>
        </div>
    {/if}

    <!-- ─────────── STEP 05 · RECORDS ─────────── -->
    {#if step === 4}
        <div class="eyebrow">STEP 05 · RECORDS</div>
        <h1 class="title">최근 대회 기록을<br />알려주세요</h1>
        <p class="subtitle">
            최근 1년 이내 PB나 가장 기억에 남는 기록을 입력하면, 시즌 플래너와 페이스 도구를 자동으로 보정해드려요.
        </p>

        <div class="records-intro">
            <div class="cell"><div class="key">01 · USE</div><div class="val">시즌 페이스 자동 보정</div></div>
            <div class="cell"><div class="key">02 · USE</div><div class="val">맞춤 대회 추천 강화</div></div>
            <div class="cell"><div class="key">03 · PRIVACY</div><div class="val">기본 비공개 · 본인만 열람</div></div>
        </div>

        {#if records.length > 0}
            <div class="summary-strip">
                <span class="key">ENTERED</span>
                <span class="stat"><b>{records.length}</b> 개</span>
                <div class="sep"></div>
                <span class="key">SPORTS</span>
                <span class="stat">{[...new Set(records.map((r) => sportMeta(r.sport).code))].join(' · ')}</span>
            </div>

            <div class="records-list">
                <div class="records-head">
                    <div>SPORT</div><div>대회</div><div>거리</div><div>날짜</div>
                    <div style="text-align:right">기록</div><div></div>
                </div>
                {#each records as r (r.id)}
                    <div class="record-item">
                        <div class="record-tag {sportMeta(r.sport).tag}">{sportMeta(r.sport).code}</div>
                        <div class="record-name">{r.name}</div>
                        <div class="record-dist">{r.distance}</div>
                        <div class="record-date">{r.date}</div>
                        <div class="record-time" style="text-align:right">{r.time}</div>
                        <button type="button" class="record-del" onclick={() => removeRecord(r.id)} aria-label="삭제">×</button>
                    </div>
                {/each}
            </div>
        {/if}

        {#if adding}
            <div class="add-form">
                <div class="add-form-head">
                    <div class="add-form-title">+ 기록 추가</div>
                    {#if records.length > 0}
                        <button type="button" class="text-link" onclick={() => (adding = false)}>접기</button>
                    {/if}
                </div>

                <div class="add-form-row">
                    <div class="field-label">종목 *</div>
                    <div class="sport-chips">
                        {#each SPORTS as s}
                            <button type="button" class="sport-chip" class:on={draft.sport === s.value} onclick={() => setDraftSport(s.value)}>
                                {s.code} <span class="ko">{s.ko}</span>
                            </button>
                        {/each}
                    </div>
                </div>

                <div class="add-form-row">
                    <div class="field-label">거리 / 종목 카테고리 * <span class="hint">자주 쓰는 카테고리를 고르거나 직접 입력</span></div>
                    <div class="dist-chips">
                        {#each draftDistances as d}
                            <button type="button" class="dist-chip" class:on={draft.distance === d} onclick={() => pickDistance(d)}>{d}</button>
                        {/each}
                        <button type="button" class="dist-chip custom-trigger" class:on={isCustomDistance} onclick={toggleCustomDistance}>
                            + 직접 입력
                        </button>
                    </div>
                    {#if isCustomDistance}
                        <!-- svelte-ignore a11y_autofocus -->
                        <input
                            class="input dist-custom-input"
                            placeholder="예: 21.0975K, 100마일, 2.4mi 수영 등"
                            autofocus
                            value={draft.distance === '__custom__' ? '' : draft.distance}
                            oninput={(e) => (draft = { ...draft, distance: e.currentTarget.value })}
                            onblur={() => { if (draft.distance === '__custom__') draft = { ...draft, distance: '' }; }}
                        />
                    {/if}
                </div>

                <div class="add-form-row">
                    <div class="field-label">기록 (시:분:초) *</div>
                    <div class="time-input">
                        <input placeholder="HH" maxlength="2" value={draft.h} oninput={(e) => (draft = { ...draft, h: e.currentTarget.value.replace(/\D/g, '') })} />
                        <span class="colon">:</span>
                        <input placeholder="MM" maxlength="2" value={draft.m} oninput={(e) => (draft = { ...draft, m: e.currentTarget.value.replace(/\D/g, '') })} />
                        <span class="colon">:</span>
                        <input placeholder="SS" maxlength="2" value={draft.s} oninput={(e) => (draft = { ...draft, s: e.currentTarget.value.replace(/\D/g, '') })} />
                    </div>
                </div>

                <div class="add-form-row two">
                    <div>
                        <div class="field-label">대회명 <span class="hint">선택</span></div>
                        <input class="input" placeholder="예: 서울국제마라톤 2025" bind:value={draft.name} />
                    </div>
                    <div>
                        <div class="field-label">대회 날짜 <span class="hint">선택</span></div>
                        <input class="input" placeholder="2025-03-16" bind:value={draft.date} />
                    </div>
                </div>

                <div class="add-form-actions">
                    <button type="button" class="btn ghost tiny" onclick={() => { resetDraft(); if (records.length > 0) adding = false; }}>취소</button>
                    <button type="button" class="btn tiny {canSaveRecord ? 'primary' : 'muted'}" disabled={!canSaveRecord} onclick={saveRecord}>
                        저장 <span class="arrow">→</span>
                    </button>
                </div>
            </div>
        {:else}
            <button type="button" class="add-trigger" onclick={() => (adding = true)}>
                <span class="plus">+</span> 기록 더 추가하기
            </button>
        {/if}

        {#if completeErrors.profile || completeErrors.preferred_sports || completeErrors.preferred_regions}
            <div class="field-help err">{completeErrors.profile || completeErrors.preferred_sports || completeErrors.preferred_regions}</div>
        {/if}

        <form
            method="POST"
            action="?/complete"
            use:enhance={() => {
                isSubmitting = true;
                return async ({ result }) => {
                    isSubmitting = false;
                    await applyAction(result);
                    if (result.type === 'success' && (result.data as { done?: boolean })?.done) {
                        if ((result.data as { user?: AuthUser })?.user) user = (result.data as { user: AuthUser }).user;
                        step = 5;
                    }
                };
            }}
        >
            <input type="hidden" name="preferred_sports" value={sports.join(',')} />
            <input type="hidden" name="preferred_regions" value={regions.join(',')} />
            <input type="hidden" name="records" value={recordsPayload} />

            <div class="button-row">
                <button type="button" class="btn back" onclick={() => (step = 3)}>← 이전</button>
                <button type="submit" class="btn primary" disabled={isSubmitting}>
                    {records.length > 0 ? `${records.length}개 기록으로 시작하기` : '시작하기'} <span class="arrow">→</span>
                </button>
            </div>
            <div class="footer-link">
                <button type="submit" class="text-link" disabled={isSubmitting}>나중에 입력할게요</button>
            </div>
        </form>
    {/if}

    <!-- ─────────── DONE ─────────── -->
    {#if step === 5}
        <div class="done-wrap">
            <div class="done-mark">✓</div>
            <div class="eyebrow">SETUP COMPLETE</div>
            <h1 class="title" style="text-align:center">준비 완료</h1>
            <p class="subtitle done-sub">입력하신 정보로 맞춤 대시보드를 구성했어요. 캘린더에서 곧 열릴 대회를 확인해보세요.</p>

            <div class="records-intro done-summary">
                <div class="cell">
                    <div class="key">SPORTS</div>
                    <div class="val">{sports.length ? sports.map((s) => sportMeta(s).ko).join(' · ') : '—'}</div>
                </div>
                <div class="cell">
                    <div class="key">REGIONS</div>
                    <div class="val">{regions.length ? regions.join(' · ') : '—'}</div>
                </div>
                <div class="cell">
                    <div class="key">RECORDS</div>
                    <div class="val">{records.length}개 등록</div>
                </div>
            </div>

            <div style="height: 24px"></div>
            <a href="/calendar" class="btn primary done-cta">캘린더로 이동 <span class="arrow">→</span></a>
        </div>
    {/if}
</div>

<style>
    .ob-page {
        max-width: 720px;
        margin: 0 auto;
        padding: 56px 24px 120px;
    }

    /* Step tabs */
    .step-tabs {
        display: flex;
        border: 1px solid var(--arena-line-soft);
        margin-bottom: 40px;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        letter-spacing: 0.14em;
    }
    .step-tabs .tab {
        flex: 1;
        padding: 10px 8px;
        text-align: center;
        color: var(--arena-ink-mute);
        border: 0;
        border-right: 1px solid var(--arena-line-soft);
        cursor: pointer;
        text-transform: uppercase;
        background: transparent;
        font: inherit;
        letter-spacing: inherit;
    }
    .step-tabs .tab:last-child { border-right: 0; }
    .step-tabs .tab.on { background: var(--arena-ink); color: var(--arena-paper); }
    .step-tabs .tab.done { color: var(--arena-accent-deep); }

    /* Progress */
    .progress-row { display: flex; align-items: center; gap: 16px; margin-bottom: 40px; }
    .progress-track { flex: 1; height: 2px; background: var(--arena-line-soft); position: relative; }
    .progress-fill { position: absolute; inset: 0 auto 0 0; background: var(--arena-ink); transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
    .progress-label { font-family: var(--arena-f-mono); font-size: 12px; color: var(--arena-ink-soft); white-space: nowrap; }
    .progress-label b { color: var(--arena-ink); font-weight: 500; }

    /* Eyebrow + title */
    .eyebrow {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        letter-spacing: 0.18em;
        color: var(--arena-accent-deep);
        text-transform: uppercase;
        margin-bottom: 16px;
    }
    .title {
        font-family: var(--arena-f-display);
        font-size: 44px;
        line-height: 1.1;
        margin: 0 0 16px;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: var(--arena-ink);
    }
    .subtitle {
        color: var(--arena-ink-soft);
        font-size: 15px;
        line-height: 1.55;
        margin: 0 0 40px;
        max-width: 480px;
    }

    /* Card */
    .card { border: 1px solid var(--arena-line); padding: 28px; background: var(--arena-paper); }
    .step-row { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
    .step-num {
        width: 26px; height: 26px;
        background: var(--arena-ink); color: var(--arena-paper);
        font-family: var(--arena-f-mono); font-size: 13px; font-weight: 500;
        display: grid; place-items: center;
    }
    .step-row h3 { margin: 0; font-size: 15px; font-weight: 600; color: var(--arena-ink); }
    .field-label { font-size: 13px; font-weight: 600; margin-bottom: 8px; color: var(--arena-ink); }
    .field-label.mono-label { font-family: var(--arena-f-mono); font-size: 11px; letter-spacing: 0.14em; color: var(--arena-ink-soft); }
    .field-label .hint { font-weight: 400; color: var(--arena-ink-mute); margin-left: 8px; font-family: var(--arena-f-mono); font-size: 11px; }
    .field-help { font-size: 12px; color: var(--arena-ink-mute); margin-top: 8px; }
    .field-help.err { color: var(--arena-urgent); }

    .input {
        width: 100%;
        border: 1px solid var(--arena-line);
        background: transparent;
        padding: 14px 16px;
        font-size: 14px;
        font-family: var(--arena-f-body);
        color: var(--arena-ink);
        outline: none;
    }
    .input::placeholder { color: var(--arena-ink-mute); }
    .input:focus { border-color: var(--arena-accent); box-shadow: inset 0 0 0 1px var(--arena-accent); }

    /* Buttons */
    .btn {
        display: inline-flex; align-items: center; justify-content: center; gap: 10px;
        padding: 16px 22px;
        border: 1px solid var(--arena-line);
        background: transparent;
        font-family: var(--arena-f-body);
        font-size: 14px; font-weight: 600;
        color: var(--arena-ink);
        width: 100%;
        cursor: pointer;
        text-decoration: none;
    }
    .btn.primary { background: var(--arena-ink); color: var(--arena-paper); border-color: var(--arena-ink); }
    .btn.primary .arrow { color: var(--arena-accent); }
    .btn.muted { background: var(--arena-ink-mute); color: var(--arena-paper); border-color: var(--arena-ink-mute); }
    .btn.muted .arrow { color: var(--arena-accent); }
    .btn:disabled { cursor: not-allowed; }
    .btn.ghost { background: transparent; border-color: var(--arena-line); }
    .btn.tiny { padding: 8px 12px; font-size: 12px; width: auto; font-weight: 500; }
    .arrow { font-family: var(--arena-f-mono); }

    .text-link {
        background: transparent; border: 0; padding: 6px 0;
        color: var(--arena-ink-soft); font-size: 13px; font-family: var(--arena-f-body);
        border-bottom: 1px solid var(--arena-line-soft);
        cursor: pointer;
    }
    .text-link:hover { color: var(--arena-ink); border-bottom-color: var(--arena-ink); }
    .text-link:disabled { opacity: 0.5; cursor: not-allowed; }

    /* Consent */
    .consent {
        display: flex; gap: 12px; align-items: flex-start;
        background: var(--arena-paper-alt);
        border: 1px solid var(--arena-line-soft);
        padding: 14px 16px;
        margin-top: 18px;
        cursor: pointer;
    }
    .consent input { position: absolute; opacity: 0; pointer-events: none; }
    .consent .cb {
        width: 18px; height: 18px; border: 1px solid var(--arena-line);
        background: var(--arena-paper); flex-shrink: 0;
        display: grid; place-items: center; margin-top: 2px;
    }
    .consent input:checked + .cb::after { content: ''; width: 10px; height: 10px; background: var(--arena-ink); }
    .consent-body { font-size: 13px; line-height: 1.55; color: var(--arena-ink); }
    .consent-body .tag {
        display: inline-block;
        background: var(--arena-ink); color: var(--arena-paper);
        font-family: var(--arena-f-mono); font-size: 10px;
        padding: 2px 6px; margin-right: 6px; vertical-align: 2px;
    }
    .consent-body .sub { display: block; margin-top: 4px; color: var(--arena-ink-mute); font-size: 12px; }

    .send-ok { margin-top: 12px; display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 500; color: var(--arena-accent-deep); }
    .send-ok-dot { width: 8px; height: 8px; background: var(--arena-accent); flex-shrink: 0; }

    /* OTP */
    .otp { display: flex; gap: 10px; border: 1px solid var(--arena-line); padding: 14px; justify-content: space-between; position: relative; cursor: text; }
    .otp .cell {
        flex: 1; aspect-ratio: 1 / 1.2;
        display: grid; place-items: center;
        font-family: var(--arena-f-mono); font-size: 28px; font-weight: 500;
        color: var(--arena-ink-mute);
        border-right: 1px dashed var(--arena-line-soft);
    }
    .otp .cell:last-of-type { border-right: 0; }
    .otp .cell.filled { color: var(--arena-ink); }
    .otp-hidden { position: absolute; opacity: 0; pointer-events: none; }

    .divider { height: 1px; background: var(--arena-line-soft); margin: 28px 0; }

    /* Sport list */
    .sport-list { display: flex; flex-direction: column; gap: 12px; margin-bottom: 32px; }
    .sport-row {
        display: grid; grid-template-columns: 80px 1fr 24px;
        align-items: center; gap: 16px;
        border: 1px solid var(--arena-line-soft);
        padding: 18px 20px;
        cursor: pointer;
        background: var(--arena-paper);
        text-align: left;
        font: inherit;
        transition: background 0.15s, border-color 0.15s;
    }
    .sport-row:hover { border-color: var(--arena-line); }
    .sport-row.on { border-color: var(--arena-ink); background: var(--arena-paper-alt); }
    .sport-row .code { font-family: var(--arena-f-mono); font-size: 12px; color: var(--arena-ink-soft); letter-spacing: 0.06em; }
    .sport-row .name { font-size: 16px; font-weight: 600; color: var(--arena-ink); }
    .sport-row .cb { width: 22px; height: 22px; border: 1px solid var(--arena-line); display: grid; place-items: center; background: var(--arena-paper); }
    .sport-row.on .cb { background: var(--arena-ink); border-color: var(--arena-ink); }
    .sport-row.on .cb::after { content: ''; width: 8px; height: 12px; border: solid var(--arena-paper); border-width: 0 2px 2px 0; transform: rotate(45deg) translate(-1px, -1px); }

    /* Region chips */
    .region-grid { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 22px; }
    .chip {
        border: 1px solid var(--arena-line-soft);
        background: var(--arena-paper);
        padding: 8px 14px;
        font-size: 13px; font-weight: 500;
        color: var(--arena-ink);
        cursor: pointer;
        font-family: var(--arena-f-body);
    }
    .chip:hover { border-color: var(--arena-line); }
    .chip.on { background: var(--arena-ink); color: var(--arena-paper); border-color: var(--arena-ink); }
    .selected-bar {
        border: 1px solid var(--arena-line-soft);
        background: var(--arena-paper-alt);
        padding: 14px 16px;
        font-size: 13px;
        margin-bottom: 28px;
        display: flex; align-items: center; gap: 12px;
        min-height: 48px;
    }
    .selected-bar .key { font-family: var(--arena-f-mono); font-size: 11px; letter-spacing: 0.12em; color: var(--arena-ink-soft); }
    .selected-bar .vals { color: var(--arena-ink); }

    /* Button row */
    .button-row { display: grid; grid-template-columns: auto 1fr; gap: 12px; margin-top: 32px; }
    .button-row .back { width: auto; padding: 16px 22px; }
    .footer-link { text-align: center; margin-top: 24px; }

    /* Records intro */
    .records-intro { display: grid; grid-template-columns: 1fr 1fr 1fr; border: 1px solid var(--arena-line-soft); margin-bottom: 28px; }
    .records-intro .cell { padding: 16px 18px; border-right: 1px solid var(--arena-line-soft); }
    .records-intro .cell:last-child { border-right: 0; }
    .records-intro .key { font-family: var(--arena-f-mono); font-size: 10px; color: var(--arena-ink-soft); letter-spacing: 0.14em; margin-bottom: 6px; }
    .records-intro .val { font-size: 14px; font-weight: 600; line-height: 1.4; color: var(--arena-ink); }

    .summary-strip {
        display: flex; align-items: center; gap: 14px;
        padding: 14px 18px;
        border: 1px solid var(--arena-line-soft);
        background: var(--arena-paper-alt);
        margin-bottom: 16px;
        font-size: 13px;
    }
    .summary-strip .key { font-family: var(--arena-f-mono); font-size: 10px; letter-spacing: 0.14em; color: var(--arena-ink-soft); }
    .summary-strip .stat b { font-family: var(--arena-f-mono); font-size: 16px; }
    .summary-strip .sep { width: 1px; align-self: stretch; background: var(--arena-line-soft); }

    .records-list { border: 1px solid var(--arena-line); background: var(--arena-paper); margin-bottom: 16px; }
    .records-head, .record-item {
        display: grid;
        grid-template-columns: 60px 1.5fr 0.9fr 1fr 80px 28px;
        gap: 12px;
        padding: 12px 20px;
        border-bottom: 1px solid var(--arena-line-soft);
        align-items: center;
    }
    .records-head { font-family: var(--arena-f-mono); font-size: 10px; letter-spacing: 0.14em; color: var(--arena-ink-soft); text-transform: uppercase; }
    .record-item { padding: 18px 20px; }
    .record-item:last-child { border-bottom: 0; }
    .record-tag { font-family: var(--arena-f-mono); font-size: 11px; background: var(--arena-ink); color: var(--arena-paper); padding: 4px 6px; text-align: center; letter-spacing: 0.04em; }
    .record-tag.run { background: oklch(40% 0.16 145); }
    .record-tag.trl { background: oklch(45% 0.12 60); }
    .record-tag.cycle { background: oklch(40% 0.14 240); }
    .record-tag.swim { background: oklch(45% 0.12 220); }
    .record-tag.tri { background: oklch(40% 0.18 330); }
    .record-name { font-size: 14px; font-weight: 600; line-height: 1.3; color: var(--arena-ink); }
    .record-dist { font-family: var(--arena-f-mono); font-size: 13px; color: var(--arena-ink); }
    .record-time { font-family: var(--arena-f-mono); font-size: 15px; font-weight: 600; letter-spacing: -0.01em; color: var(--arena-ink); }
    .record-date { font-family: var(--arena-f-mono); font-size: 12px; color: var(--arena-ink-soft); }
    .record-del { background: transparent; border: 0; cursor: pointer; color: var(--arena-ink-mute); font-size: 18px; display: grid; place-items: center; width: 28px; height: 28px; }
    .record-del:hover { color: var(--arena-urgent); }

    /* Add form */
    .add-form { border: 1px solid var(--arena-line); background: var(--arena-paper); padding: 24px; margin-bottom: 16px; }
    .add-form-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; }
    .add-form-title { font-size: 13px; font-weight: 600; font-family: var(--arena-f-mono); letter-spacing: 0.1em; text-transform: uppercase; color: var(--arena-ink); }
    .add-form-row { display: grid; gap: 16px; margin-bottom: 16px; }
    .add-form-row.two { grid-template-columns: 1fr 1fr; }

    .sport-chips { display: flex; gap: 8px; flex-wrap: wrap; }
    .sport-chip {
        border: 1px solid var(--arena-line-soft);
        background: var(--arena-paper);
        padding: 10px 14px;
        font-family: var(--arena-f-mono);
        font-size: 12px; letter-spacing: 0.06em;
        cursor: pointer;
        display: flex; align-items: center; gap: 8px;
        color: var(--arena-ink);
    }
    .sport-chip .ko { font-family: var(--arena-f-body); font-weight: 600; font-size: 13px; letter-spacing: 0; }
    .sport-chip.on { background: var(--arena-ink); color: var(--arena-paper); border-color: var(--arena-ink); }

    .dist-chips { display: flex; gap: 6px; flex-wrap: wrap; }
    .dist-chip { border: 1px solid var(--arena-line-soft); background: var(--arena-paper); padding: 8px 12px; font-family: var(--arena-f-mono); font-size: 12px; cursor: pointer; color: var(--arena-ink); }
    .dist-chip.on { background: var(--arena-ink); color: var(--arena-paper); border-color: var(--arena-ink); }
    .dist-chip.custom-trigger { border-style: dashed; color: var(--arena-ink-soft); }
    .dist-chip.custom-trigger.on { border-style: solid; }
    .dist-custom-input { margin-top: 10px; font-family: var(--arena-f-mono); font-size: 13px; }

    .time-input { display: grid; grid-template-columns: 1fr 12px 1fr 12px 1fr; align-items: center; gap: 6px; border: 1px solid var(--arena-line); padding: 12px 14px; }
    .time-input input { border: 0; background: transparent; outline: none; font-family: var(--arena-f-mono); font-size: 18px; font-weight: 500; text-align: center; width: 100%; color: var(--arena-ink); padding: 0; }
    .time-input input::placeholder { color: var(--arena-ink-mute); }
    .time-input .colon { font-family: var(--arena-f-mono); font-size: 16px; color: var(--arena-ink-mute); text-align: center; }

    .add-form-actions { display: flex; gap: 12px; justify-content: flex-end; margin-top: 8px; padding-top: 18px; border-top: 1px solid var(--arena-line-soft); }

    .add-trigger {
        border: 1px dashed var(--arena-line);
        background: transparent;
        padding: 18px;
        width: 100%;
        color: var(--arena-ink-soft);
        font-size: 14px; font-family: var(--arena-f-body);
        display: flex; align-items: center; justify-content: center; gap: 10px;
        margin-bottom: 16px;
        cursor: pointer;
    }
    .add-trigger:hover { color: var(--arena-ink); border-color: var(--arena-ink); border-style: solid; }
    .add-trigger .plus { width: 22px; height: 22px; display: grid; place-items: center; border: 1px solid currentColor; font-size: 16px; line-height: 1; }

    /* Done */
    .done-wrap { text-align: center; padding: 40px 0; }
    .done-mark { width: 72px; height: 72px; border: 2px solid var(--arena-ink); margin: 0 auto 28px; display: grid; place-items: center; font-size: 32px; color: var(--arena-accent-deep); }
    .done-sub { margin: 0 auto 36px; }
    .done-summary { text-align: left; }
    .done-cta { max-width: 320px; margin: 0 auto; }

    @media (max-width: 560px) {
        .title { font-size: 34px; }
        .records-head, .record-item { grid-template-columns: 48px 1.3fr 0.8fr 64px 24px; }
        .records-head > :nth-child(4), .record-item > :nth-child(4) { display: none; }
        .add-form-row.two { grid-template-columns: 1fr; }
    }
</style>
