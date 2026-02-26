export type CalculationMode = 'time-to-pace' | 'pace-to-time' | 'split-table';

export type DistancePreset = '5k' | '10k' | 'half' | 'full' | 'custom';

export type SplitStrategy = 'even' | 'negative';

export interface SplitRow {
    km: number;
    label: string;
    pace: string;
    splitTime: string;
    cumulativeTime: string;
}

export type TrainingDistance = 'half' | 'full';

export type TrainingWeeks = 12 | 16;

export type TrainingPhase = 'base' | 'build' | 'peak' | 'taper';

export const phaseLabels: Record<TrainingPhase, string> = {
    base: '기초',
    build: '강화',
    peak: '정점',
    taper: '테이퍼',
};

export const phaseColors: Record<TrainingPhase, string> = {
    base: 'bg-info',
    build: 'bg-warning',
    peak: 'bg-error',
    taper: 'bg-success',
};

export const phaseBadgeColors: Record<TrainingPhase, string> = {
    base: 'badge-info',
    build: 'badge-warning',
    peak: 'badge-error',
    taper: 'badge-success',
};

export type WorkoutType = 'easy' | 'tempo' | 'interval' | 'long_run' | 'rest' | 'cross_training' | 'race_pace';

export const workoutLabels: Record<WorkoutType, string> = {
    easy: '이지런',
    tempo: '템포런',
    interval: '인터벌',
    long_run: '롱런',
    rest: '휴식',
    cross_training: '교차훈련',
    race_pace: '레이스페이스',
};

export const workoutColors: Record<WorkoutType, string> = {
    easy: 'badge-success',
    tempo: 'badge-warning',
    interval: 'badge-error',
    long_run: 'badge-primary',
    rest: 'badge-ghost',
    cross_training: 'badge-info',
    race_pace: 'badge-secondary',
};

export interface TargetTimePreset {
    label: string;
    totalMinutes: number;
}

export interface DailyWorkout {
    type: WorkoutType;
    description: string;
    distanceKm?: number;
    paceGuide?: string;
}

export interface TrainingWeek {
    week: number;
    phase: TrainingPhase;
    totalDistanceKm: number;
    days: DailyWorkout[];
}

export interface TrainingPlanData {
    distance: TrainingDistance;
    targetLabel: string;
    totalWeeks: TrainingWeeks;
    weeks: TrainingWeek[];
}
