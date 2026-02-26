/**
 * Jack Daniels VO2max estimation from race performance.
 *
 * Reference: "Daniels' Running Formula", Jack Daniels PhD
 */

export function calculateVO2max(distanceMeters: number, timeMinutes: number): number {
    if (distanceMeters <= 0 || timeMinutes <= 0) return 0;

    const velocity = distanceMeters / timeMinutes; // m/min

    const vo2 = -4.60 + 0.182258 * velocity + 0.000104 * velocity * velocity;

    const pctVO2max =
        0.8 +
        0.1894393 * Math.exp(-0.012778 * timeMinutes) +
        0.2989558 * Math.exp(-0.1932605 * timeMinutes);

    if (pctVO2max <= 0) return 0;

    return vo2 / pctVO2max;
}

export type Gender = 'male' | 'female';

export interface VO2maxRating {
    label: string;
    color: string;
    description: string;
}

const maleRatings: { min: number; rating: VO2maxRating }[] = [
    { min: 60, rating: { label: '최상', color: 'badge-error', description: '상위 1~5% 수준의 엘리트 체력' } },
    { min: 52, rating: { label: '우수', color: 'badge-warning', description: '상위 5~20% 수준' } },
    { min: 45, rating: { label: '좋음', color: 'badge-success', description: '상위 20~40% 수준' } },
    { min: 40, rating: { label: '보통', color: 'badge-info', description: '평균 수준 (40~60%)' } },
    { min: 35, rating: { label: '평균이하', color: 'badge-ghost', description: '하위 20~40% 수준' } },
    { min: 0, rating: { label: '낮음', color: 'badge-ghost', description: '하위 20% 이하' } },
];

const femaleRatings: { min: number; rating: VO2maxRating }[] = [
    { min: 52, rating: { label: '최상', color: 'badge-error', description: '상위 1~5% 수준의 엘리트 체력' } },
    { min: 45, rating: { label: '우수', color: 'badge-warning', description: '상위 5~20% 수준' } },
    { min: 38, rating: { label: '좋음', color: 'badge-success', description: '상위 20~40% 수준' } },
    { min: 33, rating: { label: '보통', color: 'badge-info', description: '평균 수준 (40~60%)' } },
    { min: 28, rating: { label: '평균이하', color: 'badge-ghost', description: '하위 20~40% 수준' } },
    { min: 0, rating: { label: '낮음', color: 'badge-ghost', description: '하위 20% 이하' } },
];

export function getVO2maxRating(vo2max: number, gender: Gender): VO2maxRating {
    const table = gender === 'male' ? maleRatings : femaleRatings;
    for (const entry of table) {
        if (vo2max >= entry.min) return entry.rating;
    }
    return table[table.length - 1].rating;
}

export function estimatePercentile(vo2max: number, gender: Gender): number {
    const mean = gender === 'male' ? 42 : 35;
    const stdDev = gender === 'male' ? 8 : 7;

    const z = (vo2max - mean) / stdDev;

    const percentile = 100 / (1 + Math.exp(-1.7 * z));
    return Math.max(1, Math.min(99, Math.round(percentile)));
}

export function getTrainingPaces(vo2max: number): {
    easy: string;
    marathon: string;
    tempo: string;
    interval: string;
    repetition: string;
} {
    if (vo2max <= 0) {
        return { easy: '-', marathon: '-', tempo: '-', interval: '-', repetition: '-' };
    }

    function velocityFromVO2(vo2: number): number {
        const a = 0.000104;
        const b = 0.182258;
        const c = -4.60 - vo2;
        const discriminant = b * b - 4 * a * c;
        if (discriminant < 0) return 0;
        return (-b + Math.sqrt(discriminant)) / (2 * a);
    }

    function velocityToPace(vMPerMin: number): string {
        if (vMPerMin <= 0) return '-';
        const secPerKm = (1000 / vMPerMin) * 60;
        const min = Math.floor(secPerKm / 60);
        const sec = Math.round(secPerKm % 60);
        return `${min}:${String(sec).padStart(2, '0')}`;
    }

    const easyVO2 = vo2max * 0.65;
    const marathonVO2 = vo2max * 0.80;
    const tempoVO2 = vo2max * 0.88;
    const intervalVO2 = vo2max * 0.98;
    const repVO2 = vo2max * 1.05;

    return {
        easy: velocityToPace(velocityFromVO2(easyVO2)),
        marathon: velocityToPace(velocityFromVO2(marathonVO2)),
        tempo: velocityToPace(velocityFromVO2(tempoVO2)),
        interval: velocityToPace(velocityFromVO2(intervalVO2)),
        repetition: velocityToPace(velocityFromVO2(repVO2)),
    };
}
