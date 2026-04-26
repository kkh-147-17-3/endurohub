import type { PageServerLoad } from './$types';
import { apiFetch } from '$lib/api';
import type { PaginatedResponse, Race } from '$lib/types';

export const load: PageServerLoad = async ({ locals }) => {
    const isAuthed = !!locals.authToken;

    let races: Race[] = [];
    let source: 'favorites' | 'sample' = 'favorites';

    if (isAuthed) {
        try {
            const data = await apiFetch<PaginatedResponse<Race>>(
                '/me/favorites/races/',
                { authToken: locals.authToken },
                { page_size: 100 },
            );
            races = data.data ?? [];
        } catch {
            races = [];
        }
    }

    if (races.length === 0) {
        try {
            const data = await apiFetch<PaginatedResponse<Race>>(
                '/races/',
                { authToken: locals.authToken || undefined },
                { page_size: 12, status: ['upcoming', 'registration_open'] },
            );
            races = data.data ?? [];
            source = 'sample';
        } catch {
            races = [];
            source = 'sample';
        }
    }

    return {
        races,
        source,
        isAuthed,
    };
};
