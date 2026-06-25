# Containerized Recovery Spec

This implementation option isolates the recovery pipeline into containers for reproducible infrastructure.

## Shape

- One service for CDX inventory and selection.
- One worker service for downloads and dependency passes.
- One service or task for normalization and validation.
- One static serving service for local review.
- Optional sidecar or host integration for tailnet/public publication.

## Tradeoffs

Containers make dependency management and repeatable environments easier, but add volume, permissions, and networking complexity. Use this option when recoveries must run in CI, on shared infrastructure, or across multiple operators.
