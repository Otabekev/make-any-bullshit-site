# Make Any Bullshit Sound Brilliant — landing page

`index.html` is the whole site: fonts and images are embedded, so it deploys as a single static file (Vercel, Netlify, anything).

## Editing
1. Change copy or styles in `source/page.html`.
2. Run `python3 source/build.py` — it rebuilds `index.html` with every asset inlined.
3. Commit and push; Vercel redeploys automatically.

## Checkout links
The buy buttons point to `#checkout` (the $27 book) and `#checkout-kit` (the $147 kit). Replace those `href`s in `source/page.html` with the real checkout URLs, then rebuild.

## Folders
- `source/` — editable page, build script, web fonts and images, and the scripts that render the covers and 3D mockups.
- `covers/` — the flagship cover and the 3D book renders at full size.
