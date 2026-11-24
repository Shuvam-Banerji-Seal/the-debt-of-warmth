TASK: FIX THE MAP `atlas/$slug/map.html`

Rendering it with headless Chromium failed or produced a blank image:

```
$error
```

Read design/MAP-GUIDE.md and the map files. Find the bug (a JavaScript error, a font-loading race, a wrong size, an infinite loop, or drawing that never runs) and fix it, keeping the map's design. The page must draw completely within a few seconds with no network access. Reply with one line when done.
