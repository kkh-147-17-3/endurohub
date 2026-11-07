import assert from 'node:assert/strict';
import test from 'node:test';
import {
    parseTime, fmtPace, fmtTime, riegel, vdot, timeFromVdot,
    recordDistanceToKm, pickRunningRecordPrefill, favoriteRacesToGoals,
} from '../src/lib/tools.ts';

test('time input accepts complete clock notation and minutes, rejects malformed or nonpositive values', () => {
    for (const [input, seconds] of [['1:42:15', 6135], ['50:00', 3000], ['50', 3000], [' 0:05 ', 5], ['120:00', 7200]]) {
        assert.equal(parseTime(input), seconds);
    }
    for (const input of ['', '0', '0:00', '-5', 'NaN', 'Infinity', '42junk', '1:99', '1:60:00', '1:20:30:40', '1::30', '1.5', '9'.repeat(400)]) {
        assert.ok(Number.isNaN(parseTime(input)), input);
    }
});

test('pace rounding carries seconds into minutes and 10K 50:00 remains 5:00/km at 12km/h', () => {
    assert.equal(fmtPace(299.9), '5\'00"');
    assert.equal(fmtPace(3599.9), '60\'00"');
    assert.equal(fmtPace(parseTime('50:00') / 10), '5\'00"');
    assert.equal(10 / (parseTime('50:00') / 3600), 12);
    assert.equal(fmtPace(NaN), '—');
    assert.equal(fmtTime(Infinity), '—');
});

test('Riegel uses the advertised 1.06 exponent and rejects unusable inputs', () => {
    assert.equal(fmtTime(riegel(3000, 10, 21.0975)), '1:50:19');
    assert.equal(fmtTime(riegel(3000, 10, 42.195)), '3:50:01');
    assert.equal(riegel(3000, 10, 10), 3000);
    for (const input of [0, -1, NaN, Infinity]) {
        assert.ok(Number.isNaN(riegel(input, 10, 21.0975)));
        assert.ok(Number.isNaN(riegel(3000, input, 21.0975)));
        assert.ok(Number.isNaN(riegel(3000, 10, input)));
    }
});

test('VDOT is a record index and equivalent times invert the same formula without an eight-hour clamp', () => {
    const index = vdot(21.0975, 6135);
    assert.ok(Math.abs(index - 43.9724476) < 1e-6);
    assert.ok(Math.abs(timeFromVdot(index, 21.0975) - 6135) < 1e-6);
    const slowMarathon = timeFromVdot(10, 42.195);
    assert.ok(slowMarathon > 8 * 3600);
    assert.ok(Math.abs(vdot(42.195, slowMarathon) - 10) < 1e-9);
    for (const input of [0, -1, NaN, Infinity]) {
        assert.ok(Number.isNaN(vdot(input, 3000)));
        assert.ok(Number.isNaN(vdot(10, input)));
        assert.ok(Number.isNaN(timeFromVdot(input, 10)));
        assert.ok(Number.isNaN(timeFromVdot(40, input)));
    }
    assert.ok(Number.isNaN(vdot(5, 100000)));
    assert.ok(Number.isNaN(timeFromVdot(40, 1e-9)));
});

test('prefill parses explicit units and skips ambiguous distances instead of inventing a distance', () => {
    for (const [distance, km] of [['1500m', 1.5], ['21.0975K', 21.0975], ['10 km', 10], ['100마일', 160.9344], ['하프', 21.0975]]) {
        assert.ok(Math.abs(recordDistanceToKm(distance) - km) < 1e-9);
    }
    for (const distance of ['울트라', '10–30K', '1,500m', '10K 릴레이', '잘못된 거리', '0km']) {
        assert.equal(recordDistanceToKm(distance), 0);
    }
    const records = [
        { sport: 'cycling', distance: '10K', durationSeconds: 1000, time: '16:40' },
        { sport: 'running', distance: '울트라', durationSeconds: 3600, time: '1:00:00' },
        { sport: 'running', distance: '10K', durationSeconds: Infinity, time: 'bad' },
        { sport: 'running', distance: '1500m', durationSeconds: 360, time: 'stale formatted text' },
    ];
    assert.deepEqual(pickRunningRecordPrefill(records), {
        distKm: 1.5, timeSec: 360, timeStr: '6:00', label: '1500m · 6:00',
    });
    assert.equal(pickRunningRecordPrefill(null), null);
});

test('personal goal candidates exclude cancelled, past and unrelated sports', () => {
    const race = { slug: 'marathon', title: '내 관심 마라톤', raceDate: '2027-02-27', sport: 'running', status: 'upcoming', daysUntilRace: 112, distances: [{ distanceMeter: 42195 }] };
    const candidates = favoriteRacesToGoals([
        { ...race, slug: 'cancelled', status: 'cancelled' },
        { ...race, slug: 'cycling', sport: 'cycling' },
        { ...race, slug: 'finished', status: 'finished' },
        { ...race, slug: 'close', daysUntilRace: 20 },
        race,
    ]);
    assert.deepEqual(candidates, [{ id: 'marathon', name: '내 관심 마라톤', date: '2027-02-27', distKm: 42.195 }]);
});
