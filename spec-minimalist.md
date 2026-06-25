# Minimalist Recovery Spec

This implementation option favors the fewest moving parts for small targets and experiments.

## Shape

- A TOML config file defines domain, aliases, CDX filters, paths, and publication policy.
- Small scripts perform CDX inventory, capture download, deduplication, normalization, and validation.
- Static output is served by Caddy, nginx, or another static server.

## Tradeoffs

This option is easy to inspect and run manually, but it has weaker resumability, retry scheduling, and report consistency than the Python async design. It is best for small static sites or proof-of-concept recoveries.
