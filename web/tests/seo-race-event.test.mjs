import assert from 'node:assert/strict';
import test from 'node:test';
import { buildRaceEventSchema, serializeJsonLd } from '../src/lib/seo/race-event.ts';

const race = {
    title: '접수 예정 테스트 대회', description: null, sport: 'running', sportLabel: '마라톤',
    raceDate: '2026-11-14', raceEndDate: null, registrationStart: '2026-11-08',
    registrationEnd: '2026-11-12', status: 'upcoming', organizer: null,
    location: '신정교 억새구장', address: '서울특별시 영등포구 영등포로2길 62', region: '서울',
    latitude: 37.5, longitude: 126.9, imageSrc: '/storage/races/poster.webp',
};
const options = {
    appUrl: 'https://www.endurohub.kr', pageUrl: 'https://www.endurohub.kr/races/test',
    officialUrl: 'https://organizer.example/race', minFee: 50000,
};
const schemaFor = (changes = {}, settings = {}) => JSON.parse(serializeJsonLd(
    buildRaceEventSchema({ ...race, ...changes }, { ...options, ...settings }),
));

test('registration before opening has the known dates and is not declared sold out', () => {
    const schema = schemaFor();
    assert.equal(schema.offers.price, '50000');
    assert.equal(schema.offers.validFrom, '2026-11-08');
    assert.equal(schema.offers.validThrough, '2026-11-12');
    assert.equal('availability' in schema.offers, false);
});

test('open registration is available; closed and finished are not assumed sold out', () => {
    assert.equal(schemaFor({ status: 'registration_open' }).offers.availability, 'https://schema.org/InStock');
    for (const status of ['registration_closed', 'finished']) {
        assert.equal('availability' in schemaFor({ status }).offers, false);
    }
    assert.equal(schemaFor({ status: 'finished' }).eventStatus, 'https://schema.org/EventScheduled');
});

test('unknown organizer, performer, price and registration dates are not invented', () => {
    const schema = schemaFor({ organizer: '  ', registrationStart: null, registrationEnd: null });
    for (const key of ['organizer', 'performer']) assert.equal(key in schema, false);
    assert.equal('validFrom' in schema.offers, false);
    assert.equal('validThrough' in schema.offers, false);
    assert.equal('offers' in schemaFor({}, { minFee: null }), false);
    assert.equal('offers' in schemaFor({}, { minFee: -1 }), false);
});

test('known organizer, address, image URL and multiday dates remain accurate', () => {
    const schema = schemaFor({ organizer: '실제 주최자', raceEndDate: '2026-11-15' });
    assert.equal(schema.organizer.name, '실제 주최자');
    assert.equal(schema.organizer.url, options.officialUrl);
    assert.equal(schema.endDate, '2026-11-15');
    assert.equal(schema.image, 'https://www.endurohub.kr/storage/races/poster.webp');
    assert.equal(schema.location.address.streetAddress, race.address);
    assert.equal('addressLocality' in schema.location.address, false);
    assert.equal('url' in schemaFor({ organizer: '실제 주최자' }, { officialUrl: null }).organizer, false);
});

test('JSON-LD source text cannot terminate the script while JSON values stay unchanged', () => {
    const title = '</script><script>alert(1)</script>';
    const json = serializeJsonLd(buildRaceEventSchema({ ...race, title }, options));
    assert.equal(json.includes('</script>'), false);
    assert.equal(JSON.parse(json).name, title);
});
