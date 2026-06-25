# Planning Document Index

This index explains the planning and specification documents for the generic Wayback/static-site recovery toolkit.

| Document | Purpose |
| --- | --- |
| [`../FINAL-SPEC.md`](../FINAL-SPEC.md) | Authoritative generic build spec for the recovery pipeline, artifact model, validation gates, and publication workflow. |
| [`../spec-pythonic-async.md`](../spec-pythonic-async.md) | Preferred implementation option using Python async workers, SQLite state, structured logs, and config-driven runs. |
| [`../spec-minimalist.md`](../spec-minimalist.md) | Simpler implementation option using small scripts and a minimal serving stack. Useful for small targets or prototypes. |
| [`../spec-containerized.md`](../spec-containerized.md) | Container-oriented implementation option for isolated crawlers, workers, serving, and publication support. |
| [`../research-cdx-api.md`](../research-cdx-api.md) | Notes on the Wayback CDX API, pagination, filters, field selection, aliases, and capture fetch URLs. |
| [`../research-tooling.md`](../research-tooling.md) | Comparison of existing Wayback and mirroring tools versus a custom recovery pipeline. |
| [`../research-hosting.md`](../research-hosting.md) | Static serving and publication notes for Caddy, nginx, Tailscale, and generic public hosting. |
| [`../research-dedup.md`](../research-dedup.md) | Deduplication, URL normalization, content addressing, and output path strategy. |
| [`../research-orchestration.md`](../research-orchestration.md) | Pipeline orchestration, retry, rate-limit, state, and resumability notes. |
| [`../review-reliability.md`](../review-reliability.md) | Reliability review of candidate implementation approaches. |
| [`../review-dx.md`](../review-dx.md) | Developer experience review of setup, debugging, reports, and maintainability. |
| [`../review-production.md`](../review-production.md) | Production readiness review of validation, serving, security posture, and publication safety. |
| [`PROGRESS.md`](PROGRESS.md) | Template for target-specific progress notes. Generated evidence belongs under ignored `runs/`. |
| [`archive/original-planning/README.md`](archive/original-planning/README.md) | Historical archive of the original planning markdown used to build the first recovery. |
