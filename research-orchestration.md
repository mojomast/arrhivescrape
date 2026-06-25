# Orchestration Research

Recoveries need resumable state because CDX inventory, downloads, dependency passes, and validation can take multiple sessions. SQLite WAL, JSONL logs, and immutable run directories provide a simple durable model without requiring external services.

Recommended defaults are one CDX request at a time, at least `1.1` seconds between CDX starts, bounded content workers, exponential backoff with jitter, and idempotent stages that can resume from manifests and state tables.
