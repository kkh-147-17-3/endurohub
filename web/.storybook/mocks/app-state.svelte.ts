/** Standalone gallery state; Storybook itself uses its framework's state mocks. */
export const page = $state({
    url: new URL('https://storybook.invalid/calendar'),
    data: {},
    params: {},
    route: { id: '/calendar' },
    status: 200,
    error: null,
    form: null,
    state: {},
});
export const navigating = { from: null, to: null, type: null, willUnload: null, delta: null, complete: null };
export const updated = { current: false, check: async () => false };
