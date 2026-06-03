<script lang="ts" module>
    // Kakao Maps SDK is loaded at runtime (autoload=false), so it has no types.
    declare const kakao: any;
</script>

<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import type { PageData } from './$types';
    import type { Race, Sport } from '$lib/types';
    import { track } from '$lib/analytics';
    import { arenaDday, arenaDdayLabel, arenaDistLabel, arenaSportShort } from '$lib/arena';

    let { data }: { data: PageData } = $props();

    const year = $derived(data.year);
    const month = $derived(data.month);
    const racesGrouped = $derived(data.racesGrouped);
    const previousMonth = $derived(data.previousMonth);
    const nextMonth = $derived(data.nextMonth);
    const sport = $derived(
        (Array.isArray(data.sport) ? data.sport : data.sport ? [data.sport] : []) as string[],
    );
    const kakaoJsKey = $derived(data.kakaoJsKey as string);

    const allRaces = $derived(Object.values(racesGrouped).flat());

    onMount(() => {
        track('calendar_kakaomap_view', { year, month });
        if (kakaoJsKey) ensureKakao(initMap);
    });
    onDestroy(() => {
        for (const mk of overlays) mk.overlay.setMap(null);
        overlays = [];
    });

    // ── Sport encoding ────────────────────────────────────────────────
    // Colors mirror the arena RaceRow / calendar grid / SVG map exactly.
    const SPORT_COLOR: Record<Sport, string> = {
        running: 'oklch(48% 0.18 280)',
        swimming: 'oklch(50% 0.14 220)',
        cycling: 'oklch(55% 0.16 60)',
        triathlon: 'oklch(48% 0.18 320)',
        trail_running: 'oklch(42% 0.14 145)',
    };
    const SPORT_ORDER: Sport[] = ['running', 'trail_running', 'cycling', 'swimming', 'triathlon'];

    // ── Derived data ──────────────────────────────────────────────────
    function byDate(a: Race, b: Race): number {
        return (a.raceDate || '').localeCompare(b.raceDate || '');
    }

    type RegionStat = { code: string; races: Race[]; count: number };
    // Group races by region — no province geometry is needed here because the
    // Kakao map positions every race by its own latitude / longitude.
    const regionStats = $derived.by<RegionStat[]>(() => {
        const m = new Map<string, Race[]>();
        for (const r of allRaces) {
            if (!r.region) continue;
            const list = m.get(r.region) ?? [];
            list.push(r);
            m.set(r.region, list);
        }
        return [...m.entries()]
            .map(([code, races]) => ({ code, races: [...races].sort(byDate), count: races.length }))
            .sort((a, b) => b.count - a.count);
    });

    const totalRaces = $derived(allRaces.length);
    const activeRegionCount = $derived(regionStats.length);
    // Races whose region is null / 기타 — they get no region grouping.
    const unmappedCount = $derived(
        totalRaces - regionStats.reduce((sum, r) => sum + r.count, 0),
    );

    // race.id → 1-based index within its region list, matching the side panel.
    const racePinNumber = $derived.by(() => {
        const m = new Map<number, number>();
        for (const r of regionStats) r.races.forEach((race, i) => m.set(race.id, i + 1));
        return m;
    });

    // ── Selection ─────────────────────────────────────────────────────
    let selected = $state<string | null>(null);
    const selectedRegion = $derived(
        selected ? (regionStats.find((r) => r.code === selected) ?? null) : null,
    );
    const regionRaces = $derived(selectedRegion ? selectedRegion.races : []);
    const regionPins = $derived(regionRaces.filter(hasCoords));
    const missingCoordCount = $derived(
        selectedRegion ? regionRaces.length - regionPins.length : 0,
    );

    function selectRegion(code: string, count: number) {
        if (count === 0 || selected === code) return;
        selected = code;
        track('calendar_kakaomap_region', { region: code, count });
    }
    function clearSelection() {
        selected = null;
    }
    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Escape' && selected) clearSelection();
    }

    // ── Kakao map ─────────────────────────────────────────────────────
    let mapEl: HTMLDivElement;
    let map: any = null;
    let infowindow: any = null;
    let kakaoReady = $state(false);
    let mapFailed = $state(false);
    // Imperative marker store — kept outside reactive state on purpose.
    // A marker is either a single-race pin or a cluster of adjacent pins.
    type Marker =
        | { kind: 'pin'; race: Race; overlay: any; el: HTMLElement }
        | { kind: 'cluster'; races: Race[]; overlay: any; el: HTMLElement };
    let overlays: Marker[] = [];
    // Bumped after the overlay layer is rebuilt, so the selection effect re-runs.
    let markersVersion = $state(0);
    // Pixel distance under which two pins are merged into a cluster at the
    // current zoom. Smaller value = clusters break up sooner when zooming in.
    const CLUSTER_PX = 32;

    function ensureKakao(cb: () => void) {
        if (typeof kakao !== 'undefined' && kakao.maps) {
            kakao.maps.load(cb);
            return;
        }
        const existing = document.querySelector('script[src*="dapi.kakao.com"]');
        if (existing) {
            existing.addEventListener('load', () => kakao.maps.load(cb));
            return;
        }
        const script = document.createElement('script');
        script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${kakaoJsKey}&autoload=false`;
        script.onload = () => kakao.maps.load(cb);
        script.onerror = () => (mapFailed = true);
        document.head.appendChild(script);
    }

    function initMap() {
        if (!mapEl) return;
        map = new kakao.maps.Map(mapEl, {
            center: new kakao.maps.LatLng(36.2, 127.9),
            level: 13,
        });
        map.setZoomable(true);
        infowindow = new kakao.maps.InfoWindow({ removable: true, zIndex: 10 });
        // Re-cluster on zoom change — pin separations shift with zoom, so the
        // grouping the user sees must follow the current pixel layout.
        kakao.maps.event.addListener(map, 'zoom_changed', () => {
            rebuildOverlays();
            applyDimming();
        });
        kakaoReady = true;
    }

    function esc(s: string): string {
        return s.replace(
            /[&<>"]/g,
            (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c] as string,
        );
    }

    function raceCoord(race: Race): any {
        return new kakao.maps.LatLng(race.latitude, race.longitude);
    }

    function openInfo(race: Race) {
        if (!infowindow || !map) return;
        const st = raceState(race);
        infowindow.setContent(
            `<div style="padding:9px 12px;min-width:172px;font-family:sans-serif;line-height:1.45;">
                <div style="font-size:12.5px;font-weight:700;color:#1a1a1a;">${esc(race.title)}</div>
                <div style="font-size:11px;color:#666;margin-top:3px;">
                    ${esc(shortDate(race.raceDate))} · ${esc(race.sportLabel)} · ${esc(arenaDistLabel(race))}
                </div>
                <div style="font-size:11px;font-weight:700;margin-top:2px;color:${
                    st.urgent ? '#c0392b' : st.closed ? '#999' : '#2563eb'
                };">${esc(st.label)}</div>
                <a href="${esc(race.url)}" style="display:inline-block;margin-top:6px;font-size:11px;font-weight:600;color:#2563eb;text-decoration:none;">대회 정보 →</a>
            </div>`,
        );
        infowindow.setPosition(raceCoord(race));
        infowindow.open(map);
    }

    function buildPin(race: Race): Marker {
        const n = racePinNumber.get(race.id) ?? 0;
        const st = raceState(race);

        const el = document.createElement('div');
        el.className = 'k-pin';
        if (st.closed) el.classList.add('closed');
        el.style.setProperty('--pc', SPORT_COLOR[race.sport]);
        el.innerHTML =
            (n > 0 ? `<span class="k-pin-num">${String(n).padStart(2, '0')}</span>` : '') +
            `<span class="k-pin-dot"></span>`;
        el.title = race.title;
        el.addEventListener('click', () => openInfo(race));

        const overlay = new kakao.maps.CustomOverlay({
            position: raceCoord(race),
            content: el,
            clickable: true,
            zIndex: 3,
        });
        overlay.setMap(map);
        return { kind: 'pin', race, overlay, el };
    }

    function buildCluster(races: Race[]): Marker {
        const sorted = [...races].sort(byDate);
        const lat = races.reduce((s, r) => s + (r.latitude as number), 0) / races.length;
        const lng = races.reduce((s, r) => s + (r.longitude as number), 0) / races.length;
        const allClosed = races.every((r) => raceState(r).closed);

        // Dominant sport drives the bubble color so the cluster still reads
        // as part of the same legend the pins use.
        const sportCount = new Map<Sport, number>();
        for (const r of races) sportCount.set(r.sport, (sportCount.get(r.sport) ?? 0) + 1);
        const dominant = [...sportCount.entries()].sort((a, b) => b[1] - a[1])[0][0];

        const rows = sorted
            .map((r) => {
                const st = raceState(r);
                const closedAttr = st.closed ? ' is-closed' : '';
                return (
                    `<a class="k-cluster-row${closedAttr}" href="${esc(r.url)}">` +
                    `<span class="k-cluster-date">${esc(shortDate(r.raceDate))}</span>` +
                    `<span class="k-cluster-dot" style="background:${SPORT_COLOR[r.sport]};"></span>` +
                    `<span class="k-cluster-name">${esc(r.title)}</span>` +
                    `<span class="k-cluster-dist">${esc(arenaDistLabel(r))}</span>` +
                    `</a>`
                );
            })
            .join('');

        const el = document.createElement('div');
        el.className = 'k-cluster';
        if (allClosed) el.classList.add('closed');
        el.style.setProperty('--pc', SPORT_COLOR[dominant]);
        el.innerHTML =
            `<span class="k-cluster-num">${races.length}</span>` +
            `<div class="k-cluster-tip" role="tooltip">` +
                `<div class="k-cluster-tip-box">` +
                    `<div class="k-cluster-tip-head">대회 ${races.length}개</div>` +
                    `<div class="k-cluster-tip-list">${rows}</div>` +
                `</div>` +
            `</div>`;
        // Clicking a cluster zooms the map to fit its members, which usually
        // separates the pixels enough to break the cluster apart.
        el.addEventListener('click', (e) => {
            // Race-row anchors inside the tooltip handle their own navigation.
            const tgt = e.target as HTMLElement | null;
            if (tgt && tgt.closest('.k-cluster-row')) return;
            const bounds = new kakao.maps.LatLngBounds();
            for (const r of races) bounds.extend(raceCoord(r));
            map.setBounds(bounds, 80, 60, 60, 60);
            if (map.getLevel() < 3) map.setLevel(3);
        });

        const overlay = new kakao.maps.CustomOverlay({
            position: new kakao.maps.LatLng(lat, lng),
            content: el,
            clickable: true,
            zIndex: 5,
        });
        overlay.setMap(map);
        return { kind: 'cluster', races, overlay, el };
    }

    // Project every race to current container pixels, then greedy-merge any
    // two pins within CLUSTER_PX of each other. Re-runs on every zoom change.
    function rebuildOverlays() {
        for (const mk of overlays) mk.overlay.setMap(null);
        overlays = [];
        if (!map) return;

        const withCoords = allRaces.filter(hasCoords);
        if (withCoords.length === 0) return;

        const proj = map.getProjection();
        const projected = withCoords.map((race) => {
            const pt = proj.containerPointFromCoords(raceCoord(race));
            return { race, x: pt.x as number, y: pt.y as number };
        });

        const used = new Set<number>();
        const thresholdSq = CLUSTER_PX * CLUSTER_PX;

        for (let i = 0; i < projected.length; i++) {
            if (used.has(i)) continue;
            const group: Race[] = [projected[i].race];
            used.add(i);
            for (let j = i + 1; j < projected.length; j++) {
                if (used.has(j)) continue;
                const dx = projected[i].x - projected[j].x;
                const dy = projected[i].y - projected[j].y;
                if (dx * dx + dy * dy < thresholdSq) {
                    group.push(projected[j].race);
                    used.add(j);
                }
            }
            overlays.push(group.length === 1 ? buildPin(group[0]) : buildCluster(group));
        }
    }

    function fitToSelection() {
        if (!map) return;
        const races = selected ? regionRaces : allRaces;
        const coords = races.filter(hasCoords);
        if (coords.length === 0) return;
        const bounds = new kakao.maps.LatLngBounds();
        for (const r of coords) bounds.extend(raceCoord(r));
        map.setBounds(bounds, 64, 48, 48, 48);
        // A lone race would zoom in absurdly far — cap it.
        if (coords.length === 1 && map.getLevel() < 6) map.setLevel(6);
    }

    function applyDimming() {
        for (const mk of overlays) {
            if (mk.kind === 'pin') {
                const inRegion = !selected || mk.race.region === selected;
                mk.el.classList.toggle('dim', !!selected && !inRegion);
                mk.overlay.setZIndex(inRegion ? 4 : 2);
            } else {
                const anyInRegion = !selected || mk.races.some((r) => r.region === selected);
                mk.el.classList.toggle('dim', !!selected && !anyInRegion);
                mk.overlay.setZIndex(anyInRegion ? 6 : 2);
            }
        }
    }

    function applySelection() {
        applyDimming();
        fitToSelection();
    }

    // Highlight the marker for a side-panel row on hover (no map movement).
    function highlightRace(id: number | null) {
        for (const mk of overlays) {
            if (mk.kind === 'pin') {
                const on = mk.race.id === id;
                mk.el.classList.toggle('active', on);
                mk.overlay.setZIndex(on ? 8 : selected && mk.race.region !== selected ? 2 : 4);
            } else {
                const on = id != null && mk.races.some((r) => r.id === id);
                mk.el.classList.toggle('active', on);
                mk.overlay.setZIndex(on ? 9 : 6);
            }
        }
    }

    // Rebuild the overlay layer whenever the map is ready or the month changes.
    $effect(() => {
        const _ = allRaces; // track
        if (!kakaoReady || !map) return;
        rebuildOverlays();
        markersVersion += 1;
    });
    // Re-apply dimming + bounds after a rebuild or a region selection change.
    $effect(() => {
        const _ = markersVersion; // track
        selected; // track
        if (!kakaoReady || !map) return;
        applySelection();
    });

    // ── Helpers ───────────────────────────────────────────────────────
    function hasCoords(race: Race): boolean {
        return race.latitude != null && race.longitude != null;
    }

    function sportBreakdown(races: Race[]): { sport: Sport; count: number }[] {
        const c = new Map<Sport, number>();
        for (const r of races) c.set(r.sport, (c.get(r.sport) ?? 0) + 1);
        return SPORT_ORDER.filter((s) => c.has(s)).map((s) => ({
            sport: s,
            count: c.get(s) as number,
        }));
    }

    type RaceState = { label: string; closed: boolean; urgent: boolean };
    function raceState(race: Race): RaceState {
        const label = arenaDdayLabel(race);
        const closed = race.status === 'finished' || label === '마감';
        return {
            label: race.status === 'finished' ? '종료' : label,
            closed,
            urgent: !closed && arenaDday(race).urgent,
        };
    }

    function shortDate(d: string | null): string {
        if (!d) return '—';
        const p = d.split('-');
        return p.length >= 3 ? `${p[1]}·${p[2]}` : d;
    }

    // ── Navigation query (carries month + sport filter across views) ──
    function navQuery(targetYear: number, targetMonth: number): string {
        const p = new URLSearchParams();
        p.set('year', String(targetYear));
        p.set('month', String(targetMonth));
        for (const s of sport) p.append('sport', s);
        return p.toString();
    }

    const todayDate = new Date();
    const currentMonth = todayDate.getMonth() + 1;
    const currentYear = todayDate.getFullYear();
    const mm = $derived(String(month).padStart(2, '0'));
</script>

<svelte:head>
    <title>{year}년 {month}월 대회 지도 (Kakao) - 엔듀로허브</title>
    <meta
        name="description"
        content="{year}년 {month}월 마라톤·수영·자전거·철인3종·트레일러닝 대회를 카카오맵에서 확인하세요."
    />
</svelte:head>

<svelte:window onkeydown={handleKeydown} />

<div class="map-wrap">
    <header class="map-head">
        <div class="head-left">
            <div class="arena-kicker">
                엔듀로허브 · 캘린더 · Kakao 지도{selected ? ` · ${selected}` : ''}
            </div>
            <h1 class="head-title">
                {year}<span class="head-sep">·</span><span class="head-month">{mm}</span>
            </h1>
            <div class="head-meta mono">
                {#if selectedRegion}
                    <span class="meta-region">{selectedRegion.code}</span> 대회
                    <span class="meta-num">{selectedRegion.count}</span>개
                {:else}
                    {activeRegionCount}개 시·도 · 대회 <span class="meta-num">{totalRaces}</span>개
                {/if}
            </div>
        </div>

        <div class="head-controls">
            <div class="view-toggle" role="group" aria-label="보기 모드">
                <a class="vt-item" href="/calendar?{navQuery(year, month)}">캘린더</a>
                <a class="vt-item" href="/calendar/map?{navQuery(year, month)}">지도 SVG</a>
                <span class="vt-item active" aria-current="page">지도 Kakao</span>
            </div>
            <nav class="month-nav" aria-label="월 이동">
                <a
                    class="nav-btn"
                    href="/calendar/kakaomap?{navQuery(previousMonth.year, previousMonth.month)}"
                    aria-label="이전 달">← {previousMonth.month}월</a
                >
                <a
                    class="nav-btn nav-today"
                    class:active={year === currentYear && month === currentMonth}
                    href="/calendar/kakaomap?{navQuery(currentYear, currentMonth)}"
                    >{currentMonth}월</a
                >
                <a
                    class="nav-btn"
                    href="/calendar/kakaomap?{navQuery(nextMonth.year, nextMonth.month)}"
                    aria-label="다음 달">{nextMonth.month}월 →</a
                >
            </nav>
        </div>
    </header>

    <section class="map-layout">
        <!-- ── Map stage ─────────────────────────────────────────── -->
        <div class="map-stage">
            {#if selected}
                <button class="map-back" onclick={clearSelection}>
                    <span aria-hidden="true">←</span> 전체 지도
                </button>
            {/if}
            <div class="map-hint mono" aria-hidden="true">
                {#if selected}
                    KAKAO · 지역 줌 · {selected}
                    {#if missingCoordCount > 0}
                        <span class="hint-warn">· {missingCoordCount}개 위치 미상</span>
                    {/if}
                {:else}
                    KAKAO · 전국 개요 · 지역을 선택해 확대
                {/if}
            </div>

            <div bind:this={mapEl} class="map-canvas"></div>

            {#if !kakaoJsKey}
                <div class="map-fallback mono">
                    카카오맵 키가 설정되지 않았습니다 (PUBLIC_KAKAO_JAVASCRIPT_KEY)
                </div>
            {:else if mapFailed}
                <div class="map-fallback mono">카카오맵을 불러오지 못했습니다</div>
            {:else if !kakaoReady}
                <div class="map-fallback mono">지도 불러오는 중…</div>
            {/if}

            <div class="map-legend mono" aria-hidden="true">
                {#each SPORT_ORDER as s}
                    <span class="legend-item">
                        <span class="legend-dot" style="background: {SPORT_COLOR[s]};"></span>
                        {arenaSportShort[s]}
                    </span>
                {/each}
            </div>
        </div>

        <!-- ── Side panel ────────────────────────────────────────── -->
        <aside class="map-panel">
            {#if selectedRegion}
                <!-- Region detail -->
                <div class="panel-head detail">
                    <button class="panel-back mono" onclick={clearSelection}>
                        <span aria-hidden="true">←</span> 전체 지도로
                    </button>
                    <div class="detail-title-row">
                        <div class="panel-title mono">
                            {selectedRegion.code}
                            <span class="panel-num">{selectedRegion.count}</span>
                        </div>
                        <div class="sport-break">
                            {#each sportBreakdown(selectedRegion.races) as b}
                                <span class="break-item" title="{arenaSportShort[b.sport]} {b.count}">
                                    <span
                                        class="break-dot"
                                        style="background: {SPORT_COLOR[b.sport]};"
                                    ></span>
                                    <span class="break-n mono">{b.count}</span>
                                </span>
                            {/each}
                        </div>
                    </div>
                </div>

                <div class="row-head mono">
                    <span class="c-idx">#</span>
                    <span class="c-date">DATE</span>
                    <span class="c-race">RACE</span>
                    <span class="c-dist">DIST</span>
                    <span class="c-stat">STATUS</span>
                </div>

                <div class="panel-scroll">
                    {#if regionRaces.length === 0}
                        <div class="panel-empty mono">이 지역에는 {month}월 대회가 없습니다</div>
                    {:else}
                        {#each regionRaces as race, i (race.id)}
                            {@const st = raceState(race)}
                            {@const pinned = hasCoords(race)}
                            <a
                                class="race-row"
                                href={race.url}
                                onmouseenter={() => highlightRace(race.id)}
                                onmouseleave={() => highlightRace(null)}
                                onfocus={() => highlightRace(race.id)}
                                onblur={() => highlightRace(null)}
                            >
                                <span
                                    class="c-idx mono"
                                    class:no-pin={!pinned}
                                    title={pinned ? `지도 핀 ${i + 1}` : '지도 위치 미상'}
                                    >{pinned ? String(i + 1).padStart(2, '0') : '··'}</span
                                >
                                <span class="c-date mono">{shortDate(race.raceDate)}</span>
                                <span class="c-race" class:closed={st.closed}>
                                    <span
                                        class="race-swatch"
                                        style="background: {SPORT_COLOR[race.sport]};"
                                    ></span>
                                    <span class="race-name">{race.title}</span>
                                </span>
                                <span class="c-dist mono">{arenaDistLabel(race)}</span>
                                <span
                                    class="c-stat mono"
                                    class:closed={st.closed}
                                    class:urgent={st.urgent}>{st.label}</span
                                >
                            </a>
                        {/each}
                    {/if}
                </div>

                {#if missingCoordCount > 0}
                    <div class="panel-foot mono">
                        <span>지도 핀 {regionPins.length}</span>
                        <span class="foot-warn">위치 미상 {missingCoordCount}</span>
                    </div>
                {/if}
            {:else}
                <!-- Overview -->
                <div class="panel-head">
                    <div class="arena-kicker">지역 선택 →</div>
                    <div class="panel-title mono">
                        전국 <span class="panel-num">{totalRaces}</span>
                    </div>
                    <p class="panel-desc">
                        지도의 핀을 누르면 대회 정보가 열리고, 아래 지역을 누르면 해당 시·도로
                        지도가 확대돼요.
                    </p>
                </div>

                <div class="row-head mono">
                    <span class="o-idx">#</span>
                    <span class="o-region">REGION</span>
                    <span class="o-n">N</span>
                    <span class="o-sports">SPORTS</span>
                    <span class="o-arrow"></span>
                </div>

                <div class="panel-scroll">
                    {#if regionStats.length === 0}
                        <div class="panel-empty mono">{month}월에 등록된 대회가 없습니다</div>
                    {:else}
                        {#each regionStats as r, i (r.code)}
                            <button
                                class="region-row"
                                onclick={() => selectRegion(r.code, r.count)}
                            >
                                <span class="o-idx mono">{String(i + 1).padStart(2, '0')}</span>
                                <span class="o-region">{r.code}</span>
                                <span class="o-n mono">{r.count}</span>
                                <span class="o-sports">
                                    {#each sportBreakdown(r.races) as b}
                                        <span
                                            class="sport-bar"
                                            title="{arenaSportShort[b.sport]} {b.count}"
                                            style="background: {SPORT_COLOR[
                                                b.sport
                                            ]}; flex: {b.count};"
                                        ></span>
                                    {/each}
                                </span>
                                <span class="o-arrow mono" aria-hidden="true">›</span>
                            </button>
                        {/each}
                    {/if}
                </div>

                <div class="panel-foot mono">
                    <span>{activeRegionCount}개 지역</span>
                    {#if unmappedCount > 0}
                        <span class="foot-warn">미지정·기타 {unmappedCount}건</span>
                    {:else}
                        <span>클릭 · esc 전체</span>
                    {/if}
                </div>
            {/if}
        </aside>
    </section>
</div>

<style>
    .map-wrap {
        max-width: 1400px;
        margin: 0 auto;
        padding: 24px 16px 40px;
        color: var(--arena-ink);
    }
    @media (min-width: 1024px) {
        .map-wrap {
            padding: 36px 32px 60px;
        }
    }
    .mono {
        font-family: var(--arena-f-mono);
    }

    /* ── Header ─────────────────────────── */
    .map-head {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 16px;
        flex-wrap: wrap;
        margin-bottom: 20px;
    }
    .head-title {
        font-family: var(--arena-f-display);
        font-size: 44px;
        font-weight: 700;
        letter-spacing: -1.5px;
        line-height: 1;
        margin: 6px 0;
        display: inline-flex;
        align-items: baseline;
        gap: 8px;
    }
    @media (min-width: 720px) {
        .head-title {
            font-size: 56px;
            letter-spacing: -2px;
        }
    }
    .head-sep {
        color: var(--arena-ink-mute);
        font-weight: 400;
    }
    .head-month {
        color: var(--arena-accent-deep);
    }
    .head-meta {
        font-size: 11px;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
    }
    .meta-num,
    .meta-region {
        color: var(--arena-accent-deep);
        font-weight: 600;
    }

    .head-controls {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        align-items: flex-end;
    }
    .view-toggle {
        display: inline-flex;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
    }
    .vt-item {
        padding: 9px 14px;
        font-family: var(--arena-f-mono);
        font-size: 12px;
        letter-spacing: 0.5px;
        color: var(--arena-ink-soft);
        text-decoration: none;
        border-right: 1px solid var(--arena-line-soft);
        white-space: nowrap;
    }
    .vt-item:last-child {
        border-right: none;
    }
    .vt-item:hover {
        background: var(--arena-paper-alt);
        color: var(--arena-ink);
    }
    .vt-item.active {
        background: var(--arena-ink);
        color: var(--arena-paper);
        font-weight: 600;
    }

    .month-nav {
        display: inline-flex;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
    }
    .nav-btn {
        padding: 9px 14px;
        font-family: var(--arena-f-mono);
        font-size: 12px;
        letter-spacing: 0.5px;
        color: var(--arena-ink);
        border-right: 1px solid var(--arena-line-soft);
        text-decoration: none;
        white-space: nowrap;
    }
    .nav-btn:last-child {
        border-right: none;
    }
    .nav-btn:hover {
        background: var(--arena-paper-alt);
    }
    .nav-today {
        background: var(--arena-ink);
        color: var(--arena-paper);
        letter-spacing: 1.5px;
        font-weight: 600;
    }
    .nav-today:hover {
        background: var(--arena-ink);
        color: var(--arena-accent);
    }

    /* ── Layout ─────────────────────────── */
    .map-layout {
        --stage-h: clamp(560px, 82vh, 900px);
        display: grid;
        grid-template-columns: 1fr;
        border: 1px solid var(--arena-line);
        background: var(--arena-paper);
    }
    @media (min-width: 880px) {
        .map-layout {
            grid-template-columns: 1fr 360px;
        }
    }

    /* ── Map stage ─────────────────────────── */
    .map-stage {
        position: relative;
        height: 460px;
        background: var(--arena-paper-alt);
        border-bottom: 1px solid var(--arena-line);
        overflow: hidden;
    }
    @media (min-width: 880px) {
        .map-stage {
            height: var(--stage-h);
            border-bottom: none;
            border-right: 1px solid var(--arena-line);
        }
    }
    .map-canvas {
        width: 100%;
        height: 100%;
    }
    .map-fallback {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 24px;
        font-size: 11px;
        letter-spacing: 0.6px;
        color: var(--arena-ink-mute);
        background: var(--arena-paper-alt);
        z-index: 6;
    }

    .map-back {
        position: absolute;
        top: 14px;
        left: 14px;
        z-index: 7;
        padding: 8px 14px;
        background: var(--arena-ink);
        color: var(--arena-paper);
        border: 1px solid var(--arena-ink);
        font-family: var(--arena-f-mono);
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.8px;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    .map-back:hover {
        background: var(--arena-ink-soft);
    }
    .map-hint {
        position: absolute;
        top: 18px;
        right: 18px;
        z-index: 7;
        font-size: 10px;
        letter-spacing: 1.6px;
        font-weight: 600;
        color: var(--arena-ink-mute);
        text-align: right;
        max-width: 62%;
        background: color-mix(in srgb, var(--arena-paper) 82%, transparent);
        padding: 3px 7px;
        pointer-events: none;
    }
    .hint-warn {
        color: var(--arena-urgent);
    }
    .map-legend {
        position: absolute;
        left: 14px;
        bottom: 14px;
        z-index: 7;
        display: flex;
        flex-wrap: wrap;
        gap: 4px 10px;
        padding: 7px 10px;
        background: color-mix(in srgb, var(--arena-paper) 88%, transparent);
        border: 1px solid var(--arena-line-soft);
        font-size: 10px;
        letter-spacing: 0.4px;
        color: var(--arena-ink-soft);
        pointer-events: none;
    }
    .legend-item {
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    .legend-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: block;
    }

    /* ── Kakao custom-overlay pins (injected outside Svelte scope) ─── */
    :global(.k-pin) {
        position: relative;
        width: 16px;
        height: 16px;
        cursor: pointer;
        transition:
            transform 0.12s ease,
            opacity 0.2s ease;
    }
    :global(.k-pin-dot) {
        position: absolute;
        inset: 0;
        border-radius: 50%;
        background: var(--pc);
        border: 2px solid #fff;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.35);
    }
    :global(.k-pin-num) {
        position: absolute;
        bottom: 19px;
        left: 50%;
        transform: translateX(-50%);
        font-family: var(--arena-f-mono, monospace);
        font-size: 9px;
        font-weight: 700;
        color: #1a1a1a;
        background: rgba(255, 255, 255, 0.9);
        padding: 0 3px;
        border-radius: 2px;
        white-space: nowrap;
    }
    :global(.k-pin:hover),
    :global(.k-pin.active) {
        transform: scale(1.45);
    }
    :global(.k-pin.dim) {
        opacity: 0.25;
    }
    :global(.k-pin.closed .k-pin-dot) {
        opacity: 0.55;
    }

    /* ── Cluster bubble (2+ adjacent races) ─────────────────────────── */
    :global(.k-cluster) {
        position: relative;
        min-width: 28px;
        height: 28px;
        padding: 0 10px;
        border-radius: 999px;
        background: var(--pc);
        color: #fff;
        font-family: var(--arena-f-mono, monospace);
        font-size: 12.5px;
        font-weight: 700;
        letter-spacing: 0.4px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        border: 2px solid #fff;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
        transition:
            transform 0.12s ease,
            opacity 0.2s ease;
        z-index: 4;
    }
    :global(.k-cluster:hover),
    :global(.k-cluster.active) {
        transform: scale(1.1);
        z-index: 30;
    }
    :global(.k-cluster.dim) {
        opacity: 0.28;
    }
    :global(.k-cluster.closed) {
        opacity: 0.6;
    }
    :global(.k-cluster-num) {
        pointer-events: none;
        line-height: 1;
    }

    /* Hover tooltip — child of the cluster so :hover stays active while the
       cursor is over the list. padding-bottom extends the hover zone over
       the (visual) gap so the tip doesn't flicker. */
    :global(.k-cluster-tip) {
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        padding-bottom: 8px;
        display: none;
        z-index: 31;
    }
    :global(.k-cluster:hover .k-cluster-tip) {
        display: block;
    }
    :global(.k-cluster-tip-box) {
        background: #fff;
        border: 1px solid #d6d6d6;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
        min-width: 240px;
        max-width: 300px;
        border-radius: 3px;
        overflow: hidden;
    }
    :global(.k-cluster-tip-box)::after {
        content: '';
        position: absolute;
        bottom: 2px;
        left: 50%;
        transform: translateX(-50%);
        width: 0;
        height: 0;
        border-left: 6px solid transparent;
        border-right: 6px solid transparent;
        border-top: 6px solid #fff;
        filter: drop-shadow(0 1px 0 #d6d6d6);
    }
    :global(.k-cluster-tip-head) {
        padding: 8px 12px;
        border-bottom: 1px solid #eee;
        font-family: var(--arena-f-mono, monospace);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.4px;
        color: #666;
        text-transform: uppercase;
    }
    :global(.k-cluster-tip-list) {
        max-height: 260px;
        overflow-y: auto;
    }
    :global(.k-cluster-row) {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 7px 12px;
        font-size: 12px;
        color: #1a1a1a;
        text-decoration: none;
        border-bottom: 1px solid #f1f1f1;
    }
    :global(.k-cluster-row:last-child) {
        border-bottom: none;
    }
    :global(.k-cluster-row:hover) {
        background: #f6f6f6;
    }
    :global(.k-cluster-row.is-closed .k-cluster-name) {
        color: #999;
        text-decoration: line-through;
        text-decoration-color: #ccc;
    }
    :global(.k-cluster-date) {
        font-family: var(--arena-f-mono, monospace);
        font-size: 10.5px;
        color: #666;
        width: 36px;
        flex-shrink: 0;
    }
    :global(.k-cluster-dot) {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
        display: block;
    }
    :global(.k-cluster-name) {
        flex: 1;
        min-width: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    :global(.k-cluster-dist) {
        font-family: var(--arena-f-mono, monospace);
        font-size: 10.5px;
        color: #888;
        flex-shrink: 0;
    }

    /* ── Side panel ─────────────────────────── */
    .map-panel {
        display: flex;
        flex-direction: column;
        background: var(--arena-paper-alt);
        min-width: 0;
    }
    @media (min-width: 880px) {
        .map-panel {
            height: var(--stage-h);
        }
    }
    .panel-head {
        padding: 16px 20px 14px;
        border-bottom: 1px solid var(--arena-line);
        background: var(--arena-paper-alt);
    }
    .panel-title {
        font-size: 22px;
        font-weight: 500;
        letter-spacing: -0.3px;
        margin-top: 6px;
    }
    .panel-num {
        color: var(--arena-accent-deep);
        font-weight: 700;
    }
    .panel-desc {
        font-size: 12px;
        line-height: 1.5;
        color: var(--arena-ink-soft);
        margin: 8px 0 0;
    }
    .panel-back {
        background: transparent;
        border: none;
        padding: 0;
        font-size: 10px;
        letter-spacing: 1.4px;
        font-weight: 600;
        color: var(--arena-ink-soft);
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .panel-back:hover {
        color: var(--arena-ink);
    }
    .detail-title-row {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 12px;
        margin-top: 8px;
    }
    .panel-head.detail .panel-title {
        margin-top: 0;
    }
    .sport-break {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        justify-content: flex-end;
    }
    .break-item {
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    .break-dot {
        width: 8px;
        height: 8px;
        display: block;
    }
    .break-n {
        font-size: 10px;
        font-weight: 600;
        color: var(--arena-ink-soft);
    }

    .row-head {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 20px 6px;
        font-size: 10px;
        letter-spacing: 1.2px;
        font-weight: 600;
        color: var(--arena-ink-mute);
    }
    .panel-scroll {
        flex: 1;
        overflow-y: auto;
        padding: 4px 0;
    }

    /* Overview rows */
    .o-idx {
        width: 22px;
        flex-shrink: 0;
    }
    .o-region {
        flex: 1;
        min-width: 0;
    }
    .o-n {
        width: 30px;
        text-align: right;
        flex-shrink: 0;
    }
    .o-sports {
        width: 104px;
        display: flex;
        gap: 2px;
        height: 10px;
        flex-shrink: 0;
        justify-content: flex-end;
    }
    .o-arrow {
        width: 14px;
        text-align: right;
        flex-shrink: 0;
    }
    .region-row {
        display: flex;
        align-items: center;
        gap: 8px;
        width: 100%;
        padding: 10px 20px;
        background: transparent;
        border: none;
        border-bottom: 1px solid var(--arena-line-soft);
        font-family: var(--arena-f-body);
        font-size: 13px;
        color: var(--arena-ink);
        cursor: pointer;
        text-align: left;
    }
    .region-row:hover {
        background: var(--arena-paper-deep);
    }
    .region-row .o-idx {
        font-size: 9px;
        font-weight: 700;
        color: var(--arena-ink-mute);
    }
    .region-row .o-region {
        font-weight: 600;
    }
    .region-row .o-n {
        font-size: 13px;
        font-weight: 700;
    }
    .sport-bar {
        height: 10px;
        min-width: 4px;
        display: block;
    }
    .region-row .o-arrow {
        color: var(--arena-ink-mute);
    }

    /* Detail race rows */
    .c-idx {
        width: 24px;
        flex-shrink: 0;
    }
    .c-date {
        width: 44px;
        flex-shrink: 0;
    }
    .c-race {
        flex: 1;
        min-width: 0;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .c-dist {
        width: 50px;
        flex-shrink: 0;
    }
    .c-stat {
        width: 48px;
        text-align: right;
        flex-shrink: 0;
    }
    .race-row {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 20px;
        border-bottom: 1px solid var(--arena-line-soft);
        font-family: var(--arena-f-body);
        font-size: 12px;
        color: var(--arena-ink);
        text-decoration: none;
    }
    .race-row:hover {
        background: var(--arena-paper-deep);
    }
    .race-row .c-idx {
        font-size: 9px;
        font-weight: 700;
        color: var(--arena-ink-mute);
    }
    .race-row .c-idx.no-pin {
        color: var(--arena-line-soft);
        font-weight: 400;
    }
    .race-row .c-date {
        font-size: 10.5px;
        color: var(--arena-ink-soft);
    }
    .race-swatch {
        width: 7px;
        height: 7px;
        flex-shrink: 0;
        display: block;
    }
    .race-name {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        min-width: 0;
    }
    .race-row:hover .race-name {
        text-decoration: underline;
    }
    .c-race.closed .race-name {
        color: var(--arena-ink-mute);
        text-decoration: line-through;
        text-decoration-color: var(--arena-line-soft);
    }
    .c-race.closed .race-swatch {
        opacity: 0.5;
    }
    .c-stat {
        font-size: 9.5px;
        font-weight: 700;
        letter-spacing: 0.6px;
        color: var(--arena-accent-deep);
    }
    .c-stat.urgent {
        color: var(--arena-urgent);
    }
    .c-stat.closed {
        color: var(--arena-ink-mute);
        font-weight: 600;
    }

    .panel-empty {
        padding: 44px 20px;
        text-align: center;
        font-size: 11px;
        color: var(--arena-ink-mute);
    }
    .panel-foot {
        display: flex;
        justify-content: space-between;
        padding: 12px 20px;
        border-top: 1px solid var(--arena-line);
        background: var(--arena-paper-deep);
        font-size: 10px;
        letter-spacing: 0.6px;
        color: var(--arena-ink-mute);
    }
    .foot-warn {
        color: var(--arena-urgent);
        font-weight: 600;
    }

    @media (prefers-reduced-motion: reduce) {
        :global(.k-pin),
        :global(.k-cluster) {
            transition: none;
        }
    }
</style>
