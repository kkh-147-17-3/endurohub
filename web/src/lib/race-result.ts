import { arenaSportCode } from '$lib/arena';
import type { Distance, Sport } from '$lib/types';

export interface RaceCourseOption {
    code: string;
    label: string;
    distanceKm: number;
}

/** Keep this in sync with accounts.serializers.course_code_for. */
export function courseCodeForDistance(distance: Distance): string {
    if (distance.distanceMeter && distance.distanceMeter > 0) {
        const km = distance.distanceMeter / 1000;
        return Number.isInteger(km) ? `${km}K` : `${km.toFixed(1)}K`;
    }
    return (distance.name || '').slice(0, 4).toUpperCase();
}

export function distanceKm(distance: Distance): number {
    if (distance.distanceMeter && distance.distanceMeter > 0) {
        return distance.distanceMeter / 1000;
    }
    const matched = (distance.name || '').match(/(\d+(?:\.\d+)?)/);
    return matched ? Number(matched[1]) : 0;
}

export function raceCourseOptions(
    distances: Distance[] | null | undefined,
    sport: Sport,
    sportLabel: string,
): RaceCourseOption[] {
    const seenCodes = new Set<string>();
    const courses = (distances ?? [])
        .map((distance) => {
            const code = courseCodeForDistance(distance);
            return {
                code,
                label: distance.name || code,
                distanceKm: distanceKm(distance),
            };
        })
        .filter((course) => {
            if (!course.code || seenCodes.has(course.code)) return false;
            seenCodes.add(course.code);
            return true;
        });

    if (courses.length > 0) return courses;
    return [{ code: arenaSportCode[sport], label: sportLabel, distanceKm: 0 }];
}
