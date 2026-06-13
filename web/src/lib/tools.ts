// Running formulas + helpers used by /tools (Pace, Training Plan, VO2max, Race Predictor)

import type { Race } from '$lib/types';

export interface DistancePreset {
    code: string;
    km: number;
    label: string;
}

export const STD_DISTANCES: DistancePreset[] = [
    { code: '5K', km: 5, label: '5K' },
    { code: '10K', km: 10, label: '10K' },
    { code: 'HM', km: 21.0975, label: '하프' },
    { code: 'FM', km: 42.195, label: '풀코스' },
];

// Map a stored race-record distance label to kilometres for the running tools.
// Handles the onboarding presets plus free-form custom text ("21.0975K", "100마일", "10–30K").
const RECORD_DIST_KM: Record<string, number> = {
    '5K': 5,
    '10K': 10,
    '하프': 21.0975,
    '풀코스': 42.195,
    '울트라': 50,
};

export function recordDistanceToKm(distance: string): number {
    if (!distance) return 0;
    const d = distance.trim();
    if (RECORD_DIST_KM[d] != null) return RECORD_DIST_KM[d];
    // Take the first number in the string (e.g. "10–30K" → 10, "21.0975K" → 21.0975).
    const match = d.replace(',', '.').match(/\d+(?:\.\d+)?/);
    if (!match) return 0;
    let n = parseFloat(match[0]);
    if (!Number.isFinite(n) || n <= 0) return 0;
    const lower = d.toLowerCase();
    if (lower.includes('마일') || lower.includes('mi')) n *= 1.60934;
    return n;
}

export interface RecordPrefill {
    distKm: number;
    timeSec: number;
    timeStr: string;
    label: string;
}

interface PrefillRecord {
    sport: string;
    distance: string;
    durationSeconds: number;
    time: string;
}

// Pick the most recent running/trail record that maps to a usable distance + time.
// `records` is expected newest-first (the API orders by -created_at).
export function pickRunningRecordPrefill(records: PrefillRecord[] | null | undefined): RecordPrefill | null {
    if (!records) return null;
    for (const r of records) {
        if (r.sport !== 'running' && r.sport !== 'trail_running') continue;
        const km = recordDistanceToKm(r.distance);
        if (km > 0 && r.durationSeconds > 0) {
            return { distKm: km, timeSec: r.durationSeconds, timeStr: r.time, label: `${r.distance} · ${r.time}` };
        }
    }
    return null;
}

export const ZONE_INK = {
    E: 'var(--arena-zone-e)',
    M: 'var(--arena-zone-m)',
    T: 'var(--arena-zone-t)',
    I: 'var(--arena-zone-i)',
    R: 'var(--arena-zone-r)',
} as const;

export type ZoneKey = keyof typeof ZONE_INK;

// ── Formulas ─────────────────────────────────
// Riegel: T2 = T1 * (D2/D1)^k  (default k = 1.06)
export function riegel(t1Sec: number, d1Km: number, d2Km: number, k = 1.06): number {
    if (d1Km <= 0 || d2Km <= 0 || t1Sec <= 0) return 0;
    return t1Sec * Math.pow(d2Km / d1Km, k);
}

// VDOT (Daniels) — approximation
//   VO2 (ml/kg/min) = -4.6 + 0.182258*v + 0.000104*v^2     (v = m/min)
//   %VO2max = 0.8 + 0.1894393*exp(-0.012778*t) + 0.2989558*exp(-0.1932605*t)  (t = min)
//   VDOT = VO2 / %VO2max
export function vdot(distKm: number, timeSec: number): number {
    if (distKm <= 0 || timeSec <= 0) return 0;
    const distMeters = distKm * 1000;
    const tMin = timeSec / 60;
    const v = distMeters / tMin; // m/min
    const vo2 = -4.6 + 0.182258 * v + 0.000104 * v * v;
    const pct =
        0.8 +
        0.1894393 * Math.exp(-0.012778 * tMin) +
        0.2989558 * Math.exp(-0.1932605 * tMin);
    return vo2 / pct;
}

// VDOT inverse — given a VDOT value, predict time for a distance via binary search
export function timeFromVdot(targetVdot: number, distKm: number): number {
    let lo = 60;
    let hi = 60 * 60 * 8;
    for (let i = 0; i < 50; i++) {
        const mid = (lo + hi) / 2;
        const v = vdot(distKm, mid);
        if (v > targetVdot) lo = mid;
        else hi = mid;
    }
    return (lo + hi) / 2;
}

export interface TrainingPace {
    label: string;
    sec: number;
    hr: string;
}

// Daniels training paces — approximate linear regression on VDOT
export function trainingPaces(v: number): Record<ZoneKey, TrainingPace> {
    const easyMin = 12.55 - 0.11 * v;
    const marathonMin = 11.42 - 0.105 * v;
    const thresholdMin = 10.85 - 0.103 * v;
    const intervalMin = 10.11 - 0.099 * v;
    const repMin = 9.49 - 0.097 * v;
    const sec = (m: number) => Math.max(120, Math.round(m * 60));
    return {
        E: { label: 'Easy', sec: sec(easyMin), hr: '65–79%' },
        M: { label: 'Marathon', sec: sec(marathonMin), hr: '80–85%' },
        T: { label: 'Threshold', sec: sec(thresholdMin), hr: '86–90%' },
        I: { label: 'Interval', sec: sec(intervalMin), hr: '95–100%' },
        R: { label: 'Repetition', sec: sec(repMin), hr: '— max' },
    };
}

// ── Format helpers ─────────────────────────────────
export function fmtTime(sec: number): string {
    if (!Number.isFinite(sec) || sec < 0) return '—';
    const t = Math.round(sec);
    const h = Math.floor(t / 3600);
    const m = Math.floor((t % 3600) / 60);
    const s = t % 60;
    if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    return `${m}:${String(s).padStart(2, '0')}`;
}

export function fmtPace(secPerKm: number): string {
    if (!Number.isFinite(secPerKm) || secPerKm < 0) return '—';
    const m = Math.floor(secPerKm / 60);
    const s = Math.round(secPerKm % 60);
    return `${m}'${String(s).padStart(2, '0')}"`;
}

// Parse "1:42:15" / "42:15" / "42" (minutes)
export function parseTime(str: string): number {
    if (!str) return 0;
    const parts = str.split(':').map((p) => parseInt(p, 10) || 0);
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
    if (parts.length === 2) return parts[0] * 60 + parts[1];
    return parts[0] * 60;
}

// Parse pace "4:51" or "4'51\"" → seconds per km
export function parsePace(str: string): number {
    if (!str) return 0;
    const cleaned = str.replace("'", ':').replace('"', '');
    const [m, s] = cleaned.split(':').map((x) => parseInt(x, 10) || 0);
    return (m || 0) * 60 + (s || 0);
}

// ── Training plan periodization ─────────────────────────────────
// Daniels-style 4-phase periodization. Ported 1:1 from the Claude Design
// handoff (v2/Tools.html · PlanTool): phase weeks distributed by %, weekly
// volume ramps within each phase, every 4th non-taper week is a -18% cutback.
export type PhaseName = 'BASE' | 'BUILD' | 'PEAK' | 'TAPER';

export interface PhaseDef {
    name: PhaseName;
    pct: number;
    color: string;
    ink: string;
    focus: ZoneKey;
    desc: string;
}

export const PHASE_DEFS: PhaseDef[] = [
    { name: 'BASE', pct: 0.34, color: 'var(--signal-100)', ink: 'var(--signal-700)', focus: 'E', desc: '유산소 베이스 · 주간 볼륨 점증' },
    { name: 'BUILD', pct: 0.3, color: 'var(--info-bg)', ink: 'var(--info)', focus: 'T', desc: '역치 템포 + LSD 거리 연장' },
    { name: 'PEAK', pct: 0.23, color: 'var(--caution-bg)', ink: 'var(--caution)', focus: 'I', desc: 'VO₂max 인터벌 + 레이스 페이스' },
    { name: 'TAPER', pct: 0.13, color: 'var(--danger-bg)', ink: 'var(--danger)', focus: 'M', desc: '볼륨 감축 · 강도 유지 · 회복' },
];

export type PlanZone = 'E' | 'LONG' | 'T' | 'I' | 'M' | 'REST' | 'RACE';
export type RunDays = 5 | 6;

// phase → 7-day pattern (MON…SUN), 5- and 6-day-per-week variants
const DAY_PATTERNS: Record<RunDays, Record<PhaseName, PlanZone[]>> = {
    5: {
        BASE: ['E', 'REST', 'E', 'REST', 'E', 'LONG', 'REST'],
        BUILD: ['E', 'T', 'REST', 'E', 'REST', 'LONG', 'REST'],
        PEAK: ['E', 'I', 'REST', 'T', 'REST', 'LONG', 'REST'],
        TAPER: ['E', 'M', 'REST', 'E', 'REST', 'RACE', 'REST'],
    },
    6: {
        BASE: ['E', 'E', 'REST', 'E', 'E', 'LONG', 'REST'],
        BUILD: ['E', 'T', 'E', 'REST', 'E', 'LONG', 'REST'],
        PEAK: ['E', 'I', 'E', 'T', 'REST', 'LONG', 'REST'],
        TAPER: ['E', 'M', 'E', 'REST', 'E', 'RACE', 'REST'],
    },
};

export const DOW = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'] as const;

// Spread `weeks` total across the four phases by their pct, never below 1 each.
export function distributeWeeks(weeks: number): number[] {
    const alloc = PHASE_DEFS.map((p) => Math.max(1, Math.round(weeks * p.pct)));
    let sum = alloc.reduce((a, b) => a + b, 0);
    while (sum > weeks) {
        const i = alloc.indexOf(Math.max(...alloc));
        alloc[i]--;
        sum--;
    }
    while (sum < weeks) {
        alloc[0]++;
        sum++;
    }
    return alloc;
}

export interface PlanDay {
    dow: string;
    zone: PlanZone;
}

export interface PlanWeek {
    wk: number;
    phase: PhaseName;
    color: string;
    ink: string;
    weekKm: number;
    days: PlanDay[];
    cutback: boolean;
    monday: Date;
}

export interface BuiltPlan {
    plan: PlanWeek[];
    alloc: number[];
    peak: PlanWeek;
    totalKm: number;
    longMax: number;
    peakKm: number;
    raceName: string;
}

export function buildPlan(
    weeks: number,
    v: number,
    daysPerWeek: RunDays,
    raceDate: string,
    raceName: string
): BuiltPlan {
    const alloc = distributeWeeks(weeks);
    const peakKm = Math.round(48 + Math.max(0, v - 38) * 2.3); // weekly peak volume
    const plan: PlanWeek[] = [];
    let wk = 0;
    PHASE_DEFS.forEach((ph, pi) => {
        const n = alloc[pi];
        for (let i = 0; i < n; i++) {
            wk++;
            const prog = n > 1 ? i / (n - 1) : 1;
            let mult =
                ph.name === 'BASE'
                    ? 0.6 + prog * 0.28
                    : ph.name === 'BUILD'
                        ? 0.88 + prog * 0.12
                        : ph.name === 'PEAK'
                            ? 1.0 + prog * 0.15
                            : 0.85 - prog * 0.42; // TAPER descends
            const cutback = ph.name !== 'TAPER' && wk % 4 === 0;
            if (cutback) mult *= 0.82;
            const weekKm = Math.round(peakKm * mult);
            const pattern = DAY_PATTERNS[daysPerWeek][ph.name];
            const days: PlanDay[] = pattern.map((z, di) => ({ dow: DOW[di], zone: z }));
            const monday = new Date(`${raceDate}T00:00:00`);
            monday.setDate(monday.getDate() - (weeks - wk + 1) * 7);
            plan.push({ wk, phase: ph.name, color: ph.color, ink: ph.ink, weekKm, days, cutback, monday });
        }
    });
    const peak = plan.reduce((m, w) => (w.weekKm > m.weekKm ? w : m), plan[0]);
    const totalKm = plan.reduce((a, w) => a + w.weekKm, 0);
    const longMax = Math.max(...plan.map((w) => Math.round(w.weekKm * 0.36)));
    return { plan, alloc, peak, totalKm, longMax, peakKm, raceName };
}

// Per-day workout detail for the focused-week grid.
interface ZoneSpec {
    label: string;
    sub: string;
    zone: ZoneKey;
    frac?: number;
    km?: number;
}

const ZSPEC: Record<'E' | 'LONG' | 'T' | 'I' | 'M', ZoneSpec> = {
    E: { label: 'Easy', sub: '회복 · 베이스', zone: 'E', frac: 0.16 },
    LONG: { label: 'LSD', sub: 'Easy 페이스 장거리', zone: 'E', frac: 0.36 },
    T: { label: 'Threshold', sub: '템포 지속주', zone: 'T', km: 8 },
    I: { label: 'Interval', sub: '5×1K · R 90s', zone: 'I', km: 5 },
    M: { label: 'Marathon', sub: '레이스 페이스', zone: 'M', km: 6 },
};

export interface DayDetail {
    label: string;
    sub: string;
    rest?: boolean;
    race?: boolean;
    km?: number;
    pace?: number;
    zoneInk?: string;
}

export function dayDetail(
    zone: PlanZone,
    weekKm: number,
    paces: Record<ZoneKey, TrainingPace>,
    raceName: string
): DayDetail {
    if (zone === 'REST') return { label: '휴식', sub: '완전 휴식 · 크로스', rest: true };
    if (zone === 'RACE') return { label: 'RACE', sub: raceName, race: true };
    const s = ZSPEC[zone];
    const km = s.km != null ? s.km : Math.round(weekKm * (s.frac ?? 0));
    return { label: s.label, sub: s.sub, km, pace: paces[s.zone].sec, zoneInk: ZONE_INK[s.zone] };
}

// ── Tools "season" demo data ─────────────────────────────────
// The app has no per-user goal/season store yet, so the Race Predictor's
// "main goal" card and the Training Plan's target-race picker use this sample
// data (mirrors the Claude Design handoff). Swap for real goal data once a
// season backend exists.
export interface GoalRace {
    id: string;
    name: string;
    date: string; // ISO yyyy-mm-dd
    distKm: number;
}

export const GOAL_RACE_OPTIONS: GoalRace[] = [
    { id: 'seoul-int-half', name: '서울국제 하프', date: '2026-05-12', distKm: 21.0975 },
    { id: 'jeonju-half', name: '전주 하프', date: '2026-08-12', distKm: 21.0975 },
    { id: 'chuncheon', name: '춘천 마라톤', date: '2026-10-25', distKm: 42.195 },
    { id: 'jiri-trail', name: '지리산 트레일런', date: '2026-07-25', distKm: 52 },
];

export const MAIN_GOAL = {
    raceId: 'chuncheon',
    raceName: '춘천 마라톤',
    date: '2026-10-25',
    distKm: 42.195,
    targetTimeStr: '3:30:00',
    targetTimeSec: 3 * 3600 + 30 * 60,
};

// A target-race option for the Training Plan, derived from the signed-in user's
// 관심대회 (favorite races) for the season.
export interface GoalRaceOption {
    id: string; // race slug — stable + unique
    name: string;
    date: string; // ISO yyyy-mm-dd
    distKm: number | null; // longest distance on offer, for the RACE-day label
}

// Longest distance (km) offered by a race, from its distances JSON.
function longestDistanceKm(race: Race): number | null {
    const meters = (race.distances ?? [])
        .map((d) => d.distanceMeter ?? 0)
        .filter((m) => m > 0);
    return meters.length ? Math.max(...meters) / 1000 : null;
}

// Minimum lead time for a race to be a viable training goal: at least a month
// out (한 달 이상 남은 대회만). Anything closer can't be meaningfully periodized.
export const MIN_GOAL_LEAD_DAYS = 30;

// Turn the user's favorite races into target-race options, keeping only races
// that are far enough ahead to plan for (마감되지 않은 + 한 달 이상 남음) and
// ordering them by race date so the nearest goal comes first.
export function favoriteRacesToGoals(races: Race[]): GoalRaceOption[] {
    return races
        .filter(
            (r) => !!r.raceDate && r.status !== 'finished' && r.daysUntilRace >= MIN_GOAL_LEAD_DAYS
        )
        .map((r) => ({
            id: r.slug,
            name: r.title,
            date: r.raceDate as string,
            distKm: longestDistanceKm(r)
        }))
        .sort((a, b) => a.date.localeCompare(b.date));
}

// Whole days from today (local) until an ISO date, floored at 0.
export function daysUntil(isoDate: string): number {
    const target = new Date(`${isoDate}T00:00:00`);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    return Math.max(0, Math.round((target.getTime() - today.getTime()) / 86400000));
}
