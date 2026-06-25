# Reliability Review

The Python async design is the preferred default because it gives the best control over CDX rate limits, retry queues, partial failure handling, binary validation, and resumable state. The minimalist design is acceptable for small targets. The containerized design is strongest when repeatable infrastructure matters more than setup simplicity.

Required reliability checks include CDX cursor persistence, retry logging, SHA256 verification, MIME mismatch detection, broken-link reporting, privacy blockers, and promotion only from validated staging output.
