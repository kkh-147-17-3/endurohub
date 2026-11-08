# Date grouping comparison snapshot

This directory preserves the working-tree race list immediately before the date grouping change. The repeated row dates and original information layout are historical evidence for the requested before/after comparison. Do not apply current visual cleanup or date grouping rules to this snapshot.

Make race list changes in `web/src/lib/components/calendar/CalendarRaceList.svelte`. Keep this snapshot byte-for-byte unchanged. Its imports already use `$lib`, so no import rewrites are needed. Both versions of the focused comparison use the current shared component and token styles and the same 36 fixture races across six dates. This baseline is distinct from the older Git snapshot in `../before` and the calendar height snapshot in `../before-density`.
