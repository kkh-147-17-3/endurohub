import type { Race } from '../types';

type RaceEventInput = Pick<
    Race,
    | 'title' | 'description' | 'raceDate' | 'raceEndDate' | 'sportLabel'
    | 'location' | 'address' | 'region' | 'latitude' | 'longitude'
    | 'imageSrc' | 'sport' | 'status' | 'registrationStart' | 'registrationEnd' | 'organizer'
>;

interface RaceEventOptions {
    appUrl: string;
    pageUrl: string;
    officialUrl: string | null;
    minFee: number | null;
}

/** Describe known facts only; a closed registration does not imply sold-out tickets. */
export function buildRaceEventSchema(race: RaceEventInput, options: RaceEventOptions) {
    const { appUrl, pageUrl, officialUrl, minFee } = options;
    const organizer = race.organizer?.trim();
    const hasCoordinates = race.latitude != null && race.longitude != null;

    return {
        '@context': 'https://schema.org',
        '@type': 'SportsEvent',
        name: race.title,
        description: race.description?.trim().slice(0, 200)
            || [race.title, race.location, race.sportLabel, '대회'].filter(Boolean).join(' · '),
        startDate: race.raceDate || undefined,
        endDate: race.raceEndDate || race.raceDate || undefined,
        // A past event remains scheduled; only an explicit cancellation changes this status.
        eventStatus: race.status === 'cancelled'
            ? 'https://schema.org/EventCancelled'
            : 'https://schema.org/EventScheduled',
        eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode',
        url: pageUrl,
        sport: race.sportLabel,
        location: race.location || race.address ? {
            '@type': 'Place',
            name: race.location || undefined,
            address: {
                '@type': 'PostalAddress',
                streetAddress: race.address || undefined,
                addressRegion: race.region || undefined,
                addressCountry: 'KR',
            },
            geo: hasCoordinates ? {
                '@type': 'GeoCoordinates',
                latitude: race.latitude,
                longitude: race.longitude,
            } : undefined,
        } : undefined,
        image: new URL(
            race.imageSrc || `/images/og-${race.sport.replace('_', '-')}.png`, appUrl,
        ).href,
        sameAs: officialUrl || undefined,
        offers: race.status !== 'cancelled' && minFee != null && Number.isFinite(minFee) && minFee >= 0 ? {
            '@type': 'Offer',
            url: officialUrl || pageUrl,
            // Upcoming, closed and finished states do not tell us whether capacity sold out.
            availability: race.status === 'registration_open' ? 'https://schema.org/InStock' : undefined,
            price: String(minFee),
            priceCurrency: 'KRW',
            validFrom: race.registrationStart || undefined,
            validThrough: race.registrationEnd || undefined,
        } : undefined,
        organizer: organizer ? {
            '@type': 'Organization',
            name: organizer,
            url: officialUrl || undefined,
        } : undefined,
    };
}

/** Keep user/source text from terminating the surrounding JSON-LD script element. */
export function serializeJsonLd(value: unknown): string {
    return JSON.stringify(value).replace(/</g, '\\u003c');
}
