# Verification

Run `npm run verify` for boundary tests and Markdown link checks. The tests cover the five example defects, successful repairs, source preservation, traversal, symlinks, active HTML, excluded secrets, invented finding IDs, external repair targets, markup injection, stale source, duplicate edits and package drift.

The example uses a fictional Detroit design studio. Its missing metadata, missing image alternative and broken services link are deliberate. Fixture mode supplies fixed repair values but still invokes the real crawl and browser tools. Live mode sends separate requests to the WebOps specialists and independent reviewer. Retained evidence must identify which mode ran.

## Recorded live example

Run `20261113T131253Z-6e15286b` completed on November 13, 2026. It repaired five supported findings across three pages in **43.443 seconds**, using three specialist calls and one independent review. The final state is `approval_required`, not deployed.

The original site remained unchanged. SiteProbe artifact verification passed before and after repairs. Lens passed its final homepage desktop/mobile checks, and the independent reviewer returned `pass`. Additional SiteProbe findings outside the four repair types remain in the crawl report; the factory does not hide them.

Inspect the [state](example-run/state.json), [exact patch](example-run/patches/repairs.diff), [independent review](example-run/review.json) and [hashed package](example-run/package.json). The package SHA-256 is `1e4676ba50bcab12753eb8b9ae7b4270ebec7948504e29b958afa779587cb2c3`. `npm run demo` imports this record and verifies all manifest files before the floor displays it.

Earlier runs were blocked when the reviewer lacked illustration evidence and when an alternative text invented an ambiguous object. The controller retained those failures without producing approval packages. The final worker instruction asks for conservative descriptions of clearly identifiable elements, and the reviewer receives the source SVG.

## Local checks

`npm run verify` passes 17 tests and repository Markdown links. `npm run doctor` launches Chromium and checks the runtime. With the floor running, `npm run verify:floor` checks six stations, five repair cards, keyboard focus, loaded screenshots, the artifact content policy, traversal rejection, mobile layout and browser errors.

The setup completed on a busy, resource-limited development machine with warm dependency caches. This was **not a clean-machine installation benchmark**. Timings from this busy development machine are observations, not onboarding promises. No search ranking, revenue, WCAG conformance or production deployment claim follows from these checks.

A [fresh-clone portability check](portability-check.json) passed against the published repository: clone, `npm ci`, setup, recorded-example import and a fixture mission. Total elapsed time was 75.179 seconds, including the fixture run; setup itself took 48.896 seconds. The check excluded account login. Existing system tools and warm caches make this unsuitable as a clean-machine onboarding estimate.

## Demo video

The 46.5-second demo uses actual browser recordings of the exported live run and example website, ElevenLabs Siren narration and the Kujo bumper. The render passed HyperFrames checks and full decoding. All 1,395 frames were scanned: no isolated flash candidates, gray startup frames, black frames or blank white frames were found. Contact sheets and all scene and navigation cuts were visually inspected.

Audio level checks passed at -16.70 LUFS and -1.65 dBTP. Listening for pronunciation and mix comfort has not been attested, so the media review remains `REVIEW_INCOMPLETE`. The film shows completed run evidence, not real-time agent execution. Exact hashes and source provenance are in the [media manifest](media/manifest.json).
