# UX Over UI

BDocGen prioritizes reading flow, navigation clarity, and predictable behavior over decorative visuals.

The generated site is intentionally simple so documentation remains fast, portable, and easy to scan.

## UX principles used in generated docs

- Keyboard-first access with a skip link to main content
- No JavaScript dependency for core navigation
- Predictable page routes and stable heading anchors
- Clear side navigation for page-level movement
- Right-rail table of contents for section-level movement
- Mobile-responsive layout with collapsible nav
- Accessible focus styles for keyboard users

## Why this matters

- Documentation should work offline and in constrained environments.
- Deterministic output makes docs reviews and releases easier.
- Stable URLs and heading IDs support reliable deep links from issues, PRs, and release notes.
- A low-complexity UI keeps maintenance overhead small during migration.

## Practical outcome

Visual styling can change through `--theme-file`, while baseline usability behavior stays consistent across builds.
