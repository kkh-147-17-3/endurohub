<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import type { PageData } from './$types';
    import type { Race, Sport } from '$lib/types';
    import { track } from '$lib/analytics';
    import { arenaDday, arenaDdayLabel, arenaDistLabel, arenaSportShort } from '$lib/arena';
    import { KOREA_PROVINCES, KOREA_VIEWBOX, type KoreaProvince } from '$lib/geo/korea-provinces';
    import { KOREA_MUNICIPALITIES } from '$lib/geo/korea-municipalities';
    import { projectLngLat, fitBbox, IDENTITY_FIT } from '$lib/geo/project';
    import WeatherIcon from '$lib/components/arena/WeatherIcon.svelte';

    let { data }: { data: PageData } = $props();

    const year = $derived(data.year);
    const month = $derived(data.month);
    const racesGrouped = $derived(data.racesGrouped);
    const previousMonth = $derived(data.previousMonth);
    const nextMonth = $derived(data.nextMonth);
    const sport = $derived(
        (Array.isArray(data.sport) ? data.sport : data.sport ? [data.sport] : []) as string[],
    );

    const allRaces = $derived(Object.values(racesGrouped).flat());

    onMount(() => {
        track('calendar_map_view', { year, month });
    });
    onDestroy(() => {
        clearTimeout(settleTimer);
        if (clusterHoverTimer) clearTimeout(clusterHoverTimer);
    });

    // ── Sport encoding ────────────────────────────────────────────────
    // Colors mirror the arena RaceRow / calendar grid exactly.
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

    const racesByRegion = $derived.by(() => {
        const m = new Map<string, Race[]>();
        for (const r of allRaces) {
            if (!r.region) continue;
            const list = m.get(r.region) ?? [];
            list.push(r);
            m.set(r.region, list);
        }
        return m;
    });

    // Real province geometry (path / centroid / bbox) joined with race counts.
    type RegionStat = KoreaProvince & { races: Race[]; count: number };
    const regionStats = $derived.by<RegionStat[]>(() =>
        KOREA_PROVINCES.map((p) => {
            const races = [...(racesByRegion.get(p.code) ?? [])].sort(byDate);
            return { ...p, races, count: races.length };
        }),
    );

    const totalRaces = $derived(allRaces.length);
    const activeRegionCount = $derived(regionStats.filter((r) => r.count > 0).length);
    const maxRegionCount = $derived(Math.max(1, ...regionStats.map((r) => r.count)));
    // Races whose region has no province geometry (기타 / null region).
    const unmappedCount = $derived(
        totalRaces - regionStats.reduce((sum, r) => sum + r.count, 0),
    );

    // Largest bubbles drawn first so small metros stay clickable on top.
    const bubbleStats = $derived(
        [...regionStats].filter((r) => r.count > 0).sort((a, b) => b.count - a.count),
    );
    // Re-order so the hovered region is rendered last → on top, so its
    // scaled-up shape isn't clipped by a neighbour drawn afterwards.
    const orderedRegionStats = $derived.by<RegionStat[]>(() => {
        if (selected || !hovered) return regionStats;
        const idx = regionStats.findIndex((r) => r.code === hovered);
        if (idx < 0) return regionStats;
        return [
            ...regionStats.slice(0, idx),
            ...regionStats.slice(idx + 1),
            regionStats[idx],
        ];
    });
    // Regions sorted by race count, used by the overview side panel.
    const overview = $derived(
        [...regionStats].filter((r) => r.count > 0).sort((a, b) => b.count - a.count),
    );

    // ── Selection / zoom ──────────────────────────────────────────────
    let selected = $state<string | null>(null);
    // The heavy SVG layers (overview bubbles, and 시·군·구 + race pins) are
    // mounted only once the zoom transition settles — so the transition
    // itself animates just the 17 province paths and stays smooth.
    let overviewVisible = $state(true);
    let detailVisible = $state(false);
    let settleTimer: ReturnType<typeof setTimeout> | undefined;
    const ZOOM_MS = 520;

    const selectedRegion = $derived(
        selected ? (regionStats.find((r) => r.code === selected) ?? null) : null,
    );
    const regionRaces = $derived(selectedRegion ? selectedRegion.races : []);

    // Overview hover — the region under the pointer/focus, for the info tooltip.
    let hovered = $state<string | null>(null);
    const hoveredRegion = $derived(
        hovered ? (regionStats.find((r) => r.code === hovered) ?? null) : null,
    );

    // Detail-view (depth-2) pin hover — the race under the pointer/focus.
    let hoveredPin = $state<number | null>(null);
    // Cluster hover index (depth-2). Set when a multi-race cluster glyph is
    // hovered; mutually exclusive with hoveredPin in practice.
    let hoveredGroup = $state<number | null>(null);
    // On-screen pixel threshold for grouping two adjacent pins.
    const CLUSTER_VIEWBOX_PX = 22;

    // 시·군·구 sub-polygons for the focused province (drill-down detail).
    const municipalities = $derived(selected ? (KOREA_MUNICIPALITIES[selected] ?? []) : []);

    const fit = $derived(selectedRegion ? fitBbox(selectedRegion.bbox) : IDENTITY_FIT);
    const groupTransform = $derived(fit.transform);
    // Counter-scale overlaid labels and pins by 1/zoom so they keep a
    // constant on-screen size however far the selected province is zoomed.
    const muniFontSize = $derived(11 / fit.scale);
    const pinScale = $derived(1 / fit.scale);

    // Race pins — only races with real coordinates. `n` is the 1-based index
    // within the full region race list, so it matches the side-panel row.
    type Pin = { race: Race; n: number; x: number; y: number };
    const regionPins = $derived.by<Pin[]>(() => {
        if (!selectedRegion) return [];
        const pins: Pin[] = [];
        regionRaces.forEach((race, i) => {
            if (race.latitude != null && race.longitude != null) {
                const [x, y] = projectLngLat(race.longitude, race.latitude);
                pins.push({ race, n: i + 1, x, y });
            }
        });
        return pins;
    });
    const missingCoordCount = $derived(
        selectedRegion ? regionRaces.length - regionPins.length : 0,
    );

    // Greedy pixel-distance clustering. Two pins merge when their projected
    // distance, multiplied by the current zoom, is below CLUSTER_VIEWBOX_PX.
    // Dominant sport drives the cluster color so it still reads as a member
    // of the same legend the pins use.
    type PinGroup = {
        pins: Pin[];
        cx: number;
        cy: number;
        dominantSport: Sport;
        allClosed: boolean;
    };
    const regionPinGroups = $derived.by<PinGroup[]>(() => {
        const pins = regionPins;
        if (pins.length === 0) return [];
        const threshold = CLUSTER_VIEWBOX_PX / fit.scale;
        const thresholdSq = threshold * threshold;
        const used = new Set<number>();
        const groups: PinGroup[] = [];
        for (let i = 0; i < pins.length; i++) {
            if (used.has(i)) continue;
            const group: Pin[] = [pins[i]];
            used.add(i);
            for (let j = i + 1; j < pins.length; j++) {
                if (used.has(j)) continue;
                const dx = pins[i].x - pins[j].x;
                const dy = pins[i].y - pins[j].y;
                if (dx * dx + dy * dy < thresholdSq) {
                    group.push(pins[j]);
                    used.add(j);
                }
            }
            const cx = group.reduce((s, p) => s + p.x, 0) / group.length;
            const cy = group.reduce((s, p) => s + p.y, 0) / group.length;
            const counts = new Map<Sport, number>();
            for (const p of group) counts.set(p.race.sport, (counts.get(p.race.sport) ?? 0) + 1);
            const dominantSport = [...counts.entries()].sort((a, b) => b[1] - a[1])[0][0];
            const allClosed = group.every((p) => raceState(p.race).closed);
            groups.push({ pins: group, cx, cy, dominantSport, allClosed });
        }
        return groups;
    });

    const hoveredPinData = $derived(
        hoveredPin != null ? (regionPins.find((p) => p.race.id === hoveredPin) ?? null) : null,
    );
    const hoveredGroupData = $derived(
        hoveredGroup != null ? (regionPinGroups[hoveredGroup] ?? null) : null,
    );

    function selectRegion(code: string, count: number) {
        if (count === 0 || selected === code) return;
        clearTimeout(settleTimer);
        hovered = null;
        hoveredPin = null;
        hoveredGroup = null;
        selected = code;
        overviewVisible = false;
        detailVisible = false;
        track('calendar_map_region', { region: code, count });
        // Reveal 시·군·구 + pins only after the zoom transition finishes.
        settleTimer = setTimeout(() => {
            detailVisible = true;
        }, ZOOM_MS);
    }
    function clearSelection() {
        if (!selected) return;
        clearTimeout(settleTimer);
        selected = null;
        hoveredPin = null;
        hoveredGroup = null;
        detailVisible = false;
        // Restore the overview bubbles after the zoom-out transition.
        settleTimer = setTimeout(() => {
            overviewVisible = true;
        }, ZOOM_MS);
    }
    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Escape' && selected) clearSelection();
    }

    // ── Helpers ───────────────────────────────────────────────────────
    // Area-proportional bubble radius (sqrt) so large metros don't dominate.
    function dotRadius(count: number): number {
        return count === 0 ? 0 : Math.min(18, 6 + Math.sqrt(count) * 2.4);
    }

    // 서울 sits geographically inside 경기, so their centroids nearly
    // coincide — nudge those two bubbles apart so both stay legible.
    const BUBBLE_NUDGE: Record<string, [number, number]> = {
        서울: [-5, -17],
        경기: [9, 19],
    };
    function bubbleXY(r: RegionStat): [number, number] {
        const [dx, dy] = BUBBLE_NUDGE[r.code] ?? [0, 0];
        return [r.centroid[0] + dx, r.centroid[1] + dy];
    }

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

    // Height of one race card in the single-pin hover tooltip.
    // Grows by 20px when the race has a location row, and by 40px when a
    // weather block is appended at the bottom (header + subline).
    function cardHeight(race: Race): number {
        let h = 72;
        if (race.location) h += 20;
        if (cardWeather(race)) h += 40;
        return h;
    }

    // Prefer the race-time window (more relevant), fall back to the full-day
    // forecast. Returns null when no usable weather data is available.
    type CardWeather = {
        code: number | null;
        condition: string | null;
        tempLow: number | null;
        tempHigh: number | null;
        isRaceWindow: boolean;
    };
    function cardWeather(race: Race): CardWeather | null {
        const w = race.weatherForecast;
        if (!w) return null;
        const rw = w.raceWindow ?? null;
        const code = rw?.weatherCode ?? w.weatherCode ?? null;
        const condition = rw?.condition ?? w.condition ?? null;
        if (code == null && !condition) return null;
        const tempLow = rw?.tempMin ?? w.tempLow ?? null;
        const tempHigh = rw?.tempMax ?? w.tempHigh ?? null;
        return { code, condition, tempLow, tempHigh, isRaceWindow: rw != null };
    }
    function tempLabel(w: CardWeather): string | null {
        if (w.tempLow != null && w.tempHigh != null) {
            return `${Math.round(w.tempLow)}° / ${Math.round(w.tempHigh)}°`;
        }
        if (w.tempHigh != null) return `${Math.round(w.tempHigh)}°`;
        if (w.tempLow != null) return `${Math.round(w.tempLow)}°`;
        return null;
    }
    // Compact equivalent of the race-detail page's weather sub-line.
    // Race-window forecast contributes 체감/비 max/wind; otherwise fall back
    // to the day forecast's rain probability + wind.
    function weatherSubline(race: Race): string {
        const w = race.weatherForecast;
        if (!w) return '';
        const rw = w.raceWindow ?? null;
        const parts: string[] = [];
        if (rw?.apparentTempMin != null && rw.apparentTempMax != null) {
            parts.push(
                `체감 ${Math.round(rw.apparentTempMin)}~${Math.round(rw.apparentTempMax)}°`,
            );
        }
        const rainProb = rw?.rainProbMax ?? w.rainProb ?? null;
        if (rainProb != null) parts.push(`비 ${rainProb}%`);
        const wind = rw?.wind ?? w.wind ?? null;
        if (wind) parts.push(wind);
        return parts.join(' · ');
    }

    // Approximate ground distance (km) between two race coordinates. Used to
    // label the rough extent of a cluster in its tooltip header.
    function haversineKm(a: Race, b: Race): number {
        if (a.latitude == null || a.longitude == null || b.latitude == null || b.longitude == null) {
            return 0;
        }
        const R = 6371;
        const toRad = Math.PI / 180;
        const dLat = (b.latitude - a.latitude) * toRad;
        const dLng = (b.longitude - a.longitude) * toRad;
        const lat1 = a.latitude * toRad;
        const lat2 = b.latitude * toRad;
        const h =
            Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
        return 2 * R * Math.asin(Math.sqrt(h));
    }
    function maxPairwiseKm(pins: Pin[]): number {
        let max = 0;
        for (let i = 0; i < pins.length; i++) {
            for (let j = i + 1; j < pins.length; j++) {
                const km = haversineKm(pins[i].race, pins[j].race);
                if (km > max) max = km;
            }
        }
        return max;
    }
    function formatProximity(km: number): string {
        if (km < 0.1) return '같은 위치';
        if (km < 1) return `근접 ${Math.round(km * 1000)}m 내`;
        if (km < 10) return `근접 ${km.toFixed(1)}km 내`;
        return `근접 ${Math.round(km)}km 내`;
    }
    function shortSportLabel(s: Sport): string {
        if (s === 'trail_running') return '트레일';
        if (s === 'triathlon') return '철인';
        return arenaSportShort[s];
    }

    // Bridge the gap between cluster pin and tooltip — without a delay the
    // tooltip vanishes the moment the cursor leaves the pin, so users can't
    // interact with rows inside.
    let clusterHoverTimer: ReturnType<typeof setTimeout> | null = null;
    function setClusterHover(gi: number) {
        if (clusterHoverTimer) {
            clearTimeout(clusterHoverTimer);
            clusterHoverTimer = null;
        }
        hoveredGroup = gi;
    }
    function scheduleClusterClear() {
        if (clusterHoverTimer) clearTimeout(clusterHoverTimer);
        clusterHoverTimer = setTimeout(() => {
            hoveredGroup = null;
            clusterHoverTimer = null;
        }, 220);
    }
    function cancelClusterClear() {
        if (clusterHoverTimer) {
            clearTimeout(clusterHoverTimer);
            clusterHoverTimer = null;
        }
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
    <title>{year}년 {month}월 대회 지도 - 엔듀로허브</title>
    <meta
        name="description"
        content="{year}년 {month}월 마라톤·수영·자전거·철인3종·트레일러닝 대회를 시·도별 지도에서 확인하세요."
    />
</svelte:head>

<svelte:window onkeydown={handleKeydown} />

<div class="map-wrap">
    <header class="map-head">
        <div class="head-left">
            <div class="arena-kicker">
                엔듀로허브 · 캘린더 · 지도{selected ? ` · ${selected}` : ''}
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
                <span class="vt-item active" aria-current="page">지도 SVG</span>
                <a class="vt-item" href="/calendar/kakaomap?{navQuery(year, month)}">지도 Kakao</a>
            </div>
            <nav class="month-nav" aria-label="월 이동">
                <a
                    class="nav-btn"
                    href="/calendar/map?{navQuery(previousMonth.year, previousMonth.month)}"
                    aria-label="이전 달">← {previousMonth.month}월</a
                >
                <a
                    class="nav-btn nav-today"
                    class:active={year === currentYear && month === currentMonth}
                    href="/calendar/map?{navQuery(currentYear, currentMonth)}">{currentMonth}월</a
                >
                <a
                    class="nav-btn"
                    href="/calendar/map?{navQuery(nextMonth.year, nextMonth.month)}"
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
                    VIEW · 지역 줌 · {selected}
                    {#if missingCoordCount > 0}
                        <span class="hint-warn">· {missingCoordCount}개 위치 미상</span>
                    {/if}
                {:else}
                    VIEW · 전국 개요 · 지역을 클릭해 확대
                {/if}
            </div>

            <svg
                viewBox="0 0 {KOREA_VIEWBOX.w} {KOREA_VIEWBOX.h}"
                preserveAspectRatio="xMidYMid meet"
                class="map-svg"
                class:has-hover={!!hovered && !selected}
            >
                <defs>
                    <pattern id="topo" patternUnits="userSpaceOnUse" width="40" height="40">
                        <path
                            d="M0 20 Q 10 10, 20 20 T 40 20"
                            stroke="var(--arena-line-soft)"
                            stroke-width="0.5"
                            fill="none"
                        />
                    </pattern>
                </defs>
                <rect
                    x="0"
                    y="0"
                    width={KOREA_VIEWBOX.w}
                    height={KOREA_VIEWBOX.h}
                    fill="url(#topo)"
                    opacity="0.6"
                />

                {#snippet raceCard(pin: Pin, y: number, tw: number)}
                    {@const st = raceState(pin.race)}
                    {@const h = cardHeight(pin.race)}
                    {@const wx = cardWeather(pin.race)}
                    {@const wxTemp = wx ? tempLabel(wx) : null}
                    {@const wxSub = wx ? weatherSubline(pin.race) : ''}
                    {@const wxDividerY = pin.race.location ? 84 : 64}
                    <g transform="translate(0 {y})">
                        <rect width={tw} height={h} class="tip-box" rx="6" ry="6" />
                        <rect width={tw} height="4" class="tip-accent" />
                        <rect
                            x="14"
                            y="16"
                            width="10"
                            height="10"
                            fill={SPORT_COLOR[pin.race.sport]}
                        />
                        <text x="29" y="25" class="tip-title">
                            <tspan class="tip-num">{String(pin.n).padStart(2, '0')}</tspan>
                            {pin.race.title.length > 20
                                ? pin.race.title.slice(0, 19) + '…'
                                : pin.race.title}
                        </text>
                        <text x="14" y="51" class="tip-meta">
                            {shortDate(pin.race.raceDate)} · {arenaDistLabel(pin.race)}
                        </text>
                        <text
                            x={tw - 14}
                            y="51"
                            text-anchor="end"
                            class="tip-meta tip-status"
                            class:urgent={st.urgent}
                            class:closed={st.closed}>{st.label}</text
                        >
                        {#if pin.race.location}
                            <text x="14" y="74" class="tip-loc">
                                {pin.race.location.length > 32
                                    ? pin.race.location.slice(0, 31) + '…'
                                    : pin.race.location}
                            </text>
                        {/if}
                        {#if wx}
                            <!-- Bottom weather block. Mirrors the race detail
                                 page layout: hairline divider, icon + condition
                                 on the left, temperature range on the right,
                                 then a subline for 체감/비/바람.
                                 The wrapping <g class="tip-wx"> sets `color`
                                 so WeatherIcon's `stroke="currentColor"`
                                 resolves to a paper tone on the dark box. -->
                            <line
                                x1="14"
                                y1={wxDividerY}
                                x2={tw - 14}
                                y2={wxDividerY}
                                class="tip-divider"
                            />
                            <g class="tip-wx" transform="translate(14 {wxDividerY + 6})">
                                <WeatherIcon
                                    weatherCode={wx.code}
                                    label={wx.condition}
                                    size={18}
                                />
                            </g>
                            {#if wx.condition}
                                <text x="38" y={wxDividerY + 20} class="tip-wx-cond"
                                    >{wx.condition.length > 10
                                        ? wx.condition.slice(0, 9) + '…'
                                        : wx.condition}</text
                                >
                            {/if}
                            {#if wxTemp}
                                <text
                                    x={tw - 14}
                                    y={wxDividerY + 20}
                                    text-anchor="end"
                                    class="tip-wx-temp">{wxTemp}</text
                                >
                            {/if}
                            {#if wxSub}
                                <text x="14" y={wxDividerY + 36} class="tip-wx-sub"
                                    >{wxSub.length > 40
                                        ? wxSub.slice(0, 39) + '…'
                                        : wxSub}</text
                                >
                            {/if}
                        {/if}
                    </g>
                {/snippet}

                <!-- Zooming group: real province polygons + bubbles + race pins -->
                <g class="zoom-group" style="transform: {groupTransform};">
                    <!-- Province polygons. At depth-1, the hovered region is
                         scaled up and brightened to act as a visual preview;
                         the polygon itself also acts as the click target so
                         users can click anywhere inside the region. -->
                    {#each orderedRegionStats as r (r.code)}
                        {@const isSel = selected === r.code}
                        {@const isHover = !selected && hovered === r.code && r.count > 0}
                        {@const isInteractive = !selected && r.count > 0}
                        <path
                            class="province"
                            class:selected={isSel}
                            class:dimmed={!!selected && !isSel}
                            class:hovered={isHover}
                            class:interactive={isInteractive}
                            d={r.d}
                            vector-effect="non-scaling-stroke"
                            onclick={() => {
                                if (isInteractive) selectRegion(r.code, r.count);
                            }}
                            onmouseenter={() => {
                                if (isInteractive) hovered = r.code;
                            }}
                            onmouseleave={() => {
                                if (hovered === r.code) hovered = null;
                            }}
                        />
                    {/each}

                    <!-- Density bubbles at real centroids — overview only -->
                    {#if overviewVisible}
                        {#each regionStats as r (r.code)}
                            {#if r.count === 0}
                                <text
                                    x={r.centroid[0]}
                                    y={r.centroid[1] + 3}
                                    text-anchor="middle"
                                    class="dot-label zero">{r.code}</text
                                >
                            {/if}
                        {/each}
                        {#each bubbleStats as r (r.code)}
                            {@const radius = dotRadius(r.count)}
                            {@const intensity = r.count / maxRegionCount}
                            {@const bp = bubbleXY(r)}
                            <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
                            <g
                                class="region-dot"
                                class:hovered={hovered === r.code}
                                role="button"
                                tabindex="0"
                                aria-label="{r.code} 대회 {r.count}개 보기"
                                onclick={() => selectRegion(r.code, r.count)}
                                onkeydown={(e) => {
                                    if (e.key === 'Enter' || e.key === ' ') {
                                        e.preventDefault();
                                        selectRegion(r.code, r.count);
                                    }
                                }}
                                onmouseenter={() => (hovered = r.code)}
                                onmouseleave={() => (hovered = null)}
                                onfocus={() => (hovered = r.code)}
                                onblur={() => (hovered = null)}
                            >
                                <circle
                                    cx={bp[0]}
                                    cy={bp[1]}
                                    r={radius * 1.7}
                                    class="dot-glow"
                                    style="opacity: {0.06 + intensity * 0.12};"
                                />
                                <circle cx={bp[0]} cy={bp[1]} r={radius} class="dot-core" />
                                <text
                                    x={bp[0]}
                                    y={bp[1] + 4}
                                    text-anchor="middle"
                                    class="dot-count">{r.count}</text
                                >
                                <text
                                    x={bp[0]}
                                    y={bp[1] + radius + 13}
                                    text-anchor="middle"
                                    class="dot-label">{r.code}</text
                                >
                            </g>
                        {/each}
                    {/if}

                    <!-- 시·군·구 sub-districts + race pins — selected region only -->
                    {#if selectedRegion && detailVisible}
                        {#each municipalities as m (m.name)}
                            <path
                                class="municipality"
                                d={m.d}
                                vector-effect="non-scaling-stroke"
                            />
                        {/each}
                        <!-- Re-stroke the province edge on top for a crisp frame -->
                        <path
                            class="province-frame"
                            d={selectedRegion.d}
                            vector-effect="non-scaling-stroke"
                        />
                        {#each municipalities as m (m.name)}
                            <text
                                class="muni-label"
                                x={m.centroid[0]}
                                y={m.centroid[1]}
                                font-size={muniFontSize}>{m.name}</text
                            >
                        {/each}
                        {#each regionPinGroups as group, gi (group.pins.map((p) => p.race.id).join(','))}
                            {#if group.pins.length === 1}
                                {@const pin = group.pins[0]}
                                {@const st = raceState(pin.race)}
                                {@const isHover = hoveredPin === pin.race.id}
                                <!-- Counter-scaled by 1/zoom: pin glyph stays a
                                     constant on-screen size at any zoom level. -->
                                <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
                                <g
                                    class="race-pin"
                                    class:hovered={isHover}
                                    style="animation-delay: {0.2 + gi * 0.03}s;"
                                    transform="translate({pin.x} {pin.y}) scale({pinScale})"
                                    role="button"
                                    tabindex="0"
                                    aria-label="{pin.race.title} — {shortDate(pin.race.raceDate)} {st.label}"
                                    onmouseenter={() => (hoveredPin = pin.race.id)}
                                    onmouseleave={() => {
                                        if (hoveredPin === pin.race.id) hoveredPin = null;
                                    }}
                                    onfocus={() => (hoveredPin = pin.race.id)}
                                    onblur={() => {
                                        if (hoveredPin === pin.race.id) hoveredPin = null;
                                    }}
                                >
                                    <line
                                        x1="0"
                                        y1="0"
                                        x2="0"
                                        y2="-13"
                                        stroke="var(--arena-ink)"
                                        stroke-width="1.2"
                                        vector-effect="non-scaling-stroke"
                                    />
                                    {#if !st.closed}
                                        <circle
                                            cx="0"
                                            cy="0"
                                            r="13"
                                            fill="none"
                                            stroke={st.urgent
                                                ? 'var(--arena-urgent)'
                                                : 'var(--arena-accent-deep)'}
                                            stroke-width="1.2"
                                            vector-effect="non-scaling-stroke"
                                            opacity="0.78"
                                        />
                                    {/if}
                                    <circle
                                        cx="0"
                                        cy="0"
                                        r="7.5"
                                        fill={SPORT_COLOR[pin.race.sport]}
                                        stroke="var(--arena-paper)"
                                        stroke-width="1.8"
                                        vector-effect="non-scaling-stroke"
                                        opacity={st.closed ? 0.55 : 1}
                                    />
                                    <text x="0" y="-18" text-anchor="middle" class="pin-num"
                                        >{String(pin.n).padStart(2, '0')}</text
                                    >
                                    <!-- Transparent hit area: wider than the visual
                                         glyph so hover/focus is forgiving at any
                                         zoom level. Drawn last so it stays on top
                                         and captures pointer events. -->
                                    <circle cx="0" cy="-6" r="20" class="pin-hit" />
                                </g>
                            {:else}
                                {@const isHover = hoveredGroup === gi}
                                {@const n = group.pins.length}
                                <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
                                <g
                                    class="race-cluster"
                                    class:hovered={isHover}
                                    class:closed={group.allClosed}
                                    style="animation-delay: {0.2 + gi * 0.03}s;"
                                    transform="translate({group.cx} {group.cy}) scale({pinScale})"
                                    role="button"
                                    tabindex="0"
                                    aria-label="{n}개 대회"
                                    onmouseenter={() => setClusterHover(gi)}
                                    onmouseleave={scheduleClusterClear}
                                    onfocus={() => setClusterHover(gi)}
                                    onblur={scheduleClusterClear}
                                >
                                    <line
                                        x1="0"
                                        y1="0"
                                        x2="0"
                                        y2="-15"
                                        stroke="var(--arena-ink)"
                                        stroke-width="1.2"
                                        vector-effect="non-scaling-stroke"
                                    />
                                    <circle
                                        cx="0"
                                        cy="0"
                                        r="15"
                                        fill={SPORT_COLOR[group.dominantSport]}
                                        stroke="var(--arena-paper)"
                                        stroke-width="2"
                                        vector-effect="non-scaling-stroke"
                                        opacity={group.allClosed ? 0.55 : 1}
                                    />
                                    <text
                                        x="0"
                                        y="0"
                                        text-anchor="middle"
                                        dominant-baseline="central"
                                        class="cluster-num">{n}</text
                                    >
                                    <circle cx="0" cy="-2" r="24" class="pin-hit" />
                                </g>
                            {/if}
                        {/each}
                    {/if}
                </g>

                <!-- Race pin info tooltip on hover/focus — detail view only.
                     Rendered OUTSIDE the zoom-group at the pin's screen-space
                     position so the tooltip stays at a constant on-screen
                     size and doesn't fight the zoom transform. -->
                {#if hoveredPinData && selectedRegion && detailVisible}
                    {@const hp = hoveredPinData}
                    {@const sx = fit.tx + hp.x * fit.scale}
                    {@const sy = fit.ty + hp.y * fit.scale}
                    {@const tw = 280}
                    {@const th = cardHeight(hp.race)}
                    {@const tx = Math.min(KOREA_VIEWBOX.w - tw - 6, Math.max(6, sx - tw / 2))}
                    {@const aboveY = sy - 26 - th}
                    {@const ty = aboveY > 6 ? aboveY : sy + 26}
                    <g class="map-tip pin-tip" transform="translate({tx} {ty})">
                        {@render raceCard(hp, 0, tw)}
                    </g>
                {/if}

                <!-- Cluster hover tooltip — detail view only.
                     A single dark container with header, sport chips, and a
                     scrollable race list. Rendered via foreignObject so the
                     rich layout uses HTML+CSS instead of SVG primitives. A
                     small mouseleave delay lets the cursor cross from the pin
                     into the panel so rows stay interactive. -->
                {#if hoveredGroupData && selectedRegion && detailVisible}
                    {@const hg = hoveredGroupData}
                    {@const hgRaces = hg.pins.map((p) => p.race)}
                    {@const closedCount = hgRaces.filter((r) => raceState(r).closed).length}
                    {@const spread = formatProximity(maxPairwiseKm(hg.pins))}
                    {@const hgSorted = [...hg.pins].sort((a, b) => byDate(a.race, b.race))}
                    {@const sx = fit.tx + hg.cx * fit.scale}
                    {@const sy = fit.ty + hg.cy * fit.scale}
                    {@const tw = 304}
                    {@const th = Math.min(440, 168 + Math.min(hg.pins.length, 5) * 56)}
                    {@const tx = Math.min(KOREA_VIEWBOX.w - tw - 6, Math.max(6, sx - tw / 2))}
                    {@const aboveY = sy - 24 - th}
                    {@const rawTy = aboveY > 6 ? aboveY : sy + 24}
                    {@const ty = Math.min(KOREA_VIEWBOX.h - th - 6, Math.max(6, rawTy))}
                    <foreignObject x={tx} y={ty} width={tw} height={th} class="cluster-fo">
                        <div
                            xmlns="http://www.w3.org/1999/xhtml"
                            class="cluster-panel"
                            role="dialog"
                            aria-label="{hg.pins.length}개 대회 묶음"
                            onmouseenter={cancelClusterClear}
                            onmouseleave={scheduleClusterClear}
                        >
                            <div class="cluster-head">
                                <div class="cluster-kicker">
                                    <span>CLUSTER</span>
                                    <button
                                        class="cluster-close"
                                        aria-label="닫기"
                                        onclick={() => (hoveredGroup = null)}>×</button
                                    >
                                </div>
                                <div class="cluster-title-row">
                                    <span class="cluster-num">{hg.pins.length}</span>
                                    <span class="cluster-title">개 대회</span>
                                    <span class="cluster-spread">{spread}</span>
                                </div>
                                <div class="cluster-chips">
                                    <span class="cluster-chip all">전체 · {hg.pins.length}</span>
                                    {#each sportBreakdown(hgRaces) as b}
                                        <span class="cluster-chip">
                                            <span
                                                class="cluster-chip-dot"
                                                style="background: {SPORT_COLOR[b.sport]};"
                                            ></span>
                                            {shortSportLabel(b.sport)} · {b.count}
                                        </span>
                                    {/each}
                                    {#if closedCount > 0}
                                        <span class="cluster-chip closed"
                                            >마감 · {closedCount}</span
                                        >
                                    {/if}
                                </div>
                            </div>
                            <div class="cluster-list">
                                {#each hgSorted as gp (gp.race.id)}
                                    {@const st = raceState(gp.race)}
                                    <a
                                        class="cluster-row"
                                        class:is-closed={st.closed}
                                        href={gp.race.url}
                                    >
                                        <span
                                            class="cluster-row-stripe"
                                            style="background: {SPORT_COLOR[gp.race.sport]};"
                                        ></span>
                                        <span class="cluster-row-main">
                                            <span class="cluster-row-title">{gp.race.title}</span>
                                            <span class="cluster-row-meta">
                                                {shortDate(gp.race.raceDate)}
                                                {#if gp.race.location}
                                                    <span class="cluster-row-sep">·</span>
                                                    {gp.race.location.length > 14
                                                        ? gp.race.location.slice(0, 13) + '…'
                                                        : gp.race.location}
                                                {/if}
                                            </span>
                                        </span>
                                        <span
                                            class="cluster-row-stat"
                                            class:urgent={st.urgent}
                                            class:closed={st.closed}>{st.label}</span
                                        >
                                    </a>
                                {/each}
                            </div>
                        </div>
                    </foreignObject>
                {/if}

                <!-- Region info tooltip on hover/focus — overview only -->
                {#if hoveredRegion && overviewVisible}
                    {@const hr = hoveredRegion}
                    {@const hp = bubbleXY(hr)}
                    {@const hRadius = dotRadius(hr.count)}
                    {@const breaks = sportBreakdown(hr.races)}
                    {@const tw = Math.max(112, 18 + breaks.length * 27)}
                    {@const th = 46}
                    {@const tx = Math.min(KOREA_VIEWBOX.w - tw - 6, Math.max(6, hp[0] - tw / 2))}
                    {@const aboveY = hp[1] - hRadius - 12 - th}
                    {@const ty = aboveY > 6 ? aboveY : hp[1] + hRadius + 12}
                    <g class="map-tip" transform="translate({tx} {ty})">
                        <rect width={tw} height={th} class="tip-box" />
                        <rect width={tw} height="3" class="tip-accent" />
                        <text x="13" y="23" class="tip-title"
                            >{hr.code} · <tspan class="tip-count">{hr.count}</tspan>개 대회</text
                        >
                        {#each breaks as b, i}
                            <rect
                                x={13 + i * 27}
                                y="30"
                                width="9"
                                height="9"
                                fill={SPORT_COLOR[b.sport]}
                            />
                            <text x={13 + i * 27 + 13} y="38" class="tip-sport">{b.count}</text>
                        {/each}
                    </g>
                {/if}
            </svg>
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
                                    <span class="break-dot" style="background: {SPORT_COLOR[b.sport]};"
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
                            <a class="race-row" href={race.url}>
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
                        지도의 버블이나 아래 지역을 누르면 해당 시·도로 확대되고, 그 지역
                        대회만 보여줘요.
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
                    {#if overview.length === 0}
                        <div class="panel-empty mono">{month}월에 등록된 대회가 없습니다</div>
                    {:else}
                        {#each overview as r, i (r.code)}
                            <button class="region-row" onclick={() => selectRegion(r.code, r.count)}>
                                <span class="o-idx mono">{String(i + 1).padStart(2, '0')}</span>
                                <span class="o-region">{r.code}</span>
                                <span class="o-n mono">{r.count}</span>
                                <span class="o-sports">
                                    {#each sportBreakdown(r.races) as b}
                                        <span
                                            class="sport-bar"
                                            title="{arenaSportShort[b.sport]} {b.count}"
                                            style="background: {SPORT_COLOR[b.sport]}; flex: {b.count};"
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
        background: var(--arena-paper);
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
    .map-svg {
        width: 100%;
        height: 100%;
        display: block;
        /* Default 'auto' lets browsers rasterize complex paths in a faster but
           more aliased mode — visible as jaggies along provincial borders and
           coastline. 'geometricPrecision' forces high-quality anti-aliasing
           for every shape in this SVG (provinces, municipalities, pins). */
        shape-rendering: geometricPrecision;
    }
    .zoom-group {
        transform-origin: 0 0;
        transition: transform 0.5s cubic-bezier(0.65, 0, 0.35, 1);
        /* Promote to its own compositor layer so the zoom animates on the
           GPU instead of repainting the province paths every frame. */
        will-change: transform;
    }

    .map-back {
        position: absolute;
        top: 14px;
        left: 14px;
        z-index: 5;
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
        z-index: 5;
        font-size: 10px;
        letter-spacing: 1.6px;
        font-weight: 600;
        color: var(--arena-ink-mute);
        text-align: right;
        max-width: 62%;
    }
    .hint-warn {
        color: var(--arena-urgent);
    }

    /* ── SVG geometry ─────────────────────────── */
    .province {
        fill: var(--arena-paper-alt);
        stroke: var(--arena-ink);
        stroke-width: 1.1;
        stroke-linejoin: round;
        stroke-linecap: round;
        /* Scale around the polygon's own bbox center so the depth-1 hover
           preview grows in place instead of around the viewBox origin. */
        transform-box: fill-box;
        transform-origin: center;
        transition:
            opacity 0.35s ease,
            fill 0.25s ease,
            stroke-width 0.25s ease,
            transform 0.3s cubic-bezier(0.65, 0, 0.35, 1);
    }
    .province.selected {
        fill: var(--arena-paper);
        stroke-width: 1.8;
    }
    .province.dimmed {
        opacity: 0.16;
    }
    .province.interactive {
        cursor: pointer;
    }
    .province.hovered {
        fill: var(--arena-accent);
        stroke-width: 1.8;
        transform: scale(1.06);
    }
    /* Dim every region that isn't the one being previewed, so the hovered
       province stays visually isolated. */
    .map-svg.has-hover .province:not(.hovered):not(.selected) {
        opacity: 0.45;
    }
    .map-svg.has-hover .region-dot:not(.hovered) {
        opacity: 0.5;
    }
    .region-dot {
        cursor: pointer;
        outline: none;
        transition: opacity 0.25s ease;
    }
    .region-dot:focus-visible {
        outline: 2px solid var(--arena-accent-deep);
        outline-offset: 2px;
    }
    .dot-glow {
        fill: var(--arena-accent-deep);
    }
    .dot-core {
        fill: var(--arena-accent-deep);
    }
    .region-dot:hover .dot-core,
    .region-dot.hovered .dot-core {
        fill: var(--arena-accent);
    }
    .dot-count {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        font-weight: 700;
        fill: var(--arena-paper);
        pointer-events: none;
    }
    .dot-label {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        font-weight: 500;
        letter-spacing: 0.5px;
        fill: var(--arena-ink-soft);
        pointer-events: none;
    }
    .dot-label.zero {
        font-size: 9px;
        fill: var(--arena-ink-mute);
        opacity: 0.7;
    }
    .pin-num {
        font-family: var(--arena-f-mono);
        font-size: 10px;
        font-weight: 700;
        fill: var(--arena-ink-soft);
        pointer-events: none;
    }
    /* 시·군·구 sub-district outlines, shown when a province is zoomed in. */
    .municipality {
        fill: var(--arena-paper);
        stroke: var(--arena-ink-soft);
        stroke-width: 0.6;
        stroke-linejoin: round;
        stroke-linecap: round;
        pointer-events: none;
        opacity: 0;
        animation: muni-fade 0.5s ease 0.05s forwards;
    }
    .province-frame {
        fill: none;
        stroke: var(--arena-ink);
        stroke-width: 1.8;
        stroke-linejoin: round;
        stroke-linecap: round;
        pointer-events: none;
    }
    .muni-label {
        font-family: var(--arena-f-mono);
        font-weight: 500;
        fill: var(--arena-ink-soft);
        text-anchor: middle;
        dominant-baseline: middle;
        pointer-events: none;
        opacity: 0;
        animation: muni-fade 0.5s ease 0.15s forwards;
    }
    @keyframes muni-fade {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }
    .race-pin {
        opacity: 0;
        animation: pin-fade 0.5s ease forwards;
        outline: none;
    }
    .race-pin.hovered {
        /* Lift the pin visually when hovered/focused so its glyph sits
           above neighbours and its tooltip clearly anchors to it. */
        filter: drop-shadow(0 1px 1.5px rgba(0, 0, 0, 0.35));
    }
    .race-pin.hovered .pin-num {
        fill: var(--arena-ink);
        font-weight: 700;
    }
    .race-pin:focus-visible {
        outline: none;
    }
    .race-pin:focus-visible .pin-num {
        fill: var(--arena-accent-deep);
    }
    .pin-hit {
        fill: transparent;
        cursor: pointer;
    }
    /* ── Cluster glyph (2+ adjacent pins merged) ─────────────── */
    .race-cluster {
        opacity: 0;
        animation: pin-fade 0.5s ease forwards;
        cursor: pointer;
        outline: none;
    }
    .race-cluster.hovered {
        filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.35));
    }
    .race-cluster:focus-visible {
        outline: none;
    }
    .cluster-num {
        font-family: var(--arena-f-mono);
        font-size: 12.5px;
        font-weight: 700;
        fill: var(--arena-paper);
        pointer-events: none;
        letter-spacing: 0.3px;
    }
    .race-cluster.closed .cluster-num {
        fill: var(--arena-paper);
        opacity: 0.8;
    }

    /* ── Cluster hover panel (foreignObject) ─────────────── */
    .cluster-fo {
        overflow: visible;
    }
    .cluster-panel {
        height: 100%;
        background: var(--arena-ink);
        color: var(--arena-paper);
        border: 1px solid color-mix(in srgb, var(--arena-accent) 60%, transparent);
        border-radius: 8px;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
        display: flex;
        flex-direction: column;
        font-family: var(--arena-f-body);
        overflow: hidden;
        pointer-events: auto;
        animation: tip-fade 0.12s ease;
    }
    .cluster-head {
        padding: 12px 14px 10px;
        border-bottom: 1px solid color-mix(in srgb, var(--arena-paper) 14%, transparent);
        flex-shrink: 0;
    }
    .cluster-kicker {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 2px;
        color: var(--arena-accent);
        margin-bottom: 6px;
    }
    .cluster-close {
        background: transparent;
        border: none;
        color: color-mix(in srgb, var(--arena-paper) 50%, transparent);
        font-size: 18px;
        line-height: 1;
        cursor: pointer;
        padding: 0 4px;
    }
    .cluster-close:hover {
        color: var(--arena-paper);
    }
    .cluster-title-row {
        display: flex;
        align-items: baseline;
        gap: 6px;
        margin-bottom: 10px;
    }
    .cluster-num {
        font-family: var(--arena-f-display, var(--arena-f-body));
        font-size: 26px;
        font-weight: 700;
        letter-spacing: -1px;
        color: var(--arena-paper);
    }
    .cluster-title {
        font-size: 14px;
        font-weight: 500;
        color: var(--arena-paper);
    }
    .cluster-spread {
        margin-left: auto;
        font-family: var(--arena-f-mono);
        font-size: 10px;
        color: var(--arena-accent);
        letter-spacing: 0.4px;
    }
    .cluster-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
    }
    .cluster-chip {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 3px 8px;
        font-family: var(--arena-f-mono);
        font-size: 10.5px;
        font-weight: 600;
        letter-spacing: 0.3px;
        background: color-mix(in srgb, var(--arena-paper) 8%, transparent);
        color: color-mix(in srgb, var(--arena-paper) 80%, transparent);
        border-radius: 3px;
    }
    .cluster-chip.all {
        background: var(--arena-paper);
        color: var(--arena-ink);
    }
    .cluster-chip.closed {
        color: color-mix(in srgb, var(--arena-paper) 50%, transparent);
    }
    .cluster-chip-dot {
        width: 8px;
        height: 8px;
        display: inline-block;
        border-radius: 1px;
    }
    .cluster-list {
        flex: 1;
        overflow-y: auto;
        min-height: 0;
    }
    .cluster-list::-webkit-scrollbar {
        width: 6px;
    }
    .cluster-list::-webkit-scrollbar-thumb {
        background: color-mix(in srgb, var(--arena-paper) 20%, transparent);
        border-radius: 3px;
    }
    .cluster-row {
        position: relative;
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 11px 14px 11px 18px;
        color: var(--arena-paper);
        text-decoration: none;
        border-bottom: 1px solid color-mix(in srgb, var(--arena-paper) 8%, transparent);
        transition: background 0.12s ease;
    }
    .cluster-row:last-child {
        border-bottom: none;
    }
    .cluster-row:hover {
        background: color-mix(in srgb, var(--arena-paper) 5%, transparent);
    }
    .cluster-row-stripe {
        position: absolute;
        left: 0;
        top: 12px;
        bottom: 12px;
        width: 3px;
    }
    .cluster-row-main {
        display: flex;
        flex-direction: column;
        gap: 3px;
        flex: 1;
        min-width: 0;
    }
    .cluster-row-title {
        font-size: 13.5px;
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .cluster-row.is-closed .cluster-row-title {
        color: color-mix(in srgb, var(--arena-paper) 55%, transparent);
        text-decoration: line-through;
        text-decoration-color: color-mix(in srgb, var(--arena-paper) 20%, transparent);
    }
    .cluster-row-meta {
        font-family: var(--arena-f-mono);
        font-size: 10.5px;
        color: color-mix(in srgb, var(--arena-paper) 55%, transparent);
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }
    .cluster-row-sep {
        opacity: 0.6;
    }
    .cluster-row-stat {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.8px;
        color: var(--arena-accent);
        flex-shrink: 0;
    }
    .cluster-row-stat.urgent {
        color: var(--arena-urgent);
    }
    .cluster-row-stat.closed {
        color: color-mix(in srgb, var(--arena-paper) 45%, transparent);
        font-weight: 600;
    }
    @keyframes pin-fade {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }

    /* ── Hover info tooltip ─────────────────────────── */
    .map-tip {
        pointer-events: none;
        animation: tip-fade 0.12s ease;
    }
    @keyframes tip-fade {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }
    .tip-box {
        fill: var(--arena-ink);
    }
    .tip-accent {
        fill: var(--arena-accent);
    }
    .tip-title {
        font-family: var(--arena-f-mono);
        font-size: 12px;
        font-weight: 600;
        fill: var(--arena-paper);
    }
    .tip-count {
        fill: var(--arena-accent);
        font-weight: 700;
    }
    .tip-sport {
        font-family: var(--arena-f-mono);
        font-size: 9.5px;
        fill: var(--arena-paper);
    }
    .pin-tip .tip-title {
        font-size: 14.5px;
        font-weight: 600;
    }
    .pin-tip .tip-num {
        fill: var(--arena-accent);
        font-weight: 700;
        margin-right: 4px;
    }
    .tip-meta {
        font-family: var(--arena-f-mono);
        font-size: 12px;
        letter-spacing: 0.4px;
        fill: var(--arena-paper);
    }
    .tip-status {
        font-weight: 700;
        letter-spacing: 0.8px;
    }
    .tip-meta.urgent {
        fill: var(--arena-urgent);
        font-weight: 700;
    }
    .tip-meta.closed {
        fill: var(--arena-ink-mute);
    }
    .tip-loc {
        font-family: var(--arena-f-body);
        font-size: 11.5px;
        fill: var(--arena-paper);
        opacity: 0.8;
    }
    /* Bottom weather block in the hover card. The wrapping <g class="tip-wx">
       sets `color` so WeatherIcon's `stroke="currentColor"` resolves to a
       paper-tone line against the dark tip box. */
    .tip-divider {
        stroke: var(--arena-paper);
        stroke-width: 1;
        opacity: 0.18;
    }
    .tip-wx {
        color: var(--arena-paper);
    }
    .tip-wx-cond {
        font-family: var(--arena-f-body);
        font-size: 12.5px;
        font-weight: 600;
        fill: var(--arena-paper);
        letter-spacing: 0.1px;
    }
    .tip-wx-temp {
        font-family: var(--arena-f-mono);
        font-size: 14px;
        font-weight: 700;
        fill: var(--arena-paper);
        letter-spacing: 0.4px;
    }
    .tip-wx-sub {
        font-family: var(--arena-f-mono);
        font-size: 10.5px;
        fill: var(--arena-paper);
        opacity: 0.65;
        letter-spacing: 0.2px;
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
        .zoom-group {
            transition: none;
        }
        .race-pin,
        .race-cluster,
        .municipality,
        .muni-label {
            animation: none;
            opacity: 1;
        }
    }
</style>
