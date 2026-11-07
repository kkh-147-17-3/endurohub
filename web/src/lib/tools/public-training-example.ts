import type { PlanWeek } from '../tools';

/** The existing model is marathon-oriented, so unsupported targets stay out. */
export function supportsMarathonPlan(race: {
	sport: string;
	status: string;
	distances?: { distanceMeter?: number | null }[] | null;
}): boolean {
	return race.sport === 'running' && race.status !== 'finished' && race.status !== 'cancelled' &&
		!!race.distances?.some((distance) => typeof distance.distanceMeter === 'number' &&
			Math.abs(distance.distanceMeter - 42_195) <= 1);
}

/** Public, fictional input data for exploring the existing marathon plan model. */
export const PUBLIC_TRAINING_SAMPLE_RECORD = {
	distKm: 21.0975,
	timeSec: 6135,
	timeStr: '1:42:15',
	label: '하프 21.0975km · 1:42:15',
} as const;

export const MIN_TRAINING_PLAN_WEEKS = 4;
export const PUBLIC_TRAINING_EXAMPLE_WEEKS = 16;

function isoDateEpoch(value: string): number | null {
	if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
	const epoch = Date.parse(`${value}T00:00:00Z`);
	return Number.isFinite(epoch) && new Date(epoch).toISOString().slice(0, 10) === value ? epoch : null;
}

/** Calendar-day difference, anchored to one SSR-supplied Korean date. */
export function trainingDaysUntil(targetDate: string, referenceDateKst: string): number {
	const target = isoDateEpoch(targetDate);
	const reference = isoDateEpoch(referenceDateKst);
	if (target === null || reference === null) return 0;
	return Math.max(0, Math.round((target - reference) / 86_400_000));
}

export function trainingPlanTiming(targetDate: string, referenceDateKst: string) {
	const daysOut = trainingDaysUntil(targetDate, referenceDateKst);
	const maxWeeks = Math.floor(daysOut / 7);
	const canPlan = maxWeeks >= MIN_TRAINING_PLAN_WEEKS;
	const lengths = canPlan ? [8, 12, 16, 18, 20].filter((weeks) => weeks <= maxWeeks) : [];
	return {
		daysOut,
		maxWeeks,
		canPlan,
		lengths: canPlan && lengths.length === 0 ? [maxWeeks] : lengths,
	};
}

export function createPublicTrainingExample(referenceDateKst: string) {
	const reference = isoDateEpoch(referenceDateKst);
	if (reference === null) throw new RangeError('A valid Korean reference date is required.');
	const targetDate = new Date(reference + PUBLIC_TRAINING_EXAMPLE_WEEKS * 7 * 86_400_000)
		.toISOString().slice(0, 10);
	return {
		referenceDateKst,
		weeks: PUBLIC_TRAINING_EXAMPLE_WEEKS,
		record: { ...PUBLIC_TRAINING_SAMPLE_RECORD },
		goal: {
			id: 'public-marathon-example',
			name: '가상 풀코스 마라톤',
			date: targetDate,
			distKm: 42.195,
		},
	};
}

/** Keep the old phase templates illustrative: only the final week has a race. */
export function referencePlanWeeks(weeks: PlanWeek[], targetDate: string): PlanWeek[] {
	const target = isoDateEpoch(targetDate);
	if (target === null) return [];
	const raceDayIndex = (new Date(target).getUTCDay() + 6) % 7; // MON = 0
	return weeks.map((week, index) => ({
		...week,
		days: week.days.map((day, dayIndex) => ({
			...day,
			zone: index === weeks.length - 1 && dayIndex >= raceDayIndex
				? dayIndex === raceDayIndex ? 'RACE' : 'REST'
				: day.zone === 'RACE' ? 'REST' : day.zone,
		})),
	}));
}
