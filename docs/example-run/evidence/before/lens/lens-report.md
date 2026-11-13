# Lens Report

Status: FAIL
URL: http://127.0.0.1:63232
Started: 2026-11-13T13:12:54Z
Finished: 2026-11-13T13:12:58Z
Duration: 4267ms
Viewports: desktop, mobile
Output Directory: /Users/robertdevore/2026/Kujolang/kujo-repos/webops-factory/.runtime/runs/20261113T131253Z-6e15286b/evidence/before/lens

## Summary

Status: FAIL
Total findings: 5
Critical: 0
Errors: 4
Warnings: 1
Info: 0
Fail threshold: error
Exit code: 1
Checks run: 9
Checks skipped: 0
Artifacts written: 10

Lens found 5 finding(s). 4 at or above the fail threshold of `error`. Start with critical issues, then errors, then warnings.

## Critical Issues

No critical issues found.

## Errors

- **LENS-A11Y-001** — Accessibility violation: document-title (serious)
  axe-core reported 'document-title' affecting 1 element(s) in the desktop viewport. Ensure each HTML document contains a non-empty <title> element
  Evidence: accessibility.json (desktop scan), rule document-title

- **LENS-A11Y-002** — Accessibility violation: image-alt (critical)
  axe-core reported 'image-alt' affecting 1 element(s) in the desktop viewport. Ensure <img> elements have alternative text or a role of none or presentation
  Evidence: accessibility.json (desktop scan), rule image-alt

- **LENS-A11Y-003** — Accessibility violation: document-title (serious)
  axe-core reported 'document-title' affecting 1 element(s) in the mobile viewport. Ensure each HTML document contains a non-empty <title> element
  Evidence: accessibility.json (mobile scan), rule document-title

- **LENS-A11Y-004** — Accessibility violation: image-alt (critical)
  axe-core reported 'image-alt' affecting 1 element(s) in the mobile viewport. Ensure <img> elements have alternative text or a role of none or presentation
  Evidence: accessibility.json (mobile scan), rule image-alt


## Warnings

- **LENS-LINKS-001** — Broken link (HTTP 404): Explore our services ↗
  Same-origin link http://127.0.0.1:63232/services-old.html returned HTTP 404.
  Evidence: links.json entry 4


## Evidence

Runtime evidence collected:

- Screenshots: `screenshots/desktop.png`, `screenshots/mobile.png`
- Console log: `console.json`
- Network log: `network.json`
- DOM summaries: `dom-summary.json`
- Link check results: `links.json`

- Accessibility results: `accessibility.json`

## Accessibility

Accessibility checks were enabled for this run.

- Engine: axe-core 4.11.4
- Scans completed: 2
- Violations found: 4
- Results: `accessibility.json`

Violations are reported as `LENS-A11Y-NNN` findings above. Review the
accessibility.json artifact for full violation details including impacted
element selectors, rule IDs, and remediation guidance.

Accessibility checks use axe-core automated rules. They do not guarantee
WCAG compliance and are not a substitute for manual accessibility review.

## Suggested Repair Tasks

1. Investigate the broken same-origin link recorded in links.json entry 4.

2. Resolve the 'document-title' accessibility issue in the desktop viewport. Documents must have <title> element to aid in navigation Reference: https://dequeuniversity.com/rules/axe/4.11/document-title?application=axeAPI

3. Resolve the 'image-alt' accessibility issue in the desktop viewport. Images must have alternative text Reference: https://dequeuniversity.com/rules/axe/4.11/image-alt?application=axeAPI

4. Resolve the 'document-title' accessibility issue in the mobile viewport. Documents must have <title> element to aid in navigation Reference: https://dequeuniversity.com/rules/axe/4.11/document-title?application=axeAPI

5. Resolve the 'image-alt' accessibility issue in the mobile viewport. Images must have alternative text Reference: https://dequeuniversity.com/rules/axe/4.11/image-alt?application=axeAPI


## Agent Repair Brief

Lens failed because 4 finding(s) met the configured fail threshold of `error`.

The page loaded successfully. Secondary findings (console, network, overflow, links) can be trusted.

Viewports tested: desktop, mobile.

Link check enabled: 1 link finding(s) reported.

First artifacts to inspect:
- `accessibility.json (desktop scan), rule document-title`
- `accessibility.json (desktop scan), rule image-alt`
- `accessibility.json (mobile scan), rule document-title`

Suggested first pass:
1. Resolve the 'document-title' accessibility issue in the desktop viewport. Documents must have <title> element to aid in navigation Reference: https://dequeuniversity.com/rules/axe/4.11/document-title?application=axeAPI
2. Resolve the 'image-alt' accessibility issue in the desktop viewport. Images must have alternative text Reference: https://dequeuniversity.com/rules/axe/4.11/image-alt?application=axeAPI
3. Resolve the 'document-title' accessibility issue in the mobile viewport. Documents must have <title> element to aid in navigation Reference: https://dequeuniversity.com/rules/axe/4.11/document-title?application=axeAPI
4. Resolve the 'image-alt' accessibility issue in the mobile viewport. Images must have alternative text Reference: https://dequeuniversity.com/rules/axe/4.11/image-alt?application=axeAPI
5. Investigate the broken same-origin link recorded in links.json entry 4.

Do not assume the root cause is framework-specific unless the source code or console output proves it. Each finding includes evidence references — inspect those artifacts before drawing conclusions.

## Artifacts

- `lens-report.md`
- `lens-report.json`
- `metadata.json`
- `console.json`
- `network.json`
- `dom-summary.json`
- `screenshots/desktop.png`
- `screenshots/mobile.png`
- `links.json`
- `accessibility.json`
