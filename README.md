# Max Verstappen — Born to Race

A private Max Verstappen fan website adapted from the visual layout at
https://landonorris.com/. It preserves the reference typography, responsive
page layouts, navigation, GSAP scrolling, Rive UI effects and WebGL circuit
viewer, with a navy blue and red theme.

The six pages include a genuine helmet photo collection with selectable views,
all 72 Grand Prix wins, all 249 Grand Prix entries across 2015–2026,
championship seasons, records, an updated calendar, career milestones and
Verstappen Racing / sim racing projects. Statistics reflect the official
sources listed in `content/max-data.json` as of **7 October 2026**.

Photos and their original URLs are documented in `content/max-assets.json`.
The helmet viewer uses published photo angles. Scale-replica product photos
are identified in the viewer. The opening screen starts navy; the official
2026 Red Bull RB22 sweeps left to right and reveals Max's name in red before
the website appears. The home hero uses Max's full-body portrait from the
previous version, with gentle pointer parallax. The loading screen retains
its navy background, left-to-right Red Bull car and red name reveal.
The loading screen is styled and controlled by `max-experience.css` and
`max-experience.js`.

Sepang uses its official track image;
the other available circuits keep the reference's 3D viewer.

## Run locally

With Node.js 18 or newer installed, run:

    npm run dev

There are no dependencies to install. Open http://localhost:4173/.
On Windows, double-click `start-windows.bat`.

Python is also supported:

    python -m http.server 8080 --directory dist

Then open http://localhost:8080/.

WebGL effects require WebGL 2 and browser hardware acceleration. A fallback
keeps the pages readable on devices without it. The custom helmet viewer,
filters, race results and session schedule work independently of WebGL.

## Edit and validate

Public pages and locally bundled resources live in `dist/`. You can edit those
files directly. `max-theme.css` and `max-app.js` contain the Max-specific
styles and interactions alongside `max-experience.css` and
`max-experience.js`. To regenerate page content from the reference
templates and verified JSON files, install Python's `lxml` package and run:

    python tools/adapt-max.py

Validate route references, script syntax, assets and driver data with:

    npm run check

The original template export helper `tools/assemble.py` is retained as source
history; running it would recreate the original reference pages.

## Deployment

This project uses Sites hosting and retains owner-only access. Store, project
and social links open official external websites. There is no purchase form,
newsletter collection or added advertising analytics in this fan project.
