# Pre-launch checklist

Things that are intentionally left half-done right now, deferred to just
before the real launch, and need a human to finish them — none of these
can be done from code alone.

## Analytics & error monitoring (deferred on purpose)

Both are already wired into `index.html` but inert — loading is skipped
entirely until a real ID replaces the placeholder, so there's nothing to
undo if you do this late.

- [ ] **Google Analytics 4** — create a property at
      https://analytics.google.com (Admin → Create Property), add a Web
      data stream for the final domain, copy its Measurement ID (format
      `G-XXXXXXXXXX`), and paste it into `index.html` in place of
      `'PASTE_YOUR_GA4_MEASUREMENT_ID'` (search for that string — one
      spot, near the top of `<head>`).
- [ ] **Sentry** — create a project at https://sentry.io, copy its DSN,
      and paste it into `index.html` in place of
      `'PASTE_YOUR_SENTRY_DSN'` (search for that string — also near the
      top of `<head>`, right after the GA4 block).
- [ ] If GA4 goes live, consider a cookie-consent notice to match the
      app's privacy-first positioning (not legally required under
      India's DPDP Act the way GDPR requires it in the EU, but worth
      doing anyway since GA4 sets tracking cookies).

## Naming

- [ ] Pick the real app name (currently "MARG-AI", a placeholder). Once
      decided, work through `docs/RENAME_CHECKLIST.md`.

## Domain

- [ ] Register and connect the custom domain (target: by end of
      November). Once live, update: the Data Stream URL in GA4, the
      canonical/OG URLs and sitemap in `index.html` /
      `sitemap.xml`, and `robots.txt`'s `Sitemap:` line.

## Still unresolved from earlier

- [ ] **Netlify auto-deploy**: this site has only ever deployed via a
      manual Netlify CLI/API trigger, never via GitHub's webhook —
      confirmed from Netlify's own deploy records (`deploy_source` was
      always `"api"`, never `"github"`). Whether that's intentional or
      a misconfigured "Continuous deployment" setting in the Netlify
      dashboard was never confirmed either way. Worth checking Site
      settings → Build & deploy → Continuous deployment if git-push-to-
      deploy is wanted instead of the current manual trigger.

## Already done (kept here for a record, not action items)

- [x] SEO infra (robots.txt, sitemap.xml, canonical/OG tags, JSON-LD)
- [x] Tailwind CDN JIT compiler replaced with a precompiled stylesheet
- [x] Basic CI (structural/syntax/JSON/browser checks on every push)
- [x] Stray unused Supabase project deleted
