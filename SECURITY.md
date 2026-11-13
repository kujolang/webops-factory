# Security boundaries

Missions, website contents and worker responses are untrusted data. The trusted controller never executes a model-supplied command or script. Workers use an ephemeral, tool-disabled Codex session in a private home. Their output is limited to finding IDs, values and reasons.

The first release accepts a bounded static export. It rejects active HTML, event handlers, executable files and symlinks. The browser preview uses a restrictive content policy: no page scripts, external assets, forms, frames or connections. Browser checks run on a loopback preview, not a public production website. No user project build, package install or server-side code runs during a mission. This boundary is not a general-purpose sandbox for arbitrary software; framework builds and executable missions need a separate execution-isolation design.

Repairs are allow-listed operations on an isolated candidate copy. A link repair must resolve to an existing local file. Metadata and alternative text are escaped. A worker cannot expand its assigned finding set. All proposed edits are validated before any candidate file is written. Original files are compared with intake hashes before packaging.

The floor binds to loopback and has read-only routes. Artifact paths reject traversal and symlinks. Site HTML served as an artifact receives the same restrictive content policy. Do not expose this local server directly to the internet.

The package verifier checks the files named in the manifest. It is an integrity check, not a digital signature or proof against someone replacing both manifest and files. Human review remains required. Source text and screenshots can contain private information; inspect them before sharing a run. Provider requests send the selected HTML and small SVG descriptions to your configured Codex account. Authentication stays in `.runtime/provider`, outside Git.

Live providers and Chromium are trusted dependencies. Use a dedicated account and machine for sensitive or hostile inputs. Do not interpret model approval as permission to publish.
