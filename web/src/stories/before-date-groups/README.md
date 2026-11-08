# Date grouping comparison baseline

`CalendarRaceList.svelte` is a byte-for-byte snapshot of the working-tree component immediately before the date grouping change. It preserves the repeated per-row dates visible in the user's reference. The capture hash and source path are recorded in `provenance.json`. No import rewrites were required.

The `date-groups` scenario renders this snapshot for BEFORE and the production component for AFTER. Each receives the same `denseCalendarRaces` array: 36 races on six dates in May 2027. Both use the current shared token and component CSS. The preview focuses on the open month list rather than showing the calendar board above it.

AFTER keeps each date once as a group heading and removes it from the individual rows. Race titles, sports, registration states, deadlines, locations, distances and fees remain available. The selected-day modal is outside this grouping change because its date is already established.

Story IDs:

- `design-preview--date-groups-before`
- `design-preview--date-groups-after`

Use the default `design-comparison--overview` story to compare these at mobile, tablet or desktop widths. The other nine comparison scenarios remain available.
