<script lang="ts">
    import { goto } from '$app/navigation';
    import EditableField from '$lib/components/admin/EditableField.svelte';
    import DistancesEditor from '$lib/components/admin/DistancesEditor.svelte';
    import GiveawaysEditor from '$lib/components/admin/GiveawaysEditor.svelte';
    import ImageGalleryAdmin from '$lib/components/admin/ImageGalleryAdmin.svelte';

    let { data } = $props();
    let race = $state<any>(data.race);

    let lastSaved = $state('');
    let lastSavedTimer: ReturnType<typeof setTimeout> | null = null;

    async function patchRace(payload: Record<string, unknown>): Promise<any> {
        const res = await fetch(`/admin/api/races/${race.slug}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const json = await res.json();
        if (!res.ok) {
            const firstField = Object.keys(payload)[0];
            const msg = json?.errors?.[firstField]?.[0]
                ?? (firstField ? json?.errors?.[fieldToCamel(firstField)]?.[0] : undefined)
                ?? json?.detail
                ?? '저장 실패';
            throw new Error(msg);
        }
        return json;
    }

    async function saveField(field: string, value: any) {
        const json = await patchRace({ [field]: value });
        const newSlug = json.slug;
        race = json;
        lastSaved = field;
        if (lastSavedTimer) clearTimeout(lastSavedTimer);
        lastSavedTimer = setTimeout(() => (lastSaved = ''), 1500);
        if (field === 'slug' && newSlug && newSlug !== data.race.slug) {
            await goto(`/admin/races/${newSlug}`, { replaceState: true });
        }
    }

    async function unlockField(field: string) {
        const current: string[] = lockedFields;
        const next = current.filter((f) => f !== field);
        const json = await patchRace({ locked_fields: next });
        race = json;
        lastSaved = `unlock:${field}`;
        if (lastSavedTimer) clearTimeout(lastSavedTimer);
        lastSavedTimer = setTimeout(() => (lastSaved = ''), 1500);
    }

    function fieldToCamel(snake: string): string {
        return snake.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
    }

    let lockedFields = $derived<string[]>(race.locked_fields ?? race.lockedFields ?? []);
    function isLocked(field: string): boolean {
        return lockedFields.includes(field);
    }

    let courseUploads = $derived<{ path: string; url: string }[]>(
        race.courseImageUploads ?? race.course_image_uploads ?? []
    );
    let giveawayUploads = $derived<{ path: string; url: string }[]>(
        race.giveawayImageUploads ?? race.giveaway_image_uploads ?? []
    );
</script>

<svelte:head>
    <title>{race.title} · 편집 · Admin</title>
</svelte:head>

<div class="page">
    <div class="page-head">
        <a href="/admin/races" class="back">← 목록</a>
        <h1>{race.title}</h1>
        {#if lastSaved}
            <span class="saved">✓ 저장됨</span>
        {/if}
        {#if lockedFields.length > 0}
            <span class="lock-summary" title={`크롤러 보호 중: ${lockedFields.join(', ')}`}>
                🔒 보호 {lockedFields.length}
            </span>
        {/if}
        <div class="spacer"></div>
        <a href={`/races/${race.slug}`} target="_blank" rel="noopener" class="ext">사이트에서 보기 ↗</a>
        <a href={`/dj-admin/races/race/${race.id}/change/`} target="_blank" rel="noopener" class="ext">Django Admin ↗</a>
    </div>

    <div class="layout">
        <div class="col-main">
            <h2>기본 정보</h2>
            <div class="grid-2">
                <EditableField label="제목" field="title" value={race.title} save={saveField} locked={isLocked('title')} onUnlock={unlockField} />
                <EditableField label="슬러그" field="slug" value={race.slug} save={saveField} />
                <EditableField label="회차 (edition)" field="edition" value={race.edition} save={saveField} placeholder="예: 12회" />
                <EditableField label="상태" field="status" value={race.status} save={saveField} placeholder="upcoming / cancelled 등" />
            </div>

            <h2>일정</h2>
            <div class="grid-2">
                <EditableField label="대회일" field="race_date" value={race.raceDate} type="date" save={saveField} locked={isLocked('race_date')} onUnlock={unlockField} />
                <EditableField label="대회 종료일" field="race_end_date" value={race.raceEndDate} type="date" save={saveField} locked={isLocked('race_end_date')} onUnlock={unlockField} />
                <EditableField label="시작 시간" field="start_time" value={race.startTime} type="time" save={saveField} locked={isLocked('start_time')} onUnlock={unlockField} />
                <EditableField label="접수 시작" field="registration_start" value={race.registrationStart} type="date" save={saveField} locked={isLocked('registration_start')} onUnlock={unlockField} />
                <EditableField label="접수 종료" field="registration_end" value={race.registrationEnd} type="date" save={saveField} locked={isLocked('registration_end')} onUnlock={unlockField} />
            </div>

            <h2>거리 / 참가비 {#if isLocked('distances')}<span class="lock-inline" title="크롤러 자동 갱신에서 보호 중">🔒</span>{/if}</h2>
            <DistancesEditor value={race.distances} save={saveField} />

            <h2>기념품</h2>
            <GiveawaysEditor value={race.giveaways} save={saveField} />

            <h2>장소</h2>
            <div class="grid-2">
                <EditableField label="지역" field="region" value={race.region} save={saveField} locked={isLocked('region')} onUnlock={unlockField} />
                <EditableField label="장소" field="location" value={race.location} save={saveField} locked={isLocked('location')} onUnlock={unlockField} />
                <EditableField label="주소" field="address" value={race.address} save={saveField} locked={isLocked('address')} onUnlock={unlockField} />
                <EditableField label="위도" field="latitude" value={race.latitude} type="number" save={saveField} locked={isLocked('latitude')} onUnlock={unlockField} />
                <EditableField label="경도" field="longitude" value={race.longitude} type="number" save={saveField} locked={isLocked('longitude')} onUnlock={unlockField} />
            </div>

            <h2>주최자</h2>
            <div class="grid-2">
                <EditableField label="주최" field="organizer" value={race.organizer} save={saveField} locked={isLocked('organizer')} onUnlock={unlockField} />
                <EditableField label="연락처" field="organizer_contact" value={race.organizerContact} save={saveField} locked={isLocked('organizer_contact')} onUnlock={unlockField} />
                <EditableField label="이메일" field="organizer_email" value={race.organizerEmail} type="url" save={saveField} locked={isLocked('organizer_email')} onUnlock={unlockField} />
                <EditableField label="공식 URL" field="official_url" value={race.officialUrl} type="url" save={saveField} locked={isLocked('official_url')} onUnlock={unlockField} />
                <EditableField label="후기 URL" field="recap_url" value={race.recapUrl} type="url" save={saveField} />
            </div>

            <h2>코스/운영</h2>
            <div class="grid-2">
                <EditableField label="코스 노면" field="course_surface" value={race.courseSurface} save={saveField} />
                <EditableField label="코스 난이도" field="course_difficulty" value={race.courseDifficulty} save={saveField} />
                <EditableField label="급수대" field="aid_stations" value={race.aidStations} save={saveField} />
                <EditableField label="기록 측정" field="timing_method" value={race.timingMethod} save={saveField} />
                <EditableField label="주차" field="parking" value={race.parking} save={saveField} />
            </div>

            <h2>설명</h2>
            <EditableField label="설명" field="description" value={race.description} type="textarea" save={saveField} locked={isLocked('description')} onUnlock={unlockField} />
            <EditableField label="AI 요약" field="ai_summary" value={race.aiSummary} type="textarea" save={saveField} />
        </div>

        <div class="col-side">
            <h2>이미지</h2>
            <ImageGalleryAdmin
                slug={race.slug}
                kind="course"
                title="코스 사진"
                initialPaths={courseUploads.map((x) => x.path)}
                initialUrls={courseUploads.map((x) => x.url)}
            />
            <ImageGalleryAdmin
                slug={race.slug}
                kind="giveaway"
                title="기념품 사진"
                initialPaths={giveawayUploads.map((x) => x.path)}
                initialUrls={giveawayUploads.map((x) => x.url)}
            />
        </div>
    </div>
</div>

<style>
    .page-head {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 24px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--arena-line, #ddd);
    }
    .back {
        font-family: var(--arena-f-mono, ui-monospace);
        font-size: 12px;
        color: var(--arena-ink-soft, #555);
        text-decoration: none;
    }
    .back:hover { color: var(--arena-ink, #111); }
    h1 {
        font-family: var(--arena-f-display, system-ui);
        font-size: 22px;
        font-weight: 700;
        margin: 0;
        flex-shrink: 0;
    }
    .saved {
        padding: 2px 8px;
        background: var(--arena-accent, #22c55e);
        color: #fff;
        font-size: 11px;
        font-family: var(--arena-f-mono, ui-monospace);
        animation: fadeOut 1.5s forwards;
    }
    .lock-summary {
        padding: 2px 8px;
        background: #fef3c7;
        color: #92400e;
        font-size: 11px;
        font-family: var(--arena-f-mono, ui-monospace);
        border: 1px solid #fbbf24;
        border-radius: 2px;
    }
    .lock-inline {
        font-size: 12px;
        margin-left: 6px;
        opacity: 0.75;
    }
    @keyframes fadeOut {
        0%, 60% { opacity: 1; }
        100% { opacity: 0; }
    }
    .spacer { flex: 1; }
    .ext {
        font-family: var(--arena-f-mono, ui-monospace);
        font-size: 11px;
        color: var(--arena-ink-mute, #888);
        text-decoration: none;
        letter-spacing: 0.3px;
    }
    .ext:hover { color: var(--arena-ink, #111); }

    .layout {
        display: grid;
        grid-template-columns: 1fr;
        gap: 24px;
    }
    @media (min-width: 1024px) {
        .layout { grid-template-columns: 1fr 460px; }
    }
    h2 {
        font-family: var(--arena-f-mono, ui-monospace);
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft, #555);
        margin: 24px 0 8px;
    }
    .col-main h2:first-child { margin-top: 0; }
    .grid-2 {
        display: grid;
        grid-template-columns: 1fr;
        gap: 8px;
    }
    @media (min-width: 640px) {
        .grid-2 { grid-template-columns: repeat(2, 1fr); }
    }
    .col-side {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }
    .col-side > :global(*:not(h2)) { width: 100%; }
</style>
