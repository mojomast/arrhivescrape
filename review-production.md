# Production Readiness Tournament Review

Reviewer: T3, Phase 2

Scope: production-readiness comparison of `spec-minimalist.md`, `spec-pythonic-async.md`, and `spec-containerized.md`, informed by the Phase 0 research documents for CDX usage, tooling, hosting, deduplication, and orchestration.

## Scoring Matrix

Scores are 1-10, where 10 means the spec is production-ready for the criterion with clear implementation details, safe defaults, and low operational ambiguity.

| Spec | Robust Serve Config For Public Traffic | HTTPS + MIME Types + Cache Headers | Security Posture | Tailscale Integration Quality | Incremental Updates When New Snapshots Exist | Average |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Minimalist | 7 | 5 | 7 | 8 | 6 | 6.6 |
| Pythonic Async | 8 | 6 | 8 | 8 | 9 | 7.8 |
| Containerized | 8 | 6 | 8 | 8 | 7 | 7.4 |

## Tournament Result

1. `spec-pythonic-async.md` wins overall. It has the strongest recovery-state model, resumability, retry discipline, path mapping, deduplication, and incremental update story. Its serving layer is solid but still light on cache policy.
2. `spec-containerized.md` is second. It has the most reproducible operational envelope and clean service isolation, but its Tailscale sidecar details are more complex and its incremental update flow is stage-based rather than a clearly idempotent end-to-end refresh loop.
3. `spec-minimalist.md` is third. It is pragmatic and auditable, with the simplest nginx/Tailscale deployment, but shell-based fetch orchestration and sparse HTTP cache/header policy make it weaker for sustained production operation.

## Criterion Notes

### Robustness Of Serve Config For Public Traffic

`spec-minimalist.md`: 7/10

- Strengths: nginx binds to `127.0.0.1:8080`, disables `autoindex`, includes MIME types, sets `default_type application/octet-stream`, and uses `try_files $uri $uri/index.html $uri.html =404` with no SPA fallback.
- Strengths: local-only nginx behind Tailscale matches the hosting research recommendation for controlled exposure.
- Critical gaps: no `server_tokens off`, no compression, no explicit access/error log strategy, no health endpoint, and no rate/connection limits for public Funnel scenarios.

`spec-pythonic-async.md`: 8/10

- Strengths: Caddy config is concise, loopback-bound, disables directory browsing, preserves `404`, uses exact path then directory index then `.html` fallback, and enables `zstd`/`gzip` compression.
- Strengths: Caddy's static serving and MIME behavior are production-friendly with less config surface area.
- Critical gaps: no health endpoint, no explicit cache policy, and `auto_https off` is correct behind Tailscale but must be changed carefully if direct public DNS is later used.

`spec-containerized.md`: 8/10

- Strengths: nginx container serves only `recovered/kyledurepos.com/site` read-only, has a health check, disables `autoindex`, disables `server_tokens`, uses deterministic `try_files`, and returns `404` for missing files.
- Strengths: operational artifacts are explicitly outside the served root.
- Critical gaps: no compression, no cache policy, no explicit location blocking dotfiles or accidental hidden files inside the site tree, and public traffic depends on a more complex sidecar path.

### HTTPS + MIME Types + Cache Headers

`spec-minimalist.md`: 5/10

- Strengths: HTTPS is delegated to Tailscale Serve/Funnel, nginx includes `/etc/nginx/mime.types`, and `default_type application/octet-stream` is safe.
- Strengths: `X-Content-Type-Options: nosniff` is present.
- Critical gaps: no `Cache-Control`, `ETag`, `Last-Modified`, immutable asset policy, HTML no-cache policy, compression, HSTS discussion, or direct public HTTPS fallback beyond Tailscale.

`spec-pythonic-async.md`: 6/10

- Strengths: Caddy handles MIME types automatically and enables `encode zstd gzip`; HTTPS via Tailscale is clear, with notes for switching to direct Caddy ACME when public DNS points directly at the host.
- Strengths: includes `X-Content-Type-Options` and `Referrer-Policy`.
- Critical gaps: no explicit cache headers. Archived static assets could benefit from long-lived caching, while HTML may need shorter/no-cache behavior during validation and incremental refreshes.

`spec-containerized.md`: 6/10

- Strengths: nginx includes MIME types, uses `default_type application/octet-stream`, and HTTPS is clearly intended to terminate at Tailscale.
- Strengths: includes `X-Content-Type-Options` and `Referrer-Policy`.
- Critical gaps: no `Cache-Control`, no compression, no ETag/conditional request discussion, and no HSTS or browser-facing HTTPS policy guidance for Funnel/public exposure.

### Security Posture

`spec-minimalist.md`: 7/10

- Strengths: no directory listing, no catch-all fallback, dotfile paths return `404`, nginx is loopback-only, and the public surface is Tailscale rather than nginx directly.
- Strengths: no open redirect logic in the serve config.
- Critical gaps: generated recovery output may include arbitrary archived HTML/JS, but the spec does not discuss sandboxing, CSP tradeoffs, outbound third-party references, or public exposure risk from recovered active content.

`spec-pythonic-async.md`: 8/10

- Strengths: directory listing is disabled, no SPA fallback, Caddy is loopback-only, no redirect rules that create open-redirect risk, and HTML cleanup is conservative rather than broad/destructive.
- Strengths: operational files are outside the Caddy root by layout.
- Critical gaps: no CSP or sandboxing strategy for potentially untrusted archived scripts, no explicit hidden-file deny matcher, and public Funnel exposure is mentioned but not gated by a concrete preflight checklist.

`spec-containerized.md`: 8/10

- Strengths: only the static site subtree is mounted into nginx, all operational state is private, nginx has `server_tokens off`, no directory listing, no open redirects, and Tailscale auth keys are runtime-only.
- Strengths: Tailscale state is persisted to avoid device churn, which reduces operational security mistakes.
- Critical gaps: `make clean` is destructive for data/logs/raw/recovered/reports, the Tailscale container includes elevated networking capabilities, and there is no CSP/sandbox plan for archived active content.

### Tailscale Integration Quality

`spec-minimalist.md`: 8/10

- Strengths: simple and correct `tailscale serve --bg --https=443 http://127.0.0.1:8080` path, status checks, reset, and Funnel alternative are documented.
- Strengths: explicitly notes custom-domain/DNS requirements for `pwned.ussyco.de`.
- Critical gaps: does not provide a persistent Tailscale service/unit setup or a preflight for Funnel/custom-domain capability.

`spec-pythonic-async.md`: 8/10

- Strengths: Tailscale Serve/Funnel commands are clear, reset is documented, and hostname requirements call out private DNS, split DNS, CNAME/custom-domain, and direct public HTTPS alternatives.
- Strengths: Caddy loopback mode fits Tailscale termination well.
- Critical gaps: no automated validation that `pwned.ussyco.de` resolves to the intended Tailscale path and no persistent service management beyond running Caddy manually.

`spec-containerized.md`: 8/10

- Strengths: Tailscale sidecar, persistent state volume, auth-key handling, Serve/Funnel commands, status commands, and DNS requirements are specified.
- Strengths: Compose gives repeatable local webserver plus Tailscale lifecycle.
- Critical gaps: sidecar config mixes `TS_SERVE_CONFIG` with manual `tailscale serve` commands, which may be operationally ambiguous; the sidecar needs careful authentication sequencing and elevated capabilities.

### Ease Of Incremental Updates When New Snapshots Exist

`spec-minimalist.md`: 6/10

- Strengths: CDX import, enqueue, and fetch scripts are idempotent; SQLite uniqueness prevents refetching completed jobs; retry state is durable.
- Strengths: rerunning discovery/enqueue/fetch/report is simple.
- Critical gaps: `UNIQUE(cdx_digest)` on `captures` can discard later URL/timestamp aliases and makes new snapshot review less rich; no explicit selection report for changed snapshots; no automated HTML cleanup/link rewrite stage; shell loop fetches one job at a time and will become slow as updates accumulate.

`spec-pythonic-async.md`: 9/10

- Strengths: strongest incremental model: query fingerprint/resume tracking, idempotent CLI stages, stale job recovery, durable retry schedule, selected captures, aliases, manifests, and report generation.
- Strengths: path mapping and dedup logic are designed to avoid overwriting different content and to record changes as aliases or collision-resolved files.
- Critical gaps: primary discovery still uses `collapse=digest`, so a separate uncollapsed or date-bounded update/audit mode may be needed to fully understand new aliases and changed URL histories.

`spec-containerized.md`: 7/10

- Strengths: durable bind-mounted SQLite, raw store, manifests, and stage reruns support resume; CDX page state and resume keys are persisted; Compose targets make repeated operations predictable.
- Strengths: raw content-addressed storage is useful for repeatable dedup and rebuilds.
- Critical gaps: `depends_on: service_completed_successfully` makes the default Compose flow more batch-oriented than continuously incremental; the CDX page schema keys by page number/resume key rather than a fully specified query/update window; update behavior when a new snapshot appears after a completed crawl is not as explicit as the Pythonic Async spec.

## Spec-By-Spec Summary

### Minimalist

Top strengths:

- Smallest operational footprint and easiest to audit manually.
- nginx loopback plus Tailscale Serve is simple, production-plausible, and aligned with the hosting research.
- Uses `id_` URLs, CDX `collapse=digest`, SQLite state, persisted retry backoff, and SHA256 dedup.
- Public serving defaults are mostly safe: no directory listing, no SPA fallback, MIME types included, dotfiles blocked.

Critical gaps:

- Cache headers are absent.
- Shell implementation is less robust for large or repeated updates than an async queue.
- `UNIQUE(cdx_digest)` sacrifices alias/history fidelity for simplicity.
- No HTML cleanup/link rewriting stage despite dedup research recommending parser-based cleanup.
- No health endpoint or production logging/access-control detail for public Funnel exposure.

### Pythonic Async

Top strengths:

- Best overall state model for production recovery and incremental reruns.
- Strong retry/backoff design with `Retry-After`, jitter, SQLite scheduling, stale job recovery, and short DB transactions.
- Strong dedup/path/manifest model, including raw and final SHA256, output aliases, collision handling, and conservative HTML cleanup.
- Caddy static hosting is clean, loopback-bound, compression-enabled, and Tailscale-compatible.

Critical gaps:

- Cache headers are not specified.
- No health endpoint or persistent service unit for Caddy.
- No explicit hidden-file deny matcher.
- Public exposure risk of recovered active content is not addressed with CSP/sandboxing guidance.
- Update mode could be clearer for discovering newly available snapshots after the original collapsed CDX pass completes.

### Containerized

Top strengths:

- Best operational reproducibility through Docker Compose, explicit volumes, isolated webserver, and Tailscale sidecar.
- Strong public-root isolation: nginx serves only `recovered/kyledurepos.com/site` read-only.
- Good nginx production defaults: no autoindex, no SPA fallback, `server_tokens off`, health check, MIME types, security headers.
- Raw content-addressed storage plus deduplicator stage gives a clean rebuild path.

Critical gaps:

- Cache headers and compression are absent.
- Tailscale sidecar setup is powerful but more complex and slightly ambiguous between serve config file and manual serve commands.
- Elevated sidecar capabilities and `/dev/net/tun` need operational care.
- Incremental update workflow is less explicit than Pythonic Async and more batch/stage oriented.
- No hidden-file deny rule inside nginx if hidden files enter the served tree.

## Production Hardening Recommendations

Recommended changes for all specs before real public Funnel exposure:

- Add explicit cache policy: short/no-cache for HTML during validation, long immutable cache for fingerprinted/static assets only when filenames are stable.
- Add compression where not already present.
- Add a `/healthz` endpoint or equivalent validation target.
- Add hidden-file deny handling for the served tree.
- Decide whether archived active JavaScript should be served as-is, restricted with CSP, or exposed only privately through the tailnet.
- Add a preflight checklist for `pwned.ussyco.de` DNS, Tailscale Serve/Funnel capability, certificate behavior, and expected private/public reachability.
- Add an explicit incremental-refresh mode that can detect new CDX captures after the first run and report changed/new candidate snapshots without losing alias history.
