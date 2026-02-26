/**
 * Race Time Predictor using Pete Riegel's formula (1981).
 *
 * T2 = T1 × (D2 / D1) ^ 1.06
 *
 * Where:
 *  T1 = known race time
 *  D1 = known race distance
 *  D2 = target race distance
 *  1.06 = fatigue factor (commonly accepted value)
 */

import { formatTime } from './pace-calculator';

export interface PredictionResult {
    distance: string;
    distanceKm: number;
    predictedSeconds: number;
    predictedTime: string;
    pacePerKm: string;
}

export const PREDICTION_DISTANCES = [
    { label: '5km', km: 5 },
    { label: '10km', km: 10 },
    { label: '15km', km: 15 },
    { label: '하프 마라톤', km: 21.0975 },
    { label: '30km', km: 30 },
    { label: '풀 마라톤', km: 42.195 },
    { label: '50km 울트라', km: 50 },
    { label: '100km 울트라', km: 100 },
];

export function predictRaceTime(
    knownDistanceKm: number,
    knownTimeSeconds: number,
    targetDistanceKm: number,
    fatigueFactor: number = 1.06,
): number {
    if (knownDistanceKm <= 0 || knownTimeSeconds <= 0 || targetDistanceKm <= 0) return 0;
    return knownTimeSeconds * Math.pow(targetDistanceKm / knownDistanceKm, fatigueFactor);
}

export function formatPaceFromSeconds(totalSeconds: number, distanceKm: number): string {
    if (distanceKm <= 0 || totalSeconds <= 0) return '-';
    const paceSeconds = totalSeconds / distanceKm;
    const min = Math.floor(paceSeconds / 60);
    const sec = Math.round(paceSeconds % 60);
    return `${min}:${String(sec).padStart(2, '0')}`;
}

export function predictAllDistances(
    knownDistanceKm: number,
    knownTimeSeconds: number,
    fatigueFactor: number = 1.06,
): PredictionResult[] {
    return PREDICTION_DISTANCES
        .filter(d => d.km !== knownDistanceKm)
        .map(d => {
            const predicted = predictRaceTime(knownDistanceKm, knownTimeSeconds, d.km, fatigueFactor);
            return {
                distance: d.label,
                distanceKm: d.km,
                predictedSeconds: predicted,
                predictedTime: formatTime(predicted),
                pacePerKm: formatPaceFromSeconds(predicted, d.km),
            };
        });
}
