// Running formulas + helpers used by /tools (Pace, Training Plan, VO2max, Race Predictor)

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
export type PhaseName = 'BASE' | 'BUILD' | 'PEAK' | 'TAPER';

export interface PlanDay {
    day: 'MON' | 'TUE' | 'WED' | 'THU' | 'FRI' | 'SAT' | 'SUN';
    zone: string;
}

export interface PlanWeek {
    weekNum: number;
    phase: PhaseName;
    phaseColor: string;
    focus: ZoneKey;
    days: PlanDay[];
    weekKm: number;
}

interface PhaseSpec {
    name: PhaseName;
    pct: number;
    focus: ZoneKey;
    color: string;
}

const PHASE_SPECS: PhaseSpec[] = [
    { name: 'BASE', pct: 0.4, focus: 'E', color: 'oklch(55% 0.10 145)' },
    { name: 'BUILD', pct: 0.3, focus: 'T', color: 'oklch(58% 0.13 80)' },
    { name: 'PEAK', pct: 0.2, focus: 'I', color: 'oklch(60% 0.16 40)' },
    { name: 'TAPER', pct: 0.1, focus: 'M', color: 'oklch(62% 0.10 250)' },
];

const DAY_NAMES: PlanDay['day'][] = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];

const WEEK_PATTERNS: Record<PhaseName, string[]> = {
    BASE: ['E', 'REST', 'E', 'E', 'REST', 'LONG E', 'REST'],
    BUILD: ['E', 'T', 'E', 'REST', 'E', 'LONG E', 'REST'],
    PEAK: ['E', 'I', 'E', 'T', 'REST', 'LONG E', 'REST'],
    TAPER: ['E', 'M', 'REST', 'E', 'REST', 'RACE/E', 'REST'],
};

export interface BuiltPlan {
    plan: PlanWeek[];
    paces: Record<ZoneKey, TrainingPace>;
}

export function buildPlan(weeks: number, v: number): BuiltPlan {
    const paces = trainingPaces(v);
    const plan: PlanWeek[] = [];
    let weekIdx = 0;
    for (const ph of PHASE_SPECS) {
        const n = Math.max(1, Math.round(weeks * ph.pct));
        for (let i = 0; i < n && plan.length < weeks; i++) {
            const days: PlanDay[] = DAY_NAMES.map((dn, di) => ({
                day: dn,
                zone: WEEK_PATTERNS[ph.name][di],
            }));
            const baseKm = 30 + (Math.max(30, v) - 40) * 1.2;
            const intensity =
                ph.name === 'BASE'
                    ? 0.7 + (i / Math.max(1, n - 1)) * 0.3
                    : ph.name === 'BUILD'
                        ? 1.0 + (i / Math.max(1, n - 1)) * 0.2
                        : ph.name === 'PEAK'
                            ? 1.2 + (i / Math.max(1, n - 1)) * 0.1
                            : 0.7 - (i / Math.max(1, n - 1)) * 0.4;
            plan.push({
                weekNum: ++weekIdx,
                phase: ph.name,
                phaseColor: ph.color,
                focus: ph.focus,
                days,
                weekKm: Math.max(8, Math.round(baseKm * intensity)),
            });
        }
    }
    return { plan, paces };
}

// Intensity score 0..5 for heatmap rendering
export function zoneIntensity(zone: string): number {
    const map: Record<string, number> = {
        REST: 0,
        E: 1,
        'LONG E': 2,
        M: 3,
        T: 4,
        I: 5,
        R: 5,
        'RACE/E': 2,
    };
    return map[zone] ?? 1;
}
