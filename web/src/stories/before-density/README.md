# Calendar height baseline

`CalendarBoard.svelte` was copied from the working tree of `web/src/lib/components/calendar/CalendarBoard.svelte` before the compact calendar height change on 2026-11-07 UTC. It preserves the dense mobile layout with separate sport counts and an open-registration count.

Original source SHA-256: `574679e01a523e49f58f896d27662952abc99d8f711d8b69fb30949fb68f651e`.

Only three relative helper imports were changed to `$lib/components/calendar/...`: `CalendarRaceList.svelte`, `CalendarDiscovery.svelte`, and `RegionCartogram.svelte`. Reversing those import rewrites restores the original source hash.

The `calendar-height` scenario uses this snapshot for BEFORE and the production calendar for AFTER. Both use the current shared component and token styles so the comparison isolates calendar layout rather than earlier style cleanup. Its separate May 2027 fixture fills all six calendar weeks with five sports and six races on each occupied date. Other scenarios retain their original November fixture and the earlier Git baseline in `../before`.
