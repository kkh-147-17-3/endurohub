import type {
    TrainingDistance, TrainingWeeks, TrainingPhase,
    TrainingWeek, DailyWorkout, TrainingPlanData, TargetTimePreset,
} from '$lib/tools/types';
import { formatPace } from './pace-calculator';

export const FULL_MARATHON_TARGETS: TargetTimePreset[] = [
    { label: 'Sub-3 (서브3)', totalMinutes: 180 },
    { label: 'Sub-3:30 (서브3:30)', totalMinutes: 210 },
    { label: 'Sub-4 (서브4)', totalMinutes: 240 },
    { label: 'Sub-4:30 (서브4:30)', totalMinutes: 270 },
    { label: 'Sub-5 (서브5)', totalMinutes: 300 },
];

export const HALF_MARATHON_TARGETS: TargetTimePreset[] = [
    { label: 'Sub-1:30', totalMinutes: 90 },
    { label: 'Sub-1:45', totalMinutes: 105 },
    { label: 'Sub-2 (서브2)', totalMinutes: 120 },
    { label: 'Sub-2:15', totalMinutes: 135 },
    { label: 'Sub-2:30', totalMinutes: 150 },
];

interface PaceZones {
    easy: number;
    tempo: number;
    interval: number;
    racePace: number;
    longRun: number;
}

function calculatePaceZones(targetPaceSeconds: number): PaceZones {
    return {
        easy: targetPaceSeconds * 1.25,
        tempo: targetPaceSeconds * 1.08,
        interval: targetPaceSeconds * 0.92,
        racePace: targetPaceSeconds,
        longRun: targetPaceSeconds * 1.20,
    };
}

function getPhaseForWeek(week: number, totalWeeks: TrainingWeeks): TrainingPhase {
    if (totalWeeks === 12) {
        if (week <= 3) return 'base';
        if (week <= 7) return 'build';
        if (week <= 10) return 'peak';
        return 'taper';
    }
    if (week <= 4) return 'base';
    if (week <= 10) return 'build';
    if (week <= 13) return 'peak';
    return 'taper';
}

function getWeeklyDistanceMultiplier(week: number, totalWeeks: TrainingWeeks): number {
    const phase = getPhaseForWeek(week, totalWeeks);
    if (phase === 'taper') {
        const taperStart = totalWeeks === 12 ? 11 : 14;
        const taperWeek = week - taperStart + 1;
        const taperWeeks = totalWeeks - taperStart + 1;
        return 0.85 - (taperWeek / taperWeeks) * 0.35;
    }
    const progress = week / totalWeeks;
    if (progress <= 0.25) return 0.55 + progress * 1.0;
    if (progress <= 0.65) return 0.80 + (progress - 0.25) * 0.5;
    return 1.0;
}

function formatPaceRange(paceSeconds: number, margin: number = 15): string {
    return `${formatPace(paceSeconds - margin)}~${formatPace(paceSeconds + margin)}/km`;
}

function rest(): DailyWorkout {
    return { type: 'rest', description: '휴식' };
}

function easy(km: number, paceSeconds: number): DailyWorkout {
    return {
        type: 'easy',
        description: `이지런 ${km}km`,
        distanceKm: km,
        paceGuide: formatPaceRange(paceSeconds),
    };
}

function tempo(km: number, tempoKm: number, paceSeconds: number): DailyWorkout {
    return {
        type: 'tempo',
        description: `템포런 ${tempoKm}km (총 ${km}km)`,
        distanceKm: km,
        paceGuide: formatPaceRange(paceSeconds, 10),
    };
}

function intervalRun(km: number, reps: string, paceSeconds: number): DailyWorkout {
    return {
        type: 'interval',
        description: `인터벌 ${reps} (총 ${km}km)`,
        distanceKm: km,
        paceGuide: formatPaceRange(paceSeconds, 10),
    };
}

function longRun(km: number, paceSeconds: number): DailyWorkout {
    return {
        type: 'long_run',
        description: `롱런 ${km}km`,
        distanceKm: km,
        paceGuide: formatPaceRange(paceSeconds, 20),
    };
}

function crossTraining(): DailyWorkout {
    return {
        type: 'cross_training',
        description: '교차훈련 (수영, 자전거 등) 30~40분',
    };
}

function racePaceRun(km: number, rpKm: number, paceSeconds: number): DailyWorkout {
    return {
        type: 'race_pace',
        description: `레이스페이스 ${rpKm}km (총 ${km}km)`,
        distanceKm: km,
        paceGuide: formatPaceRange(paceSeconds, 5),
    };
}

function generateWeeklySchedule(
    phase: TrainingPhase,
    weeklyKm: number,
    zones: PaceZones,
    week: number,
    totalWeeks: TrainingWeeks,
    distance: TrainingDistance,
): DailyWorkout[] {
    const isFull = distance === 'full';

    switch (phase) {
        case 'base': {
            const longKm = Math.round(weeklyKm * 0.30);
            const easyKm = Math.round((weeklyKm - longKm) / 3);
            return [
                rest(),
                easy(easyKm, zones.easy),
                easy(easyKm, zones.easy),
                easy(easyKm, zones.easy),
                rest(),
                longRun(longKm, zones.longRun),
                crossTraining(),
            ];
        }
        case 'build': {
            const longKm = Math.round(weeklyKm * 0.32);
            const tempoTotalKm = Math.round(weeklyKm * 0.18);
            const tempoHardKm = Math.round(tempoTotalKm * 0.6);
            const intervalTotalKm = Math.round(weeklyKm * 0.15);
            const easyKm = Math.round((weeklyKm - longKm - tempoTotalKm - intervalTotalKm) / 2);
            const reps = isFull ? '1000m x 5' : '800m x 5';
            return [
                rest(),
                tempo(tempoTotalKm, tempoHardKm, zones.tempo),
                easy(easyKm, zones.easy),
                intervalRun(intervalTotalKm, reps, zones.interval),
                easy(easyKm, zones.easy),
                longRun(longKm, zones.longRun),
                rest(),
            ];
        }
        case 'peak': {
            const longKm = Math.round(weeklyKm * 0.35);
            const maxLong = isFull ? 35 : 18;
            const actualLongKm = Math.min(longKm, maxLong);
            const tempoTotalKm = Math.round(weeklyKm * 0.16);
            const tempoHardKm = Math.round(tempoTotalKm * 0.65);
            const rpTotalKm = Math.round(weeklyKm * 0.15);
            const rpHardKm = Math.round(rpTotalKm * 0.6);
            const easyKm = Math.round((weeklyKm - actualLongKm - tempoTotalKm - rpTotalKm) / 2);
            return [
                rest(),
                tempo(tempoTotalKm, tempoHardKm, zones.tempo),
                easy(easyKm, zones.easy),
                racePaceRun(rpTotalKm, rpHardKm, zones.racePace),
                easy(easyKm, zones.easy),
                longRun(actualLongKm, zones.longRun),
                rest(),
            ];
        }
        case 'taper': {
            const isRaceWeek = week === totalWeeks;
            if (isRaceWeek) {
                const easyKm = Math.round(weeklyKm * 0.25);
                return [
                    rest(),
                    easy(easyKm, zones.easy),
                    easy(Math.round(easyKm * 0.6), zones.easy),
                    rest(),
                    easy(Math.round(easyKm * 0.4), zones.easy),
                    rest(),
                    { type: 'race_pace', description: '대회 당일!', distanceKm: isFull ? 42.195 : 21.0975 },
                ];
            }
            const easyKm = Math.round(weeklyKm * 0.25);
            const tempoKm = Math.round(weeklyKm * 0.12);
            const tempoHardKm = Math.round(tempoKm * 0.5);
            const shortLongKm = Math.round(weeklyKm * 0.28);
            return [
                rest(),
                easy(easyKm, zones.easy),
                tempo(tempoKm, tempoHardKm, zones.tempo),
                rest(),
                easy(easyKm, zones.easy),
                longRun(shortLongKm, zones.longRun),
                rest(),
            ];
        }
    }
}

export function generateTrainingPlan(
    distance: TrainingDistance,
    targetTotalMinutes: number,
    totalWeeks: TrainingWeeks,
): TrainingPlanData {
    const distanceKm = distance === 'full' ? 42.195 : 21.0975;
    const targetPaceSeconds = (targetTotalMinutes * 60) / distanceKm;
    const zones = calculatePaceZones(targetPaceSeconds);

    const peakWeeklyKm = distance === 'full'
        ? Math.min(80, Math.round(distanceKm * 1.5 + 10))
        : Math.min(55, Math.round(distanceKm * 2 + 5));

    const targetPresets = distance === 'full' ? FULL_MARATHON_TARGETS : HALF_MARATHON_TARGETS;
    const targetLabel = targetPresets.find(t => t.totalMinutes === targetTotalMinutes)?.label
        || `${Math.floor(targetTotalMinutes / 60)}:${String(targetTotalMinutes % 60).padStart(2, '0')}`;

    const weeks: TrainingWeek[] = [];

    for (let w = 1; w <= totalWeeks; w++) {
        const phase = getPhaseForWeek(w, totalWeeks);
        const multiplier = getWeeklyDistanceMultiplier(w, totalWeeks);
        const weeklyKm = Math.max(10, Math.round(peakWeeklyKm * multiplier));
        const days = generateWeeklySchedule(phase, weeklyKm, zones, w, totalWeeks, distance);

        weeks.push({
            week: w,
            phase,
            totalDistanceKm: weeklyKm,
            days,
        });
    }

    return { distance, targetLabel, totalWeeks, weeks };
}
