# Architecture

The controller snapshots a bounded static site, runs a deterministic audit and real SiteProbe/Lens checks, requests specialist proposals, applies trusted edits to a copy, repeats the checks, and requests independent model review. Each stage updates a local state receipt for the visual floor.

Metadata Auditor owns titles and descriptions. Link Health Auditor owns local destinations. Accessibility Auditor proposes image alternatives. Site QA Operator independently reviews the patch. These are separate tool-free model calls using the pinned canonical role contracts. They run sequentially and do not claim concurrent execution.

The controller owns paths, file writes, input limits, patch construction, tool commands and hashes. A model controls only values for assigned findings and its review judgment. The HTML audit and repair code do not execute source scripts. SiteProbe supplies broader crawl evidence; Lens supplies browser, link, accessibility and screenshot evidence. A successful package requires zero supported findings, a passing Lens error threshold and a passing independent review with no findings.

The visual floor is a read-only projection of run artifacts. It polls state and displays actual completed, waiting or blocked stages. Before-and-after screenshots come from Lens. Values in the repair view come from retained proposals. Extra crawl warnings remain visible, even when the supported repairs pass.

Canonical workflow reuse is explicit: the new adapter follows webops-finding-to-fix's stages and PROPOSE boundary. It adds this release's trusted repair operations rather than pretending the existing kit executes arbitrary site fixes. SearchBridge, ContentGraph, production deployment, scheduling, framework builds, authenticated crawling and automatic revision loops are not wired into this release.
