import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import {
	createPublicTrainingExample,
	referencePlanWeeks,
	supportsMarathonPlan,
	trainingDaysUntil,
	trainingPlanTiming,
} from '../src/lib/tools/public-training-example.ts';
import { buildPlan, vdot } from '../src/lib/tools.ts';

test('public example uses explicit fictional marathon and sample record, 16 weeks after the SSR reference date', () => {
	const sample = createPublicTrainingExample('2026-11-07');
	assert.equal(sample.goal.name, '가상 풀코스 마라톤');
	assert.equal(sample.goal.distKm, 42.195);
	assert.equal(sample.goal.date, '2027-02-27');
	assert.equal(sample.record.distKm, 21.0975);
	assert.equal(sample.record.timeSec, 6135);
	assert.equal(sample.record.timeStr, '1:42:15');
	assert.deepEqual(trainingPlanTiming(sample.goal.date, sample.referenceDateKst), {
		daysOut: 112, maxWeeks: 16, canPlan: true, lengths: [8, 12, 16],
	});
});

test('personal targets retain four-week minimum and only offer lengths that fit', () => {
	assert.deepEqual(trainingPlanTiming('2026-12-04', '2026-11-07'), {
		daysOut: 27, maxWeeks: 3, canPlan: false, lengths: [],
	});
	assert.deepEqual(trainingPlanTiming('2026-12-05', '2026-11-07'), {
		daysOut: 28, maxWeeks: 4, canPlan: true, lengths: [4],
	});
	assert.deepEqual(trainingPlanTiming('2027-02-06', '2026-11-07'), {
		daysOut: 91, maxWeeks: 13, canPlan: true, lengths: [8, 12],
	});
	assert.equal(trainingDaysUntil('2026-11-06', '2026-11-07'), 0);
	assert.equal(trainingDaysUntil('invalid', '2026-11-07'), 0);
	assert.equal(trainingDaysUntil('2027-02-30', '2026-11-07'), 0);
	assert.throws(() => createPublicTrainingExample('2027-02-30'), RangeError);
});

test('sample dates and target availability stay identical in UTC, Korea and a DST timezone', () => {
	const moduleUrl = new URL('../src/lib/tools/public-training-example.ts', import.meta.url).href;
	const source = `import { createPublicTrainingExample, trainingPlanTiming } from ${JSON.stringify(moduleUrl)};
		const sample = createPublicTrainingExample('2027-03-13');
		process.stdout.write(JSON.stringify({sample,timing:trainingPlanTiming(sample.goal.date,sample.referenceDateKst)}));`;
	const outputs = ['UTC', 'Asia/Seoul', 'America/New_York'].map((tz) => execFileSync(
		process.execPath, ['--experimental-strip-types', '--input-type=module', '-e', source],
		{ env: { ...process.env, TZ: tz }, encoding: 'utf8' },
	));
	assert.equal(outputs[0], outputs[1]);
	assert.equal(outputs[0], outputs[2]);
});

test('reference weeks keep exactly one final race on the target weekday and leave the model unchanged', () => {
	for (const target of ['2027-02-27', '2027-02-28', '2027-03-01', '2027-03-02']) {
		const built = buildPlan(16, vdot(21.0975, 6135), 5, target, '가상 풀코스 마라톤');
		const original = structuredClone(built.plan);
		const plan = referencePlanWeeks(built.plan, target);
		assert.deepEqual(built.plan, original);
		const raceDays = plan.flatMap((week) => week.days.filter((day) => day.zone === 'RACE').map((day) => ({ week: week.wk, day: day.dow })));
		const weekday = new Date(`${target}T00:00:00Z`).getUTCDay();
		assert.deepEqual(raceDays, [{ week: 16, day: ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'][weekday] }]);
		const raceDayIndex = (weekday + 6) % 7;
		assert.ok(plan[15].days.slice(raceDayIndex + 1).every((day) => day.zone === 'REST'));
		assert.equal(plan[0].days.filter((day) => day.zone !== 'REST').length, 4);
	}
});

test('only active road running events offering a full marathon can be personal targets', () => {
	const full = { sport: 'running', status: 'registration_open', distances: [{ distanceMeter: 42_195 }] };
	assert.equal(supportsMarathonPlan(full), true);
	assert.equal(supportsMarathonPlan({ ...full, distances: [{ distanceMeter: 10_000 }, { distanceMeter: 42_195 }] }), true);
	assert.equal(supportsMarathonPlan({ ...full, distances: [{ distanceMeter: 21_098 }] }), false);
	assert.equal(supportsMarathonPlan({ ...full, distances: null }), false);
	assert.equal(supportsMarathonPlan({ ...full, sport: 'trail_running' }), false);
	assert.equal(supportsMarathonPlan({ ...full, sport: 'triathlon' }), false);
	assert.equal(supportsMarathonPlan({ ...full, status: 'cancelled' }), false);
	assert.equal(supportsMarathonPlan({ ...full, status: 'finished' }), false);
});
