import type { Race, Sport } from '$lib/types';

export const arenaSportCode: Record<Sport, string> = {
    running: 'RUN',
    swimming: 'SWIM',
    cycling: 'CYCLE',
    triathlon: 'TRI',
    trail_running: 'TRL',
};

export const arenaSportShort: Record<Sport, string> = {
    running: '러닝',
    swimming: '수영',
    cycling: '사이클',
    triathlon: '철인3종',
    trail_running: '트레일러닝',
};

const M = (n: number) => Math.round(n * 10) / 10;

export function arenaDistLabel(race: Race): string {
    const ds = race.distances ?? [];
    if (ds.length === 0) return '—';
    const meters = ds
        .map((d) => d.distance_meter)
        .filter((m): m is number => typeof m === 'number' && m > 0);
    if (meters.length > 0) {
        const max = Math.max(...meters);
        const km = max / 1000;
        if (km >= 100) return `${Math.round(km)}K`;
        return `${M(km).toFixed(1)}K`;
    }
    return ds[0].name;
}

function parseFee(raw: string | null | undefined): number | null {
    if (!raw) return null;
    const digits = String(raw).replace(/[^0-9]/g, '');
    if (!digits) return null;
    const v = Number(digits);
    return Number.isFinite(v) ? v : null;
}

export function arenaMinFee(race: Race): number | null {
    const fees: number[] = [];
    for (const d of race.distances ?? []) {
        if (typeof d.fee === 'number' && d.fee > 0) fees.push(d.fee);
    }
    for (const ef of race.entryFee ?? []) {
        const v = parseFee(ef.fee);
        if (v && v > 0) fees.push(v);
    }
    if (fees.length === 0) return null;
    return Math.min(...fees);
}

export function arenaFeeRange(race: Race): { min: number | null; max: number | null } {
    const fees: number[] = [];
    for (const d of race.distances ?? []) {
        if (typeof d.fee === 'number' && d.fee > 0) fees.push(d.fee);
    }
    for (const ef of race.entryFee ?? []) {
        const v = parseFee(ef.fee);
        if (v && v > 0) fees.push(v);
    }
    if (fees.length === 0) return { min: null, max: null };
    return { min: Math.min(...fees), max: Math.max(...fees) };
}

export function arenaFeeShort(fee: number | null): string {
    if (fee == null) return '—';
    if (fee >= 10000) return `₩${M(fee / 10000)}만`;
    if (fee >= 1000) return `₩${M(fee / 1000)}천`;
    return `₩${fee}`;
}

export function arenaFeeFull(fee: number | null): string {
    if (fee == null) return '—';
    return `₩${fee.toLocaleString('ko-KR')}`;
}

export function arenaShortDate(date: string | null): string {
    if (!date) return '';
    const parts = date.split('-');
    if (parts.length < 3) return date;
    return `${parts[1]}.${parts[2]}`;
}

/** D-day padding: race.daysUntilRegistrationEnd preferred, fallback to daysUntilRace */
export function arenaDday(race: Race): { value: number | null; urgent: boolean } {
    const v = race.daysUntilRegistrationEnd ?? race.daysUntilRace ?? null;
    if (v == null) return { value: null, urgent: false };
    return { value: v, urgent: v >= 0 && v <= 7 };
}

export function arenaDdayLabel(race: Race): string {
    const { value } = arenaDday(race);
    if (value == null) return 'D-—';
    if (value < 0) return '마감';
    if (value === 0) return '오늘';
    return `D-${String(value).padStart(2, '0')}`;
}
