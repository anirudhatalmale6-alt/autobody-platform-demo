# Auto body shop platform — working demo

Two pieces of the brief, built and running so they can be tested rather than
described: the before/after comparison slider, and the estimate request with
vehicle photo uploads. The whole page switches between English and Spanish.

All imagery is a generated placeholder. `make_placeholders.py` builds the two
frames; both share identical geometry, which is the one property real
before/after pairs must have for a comparison slider to read correctly.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | The demo. Self-contained: no build step, no dependencies. |
| `make_placeholders.py` | Regenerates the placeholder image pair (Pillow). |
| `test_demo.py` | Playwright suite — 40 checks over slider, uploads, validation, both languages, mobile. |

## Running it

```sh
python3 -m http.server 8000
# open http://127.0.0.1:8000/

PORT=8000 python3 test_demo.py   # run the checks
```

## What is and isn't real here

Real: the slider (drag, tap, touch, arrow keys), photo attach/preview/remove,
file type-size-count validation, full EN/ES switching including select options
and error messages.

Not real: nothing is uploaded or stored. Submitting shows what the server would
receive. The live build writes to the database, stores the photos, notifies the
shop and opens the job in the owner dashboard.
