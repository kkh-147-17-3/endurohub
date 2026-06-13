<script lang="ts">
    import { enhance, applyAction } from '$app/forms';
    import ProgressBar from '$lib/components/ProgressBar.svelte';
    import type { AuthUser } from '$lib/types';

    let { data, form } = $props();

    /* ─────────── Static data ─────────── */
    type SportMeta = { value: string; code: string; ko: string; tag: string; desc: string };
    const SPORTS: SportMeta[] = [
        { value: 'running',      code: 'RUN',   ko: '러닝',    tag: 'run',   desc: '로드 마라톤 · 5K부터 풀코스까지' },
        { value: 'trail_running',code: 'TRL',   ko: '트레일',  tag: 'trl',   desc: '산악 트레일 러닝 · 스카이레이스' },
        { value: 'cycling',      code: 'CYCLE', ko: '자전거',  tag: 'cycle', desc: '로드 사이클 · 그란폰도 · MTB' },
        { value: 'swimming',     code: 'SWIM',  ko: '수영',    tag: 'swim',  desc: '오픈워터 · 실내 수영 대회' },
        { value: 'triathlon',    code: 'TRI',   ko: '철인3종', tag: 'tri',   desc: '철인3종 · 듀애슬론 · 아쿠아슬론' },
    ];
    const SPORT_BY_VALUE = Object.fromEntries(SPORTS.map((s) => [s.value, s]));

    const DISTANCES: Record<string, string[]> = {
        running:       ['5K', '10K', '하프', '풀코스', '울트라'],
        trail_running: ['10K↓', '10–30K', '30–50K', '50–100K', '100K↑'],
        cycling:       ['그란폰도', '100K', '200K', 'MTB XC', 'MTB DH'],
        swimming:      ['오픈워터 1.5K', '오픈워터 3K', '오픈워터 5K', '수영장 단축', '수영장 장축'],
        triathlon:     ['스프린트', '올림픽', '하프(70.3)', '풀(140.6)'],
    };

    const REGIONS = [
        '서울', '경기', '인천', '부산', '대구', '광주', '대전', '울산', '세종',
        '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주',
    ];

    // Design step labels (matches design file STEPS array)
    const STEP_META = [
        { n: '01', l: '이메일' },
        { n: '02', l: '닉네임' },
        { n: '03', l: '종목' },
        { n: '04', l: '지역' },
        { n: '05', l: '기록' },
    ];

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

    const sendErrors   = $derived(flatten(form?.action === 'sendEmail'    ? form?.sendErrors    : undefined));
    const sendMessage  = $derived(form?.action === 'sendEmail' ? (form?.sendMessage ?? '') : '');
    const verifyErrors = $derived(flatten(form?.action === 'verifyEmail'  ? form?.verifyErrors  : undefined));
    const nicknameErrors = $derived(flatten(form?.action === 'setNickname' ? form?.nicknameErrors : undefined));
    const completeErrors = $derived(flatten(form?.action === 'complete'   ? form?.errors        : undefined));

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
        return SPORT_BY_VALUE[value] ?? { value, code: value.toUpperCase(), ko: value, tag: 'run', desc: '' };
    }
</script>

<svelte:head>
    <title>endurohub · 온보딩</title>
    <meta name="robots" content="noindex" />
</svelte:head>

<ProgressBar active={isSending || isVerifying || isSavingNick || isSubmitting} />

<div class="ob-page">

    <!-- Step tabs (visible for steps 0–4) -->
    {#if step <= 4}
        <div class="step-tabs">
            {#each STEP_META as s, i}
                <button
                    type="button"
                    class="step-tab"
                    class:on={i === step}
                    class:done={i < step}
                    onclick={() => i < step && goTo(i)}
                >
                    <span class="n eh-data">{i < step ? '✓' : s.n}</span>
                    <span class="l">{s.l}</span>
                </button>
            {/each}
        </div>
    {/if}

    <!-- ─────────── STEP 01 · EMAIL ─────────── -->
    {#if step === 0}
        <div class="eh-micro step-eyebrow"><span class="acc">STEP 01</span> · EMAIL</div>
        <h1 class="ob-title">이메일 인증</h1>
        <p class="ob-subtitle">
            {#if data.hasPendingSocialLogin}
                소셜 로그인 가입을 완료하려면 이메일 인증이 필요합니다. 대회 마감·일정 변경 알림이 이 주소로 전송됩니다.
            {:else}
                인증 코드를 받을 이메일을 확인하고 인증을 완료해주세요.
            {/if}
        </p>

        <div class="ob-body">
            <!-- 1. 이메일 입력 -->
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
                <div class="field">
                    <label class="field-label" for="ob-email">Email</label>
                    <input
                        id="ob-email"
                        class="ob-input"
                        name="email"
                        placeholder="you@example.com"
                        autocomplete="email"
                        bind:value={email}
                    />
                    {#if sendErrors.email}
                        <div class="field-hint err">{sendErrors.email}</div>
                    {:else}
                        <div class="field-hint">인증 코드는 이 주소로 발송됩니다.</div>
                    {/if}
                </div>

                <label class="consent">
                    <input type="checkbox" name="email_updates_opt_in" bind:checked={emailUpdatesOptIn} />
                    <span class="cb"></span>
                    <span class="consent-body">
                        서비스 이용약관 · 개인정보 처리방침에 동의합니다
                    </span>
                </label>

                <div class="nav-row" style="margin-top: var(--sp-6)">
                    <span class="spacer"></span>
                    <button
                        class="ob-btn {emailValid && resendIn === 0 ? 'primary' : 'muted'}"
                        disabled={!emailValid || isSending || resendIn > 0}
                    >
                        {resendIn > 0 ? `발송 완료 · ${resendLabel} 후 재전송` : '인증 메일 보내기'}
                    </button>
                </div>
                {#if sendMessage}
                    <div class="send-ok"><span class="send-dot"></span>{sendMessage}</div>
                {/if}
            </form>

            <div class="divider"></div>

            <!-- 2. OTP 입력 -->
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

                <div class="field">
                    <label class="field-label">인증 코드 <span class="field-hint-inline">6자리 숫자</span></label>
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
                        <div class="field-hint err">{verifyErrors.code}</div>
                    {/if}
                </div>

                <div class="nav-row" style="margin-top: var(--sp-5)">
                    <span class="spacer"></span>
                    <button class="ob-btn {codeFilled ? 'primary' : 'muted'}" disabled={!codeFilled || isVerifying}>
                        인증 확인
                    </button>
                </div>
            </form>
        </div>

        <div class="footer-link">
            <a href="/auth/login" class="text-link">← 로그인 다시 하기</a>
        </div>
    {/if}

    <!-- ─────────── STEP 02 · NICKNAME ─────────── -->
    {#if step === 1}
        <div class="eh-micro step-eyebrow"><span class="acc">STEP 02</span> · NICKNAME</div>
        <h1 class="ob-title">닉네임 설정</h1>
        <p class="ob-subtitle">커뮤니티에서 사용할 닉네임을 정해주세요. 나중에 마이페이지에서 바꿀 수 있습니다.</p>

        <div class="ob-body">
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
                <div class="field">
                    <label class="field-label" for="ob-nick">Nickname</label>
                    <input
                        id="ob-nick"
                        class="ob-input"
                        name="nickname"
                        placeholder="2–50자, 한글/영문/숫자"
                        minlength="2"
                        maxlength="50"
                        bind:value={nickname}
                    />
                    {#if nicknameErrors.nickname}
                        <div class="field-hint err">{nicknameErrors.nickname}</div>
                    {:else}
                        <div class="field-hint">한글, 영문, 숫자, 밑줄(_), 하이픈(-) 사용 가능</div>
                    {/if}
                </div>

                <div class="nav-row">
                    <button type="button" class="ob-btn ghost" onclick={() => goTo(0)}>← 이전</button>
                    <span class="spacer"></span>
                    <button class="ob-btn {nickOk ? 'primary' : 'muted'}" disabled={!nickOk || isSavingNick}>다음</button>
                </div>
            </form>
        </div>
    {/if}

    <!-- ─────────── STEP 03 · SPORT ─────────── -->
    {#if step === 2}
        <div class="eh-micro step-eyebrow"><span class="acc">STEP 03</span> · SPORT</div>
        <h1 class="ob-title">어떤 종목에<br />관심 있으세요?</h1>
        <p class="ob-subtitle">관심 종목을 선택하면 맞춤 대회 정보를 받을 수 있어요. 복수 선택 가능합니다.</p>

        <div class="pick-grid">
            {#each SPORTS as s}
                <button
                    type="button"
                    class="pick"
                    class:on={sports.includes(s.value)}
                    onclick={() => toggleSport(s.value)}
                >
                    <span class="chk">✓</span>
                    <span class="pick-sport-dot" style="background: var(--sport-{s.tag})"></span>
                    <span class="pick-ko">{s.ko}</span>
                    <span class="pick-desc">{s.desc}</span>
                </button>
            {/each}
        </div>

        <div class="nav-row">
            <button type="button" class="ob-btn ghost" onclick={() => goTo(1)}>← 이전</button>
            <span class="spacer"></span>
            <button
                type="button"
                class="ob-btn {sports.length ? 'primary' : 'muted'}"
                onclick={() => (step = 3)}
            >
                {sports.length ? `다음 · ${sports.length}개 선택` : '건너뛰기'}
            </button>
        </div>
        <div class="footer-link">
            <button type="button" class="text-link" onclick={() => (step = 3)}>나중에 설정할게요</button>
        </div>
    {/if}

    <!-- ─────────── STEP 04 · REGION ─────────── -->
    {#if step === 3}
        <div class="eh-micro step-eyebrow"><span class="acc">STEP 04</span> · REGION</div>
        <h1 class="ob-title">주로 어디서<br />활동하세요?</h1>
        <p class="ob-subtitle">관심 지역의 대회를 우선 추천해드릴게요.</p>

        <div class="region-chips">
            {#each REGIONS as r}
                <button
                    type="button"
                    class="region-chip"
                    class:on={regions.includes(r)}
                    onclick={() => toggleRegion(r)}
                >{r}</button>
            {/each}
        </div>

        <div class="nav-row">
            <button type="button" class="ob-btn ghost" onclick={() => (step = 2)}>← 이전</button>
            <span class="spacer"></span>
            <button
                type="button"
                class="ob-btn {regions.length ? 'primary' : 'muted'}"
                onclick={() => (step = 4)}
            >
                {regions.length ? `다음 · ${regions.length}개 선택` : '건너뛰기'}
            </button>
        </div>
        <div class="footer-link">
            <button type="button" class="text-link" onclick={() => (step = 4)}>나중에 설정할게요</button>
        </div>
    {/if}

    <!-- ─────────── STEP 05 · RECORDS ─────────── -->
    {#if step === 4}
        <div class="eh-micro step-eyebrow"><span class="acc">STEP 05</span> · RECORDS</div>
        <h1 class="ob-title">최근 대회 기록을<br />알려주세요</h1>
        <p class="ob-subtitle">
            최근 1년 이내 PB나 기억에 남는 기록을 입력하면 시즌 플래너와 페이스 도구가 자동 보정됩니다. 건너뛰어도 됩니다.
        </p>

        {#if records.length > 0}
            <div class="v-table" style="margin-bottom: var(--sp-4)">
                {#each records as r (r.id)}
                    <div class="rec-item">
                        <span class="rec-sport" style="background: var(--sport-{sportMeta(r.sport).tag})">{sportMeta(r.sport).code}</span>
                        <span class="rec-name">
                            {r.name}
                            <span class="rec-dist">{r.distance}</span>
                        </span>
                        <b class="eh-data rec-time">{r.time}</b>
                        <button type="button" class="rec-del" onclick={() => removeRecord(r.id)} aria-label="삭제">×</button>
                    </div>
                {/each}
            </div>
        {/if}

        {#if adding}
            <div class="rec-form">
                <!-- Sport chips -->
                <div class="rec-form-row">
                    <div class="field-label-sm">종목</div>
                    <div class="chip-row">
                        {#each SPORTS as s}
                            <button type="button" class="pick-chip" class:on={draft.sport === s.value} onclick={() => setDraftSport(s.value)}>
                                <span class="spot" style="background: var(--sport-{s.tag})"></span>
                                {s.ko}
                            </button>
                        {/each}
                    </div>
                </div>

                <!-- Distance chips -->
                <div class="rec-form-row">
                    <div class="field-label-sm">거리 / 카테고리</div>
                    <div class="chip-row">
                        {#each draftDistances as d}
                            <button type="button" class="pick-chip" class:on={draft.distance === d} onclick={() => pickDistance(d)}>{d}</button>
                        {/each}
                        <button type="button" class="pick-chip custom" class:on={isCustomDistance} onclick={toggleCustomDistance}>+ 직접 입력</button>
                    </div>
                    {#if isCustomDistance}
                        <!-- svelte-ignore a11y_autofocus -->
                        <input
                            class="ob-input"
                            style="margin-top: var(--sp-2)"
                            placeholder="예: 21.0975K, 100마일"
                            autofocus
                            value={draft.distance === '__custom__' ? '' : draft.distance}
                            oninput={(e) => (draft = { ...draft, distance: e.currentTarget.value })}
                            onblur={() => { if (draft.distance === '__custom__') draft = { ...draft, distance: '' }; }}
                        />
                    {/if}
                </div>

                <!-- Time -->
                <div class="rec-form-row">
                    <div class="field-label-sm">기록 (시:분:초)</div>
                    <div class="time-input">
                        <input placeholder="HH" maxlength="2" value={draft.h} oninput={(e) => (draft = { ...draft, h: e.currentTarget.value.replace(/\D/g, '') })} />
                        <span class="colon">:</span>
                        <input placeholder="MM" maxlength="2" value={draft.m} oninput={(e) => (draft = { ...draft, m: e.currentTarget.value.replace(/\D/g, '') })} />
                        <span class="colon">:</span>
                        <input placeholder="SS" maxlength="2" value={draft.s} oninput={(e) => (draft = { ...draft, s: e.currentTarget.value.replace(/\D/g, '') })} />
                    </div>
                </div>

                <!-- Race + date (2-col) -->
                <div class="rec-grid2">
                    <div class="field">
                        <label class="field-label-sm">대회명 <span class="hint">선택</span></label>
                        <input class="ob-input" placeholder="예: 서울국제마라톤 2025" bind:value={draft.name} />
                    </div>
                    <div class="field">
                        <label class="field-label-sm">날짜 <span class="hint">선택</span></label>
                        <input class="ob-input" placeholder="2025-03-16" bind:value={draft.date} />
                    </div>
                </div>

                <div class="rec-form-actions">
                    {#if records.length > 0}
                        <button type="button" class="ob-btn ghost tiny" onclick={() => { resetDraft(); adding = false; }}>취소</button>
                    {/if}
                    <button type="button" class="ob-btn tiny {canSaveRecord ? 'primary' : 'muted'}" disabled={!canSaveRecord} onclick={saveRecord}>기록 추가</button>
                </div>
            </div>
        {:else}
            <button type="button" class="add-trigger" onclick={() => (adding = true)}>
                <span class="plus">+</span> 기록 더 추가하기
            </button>
        {/if}

        {#if completeErrors.profile || completeErrors.preferred_sports || completeErrors.preferred_regions}
            <div class="field-hint err" style="margin-top: var(--sp-3)">{completeErrors.profile || completeErrors.preferred_sports || completeErrors.preferred_regions}</div>
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

            <div class="nav-row" style="margin-top: var(--sp-8)">
                <button type="button" class="ob-btn ghost" onclick={() => (step = 3)}>← 이전</button>
                <span class="spacer"></span>
                <button type="button" class="ob-btn ghost" onclick={() => (step = 5)} disabled={isSubmitting}>건너뛰기</button>
                <button type="submit" class="ob-btn primary" disabled={isSubmitting}>
                    {records.length > 0 ? `${records.length}개 기록으로 시작` : '완료'}
                </button>
            </div>
        </form>
    {/if}

    <!-- ─────────── DONE ─────────── -->
    {#if step === 5}
        <div class="done-wrap">
            <div class="done-mark">✓</div>
            <div class="eh-micro step-eyebrow" style="justify-content:center"><span class="acc">SETUP COMPLETE</span></div>
            <h1 class="ob-title" style="text-align:center">준비 완료</h1>
            <p class="ob-subtitle done-sub">입력하신 정보로 맞춤 캘린더를 구성했어요. 곧 열릴 대회부터 확인해 보세요.</p>

            <div class="done-summary">
                <div class="done-row">
                    <span class="eh-micro">SPORT</span>
                    <span class="done-val">{sports.length ? sports.map((s) => sportMeta(s).ko).join(' · ') : '—'}</span>
                </div>
                <div class="done-row">
                    <span class="eh-micro">REGION</span>
                    <span class="done-val">{regions.length ? regions.join(' · ') : '—'}</span>
                </div>
                <div class="done-row">
                    <span class="eh-micro">RECORDS</span>
                    <span class="done-val eh-data">{records.length > 0 ? `${records.length}개 기록 등록됨` : '건너뜀 — 마이페이지에서 추가 가능'}</span>
                </div>
            </div>

            <div style="height: var(--sp-8)"></div>
            <div style="display:flex; gap: var(--sp-2); justify-content: center; flex-wrap: wrap">
                <a href="/calendar" class="ob-btn primary">캘린더 보기 →</a>
                <a href="/mypage" class="ob-btn ghost">마이페이지</a>
            </div>
        </div>
    {/if}
</div>

<style>
    .ob-page {
        max-width: 640px;
        margin: 0 auto;
        padding: 40px var(--container-pad-mobile) 80px;
    }

    /* ── Step tabs (design: border + active bottom ink rule) ── */
    .step-tabs {
        display: flex;
        gap: 0;
        border: 1px solid var(--line);
        margin-bottom: var(--sp-10);
    }
    .step-tab {
        flex: 1;
        padding: 10px 0 12px;
        background: var(--paper-0);
        border: 0;
        border-right: 1px solid var(--line);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        cursor: pointer;
        font-family: var(--font-sans);
        transition: background var(--dur-fast) var(--ease-out);
    }
    .step-tab:last-child { border-right: 0; }
    .step-tab .n {
        font-size: 10px;
        font-weight: 700;
        letter-spacing: var(--track-micro);
        color: var(--text-faint);
    }
    .step-tab .l {
        font-size: 11.5px;
        font-weight: var(--w-strong);
        color: var(--text-faint);
    }
    .step-tab.done .n,
    .step-tab.done .l { color: var(--text-muted); }
    /* Active: bottom ink rule */
    .step-tab.on { box-shadow: inset 0 -2px 0 var(--ink-900); }
    .step-tab.on .n { color: var(--text-accent); }
    .step-tab.on .l { color: var(--text-strong); }

    /* ── Eyebrow / title / subtitle ── */
    .step-eyebrow {
        margin-bottom: var(--sp-3);
    }
    .ob-title {
        font-family: var(--font-sans);
        font-size: clamp(30px, 5vw, 40px);
        font-weight: var(--w-display);
        letter-spacing: var(--track-display);
        line-height: 1.08;
        margin: var(--sp-3) 0 0;
        color: var(--text-strong);
    }
    .ob-subtitle {
        color: var(--text-muted);
        font-size: 15px;
        line-height: var(--leading-body);
        margin: var(--sp-3) 0 0;
        max-width: 460px;
        word-break: keep-all;
    }

    /* ── Body (step content column) ── */
    .ob-body {
        margin-top: var(--sp-8);
        display: flex;
        flex-direction: column;
        gap: var(--sp-5);
    }

    /* ── Inputs ── */
    .field { display: flex; flex-direction: column; gap: var(--sp-2); }
    .field-label {
        font-size: var(--text-micro);
        font-weight: var(--w-strong);
        letter-spacing: var(--track-micro);
        text-transform: uppercase;
        color: var(--text-muted);
    }
    .ob-input {
        width: 100%;
        border: 1px solid var(--line);
        background: var(--paper-0);
        padding: 14px 16px;
        font-size: var(--text-body-sm);
        font-family: var(--font-sans);
        color: var(--text-strong);
        outline: none;
        border-radius: var(--r-1);
        box-sizing: border-box;
    }
    .ob-input::placeholder { color: var(--text-faint); }
    .ob-input:focus { border-color: var(--ink-900); }
    .field-hint {
        font-size: 12px;
        color: var(--text-faint);
        margin-top: 2px;
    }
    .field-hint.err { color: var(--danger); }
    .field-hint-inline {
        font-size: 11px;
        font-weight: 400;
        color: var(--text-faint);
        margin-left: var(--sp-2);
        letter-spacing: 0;
        text-transform: none;
    }

    /* ── Consent checkbox ── */
    .consent {
        display: flex;
        gap: var(--sp-3);
        align-items: flex-start;
        background: var(--paper-50);
        border: var(--border-hair);
        padding: 14px 16px;
        cursor: pointer;
        font-size: 13.5px;
        color: var(--text-body);
        line-height: 1.55;
    }
    .consent input {
        position: absolute;
        opacity: 0;
        pointer-events: none;
    }
    .consent .cb {
        width: 16px;
        height: 16px;
        border: 1px solid var(--line);
        background: var(--paper-0);
        flex-shrink: 0;
        display: grid;
        place-items: center;
        margin-top: 2px;
    }
    .consent input:checked + .cb {
        background: var(--ink-900);
        border-color: var(--ink-900);
    }
    .consent input:checked + .cb::after {
        content: '';
        width: 8px;
        height: 6px;
        border: solid var(--paper-0);
        border-width: 0 2px 2px 0;
        transform: rotate(45deg) translate(0, -2px);
    }

    /* ── Buttons ── */
    .ob-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        padding: 16px 22px;
        border: 1px solid var(--line);
        background: transparent;
        font-family: var(--font-sans);
        font-size: var(--text-body-sm);
        font-weight: var(--w-strong);
        color: var(--text-strong);
        cursor: pointer;
        text-decoration: none;
        border-radius: var(--r-1);
        transition: background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
    }
    .ob-btn:disabled { cursor: not-allowed; opacity: 0.45; }
    .ob-btn.primary {
        background: var(--ink-900);
        color: var(--paper-0);
        border-color: var(--ink-900);
    }
    .ob-btn.primary:hover:not(:disabled) { background: var(--ink-700); border-color: var(--ink-700); }
    .ob-btn.muted {
        background: var(--ink-300);
        color: var(--paper-0);
        border-color: var(--ink-300);
    }
    .ob-btn.ghost { background: transparent; border-color: var(--line); color: var(--text-muted); }
    .ob-btn.ghost:hover:not(:disabled) { color: var(--text-strong); border-color: var(--ink-900); }
    .ob-btn.tiny { padding: 8px 14px; font-size: 12px; font-weight: 500; }

    /* ── Nav row ── */
    .nav-row {
        display: flex;
        gap: var(--sp-2);
        align-items: center;
        margin-top: var(--sp-9);
        flex-wrap: wrap;
    }
    .spacer { flex: 1; }

    /* ── Send OK ── */
    .send-ok {
        margin-top: var(--sp-3);
        display: flex;
        align-items: center;
        gap: var(--sp-2);
        font-size: 13px;
        font-weight: 500;
        color: var(--text-accent);
    }
    .send-dot {
        width: 8px;
        height: 8px;
        background: var(--accent);
        flex-shrink: 0;
    }

    /* ── OTP ── */
    .otp {
        display: flex;
        gap: 10px;
        border: 1px solid var(--line);
        padding: 14px;
        justify-content: space-between;
        position: relative;
        cursor: text;
        border-radius: var(--r-1);
    }
    .otp .cell {
        flex: 1;
        aspect-ratio: 1 / 1.2;
        display: grid;
        place-items: center;
        font-family: var(--font-sans);
        font-size: 28px;
        font-weight: 500;
        color: var(--text-faint);
        border-right: 1px dashed var(--line);
        font-variant-numeric: tabular-nums;
    }
    .otp .cell:last-of-type { border-right: 0; }
    .otp .cell.filled { color: var(--text-strong); }
    .otp-hidden { position: absolute; opacity: 0; pointer-events: none; }

    .divider { height: 1px; background: var(--line); margin: var(--sp-6) 0; }

    /* ── Sport pick grid ── */
    .pick-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: var(--sp-3);
        margin-top: var(--sp-8);
        margin-bottom: var(--sp-4);
    }
    .pick {
        border: 1px solid var(--line);
        background: var(--paper-0);
        border-radius: var(--r-0);
        padding: 18px 20px;
        text-align: left;
        display: flex;
        flex-direction: column;
        gap: var(--sp-2);
        cursor: pointer;
        position: relative;
        transition: border-color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out);
        font-family: var(--font-sans);
    }
    .pick:hover { border-color: var(--ink-900); }
    .pick.on {
        border-color: var(--ink-900);
        box-shadow: inset 0 0 0 1px var(--ink-900);
    }
    .pick .chk {
        position: absolute;
        top: 14px;
        right: 16px;
        font-size: 13px;
        font-weight: 800;
        color: var(--accent-strong);
        opacity: 0;
    }
    .pick.on .chk { opacity: 1; }
    .pick-sport-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
    }
    .pick-ko {
        font-size: 17px;
        font-weight: 700;
        letter-spacing: var(--track-heading);
        color: var(--text-strong);
    }
    .pick-desc {
        font-size: 12px;
        color: var(--text-muted);
        line-height: 1.5;
    }

    /* ── Region chips ── */
    .region-chips {
        display: flex;
        flex-wrap: wrap;
        gap: var(--sp-2);
        margin-top: var(--sp-8);
        margin-bottom: var(--sp-4);
    }
    .region-chip {
        border: 1px solid var(--line);
        background: var(--paper-0);
        padding: 8px 14px;
        font-size: 13px;
        font-weight: var(--w-strong);
        color: var(--text-strong);
        cursor: pointer;
        font-family: var(--font-sans);
        border-radius: var(--r-1);
        transition: border-color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
    }
    .region-chip:hover { border-color: var(--ink-900); }
    .region-chip.on {
        background: var(--ink-900);
        color: var(--paper-0);
        border-color: var(--ink-900);
    }

    /* ── Records table ── */
    .rec-item {
        display: grid;
        grid-template-columns: auto 1fr auto auto;
        gap: 14px;
        align-items: center;
        padding: 13px 16px;
        border-bottom: var(--border-hair);
        font-size: var(--text-body-sm);
    }
    .rec-item:last-child { border-bottom: 0; }
    .rec-sport {
        font-size: 10px;
        font-weight: 800;
        letter-spacing: var(--track-micro);
        text-transform: uppercase;
        color: #fff;
        padding: 3px 6px;
    }
    .rec-name {
        font-weight: var(--w-strong);
        font-size: var(--text-body-sm);
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: var(--text-strong);
    }
    .rec-dist {
        font-weight: 400;
        color: var(--text-faint);
        margin-left: var(--sp-2);
    }
    .rec-time {
        font-size: 15px;
        text-align: right;
        color: var(--text-strong);
        font-variant-numeric: tabular-nums;
    }
    .rec-del {
        background: transparent;
        border: 0;
        cursor: pointer;
        color: var(--text-faint);
        font-size: 18px;
        display: grid;
        place-items: center;
        width: 28px;
        height: 28px;
        padding: 0;
    }
    .rec-del:hover { color: var(--danger); }

    /* ── Record add form ── */
    .rec-form {
        border: 1px solid var(--ink-900);
        padding: 20px;
        display: flex;
        flex-direction: column;
        gap: var(--sp-4);
        margin-top: var(--sp-4);
    }
    .rec-form-row { display: flex; flex-direction: column; gap: var(--sp-2); }
    .field-label-sm {
        font-size: 12px;
        font-weight: var(--w-strong);
        color: var(--text-muted);
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .hint {
        font-weight: 400;
        color: var(--text-faint);
        margin-left: var(--sp-2);
        font-size: 11px;
        letter-spacing: 0;
        text-transform: none;
    }
    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: var(--sp-2);
    }
    .pick-chip {
        border: 1px solid var(--line);
        background: var(--paper-0);
        padding: 8px 12px;
        font-family: var(--font-sans);
        font-size: 12px;
        font-weight: var(--w-strong);
        cursor: pointer;
        color: var(--text-strong);
        display: flex;
        align-items: center;
        gap: var(--sp-2);
        border-radius: var(--r-1);
        transition: border-color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
    }
    .pick-chip.on {
        background: var(--ink-900);
        color: var(--paper-0);
        border-color: var(--ink-900);
    }
    .pick-chip.custom { border-style: dashed; color: var(--text-muted); }
    .pick-chip.custom.on { border-style: solid; }
    .spot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex: none;
    }

    /* ── Time input ── */
    .time-input {
        display: grid;
        grid-template-columns: 1fr 12px 1fr 12px 1fr;
        align-items: center;
        gap: 6px;
        border: 1px solid var(--line);
        padding: 12px 14px;
        border-radius: var(--r-1);
    }
    .time-input input {
        border: 0;
        background: transparent;
        outline: none;
        font-family: var(--font-sans);
        font-size: 18px;
        font-weight: 500;
        text-align: center;
        width: 100%;
        color: var(--text-strong);
        padding: 0;
        font-variant-numeric: tabular-nums;
    }
    .time-input input::placeholder { color: var(--text-faint); }
    .colon {
        font-size: 16px;
        color: var(--text-faint);
        text-align: center;
    }

    .rec-grid2 {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: var(--sp-3);
    }
    .rec-form-actions {
        display: flex;
        gap: var(--sp-2);
        justify-content: flex-end;
        padding-top: var(--sp-4);
        border-top: var(--border-hair);
        margin-top: var(--sp-2);
    }

    /* ── Add trigger button ── */
    .add-trigger {
        border: 1px dashed var(--line);
        background: transparent;
        padding: 18px;
        width: 100%;
        color: var(--text-muted);
        font-size: var(--text-body-sm);
        font-family: var(--font-sans);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: var(--sp-2);
        margin-top: var(--sp-4);
        cursor: pointer;
        border-radius: var(--r-1);
    }
    .add-trigger:hover { color: var(--text-strong); border-color: var(--ink-900); border-style: solid; }
    .add-trigger .plus {
        width: 22px;
        height: 22px;
        display: grid;
        place-items: center;
        border: 1px solid currentColor;
        font-size: 16px;
        line-height: 1;
    }

    /* ── Text links ── */
    .text-link {
        background: transparent;
        border: 0;
        padding: 6px 0;
        color: var(--text-muted);
        font-size: 13px;
        font-family: var(--font-sans);
        border-bottom: 1px solid var(--line);
        cursor: pointer;
        text-decoration: none;
    }
    .text-link:hover { color: var(--text-strong); border-bottom-color: var(--ink-900); }
    .text-link:disabled { opacity: 0.5; cursor: not-allowed; }
    .footer-link { text-align: center; margin-top: var(--sp-6); }

    /* ── Done screen ── */
    .done-wrap { text-align: center; padding: var(--sp-6) 0 var(--sp-10); }
    .done-mark {
        width: 64px;
        height: 64px;
        margin: 0 auto var(--sp-6);
        background: var(--accent);
        color: #fff;
        font-size: 30px;
        font-weight: 800;
        display: grid;
        place-items: center;
    }
    .done-sub { margin: var(--sp-3) auto 0; }
    .done-summary {
        border: var(--border-hair);
        margin-top: var(--sp-8);
        text-align: left;
    }
    .done-row {
        display: grid;
        grid-template-columns: 130px 1fr;
        gap: 16px;
        padding: 14px 18px;
        border-bottom: var(--border-hair);
        font-size: var(--text-body-sm);
        align-items: baseline;
    }
    .done-row:last-child { border-bottom: 0; }
    .done-val {
        font-weight: var(--w-strong);
        color: var(--text-strong);
    }

    @media (max-width: 560px) {
        .ob-title { font-size: 30px; }
        .pick-grid { grid-template-columns: 1fr; }
        .step-tab .l { display: none; }
        .rec-grid2 { grid-template-columns: 1fr; }
    }
</style>
