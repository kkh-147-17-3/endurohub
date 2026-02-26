import type { SplitRow, SplitStrategy } from '$lib/tools/types';

export const DISTANCES: Record<string, { label: string; km: number }> = {
    '5k': { label: '5km', km: 5 },
    '10k': { label: '10km', km: 10 },
    'half': { label: '하프 마라톤', km: 21.0975 },
    'full': { label: '풀 마라톤', km: 42.195 },
};

export const FULL_MARATHON_PRESETS = [
    { label: 'Sub-3', hours: 2, minutes: 59, seconds: 59 },
    { label: 'Sub-3:30', hours: 3, minutes: 29, seconds: 59 },
    { label: 'Sub-4', hours: 3, minutes: 59, seconds: 59 },
    { label: 'Sub-4:30', hours: 4, minutes: 29, seconds: 59 },
    { label: 'Sub-5', hours: 4, minutes: 59, seconds: 59 },
];

export const HALF_MARATHON_PRESETS = [
    { label: 'Sub-1:30', hours: 1, minutes: 29, seconds: 59 },
    { label: 'Sub-1:45', hours: 1, minutes: 44, seconds: 59 },
    { label: 'Sub-2', hours: 1, minutes: 59, seconds: 59 },
    { label: 'Sub-2:15', hours: 2, minutes: 14, seconds: 59 },
    { label: 'Sub-2:30', hours: 2, minutes: 29, seconds: 59 },
];

export function timeToTotalSeconds(hours: number, minutes: number, seconds: number): number {
    return hours * 3600 + minutes * 60 + seconds;
}

export function timeToPaceSeconds(hours: number, minutes: number, seconds: number, distanceKm: number): number {
    if (distanceKm <= 0) return 0;
    const totalSeconds = timeToTotalSeconds(hours, minutes, seconds);
    return totalSeconds / distanceKm;
}

export function paceToTotalSeconds(paceMinutes: number, paceSeconds: number, distanceKm: number): number {
    const paceInSeconds = paceMinutes * 60 + paceSeconds;
    return paceInSeconds * distanceKm;
}

export function paceToSpeed(paceSeconds: number): number {
    if (paceSeconds <= 0) return 0;
    return 3600 / paceSeconds;
}

export function formatTime(totalSeconds: number): string {
    if (totalSeconds <= 0 || !isFinite(totalSeconds)) return '0:00:00';
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = Math.round(totalSeconds % 60);
    if (h > 0) {
        return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    }
    return `${m}:${String(s).padStart(2, '0')}`;
}

export function formatPace(paceSeconds: number): string {
    if (paceSeconds <= 0 || !isFinite(paceSeconds)) return '0:00';
    const m = Math.floor(paceSeconds / 60);
    const s = Math.round(paceSeconds % 60);
    return `${m}:${String(s).padStart(2, '0')}`;
}

export function generateSplits(
    distanceKm: number,
    paceSeconds: number,
    strategy: SplitStrategy,
    splitInterval: number,
): SplitRow[] {
    if (distanceKm <= 0 || paceSeconds <= 0 || !isFinite(paceSeconds)) return [];

    const rows: SplitRow[] = [];
    const halfDistance = distanceKm / 2;
    let cumulativeSeconds = 0;

    let currentKm = 0;
    while (currentKm < distanceKm) {
        const nextKm = Math.min(currentKm + splitInterval, distanceKm);
        const segmentDistance = nextKm - currentKm;
        const segmentMidpoint = currentKm + segmentDistance / 2;

        let segmentPace = paceSeconds;
        if (strategy === 'negative') {
            segmentPace = segmentMidpoint < halfDistance
                ? paceSeconds * 1.015
                : paceSeconds * 0.985;
        }

        const segmentTime = segmentPace * segmentDistance;
        cumulativeSeconds += segmentTime;

        const isLastSegment = nextKm >= distanceKm;
        const displayKm = isLastSegment ? distanceKm : nextKm;
        const label = isLastSegment && distanceKm % splitInterval !== 0
            ? `${displayKm.toFixed(1)}km`
            : `${displayKm}km`;

        rows.push({
            km: displayKm,
            label,
            pace: formatPace(segmentPace),
            splitTime: formatTime(segmentTime),
            cumulativeTime: formatTime(cumulativeSeconds),
        });

        currentKm = nextKm;
    }

    return rows;
}
